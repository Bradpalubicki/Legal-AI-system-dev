"""
Instant alert system for critical courtroom developments with real-time notifications and escalation protocols.
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import json
import uuid
from concurrent.futures import ThreadPoolExecutor

from ..shared.database.models import Case, User, TranscriptSegment
from ..shared.utils.ai_client import AIClient
from .statement_analyzer import IdentifiedStatement, StatementType, UrgencyLevel
from .legal_analyzer import LegalEvent, ObjectionType
from .key_moment_detector import KeyMoment, MomentType, ImpactLevel


class AlertType(Enum):
    """Types of alerts that can be generated."""
    COURT_ORDER = "court_order"
    CONTEMPT_WARNING = "contempt_warning"
    SANCTIONS_ORDER = "sanctions_order"
    MISTRIAL_MOTION = "mistrial_motion"
    SETTLEMENT_OFFER = "settlement_offer"
    PERJURY_INDICATION = "perjury_indication"
    WITNESS_BREAKDOWN = "witness_breakdown"
    SMOKING_GUN_EVIDENCE = "smoking_gun_evidence"
    JUDICIAL_ERROR = "judicial_error"
    ATTORNEY_MISCONDUCT = "attorney_misconduct"
    EMERGENCY_MOTION = "emergency_motion"
    PROCEDURAL_VIOLATION = "procedural_violation"
    CONSTITUTIONAL_ISSUE = "constitutional_issue"
    PRIVILEGE_BREACH = "privilege_breach"
    DEADLINE_VIOLATION = "deadline_violation"
    CASE_DISMISSAL = "case_dismissal"
    DEFAULT_JUDGMENT = "default_judgment"
    INJUNCTION_ORDER = "injunction_order"
    DISCOVERY_ABUSE = "discovery_abuse"
    EVIDENCE_EXCLUSION = "evidence_exclusion"


class AlertSeverity(Enum):
    """Severity levels for alerts."""
    CRITICAL = "critical"      # Immediate action required, case outcome at risk
    HIGH = "high"             # Urgent attention needed within minutes
    MEDIUM = "medium"         # Important but can wait for break
    LOW = "low"              # Informational, review when convenient
    INFORMATIONAL = "informational"  # FYI only


class AlertChannel(Enum):
    """Channels for alert delivery."""
    PUSH_NOTIFICATION = "push_notification"
    SMS = "sms"
    EMAIL = "email"
    WEBSOCKET = "websocket"
    SLACK = "slack"
    TEAMS = "teams"
    PHONE_CALL = "phone_call"
    IN_APP = "in_app"
    DASHBOARD = "dashboard"


class AlertStatus(Enum):
    """Status of an alert."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


@dataclass
class AlertRecipient:
    """Recipient configuration for alerts."""
    user_id: str
    name: str
    role: str  # "lead_attorney", "associate", "paralegal", "client", "expert"
    channels: List[AlertChannel]
    alert_types: List[AlertType]  # Types they want to receive
    severity_threshold: AlertSeverity
    contact_info: Dict[str, str]  # phone, email, slack_id, etc.
    active: bool = True
    business_hours_only: bool = False
    time_zone: str = "UTC"


@dataclass
class AlertRule:
    """Rule for triggering alerts."""
    rule_id: str
    name: str
    description: str
    trigger_conditions: Dict[str, Any]
    alert_type: AlertType
    severity: AlertSeverity
    recipients: List[str]  # User IDs
    channels: List[AlertChannel]
    escalation_delay: Optional[int] = None  # Minutes before escalation
    escalation_recipients: List[str] = field(default_factory=list)
    cooldown_period: int = 5  # Minutes between similar alerts
    active: bool = True


@dataclass
class Alert:
    """Individual alert instance."""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    details: Dict[str, Any]
    case_id: str
    session_id: Optional[str]
    timestamp: datetime
    source_segment: Optional[TranscriptSegment]
    recipients: List[str]
    channels: List[AlertChannel]
    status: AlertStatus
    delivery_attempts: List[Dict[str, Any]] = field(default_factory=list)
    acknowledgments: List[Dict[str, Any]] = field(default_factory=list)
    escalation_time: Optional[datetime] = None
    resolved_time: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    requires_response: bool = False
    response_deadline: Optional[datetime] = None
    automated_actions: List[str] = field(default_factory=list)


class AlertSystem:
    """Real-time alert system for critical courtroom developments."""
    
    def __init__(self):
        self.ai_client = AIClient()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.recipients: Dict[str, AlertRecipient] = {}
        self.delivery_handlers: Dict[AlertChannel, Callable] = {}
        self.alert_history: List[Alert] = []
        self.escalation_tasks: Dict[str, asyncio.Task] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Initialize default alert rules
        self._initialize_default_rules()
        
    def _initialize_default_rules(self):
        """Initialize default alert rules for common critical situations."""
        default_rules = [
            AlertRule(
                rule_id="court_order_critical",
                name="Critical Court Orders",
                description="Immediate orders requiring compliance",
                trigger_conditions={
                    "statement_type": "court_order",
                    "urgency": ["critical", "high"],
                    "keywords": ["immediately", "forthwith", "emergency", "contempt"]
                },
                alert_type=AlertType.COURT_ORDER,
                severity=AlertSeverity.CRITICAL,
                recipients=[],
                channels=[AlertChannel.PUSH_NOTIFICATION, AlertChannel.SMS, AlertChannel.WEBSOCKET],
                escalation_delay=2,
                escalation_recipients=[]
            ),
            AlertRule(
                rule_id="sanctions_warning",
                name="Sanctions Orders",
                description="Court imposing sanctions",
                trigger_conditions={
                    "keywords": ["sanction", "sanctions", "fine", "penalty", "monetary"],
                    "speaker_role": "judge"
                },
                alert_type=AlertType.SANCTIONS_ORDER,
                severity=AlertSeverity.HIGH,
                recipients=[],
                channels=[AlertChannel.PUSH_NOTIFICATION, AlertChannel.EMAIL],
                escalation_delay=5
            ),
            AlertRule(
                rule_id="contempt_warning",
                name="Contempt Warnings",
                description="Contempt citations or warnings",
                trigger_conditions={
                    "keywords": ["contempt", "contempt of court", "cite for contempt"],
                    "urgency": ["critical", "high"]
                },
                alert_type=AlertType.CONTEMPT_WARNING,
                severity=AlertSeverity.CRITICAL,
                recipients=[],
                channels=[AlertChannel.PHONE_CALL, AlertChannel.SMS, AlertChannel.PUSH_NOTIFICATION]
            ),
            AlertRule(
                rule_id="smoking_gun_evidence",
                name="Smoking Gun Evidence",
                description="Critical evidence that could change case outcome",
                trigger_conditions={
                    "moment_type": "smoking_gun_evidence",
                    "impact_level": ["case_changing", "highly_significant"]
                },
                alert_type=AlertType.SMOKING_GUN_EVIDENCE,
                severity=AlertSeverity.HIGH,
                recipients=[],
                channels=[AlertChannel.PUSH_NOTIFICATION, AlertChannel.WEBSOCKET],
                escalation_delay=3
            ),
            AlertRule(
                rule_id="settlement_discussion",
                name="Settlement Discussions",
                description="Settlement offers or negotiations",
                trigger_conditions={
                    "keywords": ["settlement", "settle", "offer", "negotiate", "resolve"],
                    "statement_type": "settlement_discussion"
                },
                alert_type=AlertType.SETTLEMENT_OFFER,
                severity=AlertSeverity.HIGH,
                recipients=[],
                channels=[AlertChannel.PUSH_NOTIFICATION, AlertChannel.EMAIL]
            ),
            AlertRule(
                rule_id="mistrial_motion",
                name="Mistrial Motions",
                description="Motions for mistrial",
                trigger_conditions={
                    "keywords": ["mistrial", "declare a mistrial", "motion for mistrial"]
                },
                alert_type=AlertType.MISTRIAL_MOTION,
                severity=AlertSeverity.CRITICAL,
                recipients=[],
                channels=[AlertChannel.PHONE_CALL, AlertChannel.PUSH_NOTIFICATION, AlertChannel.SMS]
            ),
            AlertRule(
                rule_id="perjury_indication",
                name="Perjury Indications",
                description="Potential perjury or false testimony",
                trigger_conditions={
                    "keywords": ["perjury", "false testimony", "lie under oath", "untruthful"],
                    "confidence": 0.8
                },
                alert_type=AlertType.PERJURY_INDICATION,
                severity=AlertSeverity.HIGH,
                recipients=[],
                channels=[AlertChannel.PUSH_NOTIFICATION, AlertChannel.EMAIL]
            ),
            AlertRule(
                rule_id="injunction_order",
                name="Injunction Orders",
                description="Preliminary or permanent injunctions",
                trigger_conditions={
                    "keywords": ["injunction", "enjoin", "restrain", "temporary restraining order", "tro"],
                    "order_type": ["preliminary_injunction", "temporary_restraining_order"]
                },
                alert_type=AlertType.INJUNCTION_ORDER,
                severity=AlertSeverity.CRITICAL,
                recipients=[],
                channels=[AlertChannel.PHONE_CALL, AlertChannel.SMS, AlertChannel.EMAIL]
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule

    async def process_transcript_segment(
        self, 
        segment: TranscriptSegment,
        case: Case,
        legal_events: List[LegalEvent] = None,
        statements: List[IdentifiedStatement] = None,
        moments: List[KeyMoment] = None
    ) -> List[Alert]:
        """Process a transcript segment and generate alerts for critical developments."""
        try:
            generated_alerts = []
            
            # Analyze segment for alert triggers
            segment_analysis = await self._analyze_segment_for_alerts(
                segment, case, legal_events, statements, moments
            )
            
            # Check each alert rule
            for rule in self.alert_rules.values():
                if not rule.active:
                    continue
                
                if self._check_rule_conditions(rule, segment_analysis):
                    # Check cooldown period
                    if self._is_in_cooldown(rule, segment_analysis):
                        continue
                    
                    alert = await self._create_alert(rule, segment, case, segment_analysis)
                    generated_alerts.append(alert)
                    
                    # Send alert immediately
                    await self._send_alert(alert)
            
            return generated_alerts
            
        except Exception as e:
            print(f"Error processing transcript segment for alerts: {e}")
            return []

    async def _analyze_segment_for_alerts(
        self,
        segment: TranscriptSegment,
        case: Case,
        legal_events: List[LegalEvent] = None,
        statements: List[IdentifiedStatement] = None,
        moments: List[KeyMoment] = None
    ) -> Dict[str, Any]:
        """Analyze segment content for alert-triggering conditions."""
        try:
            analysis = {
                "text": segment.text.lower(),
                "speaker": segment.speaker,
                "timestamp": segment.timestamp,
                "case_id": case.id,
                "case_type": case.case_type,
                "keywords": [],
                "urgency": "medium",
                "confidence": segment.confidence,
                "speaker_role": self._identify_speaker_role(segment.speaker),
                "legal_events": legal_events or [],
                "statements": statements or [],
                "moments": moments or []
            }
            
            # Extract keywords
            critical_keywords = [
                "contempt", "sanctions", "mistrial", "perjury", "injunction",
                "settlement", "dismiss", "summary judgment", "emergency",
                "immediately", "forthwith", "restrain", "enjoin"
            ]
            
            analysis["keywords"] = [kw for kw in critical_keywords if kw in analysis["text"]]
            
            # Determine urgency from statements
            if statements:
                urgency_levels = [s.urgency for s in statements]
                if UrgencyLevel.CRITICAL in urgency_levels:
                    analysis["urgency"] = "critical"
                elif UrgencyLevel.HIGH in urgency_levels:
                    analysis["urgency"] = "high"
            
            # Add statement types
            if statements:
                analysis["statement_types"] = [s.statement_type.value for s in statements]
                analysis["order_types"] = [s.order_type.value for s in statements if s.order_type]
            
            # Add moment types and impact levels
            if moments:
                analysis["moment_types"] = [m.moment_type.value for m in moments]
                analysis["impact_levels"] = [m.impact_level.value for m in moments]
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing segment for alerts: {e}")
            return {"text": "", "keywords": [], "urgency": "low"}

    def _identify_speaker_role(self, speaker: str) -> str:
        """Identify the role of the speaker."""
        speaker_lower = speaker.lower()
        
        if any(judge_term in speaker_lower for judge_term in ["judge", "court", "magistrate", "justice"]):
            return "judge"
        elif any(attorney_term in speaker_lower for attorney_term in ["attorney", "counsel", "lawyer"]):
            return "attorney"
        elif "witness" in speaker_lower:
            return "witness"
        elif "clerk" in speaker_lower:
            return "clerk"
        elif "bailiff" in speaker_lower:
            return "bailiff"
        else:
            return "unknown"

    def _check_rule_conditions(self, rule: AlertRule, analysis: Dict[str, Any]) -> bool:
        """Check if alert rule conditions are met."""
        try:
            conditions = rule.trigger_conditions
            
            # Check keywords
            if "keywords" in conditions:
                required_keywords = conditions["keywords"]
                if not any(kw in analysis["text"] for kw in required_keywords):
                    return False
            
            # Check urgency
            if "urgency" in conditions:
                required_urgency = conditions["urgency"]
                if isinstance(required_urgency, list):
                    if analysis["urgency"] not in required_urgency:
                        return False
                else:
                    if analysis["urgency"] != required_urgency:
                        return False
            
            # Check speaker role
            if "speaker_role" in conditions:
                if analysis["speaker_role"] != conditions["speaker_role"]:
                    return False
            
            # Check confidence threshold
            if "confidence" in conditions:
                if analysis["confidence"] < conditions["confidence"]:
                    return False
            
            # Check statement types
            if "statement_type" in conditions:
                if "statement_types" not in analysis:
                    return False
                if conditions["statement_type"] not in analysis["statement_types"]:
                    return False
            
            # Check moment types
            if "moment_type" in conditions:
                if "moment_types" not in analysis:
                    return False
                if conditions["moment_type"] not in analysis["moment_types"]:
                    return False
            
            # Check impact levels
            if "impact_level" in conditions:
                if "impact_levels" not in analysis:
                    return False
                required_levels = conditions["impact_level"]
                if isinstance(required_levels, list):
                    if not any(level in analysis["impact_levels"] for level in required_levels):
                        return False
                else:
                    if required_levels not in analysis["impact_levels"]:
                        return False
            
            # Check order types
            if "order_type" in conditions:
                if "order_types" not in analysis:
                    return False
                required_types = conditions["order_type"]
                if isinstance(required_types, list):
                    if not any(ot in analysis["order_types"] for ot in required_types):
                        return False
                else:
                    if required_types not in analysis["order_types"]:
                        return False
            
            return True
            
        except Exception as e:
            print(f"Error checking rule conditions: {e}")
            return False

    def _is_in_cooldown(self, rule: AlertRule, analysis: Dict[str, Any]) -> bool:
        """Check if the alert rule is in cooldown period."""
        try:
            # Check recent alerts of the same type
            cutoff_time = datetime.now() - timedelta(minutes=rule.cooldown_period)
            
            recent_alerts = [
                alert for alert in self.alert_history
                if (alert.alert_type == rule.alert_type and
                    alert.timestamp > cutoff_time and
                    alert.case_id == analysis["case_id"])
            ]
            
            return len(recent_alerts) > 0
            
        except Exception as e:
            print(f"Error checking cooldown: {e}")
            return False

    async def _create_alert(
        self,
        rule: AlertRule,
        segment: TranscriptSegment,
        case: Case,
        analysis: Dict[str, Any]
    ) -> Alert:
        """Create an alert based on rule and analysis."""
        try:
            alert_id = str(uuid.uuid4())
            
            # Generate alert title and message
            title, message = await self._generate_alert_content(rule, analysis, case)
            
            # Determine recipients
            recipients = self._get_alert_recipients(rule, case)
            
            # Determine response requirements
            requires_response = rule.alert_type in [
                AlertType.COURT_ORDER, AlertType.CONTEMPT_WARNING,
                AlertType.SANCTIONS_ORDER, AlertType.EMERGENCY_MOTION
            ]
            
            response_deadline = None
            if requires_response:
                response_deadline = datetime.now() + timedelta(minutes=15)
            
            alert = Alert(
                alert_id=alert_id,
                alert_type=rule.alert_type,
                severity=rule.severity,
                title=title,
                message=message,
                details={
                    "rule_id": rule.rule_id,
                    "segment_text": segment.text,
                    "speaker": segment.speaker,
                    "timestamp": segment.timestamp,
                    "analysis": analysis,
                    "case_title": case.title
                },
                case_id=case.id,
                session_id=getattr(segment, 'session_id', None),
                timestamp=datetime.now(),
                source_segment=segment,
                recipients=recipients,
                channels=rule.channels,
                status=AlertStatus.PENDING,
                requires_response=requires_response,
                response_deadline=response_deadline,
                automated_actions=self._get_automated_actions(rule.alert_type)
            )
            
            # Store alert
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # Schedule escalation if needed
            if rule.escalation_delay and rule.escalation_recipients:
                alert.escalation_time = datetime.now() + timedelta(minutes=rule.escalation_delay)
                self.escalation_tasks[alert_id] = asyncio.create_task(
                    self._schedule_escalation(alert, rule.escalation_recipients, rule.escalation_delay)
                )
            
            return alert
            
        except Exception as e:
            print(f"Error creating alert: {e}")
            raise

    async def _generate_alert_content(
        self,
        rule: AlertRule,
        analysis: Dict[str, Any],
        case: Case
    ) -> tuple[str, str]:
        """Generate alert title and message content."""
        try:
            # Use AI to generate contextual alert content
            prompt = f"""
            Generate an urgent alert for a critical courtroom development:
            
            Alert Type: {rule.alert_type.value}
            Severity: {rule.severity.value}
            Case: {case.title} ({case.case_type})
            Speaker: {analysis.get('speaker', 'Unknown')}
            Keywords Detected: {', '.join(analysis.get('keywords', []))}
            Urgency: {analysis.get('urgency', 'medium')}
            
            Segment Text: {analysis.get('text', '')[:500]}
            
            Generate:
            1. A concise, urgent alert title (under 60 characters)
            2. A clear alert message explaining what happened and why it's critical
            
            Format as JSON:
            {{
                "title": "Urgent alert title",
                "message": "Clear explanation of the critical development and its implications"
            }}
            """
            
            response = await self.ai_client.generate_completion(
                prompt,
                model="gpt-4",
                temperature=0.1,
                max_tokens=300
            )
            
            content = json.loads(response)
            return content.get("title", f"Critical {rule.alert_type.value}"), content.get("message", rule.description)
            
        except Exception as e:
            print(f"Error generating alert content: {e}")
            return f"Critical {rule.alert_type.value}", rule.description

    def _get_alert_recipients(self, rule: AlertRule, case: Case) -> List[str]:
        """Get list of recipients for the alert."""
        recipients = []
        
        # Add rule-specific recipients
        recipients.extend(rule.recipients)
        
        # Add case-specific recipients (would be from case.assigned_attorneys, etc.)
        # This would be implemented based on case assignment logic
        
        return recipients

    def _get_automated_actions(self, alert_type: AlertType) -> List[str]:
        """Get automated actions to perform for alert type."""
        actions = []
        
        if alert_type == AlertType.COURT_ORDER:
            actions.extend([
                "Create compliance task",
                "Schedule deadline reminder",
                "Update case status"
            ])
        elif alert_type == AlertType.CONTEMPT_WARNING:
            actions.extend([
                "Flag for immediate attorney review",
                "Create incident report",
                "Escalate to senior attorney"
            ])
        elif alert_type == AlertType.SETTLEMENT_OFFER:
            actions.extend([
                "Create settlement evaluation task",
                "Schedule client consultation",
                "Document offer details"
            ])
        elif alert_type == AlertType.SMOKING_GUN_EVIDENCE:
            actions.extend([
                "Flag for case strategy review",
                "Create evidence analysis task",
                "Schedule team meeting"
            ])
        
        return actions

    async def _send_alert(self, alert: Alert):
        """Send alert through all specified channels."""
        try:
            delivery_tasks = []
            
            for channel in alert.channels:
                if channel in self.delivery_handlers:
                    task = asyncio.create_task(
                        self._deliver_via_channel(alert, channel)
                    )
                    delivery_tasks.append(task)
            
            # Wait for all deliveries to complete
            if delivery_tasks:
                await asyncio.gather(*delivery_tasks, return_exceptions=True)
            
            alert.status = AlertStatus.SENT
            
            # Execute automated actions
            await self._execute_automated_actions(alert)
            
        except Exception as e:
            print(f"Error sending alert {alert.alert_id}: {e}")

    async def _deliver_via_channel(self, alert: Alert, channel: AlertChannel):
        """Deliver alert via specific channel."""
        try:
            delivery_attempt = {
                "channel": channel.value,
                "timestamp": datetime.now().isoformat(),
                "status": "attempting"
            }
            
            if channel == AlertChannel.WEBSOCKET:
                await self._send_websocket_alert(alert)
            elif channel == AlertChannel.PUSH_NOTIFICATION:
                await self._send_push_notification(alert)
            elif channel == AlertChannel.SMS:
                await self._send_sms_alert(alert)
            elif channel == AlertChannel.EMAIL:
                await self._send_email_alert(alert)
            elif channel == AlertChannel.PHONE_CALL:
                await self._make_phone_call(alert)
            elif channel == AlertChannel.SLACK:
                await self._send_slack_alert(alert)
            elif channel == AlertChannel.TEAMS:
                await self._send_teams_alert(alert)
            
            delivery_attempt["status"] = "success"
            
        except Exception as e:
            delivery_attempt["status"] = "failed"
            delivery_attempt["error"] = str(e)
            print(f"Failed to deliver alert via {channel.value}: {e}")
        finally:
            alert.delivery_attempts.append(delivery_attempt)

    async def _send_websocket_alert(self, alert: Alert):
        """Send alert via WebSocket to connected clients."""
        # Implementation would integrate with WebSocket manager
        print(f"WebSocket Alert: {alert.title}")
        
    async def _send_push_notification(self, alert: Alert):
        """Send push notification to mobile devices."""
        # Implementation would integrate with push notification service
        print(f"Push Notification: {alert.title}")
        
    async def _send_sms_alert(self, alert: Alert):
        """Send SMS alert to recipients."""
        # Implementation would integrate with SMS service (Twilio, etc.)
        print(f"SMS Alert: {alert.title}")
        
    async def _send_email_alert(self, alert: Alert):
        """Send email alert to recipients."""
        # Implementation would integrate with email service
        print(f"Email Alert: {alert.title}")
        
    async def _make_phone_call(self, alert: Alert):
        """Make phone call for critical alerts."""
        # Implementation would integrate with voice calling service
        print(f"Phone Call Alert: {alert.title}")
        
    async def _send_slack_alert(self, alert: Alert):
        """Send alert to Slack channels."""
        # Implementation would integrate with Slack API
        print(f"Slack Alert: {alert.title}")
        
    async def _send_teams_alert(self, alert: Alert):
        """Send alert to Microsoft Teams."""
        # Implementation would integrate with Teams API
        print(f"Teams Alert: {alert.title}")

    async def _execute_automated_actions(self, alert: Alert):
        """Execute automated actions for the alert."""
        try:
            for action in alert.automated_actions:
                print(f"Executing automated action: {action}")
                # Implementation would execute specific actions
                
        except Exception as e:
            print(f"Error executing automated actions: {e}")

    async def _schedule_escalation(self, alert: Alert, escalation_recipients: List[str], delay_minutes: int):
        """Schedule alert escalation after delay."""
        try:
            await asyncio.sleep(delay_minutes * 60)
            
            # Check if alert is still unacknowledged
            if alert.status not in [AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED]:
                await self._escalate_alert(alert, escalation_recipients)
                
        except asyncio.CancelledError:
            print(f"Escalation cancelled for alert {alert.alert_id}")
        except Exception as e:
            print(f"Error in escalation scheduling: {e}")

    async def _escalate_alert(self, alert: Alert, escalation_recipients: List[str]):
        """Escalate alert to higher-level recipients."""
        try:
            escalated_alert = Alert(
                alert_id=str(uuid.uuid4()),
                alert_type=alert.alert_type,
                severity=AlertSeverity.CRITICAL,  # Escalated alerts are always critical
                title=f"ESCALATED: {alert.title}",
                message=f"ESCALATION: Original alert not acknowledged. {alert.message}",
                details=alert.details,
                case_id=alert.case_id,
                session_id=alert.session_id,
                timestamp=datetime.now(),
                source_segment=alert.source_segment,
                recipients=escalation_recipients,
                channels=[AlertChannel.PHONE_CALL, AlertChannel.SMS, AlertChannel.PUSH_NOTIFICATION],
                status=AlertStatus.PENDING,
                requires_response=True,
                response_deadline=datetime.now() + timedelta(minutes=5)
            )
            
            alert.status = AlertStatus.ESCALATED
            await self._send_alert(escalated_alert)
            
        except Exception as e:
            print(f"Error escalating alert: {e}")

    def acknowledge_alert(self, alert_id: str, user_id: str, response: Optional[str] = None) -> bool:
        """Acknowledge an alert."""
        try:
            if alert_id not in self.active_alerts:
                return False
            
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            
            acknowledgment = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "response": response
            }
            alert.acknowledgments.append(acknowledgment)
            
            # Cancel escalation if scheduled
            if alert_id in self.escalation_tasks:
                self.escalation_tasks[alert_id].cancel()
                del self.escalation_tasks[alert_id]
            
            return True
            
        except Exception as e:
            print(f"Error acknowledging alert: {e}")
            return False

    def resolve_alert(self, alert_id: str, user_id: str, resolution_notes: Optional[str] = None) -> bool:
        """Resolve an alert."""
        try:
            if alert_id not in self.active_alerts:
                return False
            
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_time = datetime.now()
            
            if resolution_notes:
                alert.details["resolution_notes"] = resolution_notes
                alert.details["resolved_by"] = user_id
            
            # Cancel escalation if scheduled
            if alert_id in self.escalation_tasks:
                self.escalation_tasks[alert_id].cancel()
                del self.escalation_tasks[alert_id]
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            return True
            
        except Exception as e:
            print(f"Error resolving alert: {e}")
            return False

    def add_alert_rule(self, rule: AlertRule) -> bool:
        """Add a new alert rule."""
        try:
            self.alert_rules[rule.rule_id] = rule
            return True
        except Exception as e:
            print(f"Error adding alert rule: {e}")
            return False

    def remove_alert_rule(self, rule_id: str) -> bool:
        """Remove an alert rule."""
        try:
            if rule_id in self.alert_rules:
                del self.alert_rules[rule_id]
                return True
            return False
        except Exception as e:
            print(f"Error removing alert rule: {e}")
            return False

    def add_recipient(self, recipient: AlertRecipient) -> bool:
        """Add alert recipient."""
        try:
            self.recipients[recipient.user_id] = recipient
            return True
        except Exception as e:
            print(f"Error adding recipient: {e}")
            return False

    def get_active_alerts(self, case_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of active alerts."""
        alerts = list(self.active_alerts.values())
        
        if case_id:
            alerts = [alert for alert in alerts if alert.case_id == case_id]
        
        return [
            {
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "status": alert.status.value,
                "requires_response": alert.requires_response,
                "response_deadline": alert.response_deadline.isoformat() if alert.response_deadline else None
            }
            for alert in alerts
        ]

    def get_alert_statistics(self, time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get alert system statistics."""
        try:
            alerts = self.alert_history
            
            if time_range:
                start_time, end_time = time_range
                alerts = [a for a in alerts if start_time <= a.timestamp <= end_time]
            
            # Calculate statistics
            total_alerts = len(alerts)
            alerts_by_type = {}
            alerts_by_severity = {}
            
            for alert in alerts:
                alert_type = alert.alert_type.value
                severity = alert.severity.value
                
                alerts_by_type[alert_type] = alerts_by_type.get(alert_type, 0) + 1
                alerts_by_severity[severity] = alerts_by_severity.get(severity, 0) + 1
            
            # Response times
            acknowledged_alerts = [a for a in alerts if a.acknowledgments]
            avg_response_time = None
            
            if acknowledged_alerts:
                response_times = []
                for alert in acknowledged_alerts:
                    if alert.acknowledgments:
                        ack_time = datetime.fromisoformat(alert.acknowledgments[0]["timestamp"])
                        response_time = (ack_time - alert.timestamp).total_seconds() / 60
                        response_times.append(response_time)
                
                avg_response_time = sum(response_times) / len(response_times)
            
            return {
                "total_alerts": total_alerts,
                "active_alerts": len(self.active_alerts),
                "alerts_by_type": alerts_by_type,
                "alerts_by_severity": alerts_by_severity,
                "average_response_time_minutes": avg_response_time,
                "escalated_alerts": len([a for a in alerts if a.status == AlertStatus.ESCALATED]),
                "resolved_alerts": len([a for a in alerts if a.status == AlertStatus.RESOLVED])
            }
            
        except Exception as e:
            print(f"Error getting alert statistics: {e}")
            return {}

    def register_delivery_handler(self, channel: AlertChannel, handler: Callable):
        """Register a delivery handler for a specific channel."""
        self.delivery_handlers[channel] = handler

    async def test_alert_system(self, case: Case) -> bool:
        """Test the alert system with a mock alert."""
        try:
            test_rule = AlertRule(
                rule_id="test_rule",
                name="Test Alert",
                description="Test alert for system verification",
                trigger_conditions={"keywords": ["test"]},
                alert_type=AlertType.INFORMATIONAL,
                severity=AlertSeverity.LOW,
                recipients=[],
                channels=[AlertChannel.IN_APP]
            )
            
            # Create mock segment
            test_segment = TranscriptSegment(
                id="test_segment",
                session_id="test_session",
                speaker="Test Speaker",
                text="This is a test message",
                timestamp=0.0,
                duration=1.0,
                confidence=1.0
            )
            
            # Process test segment
            alerts = await self.process_transcript_segment(test_segment, case)
            
            return len(alerts) > 0
            
        except Exception as e:
            print(f"Error testing alert system: {e}")
            return False