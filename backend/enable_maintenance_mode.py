#!/usr/bin/env python3
"""
EMERGENCY MAINTENANCE MODE ACTIVATION

This script immediately activates maintenance mode to block all user access
while critical legal compliance issues are addressed.

USAGE:
    python enable_maintenance_mode.py [reason]
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

def enable_maintenance_mode(reason=None):
    """Enable maintenance mode with optional reason"""
    
    if not reason:
        reason = "Critical legal compliance updates"
    
    timestamp = datetime.utcnow()
    
    print("[EMERGENCY] Activating maintenance mode...")
    print(f"Reason: {reason}")
    print(f"Started: {timestamp.isoformat()}")
    
    # Set environment variable for immediate effect
    os.environ['MAINTENANCE_MODE'] = 'true'
    os.environ['MAINTENANCE_REASON'] = reason
    
    # Create .env override file for persistence
    env_override_path = Path('.env.maintenance')
    with open(env_override_path, 'w') as f:
        f.write(f"MAINTENANCE_MODE=true\n")
        f.write(f"MAINTENANCE_REASON={reason}\n")
        f.write(f"MAINTENANCE_STARTED={timestamp.isoformat()}\n")
    
    # Create maintenance status file
    status_file = {
        'maintenance_active': True,
        'reason': reason,
        'started': timestamp.isoformat(),
        'estimated_duration': '2-4 hours',
        'contact': 'admin@legalai.com',
        'last_updated': timestamp.isoformat()
    }
    
    with open('maintenance_status.json', 'w') as f:
        json.dump(status_file, f, indent=2)
    
    # Create maintenance notice for web server
    maintenance_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>System Maintenance - Legal AI</title>
    <meta http-equiv="refresh" content="300">
    <style>
        body {{ font-family: Arial, sans-serif; background: #fef2f2; text-align: center; padding: 50px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; border: 2px solid #dc2626; }}
        .title {{ color: #dc2626; font-size: 24px; margin-bottom: 20px; }}
        .message {{ color: #374151; margin-bottom: 30px; }}
        .status {{ background: #fee; border: 1px solid #dc2626; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="title">[EMERGENCY] SYSTEM UNDER MAINTENANCE</h1>
        <div class="message">
            The Legal AI System is currently undergoing critical legal compliance updates.
            All user access has been temporarily suspended.
        </div>
        <div class="status">
            <strong>Status:</strong> Maintenance Active<br>
            <strong>Reason:</strong> {reason}<br>
            <strong>Started:</strong> {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
            <strong>Estimated Duration:</strong> 2-4 hours
        </div>
        <p><strong>Contact:</strong> admin@legalai.com</p>
    </div>
</body>
</html>"""
    
    with open('maintenance.html', 'w', encoding='utf-8') as f:
        f.write(maintenance_html)
    
    print("\n[SUCCESS] Maintenance mode activated!")
    print(f"- Environment variables set")
    print(f"- Status file created: maintenance_status.json") 
    print(f"- Override file created: .env.maintenance")
    print(f"- Web notice created: maintenance.html")
    print(f"\n[CRITICAL] ALL USER ACCESS IS NOW BLOCKED")
    print(f"[CRITICAL] System will remain inaccessible until maintenance is disabled")
    
    return True

def disable_maintenance_mode():
    """Disable maintenance mode and restore normal operation"""
    
    print("[MAINTENANCE] Disabling maintenance mode...")
    
    # Remove environment variables
    if 'MAINTENANCE_MODE' in os.environ:
        del os.environ['MAINTENANCE_MODE']
    if 'MAINTENANCE_REASON' in os.environ:
        del os.environ['MAINTENANCE_REASON']
    
    # Remove override files
    files_to_remove = ['.env.maintenance', 'maintenance_status.json', 'maintenance.html']
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"- Removed {file}")
    
    print("\n[SUCCESS] Maintenance mode disabled!")
    print("[SUCCESS] Normal user access restored")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--disable':
            disable_maintenance_mode()
        else:
            reason = ' '.join(sys.argv[1:])
            enable_maintenance_mode(reason)
    else:
        enable_maintenance_mode()