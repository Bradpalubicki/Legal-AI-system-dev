#!/usr/bin/env python3
"""
API System Service Mode Test Script

This script tests the Legal AI System's service status endpoint and displays
which services are running in mock mode vs live mode, helping developers
understand the current system configuration.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

def format_status_indicator(available: bool, mode: str) -> str:
    """Format a status indicator with color coding."""
    if available:
        if mode == "live":
            return f"{Colors.GREEN}[LIVE]{Colors.RESET}"
        elif mode == "mock":
            return f"{Colors.YELLOW}[MOCK]{Colors.RESET}"
        else:
            return f"{Colors.BLUE}[{mode.upper()}]{Colors.RESET}"
    else:
        return f"{Colors.RED}[OFF]{Colors.RESET}"

def print_header():
    """Print formatted header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  Legal AI System - Service Mode Analysis{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.WHITE}Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    print(f"{Colors.CYAN}{'-'*70}{Colors.RESET}\n")

def analyze_service(name: str, service_data: Dict[str, Any], category: str = "General") -> Dict[str, Any]:
    """Analyze a single service and return analysis results."""
    available = service_data.get('available', False)
    mode = service_data.get('mode', 'unknown')
    reason = service_data.get('reason', '')
    last_checked = service_data.get('last_checked', '')
    
    return {
        'name': name,
        'category': category,
        'available': available,
        'mode': mode,
        'reason': reason,
        'last_checked': last_checked,
        'status_indicator': format_status_indicator(available, mode)
    }

def print_service_summary(services: List[Dict[str, Any]]):
    """Print a summary table of all services."""
    print(f"{Colors.BOLD}{Colors.WHITE}Service Status Summary:{Colors.RESET}")
    print(f"{Colors.CYAN}{'-'*70}{Colors.RESET}")
    
    # Print table header
    print(f"{Colors.BOLD}{'Service':<25} {'Category':<15} {'Status':<12} {'Reason':<15}{Colors.RESET}")
    print(f"{Colors.CYAN}{'-'*70}{Colors.RESET}")
    
    # Print each service
    for service in services:
        name = service['name'][:24]  # Truncate long names
        category = service['category'][:14]
        status = service['status_indicator']
        reason = service['reason'][:14] if service['reason'] else 'N/A'
        
        print(f"{name:<25} {category:<15} {status:<20} {reason:<15}")
    
    print(f"{Colors.CYAN}{'-'*70}{Colors.RESET}")

def print_mode_analysis(services: List[Dict[str, Any]]):
    """Print analysis of service modes."""
    live_services = [s for s in services if s['available'] and s['mode'] == 'live']
    mock_services = [s for s in services if s['available'] and s['mode'] == 'mock']
    offline_services = [s for s in services if not s['available']]
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}Live Services ({len(live_services)}):{Colors.RESET}")
    if live_services:
        for service in live_services:
            print(f"  {Colors.GREEN}[LIVE]{Colors.RESET} {service['name']} - Real API integration active")
    else:
        print(f"  {Colors.YELLOW}No services running in live mode{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}{Colors.YELLOW}Mock Services ({len(mock_services)}):{Colors.RESET}")
    if mock_services:
        for service in mock_services:
            print(f"  {Colors.YELLOW}[MOCK]{Colors.RESET} {service['name']} - Using mock/test data")
    else:
        print(f"  {Colors.YELLOW}No services running in mock mode{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}{Colors.RED}Offline Services ({len(offline_services)}):{Colors.RESET}")
    if offline_services:
        for service in offline_services:
            reason = f" ({service['reason']})" if service['reason'] else ""
            print(f"  {Colors.RED}[OFF]{Colors.RESET} {service['name']}{reason}")
    else:
        print(f"  {Colors.GREEN}All services are online!{Colors.RESET}")

def print_recommendations(services: List[Dict[str, Any]]):
    """Print recommendations based on current service status."""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}Recommendations:{Colors.RESET}")
    
    offline_services = [s for s in services if not s['available']]
    mock_services = [s for s in services if s['available'] and s['mode'] == 'mock']
    
    if offline_services:
        print(f"  {Colors.YELLOW}[WARN]{Colors.RESET} Configure API keys for offline services to enable functionality")
        for service in offline_services[:3]:  # Show first 3
            if 'API key' in service['reason']:
                print(f"    - Set environment variable for {service['name']}")
    
    if mock_services:
        print(f"  {Colors.YELLOW}[INFO]{Colors.RESET} Mock services are using test data - suitable for development")
        print(f"  {Colors.YELLOW}[INFO]{Colors.RESET} For production, configure real credentials for mock services")
    
    live_count = len([s for s in services if s['available'] and s['mode'] == 'live'])
    total_available = len([s for s in services if s['available']])
    
    if live_count == total_available and total_available > 0:
        print(f"  {Colors.GREEN}[OK]{Colors.RESET} System fully configured with live services")
    elif total_available > 0:
        print(f"  {Colors.YELLOW}[WARN]{Colors.RESET} System partially configured - {total_available} services available")
    else:
        print(f"  {Colors.RED}[ERROR]{Colors.RESET} System needs configuration - no services available")

def test_api_system(base_url: str = "http://127.0.0.1:8003"):
    """Test the API system and analyze service modes."""
    
    print_header()
    
    try:
        # Test API connectivity
        print(f"{Colors.BLUE}Testing API connectivity...{Colors.RESET}")
        response = requests.get(f"{base_url}/api/services/status", timeout=10)
        
        if response.status_code != 200:
            print(f"{Colors.RED}[ERROR] API Error: HTTP {response.status_code}{Colors.RESET}")
            return False
        
        print(f"{Colors.GREEN}[OK] API is responding{Colors.RESET}")
        
        # Parse service data
        service_data = response.json()
        services = []
        
        # Process individual services
        for service_name, service_info in service_data.items():
            if service_name == "ai_services":
                # Handle nested AI services
                for ai_service, ai_info in service_info.items():
                    services.append(analyze_service(ai_service, ai_info, "AI Services"))
            else:
                # Handle top-level services
                category = {
                    'courtlistener': 'Legal Research',
                    'pacer': 'Legal Research', 
                    'westlaw': 'Legal Research'
                }.get(service_name, 'General')
                
                services.append(analyze_service(service_name, service_info, category))
        
        # Print analysis
        print_service_summary(services)
        print_mode_analysis(services)
        print_recommendations(services)
        
        # Print system health summary
        total_services = len(services)
        available_services = len([s for s in services if s['available']])
        health_percentage = (available_services / total_services * 100) if total_services > 0 else 0
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}System Health Summary:{Colors.RESET}")
        print(f"  Available Services: {available_services}/{total_services} ({health_percentage:.0f}%)")
        
        if health_percentage >= 80:
            health_status = f"{Colors.GREEN}Excellent{Colors.RESET}"
        elif health_percentage >= 60:
            health_status = f"{Colors.YELLOW}Good{Colors.RESET}"
        elif health_percentage >= 40:
            health_status = f"{Colors.YELLOW}Fair{Colors.RESET}"
        else:
            health_status = f"{Colors.RED}Poor{Colors.RESET}"
        
        print(f"  System Health: {health_status}")
        
        # Save detailed results to file
        results = {
            'timestamp': datetime.now().isoformat(),
            'api_url': base_url,
            'total_services': total_services,
            'available_services': available_services,
            'health_percentage': health_percentage,
            'services': services,
            'raw_response': service_data
        }
        
        with open('service_analysis_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n{Colors.GREEN}[OK] Detailed results saved to service_analysis_results.json{Colors.RESET}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}[ERROR] Connection Error: Unable to connect to {base_url}{Colors.RESET}")
        print(f"{Colors.YELLOW}  Make sure the Legal AI System server is running on port 8003{Colors.RESET}")
        return False
    
    except requests.exceptions.Timeout:
        print(f"{Colors.RED}[ERROR] Timeout Error: Server took too long to respond{Colors.RESET}")
        return False
    
    except json.JSONDecodeError as e:
        print(f"{Colors.RED}[ERROR] JSON Parse Error: {e}{Colors.RESET}")
        return False
    
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Unexpected Error: {e}{Colors.RESET}")
        return False
    
    finally:
        print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")

def main():
    """Main function."""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://127.0.0.1:8003"
    
    success = test_api_system(base_url)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()