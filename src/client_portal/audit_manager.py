"""
Client Portal Audit Manager

Handles comprehensive audit logging for client portal activities
including security events, data access, and compliance tracking.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
import uuid
import json

from .models import ClientAuditLog, ClientUser, AuditAction


class ClientAuditManager:
    """Manages comprehensive audit logging for client portal."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
        # Audit settings
        self.retention_days = 365 * 7  # 7 years for legal compliance
        self.batch_size = 1000
        
        # Sensitive actions that require detailed logging
        self.sensitive_actions = {
            AuditAction.LOGIN,
            AuditAction.LOGOUT,
            AuditAction.DOCUMENT_VIEW,
            AuditAction.DOCUMENT_DOWNLOAD,
            AuditAction.PROFILE_UPDATED
        }
    
    def log_event(
        self,
        user_id: Optional[int],
        action: AuditAction,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        action_details: Optional[Dict[str, Any]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log an audit event."""
        try:
            audit_log = ClientAuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                success=success,
                error_message=error_message,
                action_details=action_details or {},
                old_values=old_values or {},
                new_values=new_values or {}
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
            return True
            
        except Exception as e:
            # Audit logging should never fail the main operation
            print(f"Audit logging failed: {str(e)}")
            try:
                self.db.rollback()
            except:
                pass
            return False
    
    async def get_user_audit_logs(
        self,
        user_id: int,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        success_only: Optional[bool] = None,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get audit logs for a specific user."""
        try:
            # Validate user exists
            user = self.db.query(ClientUser).filter(ClientUser.id == user_id).first()
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Build query
            query = self.db.query(ClientAuditLog).filter(ClientAuditLog.user_id == user_id)
            
            # Apply filters
            if action:
                query = query.filter(ClientAuditLog.action == action)
            
            if resource_type:
                query = query.filter(ClientAuditLog.resource_type == resource_type)
            
            if date_from:
                query = query.filter(ClientAuditLog.timestamp >= date_from)
            
            if date_to:
                query = query.filter(ClientAuditLog.timestamp <= date_to)
            
            if success_only is not None:
                query = query.filter(ClientAuditLog.success == success_only)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            logs = query.order_by(desc(ClientAuditLog.timestamp)).offset(
                (page - 1) * limit
            ).limit(limit).all()
            
            return {
                'success': True,
                'audit_logs': [self._audit_log_to_dict(log) for log in logs],
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'pages': (total_count + limit - 1) // limit
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve audit logs: {str(e)}'}
    
    async def get_security_events(
        self,
        user_id: Optional[int] = None,
        hours_back: int = 24,
        include_failed_only: bool = False
    ) -> Dict[str, Any]:
        """Get recent security events for monitoring."""
        try:
            # Calculate time range
            start_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            # Build query for security-relevant events
            security_actions = [
                AuditAction.LOGIN,
                AuditAction.LOGOUT,
                AuditAction.PROFILE_UPDATED
            ]
            
            query = self.db.query(ClientAuditLog).filter(
                and_(
                    ClientAuditLog.timestamp >= start_time,
                    ClientAuditLog.action.in_(security_actions)
                )
            )
            
            if user_id:
                query = query.filter(ClientAuditLog.user_id == user_id)
            
            if include_failed_only:
                query = query.filter(ClientAuditLog.success == False)
            
            # Get events
            events = query.order_by(desc(ClientAuditLog.timestamp)).all()
            
            # Analyze patterns
            failed_logins = [e for e in events if e.action == AuditAction.LOGIN and not e.success]
            successful_logins = [e for e in events if e.action == AuditAction.LOGIN and e.success]
            profile_updates = [e for e in events if e.action == AuditAction.PROFILE_UPDATED]
            
            # Identify suspicious patterns
            suspicious_ips = {}
            for event in failed_logins:
                ip = event.ip_address
                if ip:
                    suspicious_ips[ip] = suspicious_ips.get(ip, 0) + 1
            
            # Find IPs with multiple failed attempts
            high_risk_ips = {ip: count for ip, count in suspicious_ips.items() if count >= 5}
            
            return {
                'success': True,
                'time_range': {
                    'from': start_time.isoformat(),
                    'to': datetime.utcnow().isoformat(),
                    'hours': hours_back
                },
                'summary': {
                    'total_events': len(events),
                    'failed_logins': len(failed_logins),
                    'successful_logins': len(successful_logins),
                    'profile_updates': len(profile_updates),
                    'suspicious_ips': len(high_risk_ips)
                },
                'events': [self._audit_log_to_dict(log, include_sensitive=True) for log in events],
                'high_risk_ips': high_risk_ips
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve security events: {str(e)}'}
    
    async def get_access_statistics(
        self,
        user_id: int,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get access statistics for a user."""
        try:
            # Calculate time range
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Get user's audit logs in the time range
            logs = self.db.query(ClientAuditLog).filter(
                and_(
                    ClientAuditLog.user_id == user_id,
                    ClientAuditLog.timestamp >= start_date
                )
            ).all()
            
            # Count by action
            action_counts = {}
            for log in logs:
                action_name = log.action.value if log.action else 'unknown'
                action_counts[action_name] = action_counts.get(action_name, 0) + 1
            
            # Count by resource type
            resource_counts = {}
            for log in logs:
                if log.resource_type:
                    resource_counts[log.resource_type] = resource_counts.get(log.resource_type, 0) + 1
            
            # Daily activity
            daily_activity = {}
            for log in logs:
                day_key = log.timestamp.date().isoformat() if log.timestamp else 'unknown'
                daily_activity[day_key] = daily_activity.get(day_key, 0) + 1
            
            # Login statistics
            login_logs = [log for log in logs if log.action == AuditAction.LOGIN]
            successful_logins = len([log for log in login_logs if log.success])
            failed_logins = len([log for log in login_logs if not log.success])
            
            # IP addresses used
            ip_addresses = list(set(log.ip_address for log in logs if log.ip_address))
            
            # Most active hours
            hour_activity = {}
            for log in logs:
                if log.timestamp:
                    hour = log.timestamp.hour
                    hour_activity[hour] = hour_activity.get(hour, 0) + 1
            
            # Most active hour
            most_active_hour = max(hour_activity.keys(), key=lambda h: hour_activity[h]) if hour_activity else None
            
            return {
                'success': True,
                'time_range': {
                    'from': start_date.isoformat(),
                    'to': datetime.utcnow().isoformat(),
                    'days': days_back
                },
                'statistics': {
                    'total_activities': len(logs),
                    'by_action': action_counts,
                    'by_resource_type': resource_counts,
                    'daily_activity': daily_activity,
                    'login_statistics': {
                        'successful_logins': successful_logins,
                        'failed_logins': failed_logins,
                        'unique_ips': len(ip_addresses),
                        'ip_addresses': ip_addresses
                    },
                    'activity_patterns': {
                        'hourly_activity': hour_activity,
                        'most_active_hour': most_active_hour
                    }
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to generate access statistics: {str(e)}'}
    
    async def search_audit_logs(
        self,
        search_query: str,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search audit logs by various criteria."""
        try:
            # Build base query
            query = self.db.query(ClientAuditLog)
            
            if user_id:
                query = query.filter(ClientAuditLog.user_id == user_id)
            
            if date_from:
                query = query.filter(ClientAuditLog.timestamp >= date_from)
            
            if date_to:
                query = query.filter(ClientAuditLog.timestamp <= date_to)
            
            # Text search across multiple fields
            search_terms = search_query.lower().split()
            for term in search_terms:
                search_pattern = f"%{term}%"
                query = query.filter(
                    or_(
                        ClientAuditLog.resource_type.ilike(search_pattern),
                        ClientAuditLog.resource_id.ilike(search_pattern),
                        ClientAuditLog.ip_address.ilike(search_pattern),
                        ClientAuditLog.error_message.ilike(search_pattern)
                    )
                )
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            logs = query.order_by(desc(ClientAuditLog.timestamp)).offset(
                (page - 1) * limit
            ).limit(limit).all()
            
            return {
                'success': True,
                'search_query': search_query,
                'audit_logs': [self._audit_log_to_dict(log) for log in logs],
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total_count,
                    'pages': (total_count + limit - 1) // limit
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Search failed: {str(e)}'}
    
    async def export_audit_logs(
        self,
        user_id: int,
        date_from: datetime,
        date_to: datetime,
        format_type: str = 'json'
    ) -> Dict[str, Any]:
        """Export audit logs for compliance or analysis."""
        try:
            # Validate user
            user = self.db.query(ClientUser).filter(ClientUser.id == user_id).first()
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Get logs in date range
            logs = self.db.query(ClientAuditLog).filter(
                and_(
                    ClientAuditLog.user_id == user_id,
                    ClientAuditLog.timestamp >= date_from,
                    ClientAuditLog.timestamp <= date_to
                )
            ).order_by(ClientAuditLog.timestamp).all()
            
            # Convert to export format
            export_data = {
                'export_info': {
                    'user_id': user_id,
                    'user_email': user.email,
                    'user_name': f"{user.first_name} {user.last_name}",
                    'date_range': {
                        'from': date_from.isoformat(),
                        'to': date_to.isoformat()
                    },
                    'exported_at': datetime.utcnow().isoformat(),
                    'total_records': len(logs)
                },
                'audit_logs': [self._audit_log_to_dict(log, include_sensitive=True) for log in logs]
            }
            
            if format_type.lower() == 'json':
                export_content = json.dumps(export_data, indent=2, default=str)
                content_type = 'application/json'
                file_extension = 'json'
            else:
                # CSV format
                import csv
                import io
                
                output = io.StringIO()
                if logs:
                    # Use first log to determine fieldnames
                    fieldnames = list(self._audit_log_to_dict(logs[0], include_sensitive=True).keys())
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    for log in logs:
                        writer.writerow(self._audit_log_to_dict(log, include_sensitive=True))
                
                export_content = output.getvalue()
                content_type = 'text/csv'
                file_extension = 'csv'
            
            filename = f"audit_logs_user_{user_id}_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}.{file_extension}"
            
            return {
                'success': True,
                'export_content': export_content,
                'content_type': content_type,
                'filename': filename,
                'record_count': len(logs)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Export failed: {str(e)}'}
    
    async def cleanup_old_logs(self, days_to_keep: Optional[int] = None) -> Dict[str, Any]:
        """Clean up old audit logs based on retention policy."""
        try:
            retention_days = days_to_keep or self.retention_days
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Count logs to be deleted
            old_logs_count = self.db.query(ClientAuditLog).filter(
                ClientAuditLog.timestamp < cutoff_date
            ).count()
            
            # Delete old logs in batches
            deleted_count = 0
            while True:
                batch = self.db.query(ClientAuditLog).filter(
                    ClientAuditLog.timestamp < cutoff_date
                ).limit(self.batch_size).all()
                
                if not batch:
                    break
                
                for log in batch:
                    self.db.delete(log)
                
                deleted_count += len(batch)
                self.db.commit()
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'retention_days': retention_days,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'Cleanup failed: {str(e)}'}
    
    async def generate_compliance_report(
        self,
        user_id: int,
        report_type: str = 'gdpr'  # 'gdpr', 'ccpa', 'general'
    ) -> Dict[str, Any]:
        """Generate compliance report for data access."""
        try:
            # Get user information
            user = self.db.query(ClientUser).filter(ClientUser.id == user_id).first()
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Get all audit logs for user
            logs = self.db.query(ClientAuditLog).filter(
                ClientAuditLog.user_id == user_id
            ).order_by(desc(ClientAuditLog.timestamp)).all()
            
            # Categorize data access
            data_access_summary = {
                'personal_data_access': 0,
                'document_access': 0,
                'profile_modifications': 0,
                'login_activities': 0,
                'total_activities': len(logs)
            }
            
            for log in logs:
                if log.action == AuditAction.PROFILE_UPDATED:
                    data_access_summary['profile_modifications'] += 1
                elif log.action == AuditAction.DOCUMENT_VIEW:
                    data_access_summary['document_access'] += 1
                elif log.action == AuditAction.LOGIN:
                    data_access_summary['login_activities'] += 1
            
            # Data retention information
            oldest_log = logs[-1] if logs else None
            data_retention_info = {
                'oldest_record': oldest_log.timestamp.isoformat() if oldest_log else None,
                'retention_period_days': self.retention_days,
                'data_categories': [
                    'Authentication logs',
                    'Document access logs', 
                    'Profile modification logs',
                    'System interaction logs'
                ]
            }
            
            # Generate report based on type
            if report_type.lower() == 'gdpr':
                report_content = self._generate_gdpr_report(user, data_access_summary, data_retention_info, logs)
            elif report_type.lower() == 'ccpa':
                report_content = self._generate_ccpa_report(user, data_access_summary, data_retention_info, logs)
            else:
                report_content = self._generate_general_report(user, data_access_summary, data_retention_info, logs)
            
            return {
                'success': True,
                'report_type': report_type.upper(),
                'user_info': {
                    'user_id': user.id,
                    'email': user.email,
                    'name': f"{user.first_name} {user.last_name}"
                },
                'report_content': report_content,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Compliance report generation failed: {str(e)}'}
    
    def _audit_log_to_dict(self, log: ClientAuditLog, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert audit log to dictionary representation."""
        base_dict = {
            'log_id': log.log_id,
            'action': log.action.value if log.action else None,
            'resource_type': log.resource_type,
            'resource_id': log.resource_id,
            'success': log.success,
            'timestamp': log.timestamp.isoformat() if log.timestamp else None,
            'action_details': log.action_details
        }
        
        if include_sensitive:
            base_dict.update({
                'user_id': log.user_id,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'session_id': log.session_id,
                'error_message': log.error_message,
                'old_values': log.old_values,
                'new_values': log.new_values
            })
        
        return base_dict
    
    def _generate_gdpr_report(self, user, access_summary, retention_info, logs):
        """Generate GDPR compliance report."""
        return {
            'regulation': 'General Data Protection Regulation (GDPR)',
            'subject_rights': {
                'right_to_access': 'This report provides access to all personal data processed',
                'right_to_rectification': 'Profile modifications logged and tracked',
                'right_to_erasure': 'Data retention policy enforced automatically',
                'right_to_portability': 'Data can be exported in machine-readable format'
            },
            'data_processing_basis': 'Legitimate interest for legal service provision',
            'data_categories_processed': retention_info['data_categories'],
            'retention_period': f"{retention_info['retention_period_days']} days",
            'access_summary': access_summary,
            'data_transfers': 'No international data transfers',
            'automated_decision_making': 'No automated decision-making processes'
        }
    
    def _generate_ccpa_report(self, user, access_summary, retention_info, logs):
        """Generate CCPA compliance report."""
        return {
            'regulation': 'California Consumer Privacy Act (CCPA)',
            'consumer_rights': {
                'right_to_know': 'This report discloses personal information collected and used',
                'right_to_delete': 'Data deletion available upon request',
                'right_to_opt_out': 'No sale of personal information occurs'
            },
            'categories_collected': [
                'Identifiers (email, name)',
                'Professional information',
                'Internet activity (access logs)'
            ],
            'business_purposes': [
                'Providing legal services',
                'Communication with clients',
                'Compliance and security'
            ],
            'access_summary': access_summary,
            'data_retention': f"{retention_info['retention_period_days']} days",
            'third_party_sharing': 'No sharing with third parties for marketing'
        }
    
    def _generate_general_report(self, user, access_summary, retention_info, logs):
        """Generate general compliance report."""
        return {
            'data_subject': f"{user.first_name} {user.last_name}",
            'data_controller': 'Legal AI Portal',
            'data_processing_summary': access_summary,
            'data_retention': retention_info,
            'audit_trail_summary': {
                'total_logged_activities': len(logs),
                'date_range': {
                    'oldest': logs[-1].timestamp.isoformat() if logs else None,
                    'newest': logs[0].timestamp.isoformat() if logs else None
                }
            },
            'data_security': 'All access logged and monitored for security compliance'
        }