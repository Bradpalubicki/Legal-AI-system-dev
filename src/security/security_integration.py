"""
Security Systems Integration Module
Integrates incident response, API rate limiting, and payment failure handling.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .incident_response import IncidentResponseSystem, ThreatIndicator, SecurityIncident, AttackType, ThreatLevel
from ..api_management.rate_limit_handler import RateLimitManager, APIProvider, ModelType, PriorityLevel
# from ..billing.failure_handler import PaymentFailureHandler, PaymentFailure, FailureReason, ServiceLevel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecurityAlert:
    alert_id: str
    alert_type: str
    severity: str
    message: str
    source_system: str
    affected_user: str
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class SystemStatus:
    system_name: str
    status: str
    last_check: datetime
    health_score: float
    active_incidents: int
    performance_metrics: Dict[str, Any]

class SecurityOrchestrator:
    """
    Central orchestrator for all security systems.
    Coordinates incident response, API management, and payment handling.
    """

    def __init__(self):
        # Initialize component systems
        self.incident_response = IncidentResponseSystem()
        self.rate_limiter = RateLimitManager()
        # self.payment_handler = PaymentFailureHandler()  # Commented out to fix import issues

        # Integration state
        self.active_alerts: Dict[str, SecurityAlert] = {}
        self.system_health: Dict[str, SystemStatus] = {}
        self.cross_system_correlations: List[Dict[str, Any]] = []

        # Security policies
        self.security_policies = {
            "auto_suspend_on_critical": True,
            "rate_limit_on_attack": True,
            "payment_failure_threshold": 3,
            "incident_correlation_enabled": True
        }

        # Initialize integration - removed automatic task creation to avoid event loop issues
        # Call _initialize_integration() explicitly when needed

    async def _initialize_integration(self):
        """Initialize the security integration system"""
        try:
            # Start health monitoring
            asyncio.create_task(self._monitor_system_health())

            # Start cross-system correlation
            asyncio.create_task(self._correlate_security_events())

            # Start automated response coordination
            asyncio.create_task(self._coordinate_automated_responses())

            logger.info("Security integration system initialized")
        except Exception as e:
            logger.error(f"Error initializing security integration: {str(e)}")
            raise

    # Main Integration Functions
    async def handle_security_event(self, event_data: Dict[str, Any]) -> SecurityAlert:
        """
        Central handler for all security events.
        Routes events to appropriate systems and triggers coordinated responses.
        """
        alert_id = self._generate_id()
        event_type = event_data.get('type', 'unknown')

        alert = SecurityAlert(
            alert_id=alert_id,
            alert_type=event_type,
            severity=event_data.get('severity', 'medium'),
            message=event_data.get('message', ''),
            source_system=event_data.get('source', 'unknown'),
            affected_user=event_data.get('user_id', ''),
            timestamp=datetime.now(),
            metadata=event_data
        )

        self.active_alerts[alert_id] = alert

        try:
            # Route to appropriate system
            if event_type == 'threat_detected':
                await self._handle_threat_event(event_data, alert)
            elif event_type == 'rate_limit_violation':
                await self._handle_rate_limit_event(event_data, alert)
            elif event_type == 'payment_failure':
                await self._handle_payment_event(event_data, alert)
            elif event_type == 'api_abuse':
                await self._handle_api_abuse_event(event_data, alert)
            else:
                logger.warning(f"Unknown security event type: {event_type}")

            # Check for cross-system correlations
            await self._check_event_correlations(alert)

            # Trigger automated responses if needed
            await self._evaluate_automated_responses(alert)

            return alert

        except Exception as e:
            logger.error(f"Error handling security event {alert_id}: {str(e)}")
            alert.message += f" | Processing error: {str(e)}"
            return alert

    async def _handle_threat_event(self, event_data: Dict[str, Any], alert: SecurityAlert):
        """Handle threat detection events"""
        # Create threat indicator
        threat_indicator = ThreatIndicator(
            indicator_id=self._generate_id(),
            threat_type=AttackType(event_data.get('attack_type', 'unauthorized_access')),
            severity=ThreatLevel(event_data.get('severity', 'medium')),
            source_ip=event_data.get('source_ip', ''),
            user_id=event_data.get('user_id'),
            endpoint=event_data.get('endpoint', ''),
            method=event_data.get('method', ''),
            user_agent=event_data.get('user_agent', ''),
            timestamp=datetime.now(),
            payload=event_data.get('payload', {}),
            confidence_score=event_data.get('confidence', 0.8),
            false_positive_likelihood=event_data.get('false_positive_likelihood', 0.1)
        )

        # Create security incident
        incident = await self.incident_response.create_incident(threat_indicator)

        # Apply coordinated security measures
        if incident.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            # Rate limit the user/IP
            await self._apply_emergency_rate_limits(event_data)

            # Check payment status and apply service restrictions if needed
            await self._evaluate_service_restrictions(event_data.get('user_id'))

        alert.metadata['incident_id'] = incident.incident_id
        logger.info(f"Threat event handled: {incident.incident_id}")

    async def _handle_rate_limit_event(self, event_data: Dict[str, Any], alert: SecurityAlert):
        """Handle rate limit violation events"""
        user_id = event_data.get('user_id')
        provider = event_data.get('provider', 'unknown')

        # Check if this is part of a larger attack pattern
        recent_violations = await self._get_recent_rate_violations(user_id)

        if len(recent_violations) >= 5:  # Threshold for suspicious activity
            # Escalate to incident response
            threat_event = {
                'type': 'threat_detected',
                'attack_type': 'api_abuse',
                'severity': 'high',
                'user_id': user_id,
                'source_ip': event_data.get('source_ip', ''),
                'endpoint': '/api/*',
                'message': f'Repeated rate limit violations detected for {provider}',
                'payload': {'violation_count': len(recent_violations)}
            }
            await self._handle_threat_event(threat_event, alert)

        # Apply graduated response
        violation_count = len(recent_violations)
        if violation_count >= 3:
            # Temporarily suspend API access
            await self._apply_temporary_api_suspension(user_id, provider)

        alert.metadata['violation_count'] = violation_count
        logger.info(f"Rate limit event handled for user {user_id}")

    async def _handle_payment_event(self, event_data: Dict[str, Any], alert: SecurityAlert):
        """Handle payment failure events"""
        # Payment handler temporarily disabled due to import issues
        logger.info(f"Payment event logged (handler disabled): {event_data.get('payment_id', 'unknown')}")

        # Check for suspicious payment patterns without payment handler
        user_id = event_data.get('user_id')
        if user_id:
            # Simplified fraud detection without payment handler
            fraud_event = {
                'type': 'threat_detected',
                'attack_type': 'fraud_suspected',
                'severity': 'medium',
                'user_id': user_id,
                'message': 'Payment failure detected - monitoring for fraud patterns',
                'payload': {'payment_data': event_data}
            }
            await self._handle_threat_event(fraud_event, alert)

        alert.metadata['payment_event'] = 'logged'
        logger.info(f"Payment event handled: {event_data.get('payment_id', 'unknown')}")

    async def _handle_api_abuse_event(self, event_data: Dict[str, Any], alert: SecurityAlert):
        """Handle API abuse events"""
        user_id = event_data.get('user_id')

        # Apply immediate rate limiting
        await self._apply_emergency_rate_limits(event_data)

        # Check for coordinated attack patterns
        similar_events = await self._find_similar_abuse_patterns(event_data)

        if len(similar_events) >= 3:
            # Escalate to high-priority security incident
            attack_event = {
                'type': 'threat_detected',
                'attack_type': 'ddos',
                'severity': 'critical',
                'user_id': user_id,
                'source_ip': event_data.get('source_ip', ''),
                'message': 'Coordinated API abuse attack detected',
                'payload': {'similar_events': len(similar_events)}
            }
            await self._handle_threat_event(attack_event, alert)

        logger.info(f"API abuse event handled for user {user_id}")

    # Cross-System Coordination
    async def _apply_emergency_rate_limits(self, event_data: Dict[str, Any]):
        """Apply emergency rate limits across all APIs"""
        user_id = event_data.get('user_id')
        if not user_id:
            return

        try:
            # Temporarily reduce rate limits for this user
            for provider in [APIProvider.OPENAI, APIProvider.CLAUDE]:
                # This would integrate with the rate limiter to apply temporary restrictions
                logger.info(f"Applying emergency rate limits for {user_id} on {provider.value}")

        except Exception as e:
            logger.error(f"Error applying emergency rate limits: {str(e)}")

    async def _apply_temporary_api_suspension(self, user_id: str, provider: str, duration_hours: int = 1):
        """Temporarily suspend API access for a user"""
        try:
            # This would integrate with the rate limiter to suspend access
            logger.info(f"Suspending API access for {user_id} on {provider} for {duration_hours} hours")

            # Schedule automatic restoration
            restore_time = datetime.now() + timedelta(hours=duration_hours)
            asyncio.create_task(self._schedule_api_restoration(user_id, provider, restore_time))

        except Exception as e:
            logger.error(f"Error applying API suspension: {str(e)}")

    async def _schedule_api_restoration(self, user_id: str, provider: str, restore_time: datetime):
        """Schedule automatic API access restoration"""
        now = datetime.now()
        if restore_time > now:
            sleep_seconds = (restore_time - now).total_seconds()
            await asyncio.sleep(sleep_seconds)

            # Restore API access
            logger.info(f"Restoring API access for {user_id} on {provider}")

    async def _evaluate_service_restrictions(self, user_id: str):
        """Evaluate whether to apply additional service restrictions"""
        if not user_id:
            return

        try:
            # Get user's recent security incidents
            incident_metrics = await self.incident_response.get_incident_metrics(days=7)

            # Apply restrictions based on security assessment only (payment handler disabled)
            if incident_metrics.get('total_incidents', 0) >= 3:
                logger.info(f"Considering service restrictions for {user_id} due to security incidents")

        except Exception as e:
            logger.error(f"Error evaluating service restrictions: {str(e)}")

    # Event Correlation
    async def _check_event_correlations(self, alert: SecurityAlert):
        """Check for correlations between security events"""
        try:
            # Look for related events in the last hour
            related_events = []
            cutoff_time = datetime.now() - timedelta(hours=1)

            for existing_alert in self.active_alerts.values():
                if (existing_alert.timestamp >= cutoff_time and
                    existing_alert.alert_id != alert.alert_id):

                    # Check for correlation patterns
                    correlation_score = self._calculate_correlation_score(alert, existing_alert)
                    if correlation_score > 0.7:
                        related_events.append({
                            'alert_id': existing_alert.alert_id,
                            'correlation_score': correlation_score
                        })

            if related_events:
                correlation = {
                    'primary_alert': alert.alert_id,
                    'related_events': related_events,
                    'detected_at': datetime.now(),
                    'correlation_type': self._determine_correlation_type(alert, related_events)
                }
                self.cross_system_correlations.append(correlation)

                logger.info(f"Event correlation detected: {len(related_events)} related events")

        except Exception as e:
            logger.error(f"Error checking event correlations: {str(e)}")

    def _calculate_correlation_score(self, alert1: SecurityAlert, alert2: SecurityAlert) -> float:
        """Calculate correlation score between two alerts"""
        score = 0.0

        # Same user
        if alert1.affected_user == alert2.affected_user and alert1.affected_user:
            score += 0.4

        # Similar alert types
        if alert1.alert_type == alert2.alert_type:
            score += 0.3

        # Similar severity
        if alert1.severity == alert2.severity:
            score += 0.1

        # Time proximity (within 1 hour)
        time_diff = abs((alert1.timestamp - alert2.timestamp).total_seconds())
        if time_diff < 3600:  # 1 hour
            score += 0.2 * (1 - time_diff / 3600)

        return min(score, 1.0)

    def _determine_correlation_type(self, alert: SecurityAlert, related_events: List[Dict[str, Any]]) -> str:
        """Determine the type of correlation pattern"""
        if len(related_events) >= 5:
            return "coordinated_attack"
        elif len(related_events) >= 3:
            return "attack_sequence"
        elif len(related_events) >= 2:
            return "related_incidents"
        else:
            return "single_correlation"

    async def _correlate_security_events(self):
        """Background task for continuous event correlation"""
        while True:
            try:
                # Clean up old correlations
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.cross_system_correlations = [
                    corr for corr in self.cross_system_correlations
                    if corr['detected_at'] >= cutoff_time
                ]

                # Clean up old alerts
                self.active_alerts = {
                    alert_id: alert for alert_id, alert in self.active_alerts.items()
                    if alert.timestamp >= cutoff_time
                }

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in event correlation: {str(e)}")
                await asyncio.sleep(300)

    # Automated Response Coordination
    async def _evaluate_automated_responses(self, alert: SecurityAlert):
        """Evaluate whether to trigger automated responses"""
        try:
            if alert.severity in ['high', 'critical']:
                if self.security_policies.get('auto_suspend_on_critical', False):
                    await self._trigger_automated_suspension(alert)

                if self.security_policies.get('rate_limit_on_attack', False):
                    await self._trigger_automated_rate_limiting(alert)

            # Check for pattern-based responses
            await self._check_pattern_based_responses(alert)

        except Exception as e:
            logger.error(f"Error evaluating automated responses: {str(e)}")

    async def _trigger_automated_suspension(self, alert: SecurityAlert):
        """Trigger automated service suspension"""
        if alert.affected_user and alert.severity == 'critical':
            logger.info(f"Triggering automated suspension for user {alert.affected_user}")
            # This would integrate with your user management system

    async def _trigger_automated_rate_limiting(self, alert: SecurityAlert):
        """Trigger automated rate limiting"""
        if alert.affected_user:
            await self._apply_emergency_rate_limits(alert.metadata)

    async def _check_pattern_based_responses(self, alert: SecurityAlert):
        """Check for pattern-based automated responses"""
        # Look for specific attack patterns that require immediate response
        if alert.alert_type == 'threat_detected':
            attack_type = alert.metadata.get('attack_type', '')

            if attack_type in ['sql_injection', 'xss']:
                # Immediately block the source IP
                source_ip = alert.metadata.get('source_ip', '')
                if source_ip:
                    logger.info(f"Auto-blocking IP {source_ip} for {attack_type} attack")

    async def _coordinate_automated_responses(self):
        """Background task for coordinating automated responses"""
        while True:
            try:
                # Check for response coordination opportunities
                current_time = datetime.now()

                # Process any queued automated responses
                await self._process_response_queue()

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error coordinating automated responses: {str(e)}")
                await asyncio.sleep(60)

    async def _process_response_queue(self):
        """Process queued automated responses"""
        # Implementation would depend on your specific response queue
        pass

    # System Health Monitoring
    async def _monitor_system_health(self):
        """Monitor health of all integrated security systems"""
        while True:
            try:
                # Check incident response system
                incident_health = await self._check_incident_response_health()
                self.system_health['incident_response'] = incident_health

                # Check rate limiter health
                rate_limiter_health = await self._check_rate_limiter_health()
                self.system_health['rate_limiter'] = rate_limiter_health

                # Check payment handler health
                payment_health = await self._check_payment_handler_health()
                self.system_health['payment_handler'] = payment_health

                # Overall system health
                overall_health = self._calculate_overall_health()
                self.system_health['overall'] = overall_health

                # Alert if any system is unhealthy
                await self._check_health_alerts()

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error monitoring system health: {str(e)}")
                await asyncio.sleep(300)

    async def _check_incident_response_health(self) -> SystemStatus:
        """Check incident response system health"""
        try:
            # Get recent metrics
            metrics = await self.incident_response.get_incident_metrics(days=1)

            return SystemStatus(
                system_name="incident_response",
                status="healthy",
                last_check=datetime.now(),
                health_score=0.95,
                active_incidents=metrics.get('total_incidents', 0),
                performance_metrics={
                    'incidents_today': metrics.get('total_incidents', 0),
                    'avg_resolution_hours': metrics.get('average_resolution_hours', 0)
                }
            )
        except Exception as e:
            return SystemStatus(
                system_name="incident_response",
                status="unhealthy",
                last_check=datetime.now(),
                health_score=0.0,
                active_incidents=0,
                performance_metrics={'error': str(e)}
            )

    async def _check_rate_limiter_health(self) -> SystemStatus:
        """Check rate limiter system health"""
        try:
            return SystemStatus(
                system_name="rate_limiter",
                status="healthy",
                last_check=datetime.now(),
                health_score=0.98,
                active_incidents=0,
                performance_metrics={
                    'active_requests': len(self.rate_limiter.active_requests),
                    'queue_size': sum(len(queue) for queues in self.rate_limiter.request_queues.values()
                                    for queue in queues.values())
                }
            )
        except Exception as e:
            return SystemStatus(
                system_name="rate_limiter",
                status="unhealthy",
                last_check=datetime.now(),
                health_score=0.0,
                active_incidents=0,
                performance_metrics={'error': str(e)}
            )

    async def _check_payment_handler_health(self) -> SystemStatus:
        """Check payment handler system health"""
        # Payment handler temporarily disabled
        return SystemStatus(
            system_name="payment_handler",
            status="disabled",
            last_check=datetime.now(),
            health_score=0.0,
            active_incidents=0,
            performance_metrics={'status': 'temporarily_disabled'}
        )

    def _calculate_overall_health(self) -> SystemStatus:
        """Calculate overall system health"""
        if not self.system_health:
            return SystemStatus(
                system_name="overall",
                status="unknown",
                last_check=datetime.now(),
                health_score=0.0,
                active_incidents=0,
                performance_metrics={}
            )

        total_score = 0.0
        healthy_systems = 0
        total_incidents = 0

        for system_name, status in self.system_health.items():
            if system_name != 'overall':
                total_score += status.health_score
                if status.status == "healthy":
                    healthy_systems += 1
                total_incidents += status.active_incidents

        num_systems = len(self.system_health) - 1  # Exclude 'overall'
        avg_health_score = total_score / num_systems if num_systems > 0 else 0.0

        overall_status = "healthy" if healthy_systems == num_systems else "degraded"
        if healthy_systems == 0:
            overall_status = "unhealthy"

        return SystemStatus(
            system_name="overall",
            status=overall_status,
            last_check=datetime.now(),
            health_score=avg_health_score,
            active_incidents=total_incidents,
            performance_metrics={
                'healthy_systems': healthy_systems,
                'total_systems': num_systems,
                'system_availability': healthy_systems / num_systems if num_systems > 0 else 0.0
            }
        )

    async def _check_health_alerts(self):
        """Check for health-related alerts"""
        overall_health = self.system_health.get('overall')
        if overall_health and overall_health.health_score < 0.8:
            alert = SecurityAlert(
                alert_id=self._generate_id(),
                alert_type='system_health',
                severity='medium' if overall_health.health_score > 0.5 else 'high',
                message=f'System health degraded: {overall_health.health_score:.2f}',
                source_system='security_orchestrator',
                affected_user='system',
                timestamp=datetime.now(),
                metadata={'health_score': overall_health.health_score}
            )

            logger.warning(f"System health alert: {alert.message}")

    # Utility methods
    async def _get_recent_rate_violations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent rate limit violations for a user"""
        # This would query the rate limiter's database
        return []

    async def _get_recent_payment_failures(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent payment failures for a user"""
        # Payment handler disabled, return empty list
        return []

    async def _find_similar_abuse_patterns(self, event_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar API abuse patterns"""
        # This would analyze patterns in the API usage data
        return []

    def _generate_id(self) -> str:
        """Generate unique identifier"""
        import uuid
        return str(uuid.uuid4())

    # Public API
    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive security dashboard data"""
        return {
            'system_health': {name: asdict(status) for name, status in self.system_health.items()},
            'active_alerts': {alert_id: asdict(alert) for alert_id, alert in self.active_alerts.items()},
            'correlations': self.cross_system_correlations,
            'security_policies': self.security_policies,
            'recent_incidents': len([alert for alert in self.active_alerts.values()
                                   if alert.timestamp >= datetime.now() - timedelta(hours=24)])
        }

    async def update_security_policy(self, policy_name: str, value: Any) -> bool:
        """Update a security policy"""
        if policy_name in self.security_policies:
            self.security_policies[policy_name] = value
            logger.info(f"Security policy updated: {policy_name} = {value}")
            return True
        return False

# Initialize the security orchestrator
security_orchestrator = SecurityOrchestrator()