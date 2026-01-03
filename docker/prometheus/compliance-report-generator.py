#!/usr/bin/env python3
"""
LEGAL AI COMPLIANCE REPORT GENERATOR

Generates comprehensive compliance reports from Prometheus metrics
and creates executive summaries for legal and management teams.
"""

import requests
import json
import datetime
from typing import Dict, List, Any
import argparse
import os
from jinja2 import Template


class ComplianceReportGenerator:
    """Generate compliance reports from monitoring data"""

    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.prometheus_url = prometheus_url
        self.report_data = {}

    def query_prometheus(self, query: str, time_range: str = "24h") -> Dict:
        """Query Prometheus for compliance metrics"""
        try:
            url = f"{self.prometheus_url}/api/v1/query"
            params = {
                'query': f"{query}[{time_range}]" if not query.endswith(']') else query
            }
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error querying Prometheus: {e}")
            return {"data": {"result": []}}

    def get_upl_violations(self) -> Dict:
        """Get UPL violation metrics"""
        query = 'increase(compliance_violations_total{violation_type="upl"}[24h])'
        result = self.query_prometheus(query)

        total_violations = 0
        violations_by_service = {}

        for item in result.get("data", {}).get("result", []):
            value = float(item["value"][1])
            total_violations += value
            service = item.get("metric", {}).get("service", "unknown")
            violations_by_service[service] = violations_by_service.get(service, 0) + value

        return {
            "total": total_violations,
            "by_service": violations_by_service,
            "status": "CRITICAL" if total_violations > 0 else "COMPLIANT"
        }

    def get_attorney_review_metrics(self) -> Dict:
        """Get attorney review flag metrics"""
        queries = {
            "total_flags": 'increase(attorney_review_flags_total[24h])',
            "critical_flags": 'increase(attorney_review_flags_total{risk_level="critical"}[24h])',
            "high_flags": 'increase(attorney_review_flags_total{risk_level="high"}[24h])',
            "flag_rate": 'rate(attorney_review_flags_total[1h])'
        }

        metrics = {}
        for key, query in queries.items():
            result = self.query_prometheus(query)
            total = sum(float(item["value"][1]) for item in result.get("data", {}).get("result", []))
            metrics[key] = total

        # Calculate effectiveness score
        total_flags = metrics.get("total_flags", 0)
        critical_high = metrics.get("critical_flags", 0) + metrics.get("high_flags", 0)
        effectiveness = (critical_high / total_flags * 100) if total_flags > 0 else 0

        return {
            "total_flags_24h": total_flags,
            "critical_flags_24h": metrics.get("critical_flags", 0),
            "high_flags_24h": metrics.get("high_flags", 0),
            "current_flag_rate": metrics.get("flag_rate", 0),
            "effectiveness_score": effectiveness,
            "status": "EFFECTIVE" if effectiveness >= 80 else "NEEDS_IMPROVEMENT"
        }

    def get_disclaimer_coverage(self) -> Dict:
        """Get disclaimer coverage metrics"""
        queries = {
            "applied": 'increase(disclaimer_enforcement_total{action="applied"}[24h])',
            "missing": 'increase(disclaimer_enforcement_total{action="missing"}[24h])'
        }

        applied = 0
        missing = 0

        for key, query in queries.items():
            result = self.query_prometheus(query)
            value = sum(float(item["value"][1]) for item in result.get("data", {}).get("result", []))
            if key == "applied":
                applied = value
            else:
                missing = value

        total_requests = applied + missing
        coverage_percentage = (applied / total_requests * 100) if total_requests > 0 else 100

        return {
            "applied_disclaimers": applied,
            "missing_disclaimers": missing,
            "coverage_percentage": coverage_percentage,
            "total_requests": total_requests,
            "status": "COMPLIANT" if coverage_percentage >= 95 else "NON_COMPLIANT"
        }

    def get_service_availability(self) -> Dict:
        """Get compliance service availability metrics"""
        services = ["compliance-service", "disclaimer-api", "feedback-service"]
        availability_metrics = {}

        for service in services:
            query = f'avg_over_time(up{{job="{service}"}}[24h])'
            result = self.query_prometheus(query)

            if result.get("data", {}).get("result"):
                availability = float(result["data"]["result"][0]["value"][1]) * 100
            else:
                availability = 0.0

            availability_metrics[service] = {
                "availability_percent": availability,
                "status": "UP" if availability >= 99.9 else "SLA_BREACH"
            }

        overall_availability = sum(
            metrics["availability_percent"] for metrics in availability_metrics.values()
        ) / len(availability_metrics)

        return {
            "services": availability_metrics,
            "overall_availability": overall_availability,
            "sla_status": "MET" if overall_availability >= 99.9 else "BREACHED"
        }

    def get_compliance_response_times(self) -> Dict:
        """Get compliance check response time metrics"""
        percentiles = {
            "p50": 'histogram_quantile(0.50, rate(compliance_check_duration_seconds_bucket[24h]))',
            "p95": 'histogram_quantile(0.95, rate(compliance_check_duration_seconds_bucket[24h]))',
            "p99": 'histogram_quantile(0.99, rate(compliance_check_duration_seconds_bucket[24h]))'
        }

        response_times = {}
        for percentile, query in percentiles.items():
            result = self.query_prometheus(query)
            if result.get("data", {}).get("result"):
                response_times[percentile] = float(result["data"]["result"][0]["value"][1])
            else:
                response_times[percentile] = 0.0

        sla_status = "MET" if response_times.get("p95", 99) <= 0.5 else "BREACHED"

        return {
            "response_times": response_times,
            "sla_status": sla_status
        }

    def generate_report(self) -> Dict:
        """Generate comprehensive compliance report"""
        print("Generating compliance report...")

        self.report_data = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "report_period": "24 hours",
            "upl_violations": self.get_upl_violations(),
            "attorney_review": self.get_attorney_review_metrics(),
            "disclaimer_coverage": self.get_disclaimer_coverage(),
            "service_availability": self.get_service_availability(),
            "response_times": self.get_compliance_response_times()
        }

        # Calculate overall compliance score
        scores = []

        # UPL compliance (0 violations = 100%, any violation = 0%)
        upl_score = 100 if self.report_data["upl_violations"]["total"] == 0 else 0
        scores.append(upl_score)

        # Attorney review effectiveness
        scores.append(self.report_data["attorney_review"]["effectiveness_score"])

        # Disclaimer coverage
        scores.append(self.report_data["disclaimer_coverage"]["coverage_percentage"])

        # Service availability
        scores.append(self.report_data["service_availability"]["overall_availability"])

        # Response time score (< 500ms = 100%, > 500ms scaled down)
        p95_time = self.report_data["response_times"]["response_times"].get("p95", 0.5)
        response_score = max(0, (1.0 - p95_time) * 100) if p95_time <= 1.0 else 0
        scores.append(response_score)

        overall_score = sum(scores) / len(scores)

        self.report_data["overall_compliance"] = {
            "score": overall_score,
            "status": self._get_compliance_status(overall_score),
            "individual_scores": {
                "upl_compliance": upl_score,
                "attorney_review": self.report_data["attorney_review"]["effectiveness_score"],
                "disclaimer_coverage": self.report_data["disclaimer_coverage"]["coverage_percentage"],
                "service_availability": self.report_data["service_availability"]["overall_availability"],
                "response_time": response_score
            }
        }

        return self.report_data

    def _get_compliance_status(self, score: float) -> str:
        """Get compliance status based on score"""
        if score >= 95:
            return "FULLY_COMPLIANT"
        elif score >= 80:
            return "MOSTLY_COMPLIANT"
        elif score >= 60:
            return "PARTIAL_COMPLIANCE"
        else:
            return "NON_COMPLIANT"

    def generate_executive_summary(self) -> str:
        """Generate executive summary"""
        template_str = """
# Legal AI System - Executive Compliance Summary

**Report Date:** {{ timestamp }}
**Report Period:** {{ report_period }}
**Overall Compliance Score:** {{ "%.1f" | format(overall_compliance.score) }}%
**Compliance Status:** {{ overall_compliance.status }}

## 🎯 Key Metrics Summary

### UPL (Unauthorized Practice of Law) Protection
- **Status:** {{ upl_violations.status }}
- **Violations (24h):** {{ upl_violations.total | int }}
- **Score:** {{ "%.1f" | format(overall_compliance.individual_scores.upl_compliance) }}%

### Attorney Review System
- **Status:** {{ attorney_review.status }}
- **Total Flags (24h):** {{ attorney_review.total_flags_24h | int }}
- **Critical Flags:** {{ attorney_review.critical_flags_24h | int }}
- **Effectiveness:** {{ "%.1f" | format(attorney_review.effectiveness_score) }}%

### Legal Disclaimer Coverage
- **Status:** {{ disclaimer_coverage.status }}
- **Coverage:** {{ "%.1f" | format(disclaimer_coverage.coverage_percentage) }}%
- **Missing Disclaimers:** {{ disclaimer_coverage.missing_disclaimers | int }}

### Service Availability (SLA: 99.9%)
- **Overall Status:** {{ service_availability.sla_status }}
- **Availability:** {{ "%.2f" | format(service_availability.overall_availability) }}%

## 📊 Detailed Findings

{% if upl_violations.total > 0 %}
### 🚨 CRITICAL: UPL Violations Detected
- **Total Violations:** {{ upl_violations.total | int }}
- **Immediate Action Required:** Legal review and potential service suspension
{% endif %}

{% if attorney_review.effectiveness_score < 80 %}
### ⚠️ Attorney Review System Needs Improvement
- **Current Effectiveness:** {{ "%.1f" | format(attorney_review.effectiveness_score) }}%
- **Recommendation:** Review flagging thresholds and patterns
{% endif %}

{% if disclaimer_coverage.coverage_percentage < 95 %}
### ⚠️ Disclaimer Coverage Below Threshold
- **Current Coverage:** {{ "%.1f" | format(disclaimer_coverage.coverage_percentage) }}%
- **Missing Disclaimers:** {{ disclaimer_coverage.missing_disclaimers | int }}
- **Recommendation:** Investigate disclaimer enforcement failures
{% endif %}

{% if service_availability.sla_status == "BREACHED" %}
### ⚠️ Service Availability SLA Breach
- **Current Availability:** {{ "%.2f" | format(service_availability.overall_availability) }}%
- **SLA Target:** 99.9%
- **Recommendation:** Improve service reliability and monitoring
{% endif %}

## 🎯 Recommendations

{% if overall_compliance.score >= 95 %}
✅ **Excellent compliance posture.** Continue current practices and regular monitoring.
{% elif overall_compliance.score >= 80 %}
⚠️ **Good compliance with areas for improvement.** Focus on low-scoring areas.
{% else %}
🚨 **Compliance improvements required.** Immediate attention needed for critical issues.
{% endif %}

1. **UPL Protection:** Maintain zero tolerance for UPL violations
2. **Attorney Review:** Ensure 90%+ effectiveness in flagging high-risk content
3. **Disclaimer Coverage:** Maintain 95%+ disclaimer application rate
4. **Service Reliability:** Achieve 99.9% uptime for all compliance services
5. **Response Times:** Keep 95th percentile under 500ms

## 📈 Trend Analysis

*Note: Implement historical comparison in future reports*

---
*Generated by Legal AI Compliance Monitoring System*
        """

        template = Template(template_str)
        return template.render(**self.report_data)

    def save_report(self, output_dir: str = "./reports"):
        """Save compliance report to files"""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Save JSON report
        json_file = f"{output_dir}/compliance_report_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(self.report_data, f, indent=2)

        # Save executive summary
        summary_file = f"{output_dir}/compliance_executive_summary_{timestamp}.md"
        with open(summary_file, 'w') as f:
            f.write(self.generate_executive_summary())

        print(f"Reports saved:")
        print(f"  - JSON: {json_file}")
        print(f"  - Executive Summary: {summary_file}")

        return json_file, summary_file


def main():
    parser = argparse.ArgumentParser(description="Generate Legal AI compliance reports")
    parser.add_argument(
        "--prometheus-url",
        default="http://localhost:9090",
        help="Prometheus server URL"
    )
    parser.add_argument(
        "--output-dir",
        default="./reports",
        help="Output directory for reports"
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format"
    )

    args = parser.parse_args()

    generator = ComplianceReportGenerator(args.prometheus_url)
    report_data = generator.generate_report()

    if args.format in ["json", "both"]:
        json_file, _ = generator.save_report(args.output_dir)
        if args.format == "json":
            print(f"\nJSON report: {json_file}")

    if args.format in ["markdown", "both"]:
        summary = generator.generate_executive_summary()
        print("\n" + "="*80)
        print(summary)
        print("="*80)

    # Print compliance score
    score = report_data["overall_compliance"]["score"]
    status = report_data["overall_compliance"]["status"]
    print(f"\n🎯 Overall Compliance Score: {score:.1f}% ({status})")


if __name__ == "__main__":
    main()