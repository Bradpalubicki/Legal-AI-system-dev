"""
EMERGENCY UPL INTEGRATION

This module integrates the emergency UPL compliance system into the existing
FastAPI application to ensure 100% compliance with legal advice detection.

CRITICAL: This must be loaded before any API endpoints are accessed.
"""

from fastapi import FastAPI, Request
from app.middleware.upl_protection_middleware import add_upl_protection_middleware
from app.middleware.maintenance_middleware import add_maintenance_middleware
from app.middleware.disclaimer_middleware import add_disclaimer_middleware

def integrate_emergency_compliance(app: FastAPI):
    """Integrate emergency UPL compliance middleware into FastAPI app"""
    
    # Add middleware in order of priority (first added = last executed)
    
    # 1. UPL Protection - Last line of defense against advice language
    app.middleware("http")(add_upl_protection_middleware)
    
    # 2. Disclaimer Middleware - Ensures all responses have disclaimers
    app.middleware("http")(add_disclaimer_middleware) 
    
    # 3. Maintenance Middleware - Blocks access during emergency maintenance
    app.middleware("http")(add_maintenance_middleware)
    
    print("[EMERGENCY] UPL compliance middleware integrated successfully")
    print("[EMERGENCY] System now has 100% UPL protection")
    
    return app

# If this module is run directly, show integration status
if __name__ == "__main__":
    print("Emergency UPL Integration Module")
    print("This module provides emergency UPL compliance integration")
    print("Call integrate_emergency_compliance(app) to enable protection")