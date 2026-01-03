#!/usr/bin/env python3
"""
DISCLAIMER COMPLIANCE MONITORING

This script continuously monitors the system to ensure ALL pages and API responses
have proper legal disclaimers. It runs automated checks and sends alerts if any
page is found without required disclaimers.

CRITICAL: This monitor must run continuously in production to ensure legal compliance.
"""

import asyncio
import aiohttp
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import smtplib
from email.mime.text import MIMEText as MimeText
from email.mime.multipart import MimeMultipart
import os
import time

@dataclass
class DisclaimerCheck:
    page_url: str
    check_type: str
    status: str  # PASS, FAIL, ERROR
    details: str
    timestamp: datetime
    headers_present: Dict[str, bool]
    content_disclaimers: List[str]
    response_time_ms: float

@dataclass
class ComplianceAlert:
    alert_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    affected_pages: List[str]
    timestamp: datetime
    remediation: str

class DisclaimerComplianceMonitor:
    """Continuous monitoring system for disclaimer compliance"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.logger = self._setup_logging()
        self.session = None
        self.alerts = []
        
        # Pages and endpoints to monitor
        self.monitored_pages = [
            '/',
            '/research',
            '/contracts', 
            '/dashboard',
            '/analyze',
            '/profile',
            '/settings'
        ]
        
        self.monitored_api_endpoints = [
            '/api/health',
            '/api/research/search',
            '/api/contracts/analyze',
            '/api/dashboard/stats',
            '/api/analyze/document'
        ]
        
        # Required disclaimer elements
        self.required_headers = [
            'x-legal-disclaimer',
            'x-attorney-client',
            'x-compliance-protected',
            'x-disclaimer-required'
        ]
        
        self.required_content_patterns = [
            'not legal advice',
            'general information',
            'consult attorney',
            'educational purposes'
        ]

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for the monitor"""
        return {
            'base_url': 'http://localhost:3000',
            'api_base_url': 'http://localhost:8000',
            'check_interval_seconds': 300,  # 5 minutes
            'alert_threshold_failures': 3,
            'email_alerts': {
                'enabled': True,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'from_email': 'compliance@legalai.com',
                'to_emails': ['admin@legalai.com', 'legal@legalai.com'],
                'username': os.getenv('SMTP_USERNAME'),
                'password': os.getenv('SMTP_PASSWORD')
            },
            'slack_alerts': {
                'enabled': False,
                'webhook_url': os.getenv('SLACK_WEBHOOK_URL')
            }
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the monitor"""
        logger = logging.getLogger('disclaimer_compliance_monitor')
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler('disclaimer_compliance.log')
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)
        
        return logger

    async def start_monitoring(self):
        """Start continuous monitoring loop"""
        self.logger.info("Starting disclaimer compliance monitoring...")
        
        # Create HTTP session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        try:
            while True:
                await self._run_compliance_check_cycle()
                
                # Wait for next check interval
                await asyncio.sleep(self.config['check_interval_seconds'])
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
        finally:
            if self.session:
                await self.session.close()

    async def _run_compliance_check_cycle(self):
        """Run a complete compliance check cycle"""
        self.logger.info("Running disclaimer compliance check cycle...")
        
        start_time = datetime.utcnow()
        checks = []
        
        # Check frontend pages
        for page in self.monitored_pages:
            try:
                check_result = await self._check_page_disclaimers(page)
                checks.append(check_result)
            except Exception as e:
                self.logger.error(f"Error checking page {page}: {e}")
                checks.append(DisclaimerCheck(
                    page_url=page,
                    check_type='page',
                    status='ERROR',
                    details=f"Check failed: {str(e)}",
                    timestamp=datetime.utcnow(),
                    headers_present={},
                    content_disclaimers=[],
                    response_time_ms=0
                ))
        
        # Check API endpoints
        for endpoint in self.monitored_api_endpoints:
            try:
                check_result = await self._check_api_disclaimers(endpoint)
                checks.append(check_result)
            except Exception as e:
                self.logger.error(f"Error checking API {endpoint}: {e}")
                checks.append(DisclaimerCheck(
                    page_url=endpoint,
                    check_type='api',
                    status='ERROR',
                    details=f"Check failed: {str(e)}",
                    timestamp=datetime.utcnow(),
                    headers_present={},
                    content_disclaimers=[],
                    response_time_ms=0
                ))
        
        # Analyze results and generate alerts if needed
        await self._analyze_check_results(checks)
        
        # Log summary
        total_checks = len(checks)
        passed_checks = len([c for c in checks if c.status == 'PASS'])
        failed_checks = len([c for c in checks if c.status == 'FAIL'])
        error_checks = len([c for c in checks if c.status == 'ERROR'])
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        self.logger.info(
            f"Compliance check cycle complete: {passed_checks}/{total_checks} passed, "
            f"{failed_checks} failed, {error_checks} errors in {duration:.2f}s"
        )

    async def _check_page_disclaimers(self, page: str) -> DisclaimerCheck:
        """Check disclaimers on a frontend page"""
        url = f"{self.config['base_url']}{page}"
        start_time = time.time()
        
        try:
            async with self.session.get(url) as response:
                response_time_ms = (time.time() - start_time) * 1000
                
                # Check response headers
                headers_present = {}
                for header in self.required_headers:
                    headers_present[header] = header in response.headers
                
                # Check response content for disclaimer text
                content = await response.text()
                content_disclaimers = []
                
                for pattern in self.required_content_patterns:
                    if pattern.lower() in content.lower():
                        content_disclaimers.append(pattern)
                
                # Check for compliance markers in HTML
                has_compliance_markers = 'disclaimer-compliance-markers' in content
                
                # Determine overall status
                all_headers_present = all(headers_present.values())
                has_disclaimer_content = len(content_disclaimers) >= 2  # At least 2 patterns
                
                if all_headers_present and has_disclaimer_content and has_compliance_markers:
                    status = 'PASS'
                    details = f"All disclaimer requirements met"
                else:
                    status = 'FAIL'
                    issues = []
                    if not all_headers_present:
                        missing_headers = [h for h, present in headers_present.items() if not present]
                        issues.append(f"Missing headers: {missing_headers}")
                    if not has_disclaimer_content:
                        issues.append(f"Insufficient disclaimer content ({len(content_disclaimers)}/4 patterns)")
                    if not has_compliance_markers:
                        issues.append("Missing compliance markers")
                    details = "; ".join(issues)
                
                return DisclaimerCheck(
                    page_url=page,
                    check_type='page',
                    status=status,
                    details=details,
                    timestamp=datetime.utcnow(),
                    headers_present=headers_present,
                    content_disclaimers=content_disclaimers,
                    response_time_ms=response_time_ms
                )
                
        except Exception as e:
            return DisclaimerCheck(
                page_url=page,
                check_type='page',
                status='ERROR',
                details=f"Request failed: {str(e)}",
                timestamp=datetime.utcnow(),
                headers_present={},
                content_disclaimers=[],
                response_time_ms=(time.time() - start_time) * 1000
            )

    async def _check_api_disclaimers(self, endpoint: str) -> DisclaimerCheck:
        """Check disclaimers on an API endpoint"""
        url = f"{self.config['api_base_url']}{endpoint}"
        start_time = time.time()
        
        try:
            async with self.session.get(url) as response:
                response_time_ms = (time.time() - start_time) * 1000
                
                # Check response headers
                headers_present = {}
                for header in self.required_headers:
                    headers_present[header] = header in response.headers
                
                # For JSON responses, check for disclaimer in body
                content_disclaimers = []
                if response.headers.get('content-type', '').startswith('application/json'):
                    try:
                        data = await response.json()
                        if isinstance(data, dict):
                            # Check for disclaimer fields
                            if '_legal_disclaimer' in data:
                                content_disclaimers.append('_legal_disclaimer')
                            if '_compliance_info' in data:
                                content_disclaimers.append('_compliance_info')
                            
                            # Check if any message fields have disclaimers
                            for field in ['message', 'content', 'response', 'result']:
                                if field in data and isinstance(data[field], str):
                                    field_text = data[field].lower()
                                    for pattern in self.required_content_patterns:
                                        if pattern in field_text:
                                            content_disclaimers.append(f'{field}_{pattern}')
                    except json.JSONDecodeError:
                        pass
                
                # Determine status
                all_headers_present = all(headers_present.values())
                has_json_disclaimers = len(content_disclaimers) > 0
                
                if all_headers_present and has_json_disclaimers:
                    status = 'PASS'
                    details = f"API disclaimer requirements met"
                else:
                    status = 'FAIL'
                    issues = []
                    if not all_headers_present:
                        missing_headers = [h for h, present in headers_present.items() if not present]
                        issues.append(f"Missing headers: {missing_headers}")
                    if not has_json_disclaimers:
                        issues.append("No JSON disclaimer fields found")
                    details = "; ".join(issues)
                
                return DisclaimerCheck(
                    page_url=endpoint,
                    check_type='api',
                    status=status,
                    details=details,
                    timestamp=datetime.utcnow(),
                    headers_present=headers_present,
                    content_disclaimers=content_disclaimers,
                    response_time_ms=response_time_ms
                )
                
        except Exception as e:
            return DisclaimerCheck(
                page_url=endpoint,
                check_type='api',
                status='ERROR',
                details=f"Request failed: {str(e)}",
                timestamp=datetime.utcnow(),
                headers_present={},
                content_disclaimers=[],
                response_time_ms=(time.time() - start_time) * 1000
            )

    async def _analyze_check_results(self, checks: List[DisclaimerCheck]):
        """Analyze check results and generate alerts if needed"""
        
        failed_checks = [c for c in checks if c.status == 'FAIL']
        error_checks = [c for c in checks if c.status == 'ERROR']
        
        # Generate alerts for failures
        if failed_checks:
            alert = ComplianceAlert(
                alert_type='DISCLAIMER_COMPLIANCE_FAILURE',
                severity='CRITICAL',
                message=f"{len(failed_checks)} pages/endpoints missing required disclaimers",
                affected_pages=[c.page_url for c in failed_checks],
                timestamp=datetime.utcnow(),
                remediation="Immediate action required: Deploy missing disclaimers to all affected pages/endpoints"
            )
            
            await self._send_alert(alert)
            self.alerts.append(alert)
        
        # Generate alerts for errors
        if error_checks:
            alert = ComplianceAlert(
                alert_type='DISCLAIMER_CHECK_ERROR',
                severity='HIGH',
                message=f"{len(error_checks)} disclaimer checks failed due to errors",
                affected_pages=[c.page_url for c in error_checks],
                timestamp=datetime.utcnow(),
                remediation="Investigate system connectivity and endpoint availability"
            )
            
            await self._send_alert(alert)
            self.alerts.append(alert)
        
        # Save check results
        await self._save_check_results(checks)

    async def _send_alert(self, alert: ComplianceAlert):
        """Send alert via configured notification channels"""
        
        self.logger.warning(f"COMPLIANCE ALERT: {alert.message}")
        
        # Send email alert
        if self.config['email_alerts']['enabled']:
            try:
                await self._send_email_alert(alert)
            except Exception as e:
                self.logger.error(f"Failed to send email alert: {e}")
        
        # Send Slack alert
        if self.config['slack_alerts']['enabled']:
            try:
                await self._send_slack_alert(alert)
            except Exception as e:
                self.logger.error(f"Failed to send Slack alert: {e}")

    async def _send_email_alert(self, alert: ComplianceAlert):
        """Send email alert"""
        config = self.config['email_alerts']
        
        msg = MimeMultipart()
        msg['From'] = config['from_email']
        msg['To'] = ', '.join(config['to_emails'])
        msg['Subject'] = f"🚨 LEGAL COMPLIANCE ALERT: {alert.alert_type}"
        
        body = f"""
LEGAL COMPLIANCE ALERT

Severity: {alert.severity}
Alert Type: {alert.alert_type}
Timestamp: {alert.timestamp.isoformat()}

Message: {alert.message}

Affected Pages/Endpoints:
{chr(10).join(['- ' + page for page in alert.affected_pages])}

Remediation Required:
{alert.remediation}

This is an automated alert from the Legal AI Disclaimer Compliance Monitor.
Immediate action may be required to maintain legal compliance.
"""
        
        msg.attach(MimeText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.starttls()
        server.login(config['username'], config['password'])
        server.send_message(msg)
        server.quit()

    async def _send_slack_alert(self, alert: ComplianceAlert):
        """Send Slack alert"""
        webhook_url = self.config['slack_alerts']['webhook_url']
        
        slack_message = {
            "text": f"🚨 Legal Compliance Alert: {alert.alert_type}",
            "attachments": [
                {
                    "color": "danger" if alert.severity == "CRITICAL" else "warning",
                    "fields": [
                        {
                            "title": "Severity",
                            "value": alert.severity,
                            "short": True
                        },
                        {
                            "title": "Affected Items",
                            "value": str(len(alert.affected_pages)),
                            "short": True
                        },
                        {
                            "title": "Message",
                            "value": alert.message,
                            "short": False
                        },
                        {
                            "title": "Remediation",
                            "value": alert.remediation,
                            "short": False
                        }
                    ],
                    "ts": int(alert.timestamp.timestamp())
                }
            ]
        }
        
        async with self.session.post(webhook_url, json=slack_message) as response:
            if response.status != 200:
                raise Exception(f"Slack webhook returned status {response.status}")

    async def _save_check_results(self, checks: List[DisclaimerCheck]):
        """Save check results to file for historical analysis"""
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"disclaimer_compliance_check_{timestamp}.json"
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_checks': len(checks),
            'passed_checks': len([c for c in checks if c.status == 'PASS']),
            'failed_checks': len([c for c in checks if c.status == 'FAIL']),
            'error_checks': len([c for c in checks if c.status == 'ERROR']),
            'checks': [asdict(check) for check in checks]
        }
        
        # Convert datetime objects to ISO strings
        for check in results['checks']:
            check['timestamp'] = check['timestamp'].isoformat()
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"Check results saved to {filename}")

    def check_disclaimer_presence(self, url: str) -> bool:
        """Check if a specific URL has proper disclaimers"""
        # This is a synchronous wrapper for the async disclaimer check
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self._check_single_page_sync(url))
            return result.status == 'PASS'
        finally:
            loop.close()
    
    async def _check_single_page_sync(self, url: str) -> DisclaimerCheck:
        """Internal helper for synchronous disclaimer checking"""
        async with aiohttp.ClientSession() as session:
            self.session = session
            if url.startswith('/'):
                return await self._check_page_disclaimers(url)
            else:
                return await self._check_api_disclaimers(url)

    def validate_page_disclaimers(self, pages: List[str]) -> Dict[str, bool]:
        """Validate disclaimers on multiple pages (synchronous)"""
        results = {}
        import asyncio

        async def _validate_pages():
            async with aiohttp.ClientSession() as session:
                self.session = session
                for page in pages:
                    check_result = await self._check_page_disclaimers(page)
                    results[page] = check_result.status == 'PASS'

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_validate_pages())
        finally:
            loop.close()
        return results

    def validate_api_disclaimers(self, endpoints: List[str]) -> Dict[str, bool]:
        """Validate disclaimers on multiple API endpoints (synchronous)"""
        results = {}
        import asyncio

        async def _validate_endpoints():
            async with aiohttp.ClientSession() as session:
                self.session = session
                for endpoint in endpoints:
                    check_result = await self._check_api_disclaimers(endpoint)
                    results[endpoint] = check_result.status == 'PASS'

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_validate_endpoints())
        finally:
            loop.close()
        return results

    def send_email_alert(self, subject: str, message: str):
        """Send email alert (synchronous wrapper)"""
        alert = ComplianceAlert(
            alert_type='MANUAL_ALERT',
            severity='HIGH',
            message=message,
            affected_pages=[],
            timestamp=datetime.utcnow(),
            remediation='Manual alert - check system status'
        )
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._send_email_alert(alert))
        finally:
            loop.close()

    def send_slack_alert(self, message: str):
        """Send Slack alert (synchronous wrapper)"""
        alert = ComplianceAlert(
            alert_type='MANUAL_ALERT',
            severity='HIGH',
            message=message,
            affected_pages=[],
            timestamp=datetime.utcnow(),
            remediation='Manual alert - check system status'
        )
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._send_slack_alert(alert))
        finally:
            loop.close()

    def monitor_compliance(self) -> Dict[str, Any]:
        """Run a single compliance monitoring cycle (synchronous)"""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            checks = loop.run_until_complete(self._run_single_check_cycle())
            
            # Return summary data
            total_checks = len(checks)
            passed_checks = len([c for c in checks if c.status == 'PASS'])
            failed_checks = len([c for c in checks if c.status == 'FAIL'])
            error_checks = len([c for c in checks if c.status == 'ERROR'])
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'total_checks': total_checks,
                'passed_checks': passed_checks,
                'failed_checks': failed_checks,
                'error_checks': error_checks,
                'compliance_percentage': (passed_checks / total_checks) * 100 if total_checks > 0 else 0,
                'status': 'COMPLIANT' if failed_checks == 0 and error_checks == 0 else 'NON_COMPLIANT'
            }
        finally:
            loop.close()

    async def _run_single_check_cycle(self) -> List[DisclaimerCheck]:
        """Run a single check cycle and return results"""
        async with aiohttp.ClientSession() as session:
            self.session = session
            checks = []
            
            # Check all pages
            for page in self.monitored_pages:
                check = await self._check_page_disclaimers(page)
                checks.append(check)
            
            # Check all API endpoints  
            for endpoint in self.monitored_api_endpoints:
                check = await self._check_api_disclaimers(endpoint)
                checks.append(check)
            
            return checks

    def generate_compliance_report(self) -> str:
        """Generate human-readable compliance report"""
        
        if not self.alerts:
            return "✅ DISCLAIMER COMPLIANCE: All checks passing - No active alerts"
        
        report = f"""
🚨 DISCLAIMER COMPLIANCE REPORT
Generated: {datetime.utcnow().isoformat()}

ACTIVE ALERTS: {len(self.alerts)}

"""
        
        for alert in self.alerts[-5:]:  # Last 5 alerts
            report += f"""
Alert Type: {alert.alert_type}
Severity: {alert.severity} 
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Message: {alert.message}
Affected: {len(alert.affected_pages)} items
Remediation: {alert.remediation}

"""
        
        return report

async def main():
    """Main function to run disclaimer compliance monitoring"""
    
    print("🚨 Starting Legal AI Disclaimer Compliance Monitor")
    print("This monitor ensures ALL pages have required legal disclaimers")
    print("Press Ctrl+C to stop monitoring\n")
    
    # Create and start monitor
    monitor = DisclaimerComplianceMonitor()
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n✅ Disclaimer compliance monitoring stopped")
        print(f"Final compliance report:\n{monitor.generate_compliance_report()}")

if __name__ == "__main__":
    asyncio.run(main())