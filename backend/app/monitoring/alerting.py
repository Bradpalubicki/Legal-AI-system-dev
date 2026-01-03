# =============================================================================
# Legal AI System - Real-time Alerting System with Escalation
# =============================================================================
# Advanced alerting system with multi-channel notifications, escalation
# policies, alert correlation, and legal compliance integration
# =============================================================================

from typing import Optional, Dict, Any, List, Tuple, Set, Callable
from datetime import datetime, timezone, timedelta
from pathlib import Path
import asyncio
import logging
import json
import uuid
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import concurrent.futures
from collections import deque, defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_, desc, func, text
import aiohttp
import redis
import twilio
from twilio.rest import Client as TwilioClient
import pagerduty

from .models import (
    AlertRule, Alert, AlertAnnotation, MetricDefinition, MetricSample,
    AlertSeverity, AlertStatus, ThresholdOperator,
    AlertRuleCreate, AlertUpdate
)
from ..audit.service import AuditLoggingService, AuditEventCreate
from ..audit.models import AuditEventType, AuditSeverity as AuditSeverity_Enum, AuditStatus
from ..core.config import get_settings

logger = logging.getLogger(__name__)

# =============================================================================
# ALERTING ENUMS AND MODELS
# =============================================================================

class NotificationChannel(Enum):
    """Available notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    SMS = "sms"
    PHONE = "phone"

class EscalationAction(Enum):
    """Escalation actions."""
    NOTIFY_MANAGER = "notify_manager"
    CREATE_INCIDENT = "create_incident"
    CALL_ONCALL = "call_oncall"
    SEND_URGENT_EMAIL = "send_urgent_email"
    PAGE_LEADERSHIP = "page_leadership"

@dataclass
class AlertCorrelationRule:
    """Alert correlation rule for grouping related alerts."""
    rule_id: str
    name: str
    correlation_window_minutes: int
    correlation_criteria: Dict[str, Any]
    suppress_individual_alerts: bool
    create_composite_alert: bool

@dataclass
class EscalationPolicy:
    """Escalation policy configuration."""
    policy_id: str
    name: str
    escalation_levels: List[Dict[str, Any]]
    max_escalation_level: int
    escalation_interval_minutes: int
    auto_resolve_timeout_hours: int

@dataclass
class NotificationTemplate:
    """Notification template configuration."""
    template_id: str
    channel: NotificationChannel
    severity: AlertSeverity
    template: str
    variables: List[str]

@dataclass
class AlertContext:
    """Alert context and metadata."""
    alert_id: str
    rule_name: str
    metric_name: str
    current_value: float
    threshold_value: float
    severity: AlertSeverity
    triggered_at: datetime
    affected_services: List[str]
    business_impact: Dict[str, Any]
    compliance_impact: Dict[str, Any]
    additional_metadata: Dict[str, Any] = field(default_factory=dict)

# =============================================================================
# NOTIFICATION CHANNELS
# =============================================================================

class EmailNotificationChannel:
    """Email notification channel."""
    
    def __init__(self):
        self.settings = get_settings()
        
    async def send_notification(self, alert_context: AlertContext, recipients: List[str], template: NotificationTemplate) -> bool:
        """Send email notification."""
        try:
            smtp_server = getattr(self.settings, "SMTP_SERVER", "localhost")
            smtp_port = getattr(self.settings, "SMTP_PORT", 587)
            smtp_username = getattr(self.settings, "SMTP_USERNAME", "")
            smtp_password = getattr(self.settings, "SMTP_PASSWORD", "")
            from_email = getattr(self.settings, "ALERT_FROM_EMAIL", "alerts@legal-ai.example.com")
            
            # Render email content
            subject = self._render_template(
                f"[LEGAL AI ALERT] {alert_context.severity.value.upper()}: {alert_context.rule_name}",
                alert_context
            )
            
            body = self._render_template(template.template, alert_context)
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = from_email
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            msg.attach(MimeText(body, 'html' if '<html>' in body else 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if smtp_username:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent: {alert_context.alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _render_template(self, template: str, context: AlertContext) -> str:
        """Render notification template with alert context."""
        variables = {
            'alert_id': context.alert_id,
            'rule_name': context.rule_name,
            'metric_name': context.metric_name,
            'current_value': context.current_value,
            'threshold_value': context.threshold_value,
            'severity': context.severity.value.upper(),
            'triggered_at': context.triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'affected_services': ', '.join(context.affected_services),
            'business_impact': json.dumps(context.business_impact, indent=2),
            'compliance_impact': json.dumps(context.compliance_impact, indent=2)
        }
        
        rendered = template
        for key, value in variables.items():
            rendered = rendered.replace(f'{{{key}}}', str(value))
        
        return rendered

class SlackNotificationChannel:
    """Slack notification channel."""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def send_notification(self, alert_context: AlertContext, webhook_url: str, template: NotificationTemplate) -> bool:
        """Send Slack notification."""
        try:
            # Color based on severity
            color_map = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ff9900", 
                AlertSeverity.ERROR: "#ff0000",
                AlertSeverity.CRITICAL: "#8B0000"
            }
            
            # Build Slack payload
            payload = {
                "username": "Legal AI Monitoring",
                "icon_emoji": ":warning:",
                "attachments": [{
                    "color": color_map.get(alert_context.severity, "#ff0000"),
                    "title": f"{alert_context.severity.value.upper()}: {alert_context.rule_name}",
                    "fields": [
                        {"title": "Metric", "value": alert_context.metric_name, "short": True},
                        {"title": "Current Value", "value": str(alert_context.current_value), "short": True},
                        {"title": "Threshold", "value": str(alert_context.threshold_value), "short": True},
                        {"title": "Triggered At", "value": alert_context.triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC'), "short": True}
                    ],
                    "footer": "Legal AI System",
                    "ts": int(alert_context.triggered_at.timestamp())
                }]
            }
            
            # Add business/compliance impact if available
            if alert_context.business_impact:
                payload["attachments"][0]["fields"].append({
                    "title": "Business Impact",
                    "value": json.dumps(alert_context.business_impact, indent=2),
                    "short": False
                })
            
            if alert_context.compliance_impact:
                payload["attachments"][0]["fields"].append({
                    "title": "Compliance Impact", 
                    "value": json.dumps(alert_context.compliance_impact, indent=2),
                    "short": False
                })
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent: {alert_context.alert_id}")
                        return True
                    else:
                        logger.error(f"Slack notification failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

class PagerDutyNotificationChannel:
    """PagerDuty notification channel."""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def send_notification(self, alert_context: AlertContext, integration_key: str, template: NotificationTemplate) -> bool:
        """Send PagerDuty notification."""
        try:
            service_url = "https://events.pagerduty.com/v2/enqueue"
            
            # Map severity to PagerDuty severity
            severity_map = {
                AlertSeverity.INFO: "info",
                AlertSeverity.WARNING: "warning", 
                AlertSeverity.ERROR: "error",
                AlertSeverity.CRITICAL: "critical"
            }
            
            payload = {
                "routing_key": integration_key,
                "event_action": "trigger",
                "dedup_key": f"legal-ai-{alert_context.alert_id}",
                "payload": {
                    "summary": f"{alert_context.rule_name}: {alert_context.current_value} vs {alert_context.threshold_value}",
                    "severity": severity_map.get(alert_context.severity, "error"),
                    "source": "Legal AI System",
                    "component": alert_context.metric_name,
                    "group": "legal-ai-monitoring",
                    "class": "performance-alert",
                    "custom_details": {
                        "metric_name": alert_context.metric_name,
                        "current_value": alert_context.current_value,
                        "threshold_value": alert_context.threshold_value,
                        "triggered_at": alert_context.triggered_at.isoformat(),
                        "affected_services": alert_context.affected_services,
                        "business_impact": alert_context.business_impact,
                        "compliance_impact": alert_context.compliance_impact
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(service_url, json=payload) as response:
                    if response.status == 202:
                        logger.info(f"PagerDuty alert sent: {alert_context.alert_id}")
                        return True
                    else:
                        logger.error(f"PagerDuty notification failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send PagerDuty notification: {e}")
            return False

class SMSNotificationChannel:
    """SMS notification channel using Twilio."""
    
    def __init__(self):
        self.settings = get_settings()
        account_sid = getattr(self.settings, "TWILIO_ACCOUNT_SID", "")
        auth_token = getattr(self.settings, "TWILIO_AUTH_TOKEN", "")
        
        if account_sid and auth_token:
            self.client = TwilioClient(account_sid, auth_token)
            self.from_phone = getattr(self.settings, "TWILIO_FROM_PHONE", "")
        else:
            self.client = None
    
    async def send_notification(self, alert_context: AlertContext, phone_numbers: List[str], template: NotificationTemplate) -> bool:
        """Send SMS notification."""
        if not self.client:
            logger.warning("Twilio not configured for SMS notifications")
            return False
        
        try:
            message_body = (
                f"Legal AI Alert [{alert_context.severity.value.upper()}]\n"
                f"{alert_context.rule_name}\n"
                f"Value: {alert_context.current_value} (threshold: {alert_context.threshold_value})\n"
                f"Time: {alert_context.triggered_at.strftime('%H:%M:%S UTC')}"
            )
            
            success_count = 0
            for phone_number in phone_numbers:
                try:
                    message = self.client.messages.create(
                        body=message_body,
                        from_=self.from_phone,
                        to=phone_number
                    )
                    success_count += 1
                    logger.info(f"SMS sent to {phone_number}: {message.sid}")
                except Exception as sms_error:
                    logger.error(f"Failed to send SMS to {phone_number}: {sms_error}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to send SMS notifications: {e}")
            return False

# =============================================================================
# ALERT CORRELATION ENGINE
# =============================================================================

class AlertCorrelationEngine:
    """Correlates related alerts to reduce noise."""
    
    def __init__(self):
        self.correlation_rules = self._load_correlation_rules()
        self.recent_alerts = deque(maxlen=10000)  # Keep recent alerts for correlation
    
    def _load_correlation_rules(self) -> List[AlertCorrelationRule]:
        """Load alert correlation rules."""
        return [
            AlertCorrelationRule(
                rule_id="system_resource_correlation",
                name="System Resource Alerts",
                correlation_window_minutes=10,
                correlation_criteria={
                    "metrics": ["system_cpu_usage_percent", "system_memory_used_percent", "system_disk_used_percent"],
                    "threshold_exceeded": True
                },
                suppress_individual_alerts=True,
                create_composite_alert=True
            ),
            AlertCorrelationRule(
                rule_id="ai_service_correlation",
                name="AI Service Performance",
                correlation_window_minutes=5,
                correlation_criteria={
                    "metrics": ["ai_request_duration_seconds", "ai_api_rate_limit_errors_total"],
                    "same_provider": True
                },
                suppress_individual_alerts=False,
                create_composite_alert=True
            ),
            AlertCorrelationRule(
                rule_id="database_performance_correlation",
                name="Database Performance Issues",
                correlation_window_minutes=15,
                correlation_criteria={
                    "metrics": ["database_connection_pool_active", "http_request_duration_seconds"],
                    "impact_threshold": 0.8
                },
                suppress_individual_alerts=False,
                create_composite_alert=True
            )
        ]
    
    def should_correlate_alert(self, new_alert: AlertContext) -> Tuple[bool, Optional[str]]:
        """Check if alert should be correlated with recent alerts."""
        current_time = datetime.now(timezone.utc)
        
        for rule in self.correlation_rules:
            # Check if metric matches correlation rule
            if new_alert.metric_name not in rule.correlation_criteria.get("metrics", []):
                continue
            
            # Find recent alerts within correlation window
            window_start = current_time - timedelta(minutes=rule.correlation_window_minutes)
            recent_related = [
                alert for alert in self.recent_alerts 
                if (alert.triggered_at >= window_start and 
                    alert.metric_name in rule.correlation_criteria.get("metrics", []))
            ]
            
            # Check correlation criteria
            if len(recent_related) >= 2:  # At least 2 related alerts
                return True, rule.rule_id
        
        return False, None
    
    def add_alert_to_correlation(self, alert: AlertContext):
        """Add alert to correlation tracking."""
        self.recent_alerts.append(alert)

# =============================================================================
# ESCALATION ENGINE
# =============================================================================

class EscalationEngine:
    """Manages alert escalation policies and procedures."""
    
    def __init__(self):
        self.escalation_policies = self._load_escalation_policies()
        self.active_escalations: Dict[str, Dict[str, Any]] = {}
    
    def _load_escalation_policies(self) -> Dict[str, EscalationPolicy]:
        """Load escalation policies."""
        return {
            "critical_legal_system": EscalationPolicy(
                policy_id="critical_legal_system",
                name="Critical Legal System Alerts",
                escalation_levels=[
                    {
                        "level": 1,
                        "wait_minutes": 5,
                        "actions": [
                            {"type": "notify", "channels": ["slack", "email"], "recipients": ["oncall-engineer"]}
                        ]
                    },
                    {
                        "level": 2, 
                        "wait_minutes": 15,
                        "actions": [
                            {"type": "notify", "channels": ["pagerduty", "sms"], "recipients": ["engineering-manager"]},
                            {"type": "create_incident", "severity": "high"}
                        ]
                    },
                    {
                        "level": 3,
                        "wait_minutes": 30,
                        "actions": [
                            {"type": "notify", "channels": ["phone", "email"], "recipients": ["director-engineering", "cto"]},
                            {"type": "escalate_incident", "severity": "critical"}
                        ]
                    }
                ],
                max_escalation_level=3,
                escalation_interval_minutes=15,
                auto_resolve_timeout_hours=24
            ),
            "compliance_violation": EscalationPolicy(
                policy_id="compliance_violation",
                name="Compliance Violation Alerts",
                escalation_levels=[
                    {
                        "level": 1,
                        "wait_minutes": 0,  # Immediate
                        "actions": [
                            {"type": "notify", "channels": ["email", "slack"], "recipients": ["compliance-officer", "legal-team"]}
                        ]
                    },
                    {
                        "level": 2,
                        "wait_minutes": 10,
                        "actions": [
                            {"type": "notify", "channels": ["pagerduty"], "recipients": ["compliance-manager"]},
                            {"type": "create_incident", "severity": "critical", "tags": ["compliance", "legal"]}
                        ]
                    }
                ],
                max_escalation_level=2,
                escalation_interval_minutes=10,
                auto_resolve_timeout_hours=4
            ),
            "data_breach_potential": EscalationPolicy(
                policy_id="data_breach_potential",
                name="Potential Data Breach Alerts",
                escalation_levels=[
                    {
                        "level": 1,
                        "wait_minutes": 0,  # Immediate
                        "actions": [
                            {"type": "notify", "channels": ["pagerduty", "sms", "email"], "recipients": ["security-team", "legal-counsel"]},
                            {"type": "create_incident", "severity": "critical", "tags": ["security", "data-breach"]}
                        ]
                    }
                ],
                max_escalation_level=1,
                escalation_interval_minutes=5,
                auto_resolve_timeout_hours=1
            )
        }
    
    async def start_escalation(self, alert: Alert, policy_id: str) -> bool:
        """Start escalation process for alert."""
        try:
            policy = self.escalation_policies.get(policy_id)
            if not policy:
                logger.error(f"Escalation policy not found: {policy_id}")
                return False
            
            escalation_state = {
                "alert_id": str(alert.id),
                "policy_id": policy_id,
                "current_level": 0,
                "started_at": datetime.now(timezone.utc),
                "next_escalation_at": datetime.now(timezone.utc) + timedelta(minutes=policy.escalation_levels[0]["wait_minutes"]),
                "completed_levels": [],
                "active": True
            }
            
            self.active_escalations[str(alert.id)] = escalation_state
            
            # Execute first level immediately if wait_minutes is 0
            if policy.escalation_levels[0]["wait_minutes"] == 0:
                await self._execute_escalation_level(alert, policy, 0)
                escalation_state["current_level"] = 1
                escalation_state["completed_levels"].append(0)
                
                if len(policy.escalation_levels) > 1:
                    escalation_state["next_escalation_at"] = datetime.now(timezone.utc) + timedelta(
                        minutes=policy.escalation_levels[1]["wait_minutes"]
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start escalation: {e}")
            return False
    
    async def process_escalations(self):
        """Process pending escalations."""
        current_time = datetime.now(timezone.utc)
        
        for alert_id, escalation_state in list(self.active_escalations.items()):
            if not escalation_state["active"]:
                continue
            
            policy = self.escalation_policies.get(escalation_state["policy_id"])
            if not policy:
                continue
            
            # Check if it's time to escalate
            if current_time >= escalation_state["next_escalation_at"]:
                current_level = escalation_state["current_level"]
                
                if current_level < len(policy.escalation_levels):
                    # Execute escalation level
                    try:
                        # Would need to fetch alert from database
                        await self._execute_escalation_level(None, policy, current_level)
                        
                        escalation_state["completed_levels"].append(current_level)
                        escalation_state["current_level"] = current_level + 1
                        
                        # Schedule next escalation
                        if escalation_state["current_level"] < len(policy.escalation_levels):
                            escalation_state["next_escalation_at"] = current_time + timedelta(
                                minutes=policy.escalation_levels[escalation_state["current_level"]]["wait_minutes"]
                            )
                        else:
                            # No more escalation levels
                            escalation_state["active"] = False
                            
                    except Exception as e:
                        logger.error(f"Failed to execute escalation level: {e}")
    
    async def _execute_escalation_level(self, alert: Alert, policy: EscalationPolicy, level: int):
        """Execute specific escalation level actions."""
        level_config = policy.escalation_levels[level]
        
        for action in level_config["actions"]:
            action_type = action["type"]
            
            if action_type == "notify":
                # Send notifications through specified channels
                channels = action["channels"]
                recipients = action["recipients"]
                
                # This would integrate with notification channels
                logger.info(f"Escalation notification: {channels} -> {recipients}")
                
            elif action_type == "create_incident":
                # Create incident in incident management system
                severity = action.get("severity", "medium")
                tags = action.get("tags", [])
                
                logger.info(f"Creating incident: severity={severity}, tags={tags}")
                
            elif action_type == "escalate_incident":
                # Escalate existing incident
                severity = action.get("severity", "high")
                
                logger.info(f"Escalating incident to severity: {severity}")

# =============================================================================
# MAIN ALERTING ENGINE
# =============================================================================

class AlertingEngine:
    """Main alerting engine coordinating all alerting functionality."""
    
    def __init__(self):
        self.settings = get_settings()
        self.audit_service = AuditLoggingService()
        
        # Notification channels
        self.email_channel = EmailNotificationChannel()
        self.slack_channel = SlackNotificationChannel()
        self.pagerduty_channel = PagerDutyNotificationChannel()
        self.sms_channel = SMSNotificationChannel()
        
        # Engines
        self.correlation_engine = AlertCorrelationEngine()
        self.escalation_engine = EscalationEngine()
        
        # Notification templates
        self.notification_templates = self._load_notification_templates()
        
        # Alert suppression tracking
        self.suppressed_alerts: Dict[str, datetime] = {}
        
        # Running state
        self.running = False
    
    def _load_notification_templates(self) -> Dict[str, NotificationTemplate]:
        """Load notification templates."""
        return {
            "email_critical": NotificationTemplate(
                template_id="email_critical",
                channel=NotificationChannel.EMAIL,
                severity=AlertSeverity.CRITICAL,
                template="""
                <html>
                <body>
                <h2 style="color: #d32f2f;">🚨 CRITICAL ALERT - Legal AI System</h2>
                
                <div style="background-color: #ffebee; padding: 15px; border-left: 4px solid #d32f2f;">
                    <h3>{rule_name}</h3>
                    <p><strong>Metric:</strong> {metric_name}</p>
                    <p><strong>Current Value:</strong> {current_value}</p>
                    <p><strong>Threshold:</strong> {threshold_value}</p>
                    <p><strong>Triggered:</strong> {triggered_at}</p>
                    <p><strong>Affected Services:</strong> {affected_services}</p>
                </div>
                
                <h4>Business Impact:</h4>
                <pre>{business_impact}</pre>
                
                <h4>Compliance Impact:</h4>
                <pre>{compliance_impact}</pre>
                
                <p><strong>Alert ID:</strong> {alert_id}</p>
                <p><em>This alert requires immediate attention for legal compliance and system stability.</em></p>
                </body>
                </html>
                """,
                variables=["rule_name", "metric_name", "current_value", "threshold_value", 
                          "triggered_at", "affected_services", "business_impact", "compliance_impact", "alert_id"]
            ),
            "slack_warning": NotificationTemplate(
                template_id="slack_warning",
                channel=NotificationChannel.SLACK,
                severity=AlertSeverity.WARNING,
                template="Basic Slack template - handled in channel implementation",
                variables=[]
            )
        }
    
    async def start_alerting_engine(self, db: AsyncSession):
        """Start the alerting engine."""
        logger.info("Starting alerting engine")
        self.running = True
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._evaluate_alert_rules_loop(db)),
            asyncio.create_task(self._process_escalations_loop()),
            asyncio.create_task(self._cleanup_old_alerts_loop(db))
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Alerting engine error: {e}")
            self.running = False
            # Restart after delay
            await asyncio.sleep(60)
            await self.start_alerting_engine(db)
    
    async def _evaluate_alert_rules_loop(self, db: AsyncSession):
        """Continuously evaluate alert rules."""
        while self.running:
            try:
                # Get active alert rules
                result = await db.execute(
                    select(AlertRule)
                    .options(selectinload(AlertRule.metric_definition))
                    .where(AlertRule.enabled == True)
                )
                alert_rules = result.scalars().all()
                
                current_time = datetime.now(timezone.utc)
                
                # Evaluate each rule
                for rule in alert_rules:
                    try:
                        # Check if rule should be evaluated
                        if (rule.next_evaluation_at and 
                            current_time < rule.next_evaluation_at):
                            continue
                        
                        # Evaluate rule
                        should_alert, current_value = await self._evaluate_alert_rule(db, rule)
                        
                        if should_alert:
                            await self._trigger_alert(db, rule, current_value)
                        
                        # Update next evaluation time
                        rule.last_evaluation_at = current_time
                        rule.next_evaluation_at = current_time + timedelta(seconds=60)  # Evaluate every minute
                        
                    except Exception as rule_error:
                        logger.error(f"Failed to evaluate alert rule {rule.id}: {rule_error}")
                
                await db.commit()
                
                # Wait before next evaluation cycle
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Alert rule evaluation loop failed: {e}")
                await asyncio.sleep(60)
    
    async def _evaluate_alert_rule(self, db: AsyncSession, rule: AlertRule) -> Tuple[bool, Optional[float]]:
        """Evaluate individual alert rule."""
        try:
            current_time = datetime.now(timezone.utc)
            window_start = current_time - timedelta(seconds=rule.evaluation_window_seconds)
            
            # Get recent metric samples
            query = select(MetricSample).where(
                and_(
                    MetricSample.metric_definition_id == rule.metric_definition_id,
                    MetricSample.timestamp >= window_start,
                    MetricSample.timestamp <= current_time
                )
            ).order_by(desc(MetricSample.timestamp))
            
            # Apply label filters if specified
            if rule.label_filters:
                for key, value in rule.label_filters.items():
                    query = query.where(MetricSample.labels[key] == value)
            
            result = await db.execute(query)
            samples = result.scalars().all()
            
            if not samples:
                return False, None
            
            # Calculate evaluation metric (avg, max, min based on rule)
            values = [float(sample.value) for sample in samples]
            current_value = sum(values) / len(values)  # Using average
            
            # Check threshold
            operator = ThresholdOperator(rule.threshold_operator)
            threshold = float(rule.threshold_value)
            
            breached = False
            if operator == ThresholdOperator.GT:
                breached = current_value > threshold
            elif operator == ThresholdOperator.GTE:
                breached = current_value >= threshold
            elif operator == ThresholdOperator.LT:
                breached = current_value < threshold
            elif operator == ThresholdOperator.LTE:
                breached = current_value <= threshold
            elif operator == ThresholdOperator.EQ:
                breached = abs(current_value - threshold) < 0.001
            elif operator == ThresholdOperator.NE:
                breached = abs(current_value - threshold) >= 0.001
            
            # Check consecutive breaches requirement
            if breached and rule.consecutive_breaches > 1:
                # Would need to implement consecutive breach tracking
                pass
            
            return breached, current_value
            
        except Exception as e:
            logger.error(f"Failed to evaluate alert rule: {e}")
            return False, None
    
    async def _trigger_alert(self, db: AsyncSession, rule: AlertRule, current_value: float):
        """Trigger alert based on rule."""
        try:
            # Check if alert should be suppressed
            suppress_key = f"{rule.id}_{current_value}"
            if suppress_key in self.suppressed_alerts:
                suppress_until = self.suppressed_alerts[suppress_key]
                if datetime.now(timezone.utc) < suppress_until:
                    return  # Alert is suppressed
            
            # Create alert
            alert = Alert(
                alert_rule_id=rule.id,
                title=f"{rule.name}: Threshold Breached",
                description=f"Metric {rule.metric_definition.name} value {current_value} breached threshold {rule.threshold_value}",
                severity=rule.severity,
                status=AlertStatus.OPEN.value,
                triggered_at=datetime.now(timezone.utc),
                trigger_value=current_value,
                threshold_value=rule.threshold_value,
                business_impact_level="medium",  # Would be determined from rule context
                client_impact=rule.client_impacting,
                compliance_impact=rule.compliance_related
            )
            
            db.add(alert)
            await db.commit()
            await db.refresh(alert)
            
            # Create alert context
            alert_context = AlertContext(
                alert_id=str(alert.id),
                rule_name=rule.name,
                metric_name=rule.metric_definition.name,
                current_value=current_value,
                threshold_value=float(rule.threshold_value),
                severity=AlertSeverity(rule.severity),
                triggered_at=alert.triggered_at,
                affected_services=[],  # Would be determined from rule/metric context
                business_impact={"level": alert.business_impact_level, "client_impacting": alert.client_impact},
                compliance_impact={"compliance_related": alert.compliance_impact}
            )
            
            # Check for correlation
            should_correlate, correlation_rule_id = self.correlation_engine.should_correlate_alert(alert_context)
            if should_correlate:
                logger.info(f"Alert {alert.id} correlated with rule: {correlation_rule_id}")
                # Add correlation metadata
                alert_context.additional_metadata["correlated"] = True
                alert_context.additional_metadata["correlation_rule"] = correlation_rule_id
            
            # Add to correlation tracking
            self.correlation_engine.add_alert_to_correlation(alert_context)
            
            # Send notifications
            await self._send_alert_notifications(alert_context, rule.notification_channels or [])
            
            # Start escalation if needed
            escalation_policy = self._determine_escalation_policy(alert, rule)
            if escalation_policy:
                await self.escalation_engine.start_escalation(alert, escalation_policy)
            
            # Add to suppression tracking
            if rule.suppress_duration_seconds > 0:
                suppress_until = datetime.now(timezone.utc) + timedelta(seconds=rule.suppress_duration_seconds)
                self.suppressed_alerts[suppress_key] = suppress_until
            
            # Audit log
            await self.audit_service.log_audit_event(db, AuditEventCreate(
                event_type=AuditEventType.SYSTEM_ALERT,
                severity=AuditSeverity_Enum.WARNING if alert.severity in ["info", "warning"] else AuditSeverity_Enum.ERROR,
                status=AuditStatus.WARNING,
                action="alert_triggered",
                description=f"Alert triggered: {rule.name}",
                details={
                    "alert_id": str(alert.id),
                    "rule_name": rule.name,
                    "metric_name": rule.metric_definition.name,
                    "current_value": current_value,
                    "threshold_value": float(rule.threshold_value),
                    "severity": rule.severity,
                    "client_impacting": rule.client_impacting,
                    "compliance_related": rule.compliance_related
                }
            ))
            
        except Exception as e:
            logger.error(f"Failed to trigger alert: {e}")
    
    def _determine_escalation_policy(self, alert: Alert, rule: AlertRule) -> Optional[str]:
        """Determine which escalation policy to use."""
        if alert.severity == AlertSeverity.CRITICAL.value:
            if rule.compliance_related:
                return "compliance_violation"
            elif "security" in rule.name.lower() or "breach" in rule.name.lower():
                return "data_breach_potential"
            else:
                return "critical_legal_system"
        
        return None
    
    async def _send_alert_notifications(self, alert_context: AlertContext, channels: List[str]):
        """Send alert notifications through specified channels."""
        tasks = []
        
        for channel_name in channels:
            if channel_name == "email":
                recipients = getattr(self.settings, "ALERT_EMAIL_RECIPIENTS", ["admin@legal-ai.example.com"])
                template = self.notification_templates["email_critical"]
                tasks.append(self.email_channel.send_notification(alert_context, recipients, template))
            
            elif channel_name == "slack":
                webhook_url = getattr(self.settings, "SLACK_WEBHOOK_URL", "")
                if webhook_url:
                    template = self.notification_templates["slack_warning"]
                    tasks.append(self.slack_channel.send_notification(alert_context, webhook_url, template))
            
            elif channel_name == "pagerduty":
                integration_key = getattr(self.settings, "PAGERDUTY_INTEGRATION_KEY", "")
                if integration_key:
                    template = self.notification_templates.get("pagerduty_default")
                    tasks.append(self.pagerduty_channel.send_notification(alert_context, integration_key, template))
            
            elif channel_name == "sms":
                phone_numbers = getattr(self.settings, "ALERT_SMS_NUMBERS", [])
                if phone_numbers:
                    template = self.notification_templates.get("sms_default")
                    tasks.append(self.sms_channel.send_notification(alert_context, phone_numbers, template))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            logger.info(f"Sent {success_count}/{len(tasks)} alert notifications for {alert_context.alert_id}")
    
    async def _process_escalations_loop(self):
        """Process escalation policies."""
        while self.running:
            try:
                await self.escalation_engine.process_escalations()
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Escalation processing failed: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_old_alerts_loop(self, db: AsyncSession):
        """Clean up old resolved alerts."""
        while self.running:
            try:
                # Clean up alerts older than 30 days
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
                
                delete_query = text("""
                    DELETE FROM alerts 
                    WHERE status IN ('resolved', 'expired') 
                    AND resolved_at < :cutoff_date
                """)
                
                result = await db.execute(delete_query, {"cutoff_date": cutoff_date})
                deleted_count = result.rowcount
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old alerts")
                
                await db.commit()
                
                # Sleep for 24 hours
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"Alert cleanup failed: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour

# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

alerting_engine = AlertingEngine()