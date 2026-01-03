"""
DISCLAIMER SERVICE - CRITICAL LEGAL COMPLIANCE

This service ensures 24/7 availability of legal disclaimers for all system components.
Provides fallback mechanisms and health monitoring for disclaimer delivery.

CRITICAL: This service must NEVER go offline as it protects against UPL violations.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Legal Disclaimer Service",
    description="Critical service for legal disclaimer delivery",
    version="1.0.0"
)

class DisclaimerService:
    """
    Critical disclaimer service that provides legal disclaimers for all system components.
    
    Features:
    - 24/7 disclaimer availability
    - Multiple fallback mechanisms
    - Health monitoring and auto-restart
    - Page-specific disclaimer delivery
    - Compliance logging and audit trails
    """
    
    def __init__(self):
        self.service_start_time = datetime.utcnow()
        self.disclaimer_requests = 0
        self.health_checks = 0
        self.last_health_check = None
        
        # Load disclaimer templates
        self.disclaimers = self._load_disclaimer_templates()
        
        # Service health status
        self.is_healthy = True
        self.last_error = None
        
        logger.info("🚨 DISCLAIMER SERVICE INITIALIZED - LEGAL COMPLIANCE ACTIVE")

    def _load_disclaimer_templates(self) -> Dict[str, Dict]:
        """Load all disclaimer templates for different pages and contexts"""
        
        return {
            "global": {
                "title": "IMPORTANT LEGAL NOTICE",
                "content": [
                    "⚖️ This system provides general information only and does NOT constitute legal advice.",
                    "🚫 No attorney-client relationship is created by using this system.",
                    "👨‍⚖️ Always consult with a qualified attorney licensed in your jurisdiction.",
                    "📋 Laws vary by state and change frequently - verify current law with legal counsel."
                ],
                "severity": "CRITICAL"
            },
            "research": {
                "title": "Legal Research Disclaimer",
                "content": [
                    "Legal research is for informational purposes only and does NOT constitute legal advice.",
                    "Information provided may be outdated, incomplete, or jurisdiction-specific.",
                    "This is NOT a substitute for attorney consultation or professional legal research.",
                    "Always verify legal information with qualified legal counsel before relying on it."
                ],
                "severity": "HIGH"
            },
            "contracts": {
                "title": "Contract Analysis Disclaimer", 
                "content": [
                    "Contract analysis does NOT constitute legal review or legal advice.",
                    "AI analysis may miss critical terms, obligations, or legal implications.",
                    "Consult a qualified attorney before signing ANY legal agreement.",
                    "Contract interpretation varies by jurisdiction and specific circumstances."
                ],
                "severity": "CRITICAL"
            },
            "dashboard": {
                "title": "Dashboard Information Disclaimer",
                "content": [
                    "Dashboard information is NOT legal advice and is for informational purposes only.",
                    "Deadlines shown are estimates - always verify actual deadlines with the court.",
                    "Case status information may be delayed or incomplete.", 
                    "Consult your attorney for official case status and deadline confirmations."
                ],
                "severity": "HIGH"
            },
            "analyze": {
                "title": "Document Analysis Disclaimer",
                "content": [
                    "Document analysis is for informational purposes only and is NOT legal advice.",
                    "AI analysis may not identify all issues, risks, or legal implications.",
                    "Results should not be relied upon for legal decisions or strategy.",
                    "Always have important documents reviewed by qualified legal counsel."
                ],
                "severity": "HIGH"
            },
            "client-portal": {
                "title": "Client Portal Disclaimer", 
                "content": [
                    "The client portal is for information sharing only and does NOT constitute legal advice.",
                    "No attorney-client relationship is established through portal use.",
                    "Communications through this portal are NOT privileged or confidential.",
                    "Consult directly with qualified legal counsel for privileged attorney-client communications."
                ],
                "severity": "HIGH"
            },
            "admin": {
                "title": "Administrative Interface Disclaimer",
                "content": [
                    "Administrative functions are for system management only.",
                    "Administrative access does NOT create attorney-client relationships or legal obligations.",
                    "System data and analytics are for informational purposes only.",
                    "Consult with qualified legal counsel regarding any legal matters or compliance issues."
                ],
                "severity": "MEDIUM"
            },
            "education": {
                "title": "Educational Content Disclaimer",
                "content": [
                    "Educational content is for general information only and does NOT constitute legal advice.",
                    "Legal education materials may be outdated or not applicable to your jurisdiction.",
                    "Educational content is NOT a substitute for formal legal education or attorney consultation.",
                    "Always verify legal information with qualified legal counsel before making any legal decisions."
                ],
                "severity": "MEDIUM"
            },
            "mobile": {
                "title": "Mobile Application Disclaimer",
                "content": [
                    "Mobile access provides general information only and does NOT constitute legal advice.",
                    "Mobile features are for convenience and do NOT create attorney-client relationships.",
                    "Legal information on mobile may have limited functionality or outdated content.",
                    "Always consult with qualified legal counsel for legal matters requiring professional advice."
                ],
                "severity": "HIGH"
            },
            "fallback": {
                "title": "CRITICAL LEGAL DISCLAIMER",
                "content": [
                    "🚨 LEGAL NOTICE: This content is for informational purposes only and does NOT constitute legal advice.",
                    "🚫 NO ATTORNEY-CLIENT RELATIONSHIP is created by accessing this information.",
                    "⚖️ ALWAYS consult with a qualified attorney for legal advice specific to your situation.",
                    "📋 This system provides general information only - not legal advice."
                ],
                "severity": "CRITICAL"
            }
        }

    async def get_disclaimer(self, page_path: str = "/", disclaimer_type: str = "global") -> Dict:
        """
        Get appropriate disclaimer for a specific page or context.
        
        Args:
            page_path: The page path requesting the disclaimer
            disclaimer_type: Type of disclaimer needed (global, research, etc.)
        
        Returns:
            Dictionary containing disclaimer data
        """
        
        try:
            self.disclaimer_requests += 1
            
            # Determine disclaimer type from path if not specified
            if disclaimer_type == "auto":
                disclaimer_type = self._determine_disclaimer_type(page_path)
            
            # Get disclaimer template
            disclaimer_data = self.disclaimers.get(disclaimer_type, self.disclaimers["fallback"])
            
            # Add metadata
            response = {
                "disclaimer": disclaimer_data,
                "metadata": {
                    "service_timestamp": datetime.utcnow().isoformat(),
                    "page_path": page_path,
                    "disclaimer_type": disclaimer_type,
                    "request_id": f"disc_{self.disclaimer_requests}",
                    "service_healthy": self.is_healthy
                },
                "compliance": {
                    "mandatory": True,
                    "not_legal_advice": True,
                    "attorney_consultation_required": True,
                    "disclaimer_version": "2.1"
                }
            }
            
            # Log disclaimer delivery
            logger.info(f"[COMPLIANCE] Disclaimer delivered: {disclaimer_type} for {page_path}")
            
            return response
            
        except Exception as e:
            logger.error(f"[ERROR] Disclaimer delivery failed: {e}")
            self.last_error = str(e)
            self.is_healthy = False
            
            # Return fallback disclaimer
            return {
                "disclaimer": self.disclaimers["fallback"],
                "metadata": {
                    "service_timestamp": datetime.utcnow().isoformat(),
                    "page_path": page_path,
                    "disclaimer_type": "fallback",
                    "service_healthy": False,
                    "error": str(e)
                },
                "compliance": {
                    "mandatory": True,
                    "not_legal_advice": True,
                    "attorney_consultation_required": True,
                    "disclaimer_version": "2.1"
                }
            }

    def _determine_disclaimer_type(self, path: str) -> str:
        """Determine appropriate disclaimer type based on page path"""
        
        path_lower = path.lower()
        
        if "/research" in path_lower:
            return "research"
        elif "/contract" in path_lower:
            return "contracts"
        elif "/dashboard" in path_lower:
            return "dashboard"
        elif "/analy" in path_lower:
            return "analyze"
        elif "/client-portal" in path_lower:
            return "client-portal"
        elif "/admin" in path_lower:
            return "admin"
        elif "/education" in path_lower:
            return "education"
        elif "/mobile" in path_lower:
            return "mobile"
        else:
            return "global"

    async def health_check(self) -> Dict:
        """Comprehensive health check for disclaimer service"""
        
        self.health_checks += 1
        self.last_health_check = datetime.utcnow()
        
        try:
            # Test disclaimer retrieval
            test_disclaimer = await self.get_disclaimer("/test", "global")
            
            # Check if disclaimers are properly loaded
            disclaimers_loaded = len(self.disclaimers) > 0
            
            # Calculate uptime
            uptime_seconds = (datetime.utcnow() - self.service_start_time).total_seconds()
            
            health_status = {
                "status": "healthy" if self.is_healthy else "degraded",
                "timestamp": self.last_health_check.isoformat(),
                "uptime_seconds": uptime_seconds,
                "disclaimers_loaded": disclaimers_loaded,
                "total_requests": self.disclaimer_requests,
                "total_health_checks": self.health_checks,
                "last_error": self.last_error,
                "disclaimer_types_available": list(self.disclaimers.keys()),
                "service_metrics": {
                    "requests_per_minute": self.disclaimer_requests / max(uptime_seconds / 60, 1),
                    "error_rate": 0.0 if self.is_healthy else 1.0
                }
            }
            
            # Reset health status if service is working
            if disclaimers_loaded and test_disclaimer:
                self.is_healthy = True
                self.last_error = None
            
            logger.info(f"[HEALTH] Service health check completed: {health_status['status']}")
            return health_status
            
        except Exception as e:
            logger.error(f"[ERROR] Health check failed: {e}")
            self.is_healthy = False
            self.last_error = str(e)
            
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "service_healthy": False
            }

# Global service instance
disclaimer_service = DisclaimerService()

@app.get("/health")
async def health_endpoint():
    """Health check endpoint for monitoring"""
    health_data = await disclaimer_service.health_check()
    
    if health_data["status"] == "healthy":
        return JSONResponse(content=health_data, status_code=200)
    else:
        return JSONResponse(content=health_data, status_code=503)

@app.get("/disclaimer/{disclaimer_type}")
async def get_disclaimer_endpoint(disclaimer_type: str, page_path: str = "/"):
    """Get disclaimer by type"""
    disclaimer_data = await disclaimer_service.get_disclaimer(page_path, disclaimer_type)
    return JSONResponse(content=disclaimer_data)

@app.get("/disclaimer")
async def get_auto_disclaimer(page_path: str = "/"):
    """Get disclaimer automatically determined by page path"""
    disclaimer_data = await disclaimer_service.get_disclaimer(page_path, "auto")
    return JSONResponse(content=disclaimer_data)

@app.get("/status")
async def service_status():
    """Detailed service status and metrics"""
    uptime = (datetime.utcnow() - disclaimer_service.service_start_time).total_seconds()
    
    return JSONResponse(content={
        "service": "Legal Disclaimer Service",
        "status": "running",
        "version": "1.0.0",
        "uptime_seconds": uptime,
        "total_requests": disclaimer_service.disclaimer_requests,
        "health_checks": disclaimer_service.health_checks,
        "disclaimers_available": list(disclaimer_service.disclaimers.keys()),
        "last_health_check": disclaimer_service.last_health_check.isoformat() if disclaimer_service.last_health_check else None,
        "is_healthy": disclaimer_service.is_healthy,
        "compliance_level": "CRITICAL"
    })

@app.get("/disclaimers/all")
async def get_all_disclaimers():
    """Get all available disclaimer templates"""
    return JSONResponse(content={
        "disclaimers": disclaimer_service.disclaimers,
        "total_count": len(disclaimer_service.disclaimers),
        "service_status": "active"
    })

if __name__ == "__main__":
    logger.info("🚨 STARTING CRITICAL DISCLAIMER SERVICE")
    logger.info("🔒 Legal compliance protection ACTIVE")
    
    # Run the service on port 8001 (separate from main API)
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=8001,
        log_level="info",
        reload=False  # Disable reload for production stability
    )