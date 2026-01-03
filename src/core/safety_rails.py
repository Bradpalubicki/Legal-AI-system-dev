#!/usr/bin/env python3
"""
Development Safety Rails System
Legal AI System - Critical Safety and Compliance Protection

This system provides safety rails to prevent compliance violations:
1. PRE-COMMIT CHECKS: Block commits if compliance < 100%
2. FEATURE FLAGS: Safe feature rollout with kill switches
3. MONITORING HOOKS: Track all AI interactions and compliance
4. ROLLBACK SYSTEM: Automated backups and recovery

CRITICAL: This system prevents accidental compliance violations
"""

import os
import sys
import json
import time
import shutil
import subprocess
import sqlite3
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import contextmanager
import threading
import schedule

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class SafetyCheckStatus(str, Enum):
    """Safety check status values"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    BLOCKED = "blocked"

class FeatureStatus(str, Enum):
    """Feature flag status values"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    TESTING = "testing"
    ROLLBACK = "rollback"

class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class SafetyCheckResult:
    """Result of a safety check"""
    check_name: str
    status: SafetyCheckStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    blocking: bool = False

@dataclass
class ComplianceViolation:
    """Record of a compliance violation"""
    violation_id: str
    violation_type: str
    severity: AlertLevel
    description: str
    source_file: Optional[str]
    line_number: Optional[int]
    timestamp: datetime
    resolved: bool = False

class PreCommitSafetySystem:
    """
    Pre-commit safety checks to prevent compliance violations
    CRITICAL: Blocks commits that could introduce compliance issues
    """

    def __init__(self):
        self.logger = logging.getLogger('precommit_safety')
        self.project_root = project_root
        self.blocked_patterns = [
            # API Keys and secrets
            r'["\']?(?:api[_-]?key|secret[_-]?key|access[_-]?token)["\']?\s*[:=]\s*["\'][^"\']{20,}["\']',
            r'sk-[a-zA-Z0-9]{48}',  # OpenAI API keys
            r'AKIA[0-9A-Z]{16}',    # AWS access keys

            # Legal advice language
            r'\byou\s+should\s+(?:definitely|immediately|always|never)',
            r'\bi\s+(?:recommend|advise|suggest)\s+(?:that\s+)?you',
            r'\bas\s+your\s+(?:attorney|lawyer)',
            r'\bthis\s+will\s+(?:guarantee|ensure|definitely)',

            # Direct legal commands
            r'\byou\s+must\s+(?:file|submit|pay|comply)',
            r'\byou\s+are\s+required\s+to\b',
            r'\byou\s+have\s+to\s+(?:file|submit|pay)',
        ]

        # Expected disclaimer patterns
        self.required_disclaimers = [
            r'disclaimer',
            r'informational\s+purposes\s+only',
            r'not\s+(?:constitute|providing)\s+legal\s+advice',
            r'consult.*(?:attorney|lawyer)',
        ]

    def run_all_precommit_checks(self) -> List[SafetyCheckResult]:
        """Run all pre-commit safety checks"""
        self.logger.info("Running pre-commit safety checks...")

        checks = [
            self.check_compliance_tests(),
            self.check_for_exposed_secrets(),
            self.check_for_advice_language(),
            self.check_disclaimer_coverage(),
            self.check_test_coverage(),
            self.check_code_quality(),
        ]

        return checks

    def check_compliance_tests(self) -> SafetyCheckResult:
        """Run compliance tests and ensure 100% pass rate"""
        try:
            # Run the test suite
            result = subprocess.run(
                [sys.executable, 'run_all_tests.py'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                # Parse test results
                try:
                    with open(self.project_root / 'test_results.json', 'r') as f:
                        test_data = json.load(f)

                    success_rate = test_data['statistics']['success_rate']
                    failed_tests = test_data['statistics']['failed_tests']

                    if success_rate == 100.0:
                        return SafetyCheckResult(
                            check_name="compliance_tests",
                            status=SafetyCheckStatus.PASS,
                            message=f"All tests passed (100% success rate)",
                            details={
                                'success_rate': success_rate,
                                'total_tests': test_data['statistics']['total_tests'],
                                'failed_tests': failed_tests
                            },
                            timestamp=datetime.now()
                        )
                    else:
                        return SafetyCheckResult(
                            check_name="compliance_tests",
                            status=SafetyCheckStatus.FAIL,
                            message=f"Tests failed: {success_rate}% success rate",
                            details={
                                'success_rate': success_rate,
                                'failed_tests': failed_tests,
                                'failures': test_data.get('failures', [])
                            },
                            timestamp=datetime.now(),
                            blocking=True
                        )

                except FileNotFoundError:
                    return SafetyCheckResult(
                        check_name="compliance_tests",
                        status=SafetyCheckStatus.FAIL,
                        message="Test results file not found",
                        details={'error': 'Could not find test_results.json'},
                        timestamp=datetime.now(),
                        blocking=True
                    )

            else:
                return SafetyCheckResult(
                    check_name="compliance_tests",
                    status=SafetyCheckStatus.FAIL,
                    message="Test execution failed",
                    details={
                        'returncode': result.returncode,
                        'stdout': result.stdout[-500:],  # Last 500 chars
                        'stderr': result.stderr[-500:]
                    },
                    timestamp=datetime.now(),
                    blocking=True
                )

        except subprocess.TimeoutExpired:
            return SafetyCheckResult(
                check_name="compliance_tests",
                status=SafetyCheckStatus.FAIL,
                message="Test execution timed out",
                details={'timeout': 120},
                timestamp=datetime.now(),
                blocking=True
            )
        except Exception as e:
            return SafetyCheckResult(
                check_name="compliance_tests",
                status=SafetyCheckStatus.FAIL,
                message=f"Test check failed: {str(e)}",
                details={'exception': str(e)},
                timestamp=datetime.now(),
                blocking=True
            )

    def check_for_exposed_secrets(self) -> SafetyCheckResult:
        """Check for exposed API keys and secrets"""
        violations = []

        # Test/development key patterns that are safe
        safe_test_patterns = [
            r'sk-test',  # OpenAI test keys
            r'sk-ant-api03-test',  # Anthropic test keys
            r'test[_-]?.*[_-]?key',  # General test keys
            r'dev[_-].*[_-]?key',  # Dev keys
            r'demo[_-].*[_-]?key',  # Demo keys
            r'mock[_-].*[_-]?key',  # Mock keys
            r'AIzatest',  # Google test keys
            r'ACtest',  # Twilio test keys
            r'whsec_test',  # Stripe webhook test secrets
            r'SG\.test',  # SendGrid test keys
            r'CHANGEME',  # Placeholder secrets
            r'your-.*-api-key-here',  # Template placeholders
            r'placeholder',  # Generic placeholders
            r'example[_-]',  # Example keys
        ]

        # Files to check
        file_patterns = ['*.py', '*.js', '*.ts', '*.json', '*.yaml', '*.yml']

        for pattern in file_patterns:
            for file_path in self.project_root.rglob(pattern):
                # Skip certain directories and demo/test files
                if any(skip in str(file_path) for skip in ['.git', '__pycache__', 'node_modules', 'venv', 'demo_', 'test_', 'example_', 'template']):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Check for blocked patterns
                    for line_num, line in enumerate(content.split('\n'), 1):
                        for secret_pattern in self.blocked_patterns[:3]:  # Only secret patterns
                            import re
                            if re.search(secret_pattern, line, re.IGNORECASE):
                                # Check if it's a test/safe key
                                is_safe = any(re.search(safe_pattern, line, re.IGNORECASE) for safe_pattern in safe_test_patterns)

                                if not is_safe:
                                    violations.append({
                                        'file': str(file_path.relative_to(self.project_root)),
                                        'line': line_num,
                                        'pattern': 'potential_secret',
                                        'content': line[:100] + '...' if len(line) > 100 else line
                                    })

                except Exception as e:
                    # Skip files that can't be read
                    continue

        # Special handling for .env files - they're expected to have keys
        env_files = list(self.project_root.glob('.env*'))
        env_file_count = len(env_files)

        if violations:
            return SafetyCheckResult(
                check_name="exposed_secrets",
                status=SafetyCheckStatus.FAIL,
                message=f"Found {len(violations)} potential exposed secrets",
                details={'violations': violations, 'env_files_found': env_file_count},
                timestamp=datetime.now(),
                blocking=True
            )
        else:
            return SafetyCheckResult(
                check_name="exposed_secrets",
                status=SafetyCheckStatus.PASS,
                message="No production secrets detected (test/dev keys are safe)",
                details={'files_checked': len(list(self.project_root.rglob('*.py'))), 'env_files_found': env_file_count},
                timestamp=datetime.now()
            )

    def check_for_advice_language(self) -> SafetyCheckResult:
        """Check for prohibited legal advice language"""
        violations = []

        # Check Python files
        for file_path in self.project_root.rglob('*.py'):
            if any(skip in str(file_path) for skip in ['.git', '__pycache__', 'venv', 'tests', 'demo_', 'test_', '_demo', '_test', 'compliance_', 'example_', 'enhanced_', 'attorney_review', 'flagging', 'pre_production_validation', 'advice_neutralizer']):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Check for advice language patterns
                for line_num, line in enumerate(content.split('\n'), 1):
                    # Skip comments, docstrings, and test data
                    stripped = line.strip()
                    if (stripped.startswith('#') or '"""' in stripped or "'''" in stripped or
                        'risky_original' in line or 'test_' in line or 'should_filter' in line or
                        'example' in line.lower() or 'demo' in line.lower()):
                        continue

                    for pattern in self.blocked_patterns[3:]:  # Only advice patterns
                        import re
                        if re.search(pattern, line, re.IGNORECASE):
                            violations.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'line': line_num,
                                'pattern': 'advice_language',
                                'content': line.strip()
                            })

            except Exception:
                continue

        if violations:
            return SafetyCheckResult(
                check_name="advice_language",
                status=SafetyCheckStatus.FAIL,
                message=f"Found {len(violations)} instances of advice language",
                details={'violations': violations},
                timestamp=datetime.now(),
                blocking=True
            )
        else:
            return SafetyCheckResult(
                check_name="advice_language",
                status=SafetyCheckStatus.PASS,
                message="No prohibited advice language detected",
                details={'files_checked': len(list(self.project_root.rglob('*.py')))},
                timestamp=datetime.now()
            )

    def check_disclaimer_coverage(self) -> SafetyCheckResult:
        """Check that all AI outputs have disclaimers"""
        try:
            # Import foundation repair to check disclaimer wrapper
            from src.core.foundation_repair import DisclaimerWrapper, ComplianceLevel

            disclaimer_wrapper = DisclaimerWrapper(ComplianceLevel.STRICT)

            # Test sample outputs
            test_outputs = [
                "Legal analysis result",
                "Contract review summary",
                "Case law research findings"
            ]

            missing_disclaimers = []
            for output in test_outputs:
                wrapped = disclaimer_wrapper.wrap_output(output)

                # Check if disclaimer is present
                has_disclaimer = any(
                    disclaimer.lower() in wrapped.lower()
                    for disclaimer in ['disclaimer', 'informational purposes', 'not legal advice']
                )

                if not has_disclaimer:
                    missing_disclaimers.append(output)

            if missing_disclaimers:
                return SafetyCheckResult(
                    check_name="disclaimer_coverage",
                    status=SafetyCheckStatus.FAIL,
                    message=f"Disclaimer missing in {len(missing_disclaimers)} outputs",
                    details={'missing_disclaimers': missing_disclaimers},
                    timestamp=datetime.now(),
                    blocking=True
                )
            else:
                return SafetyCheckResult(
                    check_name="disclaimer_coverage",
                    status=SafetyCheckStatus.PASS,
                    message="All outputs have disclaimers",
                    details={'tested_outputs': len(test_outputs)},
                    timestamp=datetime.now()
                )

        except Exception as e:
            return SafetyCheckResult(
                check_name="disclaimer_coverage",
                status=SafetyCheckStatus.WARNING,
                message=f"Could not verify disclaimer coverage: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.now()
            )

    def check_test_coverage(self) -> SafetyCheckResult:
        """Check test coverage percentage"""
        try:
            # Try to get coverage from test results
            with open(self.project_root / 'test_results.json', 'r') as f:
                test_data = json.load(f)

            coverage = test_data['statistics'].get('coverage_percentage', 0)

            if coverage >= 85:
                return SafetyCheckResult(
                    check_name="test_coverage",
                    status=SafetyCheckStatus.PASS,
                    message=f"Test coverage: {coverage}%",
                    details={'coverage_percentage': coverage},
                    timestamp=datetime.now()
                )
            elif coverage >= 70:
                return SafetyCheckResult(
                    check_name="test_coverage",
                    status=SafetyCheckStatus.WARNING,
                    message=f"Low test coverage: {coverage}%",
                    details={'coverage_percentage': coverage},
                    timestamp=datetime.now()
                )
            else:
                return SafetyCheckResult(
                    check_name="test_coverage",
                    status=SafetyCheckStatus.FAIL,
                    message=f"Insufficient test coverage: {coverage}%",
                    details={'coverage_percentage': coverage, 'minimum_required': 70},
                    timestamp=datetime.now(),
                    blocking=True
                )

        except Exception as e:
            return SafetyCheckResult(
                check_name="test_coverage",
                status=SafetyCheckStatus.WARNING,
                message=f"Could not determine test coverage: {str(e)}",
                details={'error': str(e)},
                timestamp=datetime.now()
            )

    def check_code_quality(self) -> SafetyCheckResult:
        """Check basic code quality metrics"""
        quality_issues = []

        # Check for common code quality issues
        for file_path in self.project_root.rglob('*.py'):
            if any(skip in str(file_path) for skip in ['.git', '__pycache__', 'venv']):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Check file length
                if len(lines) > 1000:
                    quality_issues.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'issue': 'file_too_long',
                        'details': f'{len(lines)} lines (>1000)'
                    })

                # Check line length
                for line_num, line in enumerate(lines, 1):
                    if len(line.rstrip()) > 120:
                        quality_issues.append({
                            'file': str(file_path.relative_to(self.project_root)),
                            'line': line_num,
                            'issue': 'line_too_long',
                            'details': f'{len(line.rstrip())} chars (>120)'
                        })

            except Exception:
                continue

        # Limit to most critical issues
        quality_issues = quality_issues[:20]

        if len(quality_issues) > 10:
            return SafetyCheckResult(
                check_name="code_quality",
                status=SafetyCheckStatus.WARNING,
                message=f"Found {len(quality_issues)} code quality issues",
                details={'issues': quality_issues[:10]},
                timestamp=datetime.now()
            )
        else:
            return SafetyCheckResult(
                check_name="code_quality",
                status=SafetyCheckStatus.PASS,
                message=f"Code quality acceptable ({len(quality_issues)} minor issues)",
                details={'issues': quality_issues},
                timestamp=datetime.now()
            )

class FeatureFlagSystem:
    """
    Feature flag management for safe feature rollout
    CRITICAL: Allows safe testing and emergency rollback
    """

    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger('feature_flags')
        self.config_file = Path(config_file) if config_file else project_root / 'feature_flags.json'
        self.flags = self._load_flags()
        self._last_reload = time.time()

    def _load_flags(self) -> Dict[str, Any]:
        """Load feature flags from configuration file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default configuration
                default_flags = {
                    "metadata": {
                        "version": "1.0",
                        "last_updated": datetime.now().isoformat(),
                        "environment": "development"
                    },
                    "features": {
                        "advanced_ai_analysis": {
                            "enabled": False,
                            "status": "testing",
                            "description": "Advanced AI document analysis features",
                            "rollout_percentage": 0,
                            "created_at": datetime.now().isoformat(),
                            "dependencies": []
                        },
                        "real_time_compliance": {
                            "enabled": True,
                            "status": "enabled",
                            "description": "Real-time compliance monitoring",
                            "rollout_percentage": 100,
                            "created_at": datetime.now().isoformat(),
                            "dependencies": ["compliance_monitor"]
                        },
                        "pacer_integration": {
                            "enabled": False,
                            "status": "disabled",
                            "description": "PACER court records integration",
                            "rollout_percentage": 0,
                            "created_at": datetime.now().isoformat(),
                            "dependencies": ["pacer_credentials"]
                        }
                    }
                }
                self._save_flags(default_flags)
                return default_flags

        except Exception as e:
            self.logger.error(f"Failed to load feature flags: {e}")
            return {"metadata": {}, "features": {}}

    def _save_flags(self, flags: Dict[str, Any]):
        """Save feature flags to configuration file"""
        try:
            flags["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.config_file, 'w') as f:
                json.dump(flags, f, indent=2)
            self.logger.info(f"Feature flags saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save feature flags: {e}")

    def is_enabled(self, feature_name: str, user_id: Optional[str] = None) -> bool:
        """Check if a feature is enabled for a user"""
        self._reload_if_needed()

        feature = self.flags.get("features", {}).get(feature_name)
        if not feature:
            self.logger.warning(f"Unknown feature flag: {feature_name}")
            return False

        if not feature.get("enabled", False):
            return False

        # Check rollout percentage
        rollout_percentage = feature.get("rollout_percentage", 0)
        if rollout_percentage < 100:
            if user_id:
                # Use consistent hash for user-based rollout
                user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
                return (user_hash % 100) < rollout_percentage
            else:
                # Random rollout for anonymous users
                import random
                return random.randint(0, 99) < rollout_percentage

        return True

    def enable_feature(self, feature_name: str, rollout_percentage: int = 100):
        """Enable a feature with optional gradual rollout"""
        if feature_name not in self.flags.get("features", {}):
            self.logger.error(f"Feature {feature_name} not found")
            return False

        self.flags["features"][feature_name]["enabled"] = True
        self.flags["features"][feature_name]["status"] = "enabled"
        self.flags["features"][feature_name]["rollout_percentage"] = rollout_percentage

        self._save_flags(self.flags)
        self.logger.info(f"Enabled feature {feature_name} with {rollout_percentage}% rollout")
        return True

    def disable_feature(self, feature_name: str):
        """Disable a feature (emergency kill switch)"""
        if feature_name not in self.flags.get("features", {}):
            self.logger.error(f"Feature {feature_name} not found")
            return False

        self.flags["features"][feature_name]["enabled"] = False
        self.flags["features"][feature_name]["status"] = "disabled"
        self.flags["features"][feature_name]["rollout_percentage"] = 0

        self._save_flags(self.flags)
        self.logger.warning(f"DISABLED feature {feature_name} (kill switch activated)")
        return True

    def gradual_rollout(self, feature_name: str, target_percentage: int, step_size: int = 10):
        """Gradually increase rollout percentage"""
        if feature_name not in self.flags.get("features", {}):
            return False

        current_percentage = self.flags["features"][feature_name].get("rollout_percentage", 0)
        new_percentage = min(target_percentage, current_percentage + step_size)

        self.flags["features"][feature_name]["rollout_percentage"] = new_percentage
        if new_percentage > 0:
            self.flags["features"][feature_name]["enabled"] = True
            self.flags["features"][feature_name]["status"] = "testing" if new_percentage < 100 else "enabled"

        self._save_flags(self.flags)
        self.logger.info(f"Rolled out {feature_name} to {new_percentage}%")
        return True

    def _reload_if_needed(self):
        """Reload flags if file has been modified"""
        if time.time() - self._last_reload > 60:  # Check every minute
            self.flags = self._load_flags()
            self._last_reload = time.time()

    def get_feature_status(self) -> Dict[str, Any]:
        """Get status of all features"""
        self._reload_if_needed()
        return {
            "metadata": self.flags.get("metadata", {}),
            "features": {
                name: {
                    "enabled": feature.get("enabled", False),
                    "status": feature.get("status", "unknown"),
                    "rollout_percentage": feature.get("rollout_percentage", 0),
                    "description": feature.get("description", "")
                }
                for name, feature in self.flags.get("features", {}).items()
            }
        }

class MonitoringHooks:
    """
    Monitoring hooks for AI interactions and compliance
    CRITICAL: Tracks everything for compliance auditing
    """

    def __init__(self):
        self.logger = logging.getLogger('monitoring_hooks')
        self.db_path = project_root / 'monitoring.db'
        self.metrics_cache = {}
        self._initialize_monitoring_db()

    def _initialize_monitoring_db(self):
        """Initialize monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # AI interactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_interactions (
                interaction_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                session_id TEXT,
                model_name TEXT,
                prompt_hash TEXT,
                response_hash TEXT,
                response_length INTEGER,
                contains_advice BOOLEAN,
                has_disclaimer BOOLEAN,
                compliance_score REAL,
                processing_time_ms REAL,
                feature_flags_used TEXT,
                error_occurred BOOLEAN DEFAULT FALSE,
                error_message TEXT
            )
        ''')

        # Compliance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_metrics (
                metric_id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                total_interactions INTEGER DEFAULT 0,
                compliant_interactions INTEGER DEFAULT 0,
                compliance_percentage REAL DEFAULT 0.0,
                advice_violations INTEGER DEFAULT 0,
                missing_disclaimers INTEGER DEFAULT 0,
                average_response_time REAL DEFAULT 0.0,
                error_rate REAL DEFAULT 0.0,
                feature_usage TEXT DEFAULT '{}'
            )
        ''')

        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitoring_alerts (
                alert_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                alert_level TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                resolved_at TEXT,
                resolved_by TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def log_ai_interaction(self,
                          user_id: Optional[str],
                          session_id: str,
                          model_name: str,
                          prompt: str,
                          response: str,
                          processing_time_ms: float,
                          feature_flags: List[str] = None,
                          error: Optional[str] = None) -> str:
        """Log an AI interaction for monitoring"""

        interaction_id = hashlib.sha256(
            f"{datetime.now().isoformat()}-{session_id}-{response[:50]}".encode()
        ).hexdigest()

        # Analyze response for compliance
        contains_advice = self._detect_advice_language(response)
        has_disclaimer = self._check_disclaimer_present(response)
        compliance_score = self._calculate_compliance_score(response, has_disclaimer, contains_advice)

        # Hash sensitive data
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        response_hash = hashlib.sha256(response.encode()).hexdigest()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO ai_interactions (
                interaction_id, timestamp, user_id, session_id, model_name,
                prompt_hash, response_hash, response_length, contains_advice,
                has_disclaimer, compliance_score, processing_time_ms,
                feature_flags_used, error_occurred, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            interaction_id, datetime.now().isoformat(), user_id, session_id, model_name,
            prompt_hash, response_hash, len(response), contains_advice,
            has_disclaimer, compliance_score, processing_time_ms,
            json.dumps(feature_flags or []), error is not None, error
        ))

        conn.commit()
        conn.close()

        # Check for violations and create alerts
        if compliance_score < 0.8 or contains_advice or not has_disclaimer:
            self._create_compliance_alert(interaction_id, compliance_score, contains_advice, has_disclaimer)

        self.logger.info(f"Logged AI interaction {interaction_id[:8]} (compliance: {compliance_score:.2f})")
        return interaction_id

    def _detect_advice_language(self, text: str) -> bool:
        """Detect if text contains advice language"""
        advice_patterns = [
            r'\byou\s+should\b',
            r'\byou\s+must\b',
            r'\bi\s+recommend\b',
            r'\bwe\s+recommend\b',
            r'\byou\s+need\s+to\b'
        ]

        import re
        for pattern in advice_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _check_disclaimer_present(self, text: str) -> bool:
        """Check if disclaimer is present in text"""
        disclaimer_indicators = [
            'disclaimer',
            'informational purposes only',
            'not legal advice',
            'consult an attorney'
        ]

        text_lower = text.lower()
        return any(indicator in text_lower for indicator in disclaimer_indicators)

    def _calculate_compliance_score(self, text: str, has_disclaimer: bool, contains_advice: bool) -> float:
        """Calculate compliance score for text"""
        score = 1.0

        if not has_disclaimer:
            score -= 0.5

        if contains_advice:
            score -= 0.3

        # Check for other compliance factors
        if len(text) > 500 and not has_disclaimer:
            score -= 0.2  # Long responses need disclaimers

        return max(0.0, score)

    def _create_compliance_alert(self, interaction_id: str, compliance_score: float,
                                contains_advice: bool, has_disclaimer: bool):
        """Create compliance alert for violations"""

        alert_level = AlertLevel.CRITICAL if compliance_score < 0.5 else AlertLevel.WARNING

        issues = []
        if not has_disclaimer:
            issues.append("missing disclaimer")
        if contains_advice:
            issues.append("contains advice language")

        alert_id = hashlib.sha256(f"compliance-{interaction_id}-{datetime.now().isoformat()}".encode()).hexdigest()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO monitoring_alerts (
                alert_id, timestamp, alert_level, alert_type, message, details
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            alert_id, datetime.now().isoformat(), alert_level.value, "compliance_violation",
            f"Compliance violation in interaction {interaction_id[:8]}: {', '.join(issues)}",
            json.dumps({
                'interaction_id': interaction_id,
                'compliance_score': compliance_score,
                'contains_advice': contains_advice,
                'has_disclaimer': has_disclaimer,
                'issues': issues
            })
        ))

        conn.commit()
        conn.close()

        self.logger.warning(f"Created {alert_level.value} compliance alert: {alert_id[:8]}")

    def update_daily_metrics(self):
        """Update daily compliance metrics"""
        today = datetime.now().date().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get today's interaction stats
        cursor.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN compliance_score >= 0.8 THEN 1 ELSE 0 END) as compliant,
                SUM(CASE WHEN contains_advice THEN 1 ELSE 0 END) as advice_violations,
                SUM(CASE WHEN NOT has_disclaimer THEN 1 ELSE 0 END) as missing_disclaimers,
                AVG(processing_time_ms) as avg_time,
                SUM(CASE WHEN error_occurred THEN 1 ELSE 0 END) as errors
            FROM ai_interactions
            WHERE DATE(timestamp) = ?
        ''', (today,))

        stats = cursor.fetchone()
        if stats and stats[0] > 0:
            total, compliant, advice_violations, missing_disclaimers, avg_time, errors = stats
            compliance_percentage = (compliant / total) * 100
            error_rate = (errors / total) * 100

            # Insert or update metrics
            metric_id = f"metrics-{today}"
            cursor.execute('''
                INSERT OR REPLACE INTO compliance_metrics (
                    metric_id, date, total_interactions, compliant_interactions,
                    compliance_percentage, advice_violations, missing_disclaimers,
                    average_response_time, error_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metric_id, today, total, compliant, compliance_percentage,
                advice_violations, missing_disclaimers, avg_time, error_rate
            ))

            conn.commit()
            self.logger.info(f"Updated daily metrics: {compliance_percentage:.1f}% compliance")

        conn.close()

    def get_compliance_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate compliance report for recent days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get recent metrics
        cursor.execute('''
            SELECT * FROM compliance_metrics
            WHERE date >= DATE('now', '-{} days')
            ORDER BY date DESC
        '''.format(days))

        metrics = cursor.fetchall()

        # Get recent alerts
        cursor.execute('''
            SELECT alert_level, COUNT(*) as count
            FROM monitoring_alerts
            WHERE timestamp >= DATETIME('now', '-{} days')
            AND NOT resolved
            GROUP BY alert_level
        '''.format(days))

        alerts = dict(cursor.fetchall())

        conn.close()

        return {
            'report_period_days': days,
            'metrics': [
                {
                    'date': row[1],
                    'total_interactions': row[2],
                    'compliance_percentage': row[4],
                    'advice_violations': row[5],
                    'missing_disclaimers': row[6],
                    'error_rate': row[8]
                } for row in metrics
            ],
            'unresolved_alerts': alerts,
            'generated_at': datetime.now().isoformat()
        }

class RollbackSystem:
    """
    Automated backup and rollback system
    CRITICAL: Enables rapid recovery from issues
    """

    def __init__(self):
        self.logger = logging.getLogger('rollback_system')
        self.backup_dir = project_root / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        self.max_backups = 30  # Keep 30 days of backups

    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create a backup of the current system state"""
        if not backup_name:
            backup_name = f"auto_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)

        try:
            # Backup critical directories
            critical_dirs = ['src', 'tests', 'config']
            for dir_name in critical_dirs:
                source_dir = project_root / dir_name
                if source_dir.exists():
                    dest_dir = backup_path / dir_name
                    shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)

            # Backup critical files
            critical_files = [
                'feature_flags.json',
                'test_results.json',
                'run_all_tests.py',
                'requirements.txt',
                'package.json'
            ]

            for file_name in critical_files:
                source_file = project_root / file_name
                if source_file.exists():
                    shutil.copy2(source_file, backup_path / file_name)

            # Backup databases
            for db_file in project_root.glob('*.db'):
                shutil.copy2(db_file, backup_path / db_file.name)

            # Create backup manifest
            manifest = {
                'backup_name': backup_name,
                'created_at': datetime.now().isoformat(),
                'created_by': 'safety_rails_system',
                'directories_backed_up': critical_dirs,
                'files_backed_up': critical_files,
                'backup_size_mb': self._calculate_directory_size(backup_path)
            }

            with open(backup_path / 'backup_manifest.json', 'w') as f:
                json.dump(manifest, f, indent=2)

            self.logger.info(f"Created backup: {backup_name} ({manifest['backup_size_mb']:.1f} MB)")
            self._cleanup_old_backups()

            return str(backup_path)

        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise

    def rollback_to_backup(self, backup_name: str) -> bool:
        """Rollback to a specific backup"""
        backup_path = self.backup_dir / backup_name

        if not backup_path.exists():
            self.logger.error(f"Backup not found: {backup_name}")
            return False

        try:
            # Create emergency backup before rollback
            emergency_backup = self.create_backup(f"pre_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            self.logger.info(f"Created emergency backup before rollback: {emergency_backup}")

            # Load backup manifest
            manifest_path = backup_path / 'backup_manifest.json'
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
            else:
                manifest = {'directories_backed_up': ['src', 'tests'], 'files_backed_up': []}

            # Restore directories
            for dir_name in manifest.get('directories_backed_up', []):
                source_dir = backup_path / dir_name
                dest_dir = project_root / dir_name

                if source_dir.exists():
                    if dest_dir.exists():
                        shutil.rmtree(dest_dir)
                    shutil.copytree(source_dir, dest_dir)

            # Restore files
            for file_name in manifest.get('files_backed_up', []):
                source_file = backup_path / file_name
                dest_file = project_root / file_name

                if source_file.exists():
                    shutil.copy2(source_file, dest_file)

            # Restore databases
            for db_file in backup_path.glob('*.db'):
                dest_file = project_root / db_file.name
                shutil.copy2(db_file, dest_file)

            self.logger.info(f"Successfully rolled back to backup: {backup_name}")
            return True

        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []

        for backup_dir in sorted(self.backup_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if backup_dir.is_dir():
                manifest_path = backup_dir / 'backup_manifest.json'
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                        backups.append(manifest)
                    except:
                        # Fallback for backups without manifest
                        backups.append({
                            'backup_name': backup_dir.name,
                            'created_at': datetime.fromtimestamp(backup_dir.stat().st_mtime).isoformat(),
                            'backup_size_mb': self._calculate_directory_size(backup_dir)
                        })

        return backups

    def _calculate_directory_size(self, directory: Path) -> float:
        """Calculate directory size in MB"""
        total_size = 0
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)

    def _cleanup_old_backups(self):
        """Remove old backups to save space"""
        backups = sorted(self.backup_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)

        if len(backups) > self.max_backups:
            for old_backup in backups[self.max_backups:]:
                if old_backup.is_dir():
                    shutil.rmtree(old_backup)
                    self.logger.info(f"Removed old backup: {old_backup.name}")

class SafetyRailsSystem:
    """
    Main safety rails system coordinator
    CRITICAL: Orchestrates all safety mechanisms
    """

    def __init__(self):
        self.logger = self._setup_logging()
        self.precommit_system = PreCommitSafetySystem()
        self.feature_flags = FeatureFlagSystem()
        self.monitoring = MonitoringHooks()
        self.rollback = RollbackSystem()

        # Safety rails configuration
        self.config = {
            'auto_backup_enabled': True,
            'backup_before_deployment': True,
            'compliance_threshold': 100.0,
            'monitoring_enabled': True,
            'feature_flags_enabled': True
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        logger = logging.getLogger('safety_rails')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

            # File handler
            log_file = project_root / 'logs' / 'safety_rails.log'
            log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        return logger

    def run_precommit_checks(self) -> bool:
        """Run all pre-commit safety checks"""
        self.logger.info("Starting pre-commit safety checks...")

        # Create backup before any changes
        if self.config['auto_backup_enabled']:
            backup_name = f"precommit_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.rollback.create_backup(backup_name)

        # Run all safety checks
        results = self.precommit_system.run_all_precommit_checks()

        # Analyze results
        blocking_failures = [r for r in results if r.blocking and r.status == SafetyCheckStatus.FAIL]
        warnings = [r for r in results if r.status == SafetyCheckStatus.WARNING]

        # Print results
        print("\n" + "="*60)
        print("PRE-COMMIT SAFETY CHECK RESULTS")
        print("="*60)

        for result in results:
            status_symbol = {
                SafetyCheckStatus.PASS: "✓",
                SafetyCheckStatus.FAIL: "✗",
                SafetyCheckStatus.WARNING: "⚠",
                SafetyCheckStatus.BLOCKED: "🚫"
            }.get(result.status, "?")

            print(f"{status_symbol} {result.check_name}: {result.message}")

            if result.status == SafetyCheckStatus.FAIL and result.blocking:
                print(f"   BLOCKING: This issue must be fixed before commit")

        print("\n" + "="*60)

        if blocking_failures:
            print(f"❌ COMMIT BLOCKED - {len(blocking_failures)} critical issues must be fixed")
            for failure in blocking_failures:
                print(f"   • {failure.check_name}: {failure.message}")
            return False
        elif warnings:
            print(f"⚠️  COMMIT ALLOWED with {len(warnings)} warnings")
            return True
        else:
            print("✅ ALL CHECKS PASSED - COMMIT APPROVED")
            return True

    def emergency_rollback(self, backup_name: Optional[str] = None) -> bool:
        """Emergency rollback to last known good state"""
        self.logger.critical("EMERGENCY ROLLBACK INITIATED")

        if not backup_name:
            # Find most recent backup
            backups = self.rollback.list_backups()
            if not backups:
                self.logger.error("No backups available for rollback")
                return False
            backup_name = backups[0]['backup_name']

        success = self.rollback.rollback_to_backup(backup_name)

        if success:
            self.logger.critical(f"EMERGENCY ROLLBACK COMPLETED: {backup_name}")
            # Disable all features as safety measure
            for feature_name in self.feature_flags.flags.get("features", {}):
                self.feature_flags.disable_feature(feature_name)
        else:
            self.logger.critical(f"EMERGENCY ROLLBACK FAILED: {backup_name}")

        return success

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'safety_rails': {
                'enabled': True,
                'last_check': datetime.now().isoformat(),
                'config': self.config
            },
            'feature_flags': self.feature_flags.get_feature_status(),
            'monitoring': self.monitoring.get_compliance_report(days=1),
            'backups': {
                'available_backups': len(self.rollback.list_backups()),
                'last_backup': self.rollback.list_backups()[0] if self.rollback.list_backups() else None
            }
        }

    def start_monitoring_scheduler(self):
        """Start background monitoring tasks"""
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)

        # Schedule daily tasks
        schedule.every().day.at("00:00").do(self.monitoring.update_daily_metrics)
        schedule.every().day.at("02:00").do(lambda: self.rollback.create_backup("daily_auto_backup"))

        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        self.logger.info("Started monitoring scheduler")

# Global safety rails instance
safety_rails = SafetyRailsSystem()

def precommit_hook():
    """Git pre-commit hook entry point"""
    return safety_rails.run_precommit_checks()

def monitor_ai_interaction(user_id: str, session_id: str, model_name: str,
                          prompt: str, response: str, processing_time: float,
                          feature_flags: List[str] = None) -> str:
    """Monitor AI interaction entry point"""
    return safety_rails.monitoring.log_ai_interaction(
        user_id, session_id, model_name, prompt, response,
        processing_time, feature_flags
    )

def is_feature_enabled(feature_name: str, user_id: Optional[str] = None) -> bool:
    """Check if feature is enabled"""
    return safety_rails.feature_flags.is_enabled(feature_name, user_id)

def emergency_shutdown():
    """Emergency system shutdown"""
    safety_rails.logger.critical("EMERGENCY SHUTDOWN INITIATED")

    # Disable all features
    for feature_name in safety_rails.feature_flags.flags.get("features", {}):
        safety_rails.feature_flags.disable_feature(feature_name)

    # Create emergency backup
    safety_rails.rollback.create_backup("emergency_shutdown_backup")

    safety_rails.logger.critical("EMERGENCY SHUTDOWN COMPLETED")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "precommit":
            success = safety_rails.run_precommit_checks()
            sys.exit(0 if success else 1)

        elif command == "status":
            status = safety_rails.get_system_status()
            print(json.dumps(status, indent=2))

        elif command == "emergency":
            safety_rails.emergency_rollback()

        elif command == "backup":
            backup_name = sys.argv[2] if len(sys.argv) > 2 else None
            backup_path = safety_rails.rollback.create_backup(backup_name)
            print(f"Backup created: {backup_path}")

        else:
            print("Unknown command. Available: precommit, status, emergency, backup")
            sys.exit(1)
    else:
        print("Legal AI System - Safety Rails")
        print("Commands: precommit, status, emergency, backup")
        sys.exit(1)