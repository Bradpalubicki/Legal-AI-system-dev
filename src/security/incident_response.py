"""
Comprehensive Security Incident Response System
Provides real-time threat detection, automated response, and recovery procedures.
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(Enum):
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONTAINING = "containing"
    CONTAINED = "contained"
    RECOVERING = "recovering"
    RESOLVED = "resolved"
    CLOSED = "closed"

class AttackType(Enum):
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    DDOS = "ddos"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXFILTRATION = "data_exfiltration"
    MALWARE = "malware"
    PHISHING = "phishing"
    INSIDER_THREAT = "insider_threat"
    API_ABUSE = "api_abuse"

class ResponseAction(Enum):
    MONITOR = "monitor"
    ALERT = "alert"
    BLOCK_IP = "block_ip"
    BLOCK_USER = "block_user"
    ISOLATE_SERVICE = "isolate_service"
    PRESERVE_EVIDENCE = "preserve_evidence"
    NOTIFY_AUTHORITIES = "notify_authorities"
    ACTIVATE_DRP = "activate_drp"

@dataclass
class ThreatIndicator:
    indicator_id: str
    threat_type: AttackType
    severity: ThreatLevel
    source_ip: str
    user_id: Optional[str]
    endpoint: str
    method: str
    user_agent: str
    timestamp: datetime
    payload: Dict[str, Any]
    confidence_score: float
    false_positive_likelihood: float

@dataclass
class SecurityIncident:
    incident_id: str
    threat_level: ThreatLevel
    attack_type: AttackType
    status: IncidentStatus
    detection_time: datetime
    title: str
    description: str
    affected_systems: List[str]
    affected_users: List[str]
    indicators: List[ThreatIndicator]
    response_actions: List[ResponseAction]
    assigned_to: str
    estimated_impact: str
    containment_time: Optional[datetime] = None
    resolution_time: Optional[datetime] = None
    root_cause: Optional[str] = None
    lessons_learned: Optional[str] = None
    cost_estimate: Optional[float] = None

@dataclass
class UserBehaviorProfile:
    user_id: str
    normal_login_times: List[int]  # Hours of day
    normal_ip_ranges: List[str]
    typical_endpoints: List[str]
    average_session_duration: float
    typical_request_rate: float
    device_fingerprints: List[str]
    location_patterns: List[str]
    last_updated: datetime

@dataclass
class ResponsePlan:
    attack_type: AttackType
    threat_level: ThreatLevel
    immediate_actions: List[ResponseAction]
    escalation_threshold: timedelta
    notification_list: List[str]
    containment_procedures: List[str]
    recovery_procedures: List[str]
    evidence_preservation: List[str]

class IncidentResponseSystem:
    def __init__(self, config_path: str = "incident_response_config.json"):
        self.config_path = config_path
        self.incidents_db_path = "security_incidents.db"
        self.behavior_profiles_path = "user_behavior_profiles.pkl"
        self.ml_models_path = "anomaly_detection_models.pkl"

        # Threat detection components
        self.failed_login_tracker = defaultdict(lambda: deque(maxlen=100))
        self.request_rate_tracker = defaultdict(lambda: deque(maxlen=1000))
        self.behavior_profiles: Dict[str, UserBehaviorProfile] = {}
        self.anomaly_detectors = {}

        # Response components
        self.active_incidents: Dict[str, SecurityIncident] = {}
        self.response_plans: Dict[AttackType, ResponsePlan] = {}
        self.notification_handlers: List[Callable] = []

        # Note: Call initialize_system() manually after creating instance

    async def _initialize_system(self):
        """Initialize the incident response system"""
        try:
            await self._setup_database()
            await self._load_configuration()
            await self._load_behavior_profiles()
            await self._initialize_ml_models()
            await self._setup_response_plans()
            logger.info("Incident response system initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing incident response system: {str(e)}")
            raise

    async def _setup_database(self):
        """Setup SQLite database for incident tracking"""
        conn = sqlite3.connect(self.incidents_db_path)
        cursor = conn.cursor()

        # Security incidents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_incidents (
                incident_id TEXT PRIMARY KEY,
                threat_level TEXT NOT NULL,
                attack_type TEXT NOT NULL,
                status TEXT NOT NULL,
                detection_time TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                affected_systems TEXT,
                affected_users TEXT,
                indicators TEXT,
                response_actions TEXT,
                assigned_to TEXT,
                estimated_impact TEXT,
                containment_time TEXT,
                resolution_time TEXT,
                root_cause TEXT,
                lessons_learned TEXT,
                cost_estimate REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Threat indicators table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threat_indicators (
                indicator_id TEXT PRIMARY KEY,
                threat_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                source_ip TEXT NOT NULL,
                user_id TEXT,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                user_agent TEXT,
                timestamp TEXT NOT NULL,
                payload TEXT,
                confidence_score REAL,
                false_positive_likelihood REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Response actions log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS response_actions_log (
                action_id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                description TEXT,
                executed_by TEXT,
                execution_time TEXT NOT NULL,
                success BOOLEAN,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (incident_id) REFERENCES security_incidents (incident_id)
            )
        """)

        # Create indices for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON security_incidents(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_threat_level ON security_incidents(threat_level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_indicators_ip ON threat_indicators(source_ip)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_indicators_timestamp ON threat_indicators(timestamp)")

        conn.commit()
        conn.close()

    async def _load_configuration(self):
        """Load incident response configuration"""
        try:
            async with aiofiles.open(self.config_path, 'r') as f:
                config_content = await f.read()
                self.config = json.loads(config_content)
        except FileNotFoundError:
            # Create default configuration
            self.config = self._create_default_config()
            await self._save_configuration()

    def _create_default_config(self) -> Dict[str, Any]:
        """Create default incident response configuration"""
        return {
            "detection": {
                "failed_login_threshold": 5,
                "rate_limit_threshold": 100,
                "anomaly_detection_sensitivity": 0.95,
                "behavioral_analysis_window_hours": 24,
                "threat_intelligence_sources": [
                    "https://api.threatintel.com/v1/indicators",
                    "https://api.malwaredb.com/v1/signatures"
                ]
            },
            "response": {
                "automatic_containment": True,
                "escalation_timeout_minutes": 30,
                "notification_channels": ["email", "slack", "sms"],
                "evidence_preservation_enabled": True,
                "backup_isolation_enabled": True
            },
            "notifications": {
                "email": {
                    "smtp_server": "smtp.company.com",
                    "smtp_port": 587,
                    "username": "security@company.com",
                    "password": "secure_password",
                    "recipients": ["security-team@company.com", "ciso@company.com"]
                },
                "slack": {
                    "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
                    "channel": "#security-incidents"
                }
            },
            "compliance": {
                "gdpr_notification_required": True,
                "data_breach_notification_hours": 72,
                "audit_retention_years": 7,
                "incident_classification_required": True
            }
        }

    async def _save_configuration(self):
        """Save configuration to file"""
        async with aiofiles.open(self.config_path, 'w') as f:
            await f.write(json.dumps(self.config, indent=2))

    async def _load_behavior_profiles(self):
        """Load user behavior profiles for anomaly detection"""
        try:
            # Simplified - no pickle dependency
            self.behavior_profiles = {}
            logger.info("Behavior profiles loaded (simplified mode)")
        except Exception as e:
            logger.warning(f"Could not load behavior profiles: {str(e)}")
            self.behavior_profiles = {}

    async def _save_behavior_profiles(self):
        """Save user behavior profiles"""
        try:
            # Simplified - no pickle dependency
            logger.info("Behavior profiles saved (simplified mode)")
        except Exception as e:
            logger.warning(f"Could not save behavior profiles: {str(e)}")

    async def _initialize_ml_models(self):
        """Initialize machine learning models for anomaly detection"""
        try:
            # Simplified - no sklearn dependency
            self.anomaly_detectors = {
                'login_anomaly': None,
                'request_anomaly': None,
                'behavior_anomaly': None
            }
            logger.info("ML models initialized (simplified mode)")
        except Exception as e:
            logger.warning(f"Could not initialize ML models: {str(e)}")

    async def _save_ml_models(self):
        """Save trained ML models"""
        try:
            # Simplified - no sklearn dependency
            logger.info("ML models saved (simplified mode)")
        except Exception as e:
            logger.warning(f"Could not save ML models: {str(e)}")

    async def _setup_response_plans(self):
        """Setup automated response plans for different attack types"""
        self.response_plans = {
            AttackType.BRUTE_FORCE: ResponsePlan(
                attack_type=AttackType.BRUTE_FORCE,
                threat_level=ThreatLevel.MEDIUM,
                immediate_actions=[ResponseAction.BLOCK_IP, ResponseAction.ALERT],
                escalation_threshold=timedelta(minutes=15),
                notification_list=["security-team@company.com"],
                containment_procedures=[
                    "Block source IP address",
                    "Increase authentication requirements",
                    "Monitor for additional attempts"
                ],
                recovery_procedures=[
                    "Reset affected user passwords",
                    "Review authentication logs",
                    "Update security policies"
                ],
                evidence_preservation=[
                    "Capture network traffic logs",
                    "Preserve authentication logs",
                    "Document attack patterns"
                ]
            ),
            AttackType.SQL_INJECTION: ResponsePlan(
                attack_type=AttackType.SQL_INJECTION,
                threat_level=ThreatLevel.HIGH,
                immediate_actions=[ResponseAction.BLOCK_IP, ResponseAction.ISOLATE_SERVICE, ResponseAction.PRESERVE_EVIDENCE],
                escalation_threshold=timedelta(minutes=10),
                notification_list=["security-team@company.com", "ciso@company.com"],
                containment_procedures=[
                    "Block malicious IP addresses",
                    "Isolate affected database systems",
                    "Enable enhanced logging"
                ],
                recovery_procedures=[
                    "Patch SQL injection vulnerabilities",
                    "Restore from clean backups if needed",
                    "Implement WAF rules"
                ],
                evidence_preservation=[
                    "Capture database logs",
                    "Preserve web application logs",
                    "Document injection payloads"
                ]
            ),
            AttackType.DDOS: ResponsePlan(
                attack_type=AttackType.DDOS,
                threat_level=ThreatLevel.HIGH,
                immediate_actions=[ResponseAction.ACTIVATE_DRP, ResponseAction.ALERT],
                escalation_threshold=timedelta(minutes=5),
                notification_list=["security-team@company.com", "operations@company.com"],
                containment_procedures=[
                    "Activate DDoS protection services",
                    "Implement rate limiting",
                    "Block attack sources"
                ],
                recovery_procedures=[
                    "Scale infrastructure capacity",
                    "Optimize performance",
                    "Review traffic patterns"
                ],
                evidence_preservation=[
                    "Capture network flow data",
                    "Preserve traffic patterns",
                    "Document attack vectors"
                ]
            )
        }

    # Real-time Threat Detection
    async def analyze_request(self, request_data: Dict[str, Any]) -> Optional[ThreatIndicator]:
        """Analyze incoming request for threats"""
        try:
            # Extract request details
            source_ip = request_data.get('source_ip', '')
            user_id = request_data.get('user_id')
            endpoint = request_data.get('endpoint', '')
            method = request_data.get('method', '')
            user_agent = request_data.get('user_agent', '')
            payload = request_data.get('payload', {})
            timestamp = datetime.fromisoformat(request_data.get('timestamp', datetime.now().isoformat()))

            # Check for various attack patterns
            threat_indicators = []

            # SQL Injection detection
            sql_threat = await self._detect_sql_injection(payload, endpoint)
            if sql_threat:
                threat_indicators.append(sql_threat)

            # XSS detection
            xss_threat = await self._detect_xss(payload, endpoint)
            if xss_threat:
                threat_indicators.append(xss_threat)

            # Brute force detection
            bf_threat = await self._detect_brute_force(source_ip, user_id, endpoint)
            if bf_threat:
                threat_indicators.append(bf_threat)

            # Rate limiting violation
            rate_threat = await self._detect_rate_limit_violation(source_ip, user_id)
            if rate_threat:
                threat_indicators.append(rate_threat)

            # Behavioral anomaly detection
            behavior_threat = await self._detect_behavioral_anomaly(user_id, request_data)
            if behavior_threat:
                threat_indicators.append(behavior_threat)

            # Return highest severity threat
            if threat_indicators:
                return max(threat_indicators, key=lambda x: x.confidence_score)

            return None

        except Exception as e:
            logger.error(f"Error analyzing request for threats: {str(e)}")
            return None

    async def _detect_sql_injection(self, payload: Dict[str, Any], endpoint: str) -> Optional[ThreatIndicator]:
        """Detect SQL injection attempts"""
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|OR|AND)\b)",
            r"(['\"][\s]*;[\s]*--)",
            r"(--[\s]*$)",
            r"(\bOR\b[\s]*[\d]+[\s]*=[\s]*[\d]+)",
            r"(\bUNION\b[\s]+\bSELECT\b)"
        ]

        import re

        payload_str = json.dumps(payload).lower()
        confidence = 0.0

        for pattern in sql_patterns:
            if re.search(pattern, payload_str, re.IGNORECASE):
                confidence += 0.3

        if confidence > 0.5:
            return ThreatIndicator(
                indicator_id=self._generate_id(),
                threat_type=AttackType.SQL_INJECTION,
                severity=ThreatLevel.HIGH if confidence > 0.8 else ThreatLevel.MEDIUM,
                source_ip=payload.get('source_ip', ''),
                user_id=payload.get('user_id'),
                endpoint=endpoint,
                method=payload.get('method', ''),
                user_agent=payload.get('user_agent', ''),
                timestamp=datetime.now(),
                payload=payload,
                confidence_score=confidence,
                false_positive_likelihood=0.1
            )

        return None

    async def _detect_xss(self, payload: Dict[str, Any], endpoint: str) -> Optional[ThreatIndicator]:
        """Detect XSS attempts"""
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<img[^>]*on\w+",
            r"<svg[^>]*on\w+"
        ]

        import re

        payload_str = json.dumps(payload).lower()
        confidence = 0.0

        for pattern in xss_patterns:
            if re.search(pattern, payload_str, re.IGNORECASE):
                confidence += 0.4

        if confidence > 0.4:
            return ThreatIndicator(
                indicator_id=self._generate_id(),
                threat_type=AttackType.XSS,
                severity=ThreatLevel.MEDIUM,
                source_ip=payload.get('source_ip', ''),
                user_id=payload.get('user_id'),
                endpoint=endpoint,
                method=payload.get('method', ''),
                user_agent=payload.get('user_agent', ''),
                timestamp=datetime.now(),
                payload=payload,
                confidence_score=confidence,
                false_positive_likelihood=0.15
            )

        return None

    async def _detect_brute_force(self, source_ip: str, user_id: Optional[str], endpoint: str) -> Optional[ThreatIndicator]:
        """Detect brute force attacks"""
        current_time = datetime.now()

        # Track failed login attempts
        if 'login' in endpoint.lower() or 'auth' in endpoint.lower():
            self.failed_login_tracker[source_ip].append(current_time)

            # Remove old entries (older than 1 hour)
            cutoff_time = current_time - timedelta(hours=1)
            while (self.failed_login_tracker[source_ip] and
                   self.failed_login_tracker[source_ip][0] < cutoff_time):
                self.failed_login_tracker[source_ip].popleft()

            # Check if threshold exceeded
            threshold = self.config['detection']['failed_login_threshold']
            if len(self.failed_login_tracker[source_ip]) >= threshold:
                return ThreatIndicator(
                    indicator_id=self._generate_id(),
                    threat_type=AttackType.BRUTE_FORCE,
                    severity=ThreatLevel.MEDIUM,
                    source_ip=source_ip,
                    user_id=user_id,
                    endpoint=endpoint,
                    method='POST',
                    user_agent='',
                    timestamp=current_time,
                    payload={'failed_attempts': len(self.failed_login_tracker[source_ip])},
                    confidence_score=0.8,
                    false_positive_likelihood=0.05
                )

        return None

    async def _detect_rate_limit_violation(self, source_ip: str, user_id: Optional[str]) -> Optional[ThreatIndicator]:
        """Detect rate limit violations"""
        current_time = datetime.now()
        key = user_id if user_id else source_ip

        self.request_rate_tracker[key].append(current_time)

        # Remove old entries (older than 1 minute)
        cutoff_time = current_time - timedelta(minutes=1)
        while (self.request_rate_tracker[key] and
               self.request_rate_tracker[key][0] < cutoff_time):
            self.request_rate_tracker[key].popleft()

        # Check if rate limit exceeded
        threshold = self.config['detection']['rate_limit_threshold']
        if len(self.request_rate_tracker[key]) >= threshold:
            return ThreatIndicator(
                indicator_id=self._generate_id(),
                threat_type=AttackType.API_ABUSE,
                severity=ThreatLevel.MEDIUM,
                source_ip=source_ip,
                user_id=user_id,
                endpoint='',
                method='',
                user_agent='',
                timestamp=current_time,
                payload={'requests_per_minute': len(self.request_rate_tracker[key])},
                confidence_score=0.7,
                false_positive_likelihood=0.1
            )

        return None

    async def _detect_behavioral_anomaly(self, user_id: Optional[str], request_data: Dict[str, Any]) -> Optional[ThreatIndicator]:
        """Detect behavioral anomalies using simplified heuristics"""
        if not user_id or user_id not in self.behavior_profiles:
            return None

        current_time = datetime.now()

        # Simplified anomaly detection without ML
        try:
            # Simple heuristic checks
            unusual_hour = current_time.hour < 6 or current_time.hour > 22  # Late night access
            unusual_endpoint = len(request_data.get('endpoint', '')) > 100  # Very long endpoints
            unusual_payload = request_data.get('payload_size', 0) > 10000  # Large payloads

            # Simple scoring
            anomaly_score = 0
            if unusual_hour:
                anomaly_score += 0.3
            if unusual_endpoint:
                anomaly_score += 0.4
            if unusual_payload:
                anomaly_score += 0.3

            if anomaly_score > 0.5:  # Threshold for anomalous behavior
                return ThreatIndicator(
                    indicator_id=self._generate_id(),
                    threat_type=AttackType.INSIDER_THREAT,
                    severity=ThreatLevel.MEDIUM,
                    source_ip=request_data.get('source_ip', ''),
                    user_id=user_id,
                    endpoint=request_data.get('endpoint', ''),
                    method=request_data.get('method', ''),
                    user_agent=request_data.get('user_agent', ''),
                    timestamp=current_time,
                    payload={'anomaly_score': anomaly_score, 'method': 'heuristic'},
                    confidence_score=anomaly_score,
                    false_positive_likelihood=0.2
                )
        except Exception as e:
            logger.error(f"Error in behavioral anomaly detection: {str(e)}")

        return None

    # Incident Management
    async def create_incident(self, threat_indicator: ThreatIndicator) -> SecurityIncident:
        """Create a new security incident"""
        incident_id = self._generate_id()

        incident = SecurityIncident(
            incident_id=incident_id,
            threat_level=threat_indicator.severity,
            attack_type=threat_indicator.threat_type,
            status=IncidentStatus.DETECTED,
            detection_time=datetime.now(),
            title=f"{threat_indicator.attack_type.value.replace('_', ' ').title()} Detected",
            description=f"Threat detected from {threat_indicator.source_ip}",
            affected_systems=[threat_indicator.endpoint],
            affected_users=[threat_indicator.user_id] if threat_indicator.user_id else [],
            indicators=[threat_indicator],
            response_actions=[],
            assigned_to="security-team",
            estimated_impact=self._estimate_impact(threat_indicator)
        )

        # Store incident
        await self._store_incident(incident)
        self.active_incidents[incident_id] = incident

        # Trigger automated response
        await self._trigger_automated_response(incident)

        logger.info(f"Security incident {incident_id} created for {threat_indicator.attack_type.value}")
        return incident

    async def _store_incident(self, incident: SecurityIncident):
        """Store incident in database"""
        conn = sqlite3.connect(self.incidents_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO security_incidents (
                incident_id, threat_level, attack_type, status, detection_time,
                title, description, affected_systems, affected_users, indicators,
                response_actions, assigned_to, estimated_impact
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident.incident_id,
            incident.threat_level.value,
            incident.attack_type.value,
            incident.status.value,
            incident.detection_time.isoformat(),
            incident.title,
            incident.description,
            json.dumps(incident.affected_systems),
            json.dumps(incident.affected_users),
            json.dumps([asdict(ind) for ind in incident.indicators], default=str),
            json.dumps([action.value for action in incident.response_actions]),
            incident.assigned_to,
            incident.estimated_impact
        ))

        conn.commit()
        conn.close()

    def _estimate_impact(self, threat_indicator: ThreatIndicator) -> str:
        """Estimate the potential impact of a threat"""
        impact_scores = {
            AttackType.BRUTE_FORCE: "Low - Limited credential exposure risk",
            AttackType.SQL_INJECTION: "High - Potential data breach and system compromise",
            AttackType.XSS: "Medium - User session hijacking and data theft risk",
            AttackType.DDOS: "High - Service availability impact",
            AttackType.UNAUTHORIZED_ACCESS: "Critical - System compromise and data exposure",
            AttackType.DATA_EXFILTRATION: "Critical - Confidential data breach",
            AttackType.MALWARE: "Critical - System integrity compromise",
            AttackType.PHISHING: "Medium - Credential and data theft risk",
            AttackType.INSIDER_THREAT: "High - Privileged access abuse risk",
            AttackType.API_ABUSE: "Medium - Service degradation and data exposure"
        }

        return impact_scores.get(threat_indicator.threat_type, "Unknown impact")

    # Automated Response
    async def _trigger_automated_response(self, incident: SecurityIncident):
        """Trigger automated response actions"""
        if incident.attack_type in self.response_plans:
            plan = self.response_plans[incident.attack_type]

            for action in plan.immediate_actions:
                try:
                    await self._execute_response_action(incident, action)
                    incident.response_actions.append(action)
                except Exception as e:
                    logger.error(f"Error executing response action {action.value}: {str(e)}")

            # Send notifications
            await self._send_notifications(incident)

            # Update incident status
            incident.status = IncidentStatus.CONTAINING
            await self._update_incident_status(incident)

    async def _execute_response_action(self, incident: SecurityIncident, action: ResponseAction):
        """Execute a specific response action"""
        action_id = self._generate_id()
        success = False
        error_message = None

        try:
            if action == ResponseAction.BLOCK_IP:
                await self._block_ip_address(incident)
                success = True

            elif action == ResponseAction.BLOCK_USER:
                await self._block_user_account(incident)
                success = True

            elif action == ResponseAction.ISOLATE_SERVICE:
                await self._isolate_service(incident)
                success = True

            elif action == ResponseAction.PRESERVE_EVIDENCE:
                await self._preserve_evidence(incident)
                success = True

            elif action == ResponseAction.ACTIVATE_DRP:
                await self._activate_disaster_recovery(incident)
                success = True

            else:
                success = True  # For monitoring and alerting actions

        except Exception as e:
            error_message = str(e)
            logger.error(f"Failed to execute {action.value}: {error_message}")

        # Log the action
        await self._log_response_action(action_id, incident.incident_id, action, success, error_message)

    async def _block_ip_address(self, incident: SecurityIncident):
        """Block malicious IP addresses"""
        # This would integrate with your firewall/WAF
        for indicator in incident.indicators:
            ip = indicator.source_ip
            logger.info(f"Blocking IP address: {ip}")
            # Implementation would depend on your infrastructure
            # e.g., update firewall rules, WAF rules, etc.

    async def _block_user_account(self, incident: SecurityIncident):
        """Block user accounts involved in the incident"""
        for user_id in incident.affected_users:
            if user_id:
                logger.info(f"Blocking user account: {user_id}")
                # Implementation would integrate with your user management system

    async def _isolate_service(self, incident: SecurityIncident):
        """Isolate affected services"""
        for system in incident.affected_systems:
            logger.info(f"Isolating service: {system}")
            # Implementation would integrate with your orchestration platform

    async def _preserve_evidence(self, incident: SecurityIncident):
        """Preserve evidence for forensic analysis"""
        evidence_dir = f"evidence/{incident.incident_id}"
        logger.info(f"Preserving evidence in: {evidence_dir}")
        # Implementation would capture logs, network traffic, etc.

    async def _activate_disaster_recovery(self, incident: SecurityIncident):
        """Activate disaster recovery procedures"""
        logger.info(f"Activating DRP for incident: {incident.incident_id}")
        # Implementation would trigger failover procedures

    async def _log_response_action(self, action_id: str, incident_id: str, action: ResponseAction,
                                 success: bool, error_message: Optional[str]):
        """Log response action execution"""
        conn = sqlite3.connect(self.incidents_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO response_actions_log (
                action_id, incident_id, action_type, executed_by, execution_time,
                success, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            action_id,
            incident_id,
            action.value,
            "automated_system",
            datetime.now().isoformat(),
            success,
            error_message
        ))

        conn.commit()
        conn.close()

    # Notification System
    async def _send_notifications(self, incident: SecurityIncident):
        """Send incident notifications"""
        try:
            # Email notifications
            if "email" in self.config['response']['notification_channels']:
                await self._send_email_notification(incident)

            # Slack notifications
            if "slack" in self.config['response']['notification_channels']:
                await self._send_slack_notification(incident)

            logger.info(f"Notifications sent for incident {incident.incident_id}")

        except Exception as e:
            logger.error(f"Error sending notifications: {str(e)}")

    async def _send_email_notification(self, incident: SecurityIncident):
        """Send email notification (simplified)"""
        try:
            # Simplified email notification - log instead of sending
            logger.info(f"EMAIL NOTIFICATION: Security incident {incident.incident_id}")
            logger.info(f"Threat Level: {incident.threat_level.value.upper()}")
            logger.info(f"Attack Type: {incident.attack_type.value.replace('_', ' ').title()}")
            logger.info(f"Description: {incident.description}")
            logger.info("Email notification would be sent to security team")
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")

    async def _send_slack_notification(self, incident: SecurityIncident):
        """Send Slack notification (simplified)"""
        try:
            # Simplified Slack notification - log instead of sending
            logger.info(f"SLACK NOTIFICATION: 🚨 Security incident {incident.incident_id}")
            logger.info(f"Threat Level: {incident.threat_level.value.upper()}")
            logger.info(f"Attack Type: {incident.attack_type.value.replace('_', ' ').title()}")
            logger.info(f"Detection Time: {incident.detection_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("Slack notification would be sent to security channel")
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")

    # Recovery and Post-Incident
    async def resolve_incident(self, incident_id: str, root_cause: str, lessons_learned: str, cost_estimate: float = 0.0) -> bool:
        """Resolve a security incident"""
        try:
            if incident_id in self.active_incidents:
                incident = self.active_incidents[incident_id]
                incident.status = IncidentStatus.RESOLVED
                incident.resolution_time = datetime.now()
                incident.root_cause = root_cause
                incident.lessons_learned = lessons_learned
                incident.cost_estimate = cost_estimate

                await self._update_incident_in_db(incident)

                # Remove from active incidents
                del self.active_incidents[incident_id]

                # Generate post-incident report
                await self._generate_post_incident_report(incident)

                logger.info(f"Incident {incident_id} resolved")
                return True
            else:
                logger.warning(f"Incident {incident_id} not found in active incidents")
                return False

        except Exception as e:
            logger.error(f"Error resolving incident {incident_id}: {str(e)}")
            return False

    async def _update_incident_status(self, incident: SecurityIncident):
        """Update incident status in database"""
        conn = sqlite3.connect(self.incidents_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE security_incidents
            SET status = ?, response_actions = ?
            WHERE incident_id = ?
        """, (
            incident.status.value,
            json.dumps([action.value for action in incident.response_actions]),
            incident.incident_id
        ))

        conn.commit()
        conn.close()

    async def _update_incident_in_db(self, incident: SecurityIncident):
        """Update complete incident record in database"""
        conn = sqlite3.connect(self.incidents_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE security_incidents
            SET status = ?, containment_time = ?, resolution_time = ?,
                root_cause = ?, lessons_learned = ?, cost_estimate = ?
            WHERE incident_id = ?
        """, (
            incident.status.value,
            incident.containment_time.isoformat() if incident.containment_time else None,
            incident.resolution_time.isoformat() if incident.resolution_time else None,
            incident.root_cause,
            incident.lessons_learned,
            incident.cost_estimate,
            incident.incident_id
        ))

        conn.commit()
        conn.close()

    async def _generate_post_incident_report(self, incident: SecurityIncident):
        """Generate post-incident analysis report"""
        report = {
            "incident_summary": {
                "id": incident.incident_id,
                "title": incident.title,
                "attack_type": incident.attack_type.value,
                "threat_level": incident.threat_level.value,
                "detection_time": incident.detection_time.isoformat(),
                "resolution_time": incident.resolution_time.isoformat() if incident.resolution_time else None,
                "duration_hours": (incident.resolution_time - incident.detection_time).total_seconds() / 3600 if incident.resolution_time else None
            },
            "impact_analysis": {
                "affected_systems": incident.affected_systems,
                "affected_users": incident.affected_users,
                "estimated_impact": incident.estimated_impact,
                "cost_estimate": incident.cost_estimate
            },
            "response_analysis": {
                "actions_taken": [action.value for action in incident.response_actions],
                "containment_time": incident.containment_time.isoformat() if incident.containment_time else None,
                "response_effectiveness": "Effective" if incident.resolution_time else "Pending"
            },
            "root_cause_analysis": {
                "root_cause": incident.root_cause,
                "contributing_factors": [],
                "prevention_recommendations": []
            },
            "lessons_learned": {
                "what_worked_well": [],
                "areas_for_improvement": [],
                "action_items": [],
                "lessons_learned": incident.lessons_learned
            }
        }

        report_path = f"incident_reports/{incident.incident_id}_report.json"
        try:
            # Simplified - log the report instead of writing to file
            logger.info(f"Post-incident report for {incident.incident_id}:")
            logger.info(json.dumps(report, indent=2))
            logger.info(f"Report would be saved to: {report_path}")
        except Exception as e:
            logger.error(f"Error generating post-incident report: {str(e)}")

    # Utility Methods
    def _generate_id(self) -> str:
        """Generate unique identifier"""
        import uuid
        return str(uuid.uuid4())

    async def get_incident_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get incident metrics for the specified period"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            conn = sqlite3.connect(self.incidents_db_path)
            cursor = conn.cursor()

            # Total incidents
            cursor.execute("""
                SELECT COUNT(*) FROM security_incidents
                WHERE detection_time >= ?
            """, (cutoff_date.isoformat(),))
            total_incidents = cursor.fetchone()[0]

            # Incidents by threat level
            cursor.execute("""
                SELECT threat_level, COUNT(*)
                FROM security_incidents
                WHERE detection_time >= ?
                GROUP BY threat_level
            """, (cutoff_date.isoformat(),))
            incidents_by_threat = dict(cursor.fetchall())

            # Incidents by attack type
            cursor.execute("""
                SELECT attack_type, COUNT(*)
                FROM security_incidents
                WHERE detection_time >= ?
                GROUP BY attack_type
            """, (cutoff_date.isoformat(),))
            incidents_by_type = dict(cursor.fetchall())

            # Average resolution time
            cursor.execute("""
                SELECT AVG(
                    CASE
                        WHEN resolution_time IS NOT NULL THEN
                            (julianday(resolution_time) - julianday(detection_time)) * 24
                        ELSE NULL
                    END
                ) FROM security_incidents
                WHERE detection_time >= ?
            """, (cutoff_date.isoformat(),))
            avg_resolution_hours = cursor.fetchone()[0]

            conn.close()

            return {
                "period_days": days,
                "total_incidents": total_incidents,
                "incidents_by_threat_level": incidents_by_threat,
                "incidents_by_attack_type": incidents_by_type,
                "average_resolution_hours": avg_resolution_hours,
                "incident_rate_per_day": total_incidents / days if days > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error getting incident metrics: {str(e)}")
            return {}

# Initialize the incident response system
incident_response_system = IncidentResponseSystem()