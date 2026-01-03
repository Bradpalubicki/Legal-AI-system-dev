#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend Monitoring CLI Tool
Access system metrics, errors, and performance data
"""

import requests
import json
import sys
import io
from datetime import datetime
from typing import Dict, Any

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000/api/v1/monitoring"


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def get_health():
    """Display system health"""
    response = requests.get(f"{BASE_URL}/health")
    health = response.json()

    print_header("SYSTEM HEALTH")
    print(f"Status: {health['status'].upper()}")
    print(f"Uptime: {health['uptime_hours']:.2f} hours ({health['uptime_percentage']}%)")
    print(f"Total Requests: {health['total_requests']}")
    print(f"Total Errors: {health['total_errors']}")
    print(f"Error Rate: {health['error_rate']:.2f}%")
    print(f"Avg Response Time: {health['avg_response_time']:.0f}ms")
    print(f"Active Users: {health['active_users']}")
    print(f"Daily Cost: ${health['daily_cost']:.4f}")
    print(f"Monthly Projection: ${health['monthly_cost_projection']:.2f}")

    # Alerts
    if health['error_rate'] > 5:
        print("\n⚠️  WARNING: High error rate!")
    if health['avg_response_time'] > 1000:
        print("\n⚠️  WARNING: Slow response times!")
    if health['daily_cost'] > 1:
        print(f"\n⚠️  WARNING: High daily cost: ${health['daily_cost']:.2f}")


def get_endpoints():
    """Display endpoint statistics"""
    response = requests.get(f"{BASE_URL}/endpoints?time_window_hours=1")
    data = response.json()

    print_header(f"ENDPOINTS (Last {data['time_window_hours']} hour)")

    endpoints = data['endpoints']
    if not endpoints:
        print("No endpoint activity in the last hour")
        return

    # Sort by request count
    endpoints.sort(key=lambda x: x['request_count'], reverse=True)

    print(f"\n{'Endpoint':<50} {'Reqs':<6} {'Avg ms':<8} {'Errors':<7} {'Status':<10}")
    print("-" * 90)

    for ep in endpoints[:15]:  # Top 15
        status_icon = {
            'healthy': '✓',
            'normal': '○',
            'warning': '⚠',
            'critical': '✗'
        }.get(ep['status'], '?')

        print(
            f"{ep['endpoint']:<50} "
            f"{ep['request_count']:<6} "
            f"{ep['avg_response_time']:<8.0f} "
            f"{ep['error_count']:<7} "
            f"{status_icon} {ep['status']:<9}"
        )


def get_errors():
    """Display recent errors"""
    response = requests.get(f"{BASE_URL}/errors?limit=10")
    data = response.json()

    print_header("RECENT ERRORS")

    errors = data['errors']
    if not errors:
        print("\n✓ No errors detected!")
        return

    for i, error in enumerate(errors, 1):
        print(f"\n[{i}] {error['error_type']}")
        print(f"    Endpoint: {error['endpoint']}")
        print(f"    Message: {error['message']}")
        print(f"    Time: {error['timestamp']}")


def get_costs():
    """Display cost breakdown"""
    response = requests.get(f"{BASE_URL}/costs")
    data = response.json()

    print_header("COST BREAKDOWN")
    print(f"Daily Cost: ${data['daily_cost']:.4f}")
    print(f"Monthly Projection: ${data['monthly_projection']:.2f}")

    breakdown = data['breakdown']
    if breakdown:
        print(f"\n{'Operation':<50} {'Cost':<12} {'%':<6}")
        print("-" * 70)
        for item in breakdown[:10]:  # Top 10
            print(
                f"{item['operation']:<50} "
                f"${item['total_cost']:<11.4f} "
                f"{item['percentage']:>5.1f}%"
            )


def get_performance():
    """Display performance metrics and suggestions"""
    response = requests.get(f"{BASE_URL}/performance")
    data = response.json()

    print_header("PERFORMANCE ANALYSIS")

    slow_endpoints = data['slow_endpoints']
    if slow_endpoints:
        print("\n⚠️  Slow Endpoints (>500ms):")
        for ep in slow_endpoints[:5]:
            print(f"  • {ep['endpoint']}: {ep['avg_response_time']:.0f}ms avg")

    slow_queries = data['slow_queries']
    if slow_queries:
        print("\n⚠️  Slow Database Queries (>500ms):")
        for q in slow_queries[:5]:
            print(f"  • {q['description'][:60]}: {q['avg_execution_time']:.0f}ms")

    suggestions = data['suggestions']
    if suggestions:
        print("\n💡 Optimization Suggestions:")
        for s in suggestions:
            severity_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡'}.get(s['severity'], '⚪')
            print(f"\n  {severity_icon} {s['message']}")
            if 'endpoints' in s:
                for endpoint in s['endpoints']:
                    print(f"     - {endpoint}")
            if 'queries' in s:
                for query in s['queries']:
                    print(f"     - {query}")


def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Backend Monitoring CLI")
        print("\nUsage: python monitor_system.py <command>")
        print("\nCommands:")
        print("  health      - System health and uptime")
        print("  endpoints   - API endpoint statistics")
        print("  errors      - Recent errors")
        print("  costs       - Cost breakdown")
        print("  performance - Performance analysis")
        print("  all         - Show all metrics")
        sys.exit(1)

    command = sys.argv[1].lower()

    try:
        if command == "health":
            get_health()
        elif command == "endpoints":
            get_endpoints()
        elif command == "errors":
            get_errors()
        elif command == "costs":
            get_costs()
        elif command == "performance":
            get_performance()
        elif command == "all":
            get_health()
            get_endpoints()
            get_errors()
            get_costs()
            get_performance()
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to backend at http://localhost:8000")
        print("Make sure the backend server is running.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
