# =============================================================================
# Legal AI System - SLA Monitoring and Compliance Tracking
# =============================================================================
# Advanced SLA monitoring system with legal compliance focus,
# client-specific SLAs, and automated compliance reporting
# =============================================================================

from typing import Optional, Dict, Any, List, Tuple, Set
from datetime import datetime, timezone, timedelta
from pathlib import Path
import asyncio
import logging
import json
import uuid
import statistics
from dataclasses import dataclass, field, asdict
from enum import Enum
import calendar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, desc, func, text
from sqlalchemy.sql import extract

from .models import (
    SLADefinition, SLAMeasurement, MetricDefinition, MetricSample, AggregatedMetric,
    SLAStatus, SLADefinitionCreate
)
from ..audit.service import AuditLoggingService, AuditEventCreate
from ..audit.models import AuditEventType, AuditSeverity, AuditStatus
from ..core.config import get_settings

logger = logging.getLogger(__name__)

# =============================================================================
# SLA ENUMS AND MODELS
# =============================================================================

class SLAMetricType(Enum):
    """SLA metric types."""
    AVAILABILITY = "availability"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    UPTIME = "uptime"
    LEGAL_COMPLIANCE = "legal_compliance"

class SLAComplianceStatus(Enum):
    """SLA compliance status."""
    COMPLIANT = "compliant"
    AT_RISK = "at_risk"
    BREACHED = "breached"
    UNKNOWN = "unknown"

class ClientTier(Enum):
    """Client service tiers."""
    ENTERPRISE = "enterprise"
    PREMIUM = "premium"
    STANDARD = "standard"
    BASIC = "basic"

@dataclass
class SLATarget:
    """SLA target configuration."""
    metric_type: SLAMetricType
    target_value: float
    measurement_unit: str
    measurement_period: str  # hourly, daily, monthly
    tolerance_percentage: float = 5.0
    grace_period_minutes: int = 15

@dataclass
class SLABreach:
    """SLA breach event."""
    sla_id: str
    metric_type: SLAMetricType
    breach_time: datetime
    target_value: float
    actual_value: float
    breach_duration_minutes: int
    impact_level: str
    client_notification_required: bool
    resolution_time: Optional[datetime] = None

@dataclass
class ClientSLAReport:
    """Client-specific SLA report."""
    client_id: str
    client_name: str
    client_tier: ClientTier
    report_period_start: datetime
    report_period_end: datetime
    sla_metrics: Dict[str, Any]
    compliance_summary: Dict[str, Any]
    breach_summary: Dict[str, Any]
    recommendations: List[str]

@dataclass
class LegalComplianceMetrics:
    """Legal compliance specific metrics."""
    data_processing_sla: float  # Time to process legal documents
    audit_trail_completeness: float  # Percentage of complete audit trails
    privacy_compliance_score: float  # GDPR/CCPA compliance score
    backup_recovery_time: float  # Disaster recovery time
    security_incident_response_time: float  # Security response time

# =============================================================================
# SLA CALCULATOR
# =============================================================================

class SLACalculator:
    """Calculates SLA metrics from raw performance data."""
    
    def __init__(self):
        pass
    
    def calculate_availability(
        self,
        uptime_seconds: float,
        total_seconds: float
    ) -> float:
        """Calculate availability percentage."""
        if total_seconds <= 0:
            return 0.0
        return (uptime_seconds / total_seconds) * 100.0
    
    def calculate_response_time_percentile(
        self,
        response_times: List[float],
        percentile: int = 95
    ) -> float:
        """Calculate response time percentile."""
        if not response_times:
            return 0.0
        
        sorted_times = sorted(response_times)
        index = int((percentile / 100.0) * (len(sorted_times) - 1))
        return sorted_times[index]
    
    def calculate_error_rate(
        self,
        total_requests: int,
        error_requests: int
    ) -> float:
        """Calculate error rate percentage."""
        if total_requests <= 0:
            return 0.0
        return (error_requests / total_requests) * 100.0
    
    def calculate_throughput(
        self,
        total_requests: int,
        time_period_seconds: float
    ) -> float:
        """Calculate throughput (requests per second)."""
        if time_period_seconds <= 0:
            return 0.0
        return total_requests / time_period_seconds
    
    def calculate_legal_compliance_score(
        self,
        audit_completeness: float,
        privacy_compliance: float,
        security_compliance: float,
        backup_compliance: float
    ) -> float:
        """Calculate overall legal compliance score."""
        weights = {
            'audit': 0.3,
            'privacy': 0.3,
            'security': 0.3,
            'backup': 0.1
        }
        
        weighted_score = (
            audit_completeness * weights['audit'] +
            privacy_compliance * weights['privacy'] +
            security_compliance * weights['security'] +
            backup_compliance * weights['backup']
        )
        
        return min(weighted_score, 100.0)

# =============================================================================
# SLA MEASUREMENT ENGINE
# =============================================================================

class SLAMeasurementEngine:
    """Measures SLA performance against targets."""
    
    def __init__(self):
        self.calculator = SLACalculator()
        
    async def measure_sla_performance(
        self,
        db: AsyncSession,
        sla_definition: SLADefinition,
        measurement_start: datetime,
        measurement_end: datetime
    ) -> SLAMeasurement:
        """Measure SLA performance for a specific time period."""
        try:
            # Calculate measurement period duration
            period_seconds = (measurement_end - measurement_start).total_seconds()
            
            # Initialize measurement
            measurement = SLAMeasurement(
                sla_definition_id=sla_definition.id,
                measurement_start=measurement_start,
                measurement_end=measurement_end
            )
            
            # Calculate availability if target exists
            if sla_definition.availability_target:
                availability = await self._measure_availability(
                    db, sla_definition.service_name, measurement_start, measurement_end
                )
                measurement.availability_percentage = availability
                measurement.availability_status = self._determine_sla_status(
                    availability, sla_definition.availability_target
                )
            
            # Calculate response time if target exists
            if sla_definition.response_time_target_ms:
                response_time = await self._measure_response_time(
                    db, sla_definition.service_name, measurement_start, measurement_end
                )
                measurement.avg_response_time_ms = response_time['avg']
                measurement.p95_response_time_ms = response_time['p95']
                measurement.p99_response_time_ms = response_time['p99']
                measurement.response_time_status = self._determine_sla_status(
                    response_time['p95'], sla_definition.response_time_target_ms, inverse=True
                )
            
            # Calculate throughput if target exists
            if sla_definition.throughput_target_rps:
                throughput = await self._measure_throughput(
                    db, sla_definition.service_name, measurement_start, measurement_end
                )
                measurement.throughput_rps = throughput
                measurement.throughput_status = self._determine_sla_status(
                    throughput, sla_definition.throughput_target_rps
                )
            
            # Calculate error rate if target exists
            if sla_definition.error_rate_target:
                error_rate = await self._measure_error_rate(
                    db, sla_definition.service_name, measurement_start, measurement_end
                )
                measurement.error_rate_percentage = error_rate
                measurement.error_rate_status = self._determine_sla_status(
                    error_rate, sla_definition.error_rate_target, inverse=True
                )
            
            # Determine overall status
            measurement.overall_status = self._determine_overall_sla_status([
                measurement.availability_status,
                measurement.response_time_status,
                measurement.throughput_status,
                measurement.error_rate_status
            ])
            
            # Calculate data quality metrics
            measurement.sample_count = await self._count_samples(
                db, sla_definition.service_name, measurement_start, measurement_end
            )
            measurement.data_completeness_percentage = min(
                (measurement.sample_count / max(period_seconds / 300, 1)) * 100, 100
            )  # Expecting samples every 5 minutes
            
            # Determine measurement confidence
            if measurement.data_completeness_percentage >= 90:
                measurement.measurement_confidence = "high"
            elif measurement.data_completeness_percentage >= 70:
                measurement.measurement_confidence = "medium"
            else:
                measurement.measurement_confidence = "low"
            
            return measurement
            
        except Exception as e:
            logger.error(f"SLA measurement failed: {e}")
            raise
    
    async def _measure_availability(
        self,
        db: AsyncSession,
        service_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Measure service availability."""
        try:
            # Query for health check metrics or uptime indicators
            # This would typically look at metrics like system_health_status
            # For now, using a simplified approach based on error rates
            
            # Get total requests
            total_requests = await self._get_metric_sum(
                db, "http_requests_total", start_time, end_time, 
                {"service": service_name}
            )
            
            # Get error requests (5xx status codes)
            error_requests = await self._get_metric_sum(
                db, "http_requests_total", start_time, end_time,
                {"service": service_name, "status": "5"}  # 5xx errors
            )
            
            if total_requests > 0:
                success_rate = ((total_requests - error_requests) / total_requests) * 100
                return max(success_rate, 0.0)
            
            return 100.0  # Assume available if no requests
            
        except Exception as e:
            logger.error(f"Availability measurement failed: {e}")
            return 0.0
    
    async def _measure_response_time(
        self,
        db: AsyncSession,
        service_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, float]:
        """Measure response time metrics."""
        try:
            # Get aggregated response time data
            result = await db.execute(
                select(
                    func.avg(AggregatedMetric.avg_value).label('avg'),
                    func.avg(AggregatedMetric.percentile_95).label('p95'),
                    func.avg(AggregatedMetric.percentile_99).label('p99')
                )
                .join(MetricDefinition)
                .where(and_(
                    MetricDefinition.name == "http_request_duration_seconds",
                    AggregatedMetric.window_start >= start_time,
                    AggregatedMetric.window_end <= end_time
                ))
            )
            
            row = result.first()
            if row and row.avg:
                return {
                    'avg': float(row.avg) * 1000,  # Convert to milliseconds
                    'p95': float(row.p95 or 0) * 1000,
                    'p99': float(row.p99 or 0) * 1000
                }
            
            return {'avg': 0.0, 'p95': 0.0, 'p99': 0.0}
            
        except Exception as e:
            logger.error(f"Response time measurement failed: {e}")
            return {'avg': 0.0, 'p95': 0.0, 'p99': 0.0}
    
    async def _measure_throughput(
        self,
        db: AsyncSession,
        service_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Measure service throughput."""
        try:
            # Get total requests in time period
            total_requests = await self._get_metric_sum(
                db, "http_requests_total", start_time, end_time,
                {"service": service_name}
            )
            
            period_seconds = (end_time - start_time).total_seconds()
            if period_seconds > 0:
                return total_requests / period_seconds
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Throughput measurement failed: {e}")
            return 0.0
    
    async def _measure_error_rate(
        self,
        db: AsyncSession,
        service_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Measure service error rate."""
        try:
            # Get total requests
            total_requests = await self._get_metric_sum(
                db, "http_requests_total", start_time, end_time,
                {"service": service_name}
            )
            
            # Get error requests (4xx and 5xx status codes)
            error_requests = await self._get_metric_sum(
                db, "http_requests_total", start_time, end_time,
                {"service": service_name}  # Would need status code filtering
            )
            
            return self.calculator.calculate_error_rate(total_requests, error_requests)
            
        except Exception as e:
            logger.error(f"Error rate measurement failed: {e}")
            return 0.0
    
    async def _get_metric_sum(
        self,
        db: AsyncSession,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        labels: Optional[Dict[str, str]] = None
    ) -> float:
        """Get sum of metric values over time period."""
        try:
            query = select(func.sum(AggregatedMetric.sum_value)) \
                .join(MetricDefinition) \
                .where(and_(
                    MetricDefinition.name == metric_name,
                    AggregatedMetric.window_start >= start_time,
                    AggregatedMetric.window_end <= end_time
                ))
            
            # Add label filters if provided
            if labels:
                for key, value in labels.items():
                    query = query.where(AggregatedMetric.labels[key] == value)
            
            result = await db.execute(query)
            return float(result.scalar() or 0)
            
        except Exception as e:
            logger.error(f"Metric sum calculation failed: {e}")
            return 0.0
    
    async def _count_samples(
        self,
        db: AsyncSession,
        service_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """Count metric samples in time period."""
        try:
            result = await db.execute(
                select(func.sum(AggregatedMetric.sample_count))
                .join(MetricDefinition)
                .where(and_(
                    AggregatedMetric.window_start >= start_time,
                    AggregatedMetric.window_end <= end_time
                ))
            )
            return int(result.scalar() or 0)
            
        except Exception as e:
            logger.error(f"Sample count failed: {e}")
            return 0
    
    def _determine_sla_status(
        self,
        actual_value: Optional[float],
        target_value: float,
        inverse: bool = False
    ) -> str:
        """Determine SLA status based on actual vs target value."""
        if actual_value is None:
            return SLAStatus.UNKNOWN.value
        
        if inverse:  # For metrics where lower is better (response time, error rate)
            if actual_value <= target_value:
                return SLAStatus.MEETING.value
            elif actual_value <= target_value * 1.1:  # 10% tolerance
                return SLAStatus.AT_RISK.value
            else:
                return SLAStatus.BREACHED.value
        else:  # For metrics where higher is better (availability, throughput)
            if actual_value >= target_value:
                return SLAStatus.MEETING.value
            elif actual_value >= target_value * 0.9:  # 10% tolerance
                return SLAStatus.AT_RISK.value
            else:
                return SLAStatus.BREACHED.value
    
    def _determine_overall_sla_status(self, individual_statuses: List[Optional[str]]) -> str:
        """Determine overall SLA status from individual metric statuses."""
        statuses = [status for status in individual_statuses if status is not None]
        
        if not statuses:
            return SLAStatus.UNKNOWN.value
        
        # If any metric is breached, overall is breached
        if SLAStatus.BREACHED.value in statuses:
            return SLAStatus.BREACHED.value
        
        # If any metric is at risk, overall is at risk
        if SLAStatus.AT_RISK.value in statuses:
            return SLAStatus.AT_RISK.value
        
        # If all metrics are meeting targets
        if all(status == SLAStatus.MEETING.value for status in statuses):
            return SLAStatus.MEETING.value
        
        return SLAStatus.UNKNOWN.value

# =============================================================================
# LEGAL COMPLIANCE SLA TRACKER
# =============================================================================

class LegalComplianceSLATracker:
    """Tracks legal compliance specific SLAs."""
    
    def __init__(self):
        self.calculator = SLACalculator()
    
    async def measure_legal_compliance_slas(
        self,
        db: AsyncSession,
        measurement_start: datetime,
        measurement_end: datetime
    ) -> LegalComplianceMetrics:
        """Measure legal compliance specific SLA metrics."""
        try:
            # Document processing SLA
            doc_processing_time = await self._measure_document_processing_sla(
                db, measurement_start, measurement_end
            )
            
            # Audit trail completeness
            audit_completeness = await self._measure_audit_completeness(
                db, measurement_start, measurement_end
            )
            
            # Privacy compliance score
            privacy_score = await self._measure_privacy_compliance(
                db, measurement_start, measurement_end
            )
            
            # Backup recovery time
            backup_recovery_time = await self._measure_backup_recovery_sla(
                db, measurement_start, measurement_end
            )
            
            # Security incident response time
            security_response_time = await self._measure_security_response_sla(
                db, measurement_start, measurement_end
            )
            
            return LegalComplianceMetrics(
                data_processing_sla=doc_processing_time,
                audit_trail_completeness=audit_completeness,
                privacy_compliance_score=privacy_score,
                backup_recovery_time=backup_recovery_time,
                security_incident_response_time=security_response_time
            )
            
        except Exception as e:
            logger.error(f"Legal compliance SLA measurement failed: {e}")
            raise
    
    async def _measure_document_processing_sla(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Measure document processing time SLA."""
        try:
            # Get average document processing time from metrics
            result = await db.execute(
                select(func.avg(AggregatedMetric.avg_value))
                .join(MetricDefinition)
                .where(and_(
                    MetricDefinition.name == "document_processing_duration_seconds",
                    AggregatedMetric.window_start >= start_time,
                    AggregatedMetric.window_end <= end_time
                ))
            )
            
            avg_time = result.scalar()
            return float(avg_time) if avg_time else 0.0
            
        except Exception as e:
            logger.error(f"Document processing SLA measurement failed: {e}")
            return 0.0
    
    async def _measure_audit_completeness(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Measure audit trail completeness percentage."""
        try:
            # This would check audit event completeness
            # For now, returning a placeholder calculation
            
            # Get total audit events that should have been generated
            total_expected = await self._count_expected_audit_events(db, start_time, end_time)
            
            # Get actual audit events generated
            actual_events = await self._count_actual_audit_events(db, start_time, end_time)
            
            if total_expected > 0:
                completeness = (actual_events / total_expected) * 100
                return min(completeness, 100.0)
            
            return 100.0  # Assume complete if no expected events
            
        except Exception as e:
            logger.error(f"Audit completeness measurement failed: {e}")
            return 0.0
    
    async def _measure_privacy_compliance(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Measure privacy compliance score."""
        try:
            # Get compliance violation count
            violations_result = await db.execute(
                select(func.sum(AggregatedMetric.sum_value))
                .join(MetricDefinition)
                .where(and_(
                    MetricDefinition.name == "compliance_violations_detected",
                    AggregatedMetric.window_start >= start_time,
                    AggregatedMetric.window_end <= end_time
                ))
            )
            
            violations = int(violations_result.scalar() or 0)
            
            # Calculate compliance score (fewer violations = higher score)
            # This is a simplified calculation
            max_violations = 10  # Threshold for 0% score
            score = max(0, (max_violations - violations) / max_violations * 100)
            
            return score
            
        except Exception as e:
            logger.error(f"Privacy compliance measurement failed: {e}")
            return 0.0
    
    async def _measure_backup_recovery_sla(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Measure backup recovery time SLA."""
        try:
            # This would measure actual backup/recovery operations
            # For now, returning a target value
            return 120.0  # 2 hours target
            
        except Exception as e:
            logger.error(f"Backup recovery SLA measurement failed: {e}")
            return 0.0
    
    async def _measure_security_response_sla(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Measure security incident response time SLA."""
        try:
            # This would measure actual security incident response times
            # For now, returning a target value
            return 30.0  # 30 minutes target
            
        except Exception as e:
            logger.error(f"Security response SLA measurement failed: {e}")
            return 0.0
    
    async def _count_expected_audit_events(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """Count expected audit events (placeholder)."""
        # This would implement logic to count expected audit events
        # based on system activity
        return 1000
    
    async def _count_actual_audit_events(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """Count actual audit events generated."""
        try:
            result = await db.execute(
                select(func.sum(AggregatedMetric.sum_value))
                .join(MetricDefinition)
                .where(and_(
                    MetricDefinition.name == "audit_events_generated",
                    AggregatedMetric.window_start >= start_time,
                    AggregatedMetric.window_end <= end_time
                ))
            )
            
            return int(result.scalar() or 0)
            
        except Exception as e:
            logger.error(f"Actual audit events count failed: {e}")
            return 0

# =============================================================================
# SLA REPORTING ENGINE
# =============================================================================

class SLAReportingEngine:
    """Generates SLA reports for clients and compliance."""
    
    def __init__(self):
        self.compliance_tracker = LegalComplianceSLATracker()
    
    async def generate_client_sla_report(
        self,
        db: AsyncSession,
        client_id: str,
        report_start: datetime,
        report_end: datetime
    ) -> ClientSLAReport:
        """Generate comprehensive SLA report for client."""
        try:
            # Get client SLA definitions
            result = await db.execute(
                select(SLADefinition)
                .where(and_(
                    SLADefinition.enabled == True,
                    SLADefinition.client_tier.isnot(None)  # Client-specific SLAs
                ))
            )
            client_slas = result.scalars().all()
            
            # Get SLA measurements for the period
            measurements_result = await db.execute(
                select(SLAMeasurement, SLADefinition)
                .join(SLADefinition)
                .where(and_(
                    SLAMeasurement.measurement_start >= report_start,
                    SLAMeasurement.measurement_end <= report_end,
                    SLADefinition.enabled == True
                ))
            )
            measurements = measurements_result.fetchall()
            
            # Aggregate SLA metrics
            sla_metrics = self._aggregate_sla_metrics(measurements)
            
            # Generate compliance summary
            compliance_summary = await self._generate_compliance_summary(
                db, measurements, report_start, report_end
            )
            
            # Generate breach summary
            breach_summary = self._generate_breach_summary(measurements)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(sla_metrics, breach_summary)
            
            return ClientSLAReport(
                client_id=client_id,
                client_name=f"Client {client_id}",  # Would get from client DB
                client_tier=ClientTier.PREMIUM,  # Would get from client DB
                report_period_start=report_start,
                report_period_end=report_end,
                sla_metrics=sla_metrics,
                compliance_summary=compliance_summary,
                breach_summary=breach_summary,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Client SLA report generation failed: {e}")
            raise
    
    def _aggregate_sla_metrics(self, measurements: List[Tuple]) -> Dict[str, Any]:
        """Aggregate SLA measurements into summary metrics."""
        metrics = {
            'availability': {'values': [], 'target': 99.9},
            'response_time': {'values': [], 'target': 500},
            'throughput': {'values': [], 'target': 100},
            'error_rate': {'values': [], 'target': 0.1},
            'overall_compliance': 0.0
        }
        
        for measurement, sla_def in measurements:
            if measurement.availability_percentage is not None:
                metrics['availability']['values'].append(float(measurement.availability_percentage))
                metrics['availability']['target'] = float(sla_def.availability_target or 99.9)
            
            if measurement.p95_response_time_ms is not None:
                metrics['response_time']['values'].append(float(measurement.p95_response_time_ms))
                metrics['response_time']['target'] = float(sla_def.response_time_target_ms or 500)
            
            if measurement.throughput_rps is not None:
                metrics['throughput']['values'].append(float(measurement.throughput_rps))
                metrics['throughput']['target'] = float(sla_def.throughput_target_rps or 100)
            
            if measurement.error_rate_percentage is not None:
                metrics['error_rate']['values'].append(float(measurement.error_rate_percentage))
                metrics['error_rate']['target'] = float(sla_def.error_rate_target or 0.1)
        
        # Calculate aggregated values
        for metric_name, metric_data in metrics.items():
            if metric_name == 'overall_compliance':
                continue
            
            values = metric_data['values']
            if values:
                metric_data['avg'] = statistics.mean(values)
                metric_data['min'] = min(values)
                metric_data['max'] = max(values)
                metric_data['compliance_rate'] = self._calculate_compliance_rate(
                    values, metric_data['target'], metric_name in ['response_time', 'error_rate']
                )
            else:
                metric_data.update({'avg': 0, 'min': 0, 'max': 0, 'compliance_rate': 0})
        
        # Calculate overall compliance
        compliance_rates = [
            metrics[m]['compliance_rate'] for m in ['availability', 'response_time', 'throughput', 'error_rate']
            if metrics[m]['values']
        ]
        metrics['overall_compliance'] = statistics.mean(compliance_rates) if compliance_rates else 0
        
        return metrics
    
    def _calculate_compliance_rate(self, values: List[float], target: float, inverse: bool = False) -> float:
        """Calculate compliance rate for metric values."""
        if not values:
            return 0.0
        
        compliant_count = 0
        for value in values:
            if inverse:  # Lower is better
                if value <= target:
                    compliant_count += 1
            else:  # Higher is better
                if value >= target:
                    compliant_count += 1
        
        return (compliant_count / len(values)) * 100
    
    async def _generate_compliance_summary(
        self,
        db: AsyncSession,
        measurements: List[Tuple],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Generate legal compliance summary."""
        try:
            # Get legal compliance metrics
            legal_metrics = await self.compliance_tracker.measure_legal_compliance_slas(
                db, start_time, end_time
            )
            
            return {
                'legal_compliance_score': self._calculate_overall_legal_compliance(legal_metrics),
                'document_processing_sla': legal_metrics.data_processing_sla,
                'audit_completeness': legal_metrics.audit_trail_completeness,
                'privacy_compliance': legal_metrics.privacy_compliance_score,
                'backup_recovery_readiness': legal_metrics.backup_recovery_time <= 120,  # 2 hours
                'security_response_readiness': legal_metrics.security_incident_response_time <= 30  # 30 minutes
            }
            
        except Exception as e:
            logger.error(f"Compliance summary generation failed: {e}")
            return {'legal_compliance_score': 0.0}
    
    def _calculate_overall_legal_compliance(self, metrics: LegalComplianceMetrics) -> float:
        """Calculate overall legal compliance score."""
        # Document processing: target 60 seconds
        doc_score = max(0, (60 - metrics.data_processing_sla) / 60 * 100) if metrics.data_processing_sla > 0 else 0
        
        # Audit completeness: direct percentage
        audit_score = metrics.audit_trail_completeness
        
        # Privacy compliance: direct score
        privacy_score = metrics.privacy_compliance_score
        
        # Backup: target 120 minutes
        backup_score = max(0, (240 - metrics.backup_recovery_time) / 240 * 100) if metrics.backup_recovery_time > 0 else 0
        
        # Security: target 30 minutes
        security_score = max(0, (60 - metrics.security_incident_response_time) / 60 * 100) if metrics.security_incident_response_time > 0 else 0
        
        # Weighted average
        weights = {'doc': 0.2, 'audit': 0.3, 'privacy': 0.3, 'backup': 0.1, 'security': 0.1}
        weighted_score = (
            doc_score * weights['doc'] +
            audit_score * weights['audit'] +
            privacy_score * weights['privacy'] +
            backup_score * weights['backup'] +
            security_score * weights['security']
        )
        
        return min(weighted_score, 100.0)
    
    def _generate_breach_summary(self, measurements: List[Tuple]) -> Dict[str, Any]:
        """Generate SLA breach summary."""
        breaches = {
            'total_breaches': 0,
            'availability_breaches': 0,
            'response_time_breaches': 0,
            'throughput_breaches': 0,
            'error_rate_breaches': 0,
            'breach_details': []
        }
        
        for measurement, sla_def in measurements:
            if measurement.availability_status == SLAStatus.BREACHED.value:
                breaches['availability_breaches'] += 1
                breaches['total_breaches'] += 1
            
            if measurement.response_time_status == SLAStatus.BREACHED.value:
                breaches['response_time_breaches'] += 1
                breaches['total_breaches'] += 1
            
            if measurement.throughput_status == SLAStatus.BREACHED.value:
                breaches['throughput_breaches'] += 1
                breaches['total_breaches'] += 1
            
            if measurement.error_rate_status == SLAStatus.BREACHED.value:
                breaches['error_rate_breaches'] += 1
                breaches['total_breaches'] += 1
        
        return breaches
    
    def _generate_recommendations(self, sla_metrics: Dict[str, Any], breach_summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on SLA performance."""
        recommendations = []
        
        # Availability recommendations
        if sla_metrics['availability']['compliance_rate'] < 95:
            recommendations.append("Improve system availability through redundancy and failover mechanisms")
            recommendations.append("Implement proactive monitoring for availability issues")
        
        # Response time recommendations
        if sla_metrics['response_time']['compliance_rate'] < 95:
            recommendations.append("Optimize application performance and database queries")
            recommendations.append("Consider implementing caching mechanisms")
            recommendations.append("Review infrastructure capacity and scaling policies")
        
        # Throughput recommendations
        if sla_metrics['throughput']['compliance_rate'] < 95:
            recommendations.append("Evaluate system capacity and consider horizontal scaling")
            recommendations.append("Optimize resource utilization and load balancing")
        
        # Error rate recommendations
        if sla_metrics['error_rate']['compliance_rate'] < 95:
            recommendations.append("Improve error handling and system reliability")
            recommendations.append("Enhance monitoring and alerting for early issue detection")
        
        # General recommendations
        if breach_summary['total_breaches'] > 0:
            recommendations.append("Conduct root cause analysis for SLA breaches")
            recommendations.append("Review and update incident response procedures")
        
        # Legal compliance recommendations
        recommendations.append("Maintain comprehensive audit trails for legal compliance")
        recommendations.append("Regular review of data retention and privacy policies")
        
        return recommendations

# =============================================================================
# MAIN SLA MONITORING SERVICE
# =============================================================================

class SLAMonitoringService:
    """Main SLA monitoring and compliance service."""
    
    def __init__(self):
        self.measurement_engine = SLAMeasurementEngine()
        self.reporting_engine = SLAReportingEngine()
        self.audit_service = AuditLoggingService()
        
        # Running state
        self.running = False
    
    async def start_sla_monitoring(self, db: AsyncSession):
        """Start SLA monitoring service."""
        logger.info("Starting SLA monitoring service")
        self.running = True
        
        # Initialize default SLA definitions
        await self._initialize_default_slas(db)
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._sla_measurement_loop(db)),
            asyncio.create_task(self._sla_reporting_loop(db)),
            asyncio.create_task(self._sla_alerting_loop(db))
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"SLA monitoring service error: {e}")
            self.running = False
            # Restart after delay
            await asyncio.sleep(300)
            await self.start_sla_monitoring(db)
    
    async def _initialize_default_slas(self, db: AsyncSession):
        """Initialize default SLA definitions."""
        default_slas = [
            SLADefinitionCreate(
                name="API Response Time SLA",
                service_name="legal-ai-api",
                availability_target=99.95,
                response_time_target_ms=500,
                error_rate_target=0.1,
                measurement_window_hours=24,
                client_tier="premium",
                business_criticality="high",
                regulatory_requirements=["uptime", "performance"]
            ),
            SLADefinitionCreate(
                name="Document Processing SLA", 
                service_name="document-processor",
                response_time_target_ms=30000,  # 30 seconds
                throughput_target_rps=10,
                error_rate_target=0.5,
                measurement_window_hours=24,
                client_tier="standard",
                business_criticality="high"
            ),
            SLADefinitionCreate(
                name="Legal Compliance SLA",
                service_name="legal-ai-system",
                availability_target=99.9,
                measurement_window_hours=24,
                business_criticality="critical",
                regulatory_requirements=["gdpr", "ccpa", "aba_rules"]
            )
        ]
        
        for sla_create in default_slas:
            # Check if SLA already exists
            existing = await db.execute(
                select(SLADefinition).where(SLADefinition.name == sla_create.name)
            )
            if not existing.scalar_one_or_none():
                sla_def = SLADefinition(
                    name=sla_create.name,
                    service_name=sla_create.service_name,
                    availability_target=sla_create.availability_target,
                    response_time_target_ms=sla_create.response_time_target_ms,
                    throughput_target_rps=sla_create.throughput_target_rps,
                    error_rate_target=sla_create.error_rate_target,
                    measurement_window_hours=sla_create.measurement_window_hours,
                    client_tier=sla_create.client_tier,
                    business_criticality=sla_create.business_criticality,
                    regulatory_requirements=sla_create.regulatory_requirements
                )
                db.add(sla_def)
        
        await db.commit()
    
    async def _sla_measurement_loop(self, db: AsyncSession):
        """Run SLA measurements periodically."""
        while self.running:
            try:
                logger.info("Running SLA measurements")
                
                # Get active SLA definitions
                result = await db.execute(
                    select(SLADefinition).where(SLADefinition.enabled == True)
                )
                sla_definitions = result.scalars().all()
                
                current_time = datetime.now(timezone.utc)
                
                for sla_def in sla_definitions:
                    try:
                        # Calculate measurement period
                        measurement_end = current_time.replace(minute=0, second=0, microsecond=0)
                        measurement_start = measurement_end - timedelta(hours=sla_def.measurement_window_hours)
                        
                        # Check if measurement already exists
                        existing = await db.execute(
                            select(SLAMeasurement).where(and_(
                                SLAMeasurement.sla_definition_id == sla_def.id,
                                SLAMeasurement.measurement_start == measurement_start,
                                SLAMeasurement.measurement_end == measurement_end
                            ))
                        )
                        
                        if existing.scalar_one_or_none():
                            continue  # Measurement already exists
                        
                        # Perform measurement
                        measurement = await self.measurement_engine.measure_sla_performance(
                            db, sla_def, measurement_start, measurement_end
                        )
                        
                        db.add(measurement)
                        logger.info(f"SLA measurement completed: {sla_def.name} - {measurement.overall_status}")
                        
                    except Exception as sla_error:
                        logger.error(f"SLA measurement failed for {sla_def.name}: {sla_error}")
                
                await db.commit()
                
                # Wait 1 hour before next measurement cycle
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"SLA measurement loop failed: {e}")
                await asyncio.sleep(1800)
    
    async def _sla_reporting_loop(self, db: AsyncSession):
        """Generate SLA reports periodically."""
        while self.running:
            try:
                current_time = datetime.now(timezone.utc)
                
                # Generate daily reports at midnight
                if current_time.hour == 0:
                    logger.info("Generating daily SLA reports")
                    
                    report_end = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
                    report_start = report_end - timedelta(days=1)
                    
                    # Generate reports for each client tier
                    for tier in ClientTier:
                        try:
                            report = await self.reporting_engine.generate_client_sla_report(
                                db, f"tier_{tier.value}", report_start, report_end
                            )
                            
                            # Store or send report (implementation would depend on requirements)
                            logger.info(f"Generated SLA report for {tier.value}: {report.compliance_summary['legal_compliance_score']:.1f}% compliance")
                            
                        except Exception as report_error:
                            logger.error(f"Failed to generate report for {tier.value}: {report_error}")
                
                # Wait 1 hour before next check
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"SLA reporting loop failed: {e}")
                await asyncio.sleep(3600)
    
    async def _sla_alerting_loop(self, db: AsyncSession):
        """Monitor for SLA breaches and send alerts."""
        while self.running:
            try:
                # Get recent SLA measurements with breaches
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
                
                result = await db.execute(
                    select(SLAMeasurement, SLADefinition)
                    .join(SLADefinition)
                    .where(and_(
                        SLAMeasurement.measurement_end >= cutoff_time,
                        SLAMeasurement.overall_status == SLAStatus.BREACHED.value
                    ))
                )
                
                breached_measurements = result.fetchall()
                
                for measurement, sla_def in breached_measurements:
                    # Create audit log for SLA breach
                    await self.audit_service.log_audit_event(db, AuditEventCreate(
                        event_type=AuditEventType.SLA_BREACH,
                        severity=AuditSeverity.ERROR,
                        status=AuditStatus.ERROR,
                        action="sla_breach_detected",
                        description=f"SLA breach detected: {sla_def.name}",
                        details={
                            "sla_name": sla_def.name,
                            "service_name": sla_def.service_name,
                            "measurement_period": f"{measurement.measurement_start} to {measurement.measurement_end}",
                            "availability_status": measurement.availability_status,
                            "response_time_status": measurement.response_time_status,
                            "throughput_status": measurement.throughput_status,
                            "error_rate_status": measurement.error_rate_status,
                            "business_criticality": sla_def.business_criticality,
                            "client_tier": sla_def.client_tier
                        }
                    ))
                
                if breached_measurements:
                    logger.warning(f"Detected {len(breached_measurements)} SLA breaches in last hour")
                
                # Wait 15 minutes before next check
                await asyncio.sleep(900)
                
            except Exception as e:
                logger.error(f"SLA alerting loop failed: {e}")
                await asyncio.sleep(900)

# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

sla_monitoring_service = SLAMonitoringService()
sla_measurement_engine = SLAMeasurementEngine()
sla_reporting_engine = SLAReportingEngine()
legal_compliance_sla_tracker = LegalComplianceSLATracker()