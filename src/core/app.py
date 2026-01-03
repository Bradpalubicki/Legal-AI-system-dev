from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
from pydantic import BaseModel
import logging
import importlib.util
import os

from .config import settings
from .logging import setup_logging

# Setup logging first
setup_logging()
logger = logging.getLogger("legal_ai")

# Load PACER router directly from file without triggering package imports
def load_pacer_router():
    """Load PACER router directly from file without triggering package imports."""
    router_path = os.path.join(os.path.dirname(__file__), "..", "pacer_gateway", "router.py")
    spec = importlib.util.spec_from_file_location("pacer_router", router_path)
    pacer_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pacer_module)
    return pacer_module.router

pacer_router = load_pacer_router()

# Create FastAPI app directly at module level
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A comprehensive AI-powered legal document analysis and research system",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# Add CORS middleware to allow requests from localhost:3006
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3006", "http://127.0.0.1:3006"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class FeedbackData(BaseModel):
    rating: int
    comments: str
    helpful: bool

class DocumentInfo(BaseModel):
    id: str
    title: str
    fileName: str
    fileSize: int
    uploadedAt: str
    status: str

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEBUG else "production"
    }

# Root endpoint
@app.get("/", tags=["root"])
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME} - TEST MODIFICATION",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Documentation not available in production"
    }

# Services status endpoint
@app.get("/api/services/status", tags=["services"])
async def get_services_status() -> Dict[str, Any]:
    """Get the status of all external services."""
    from datetime import datetime
    
    # Debug logging
    use_mock = os.getenv("USE_MOCK_SERVICES")
    pacer_user = os.getenv("PACER_USERNAME")
    westlaw_key = os.getenv("WESTLAW_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    logger.info(f"Environment check - USE_MOCK_SERVICES: {use_mock}, PACER_USERNAME: {bool(pacer_user)}, WESTLAW_API_KEY: {bool(westlaw_key)}")
    
    # Return status in the requested JSON format
    return {
        "courtlistener": {
            "available": True,
            "mode": "live",
            "last_checked": datetime.utcnow().isoformat() + "Z"
        },
        "pacer": {
            "available": bool(os.getenv("PACER_USERNAME")) or bool(os.getenv("USE_MOCK_SERVICES")),
            "mode": "mock" if os.getenv("USE_MOCK_SERVICES") else ("live" if os.getenv("PACER_USERNAME") else "disabled"),
            "reason": None if (os.getenv("PACER_USERNAME") or os.getenv("USE_MOCK_SERVICES")) else "No credentials configured"
        },
        "westlaw": {
            "available": bool(os.getenv("WESTLAW_API_KEY")) or bool(os.getenv("USE_MOCK_SERVICES")),
            "mode": "mock" if os.getenv("USE_MOCK_SERVICES") else ("live" if os.getenv("WESTLAW_API_KEY") else "disabled"),
            "reason": None if (os.getenv("WESTLAW_API_KEY") or os.getenv("USE_MOCK_SERVICES")) else "API key not provided"
        },
        "ai_services": {
            "openai": {
                "available": bool(os.getenv("OPENAI_API_KEY")) or bool(os.getenv("USE_MOCK_SERVICES")),
                "mode": "mock" if os.getenv("USE_MOCK_SERVICES") else ("live" if os.getenv("OPENAI_API_KEY") else "disabled")
            },
            "anthropic": {
                "available": bool(os.getenv("ANTHROPIC_API_KEY")) or bool(os.getenv("USE_MOCK_SERVICES")),
                "mode": "mock" if os.getenv("USE_MOCK_SERVICES") else ("live" if os.getenv("ANTHROPIC_API_KEY") else "disabled")
            }
        }
    }

# Simple test endpoint
@app.get("/api/test-simple")
async def test_simple():
    """Simple test endpoint."""
    return {"message": "Simple endpoint works"}

# Test Anthropic endpoint - simple version first
@app.get("/api/test-anthropic", tags=["test"])
async def test_anthropic() -> Dict[str, Any]:
    """Test Anthropic API functionality."""
    return {
        "status": "success",
        "message": "Anthropic test endpoint is working",
        "endpoint_registered": True
    }

# Mock document analysis endpoint for testing
@app.get("/api/documents/analysis/{document_id}", tags=["test"])
async def get_mock_document_analysis(document_id: str) -> Dict[str, Any]:
    """Mock document analysis endpoint for testing the frontend."""
    from datetime import datetime

    # Mock analysis data
    return {
        "document_id": document_id,
        "analysis_id": f"analysis_{document_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "document_type": {
            "category": "Software Development Contract",
            "confidence": 0.95,
            "subcategory": "Service Agreement"
        },
        "key_information": [
            {
                "entity_type": "party_1",
                "value": "TechCorp Solutions LLC",
                "confidence": 0.98,
                "location": "Page 1, Header"
            },
            {
                "entity_type": "party_2",
                "value": "ClientCorp Inc.",
                "confidence": 0.96,
                "location": "Page 1, Header"
            },
            {
                "entity_type": "contract_value",
                "value": "$250,000",
                "confidence": 0.89,
                "location": "Section 3.1"
            },
            {
                "entity_type": "contract_duration",
                "value": "12 months",
                "confidence": 0.92,
                "location": "Section 2.2"
            },
            {
                "entity_type": "start_date",
                "value": "2024-09-01",
                "confidence": 0.94,
                "location": "Section 2.1"
            }
        ],
        "summary": "This is a comprehensive software development contract between TechCorp Solutions LLC and ClientCorp Inc. for a 12-month project valued at $250,000. The contract includes standard intellectual property clauses, payment terms, and confidentiality agreements. Key deliverables include custom software development, testing, and deployment support.",
        "risk_assessment": {
            "overall_risk": "medium",
            "risk_factors": [
                "No explicit limitation of liability clause",
                "Broad intellectual property assignment terms",
                "90-day payment terms may impact cash flow",
                "Force majeure clause lacks pandemic provisions"
            ],
            "recommendations": [
                "Consider adding liability caps for both parties",
                "Review IP assignment scope with legal counsel",
                "Negotiate shorter payment terms (30-45 days)",
                "Update force majeure language for current risks"
            ]
        },
        "compliance_notes": [
            "Contract complies with standard commercial practices",
            "Confidentiality provisions meet industry standards",
            "Consider state-specific employment law implications"
        ],
        "extracted_dates": [
            {
                "date": "2024-09-01",
                "context": "Project start date",
                "importance": "critical"
            },
            {
                "date": "2025-08-31",
                "context": "Project end date",
                "importance": "critical"
            },
            {
                "date": "2024-09-30",
                "context": "First milestone delivery",
                "importance": "high"
            }
        ],
        "next_steps": [
            "Review contract with qualified legal counsel",
            "Negotiate any problematic terms before signing",
            "Set up milestone tracking system",
            "Prepare project kickoff documentation",
            "Establish regular progress review meetings"
        ],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

# Mock documents list endpoint
@app.get("/api/documents", tags=["documents"])
async def get_documents() -> List[DocumentInfo]:
    """Get list of documents."""
    from datetime import datetime

    # Return mock documents or empty list
    mock_documents = [
        {
            "id": "doc-1",
            "title": "Software Development Contract",
            "fileName": "dev_contract.pdf",
            "fileSize": 2048000,
            "uploadedAt": "2024-08-28T10:30:00Z",
            "status": "processed"
        },
        {
            "id": "doc-2",
            "title": "Employment Agreement",
            "fileName": "employment_agreement.pdf",
            "fileSize": 1024000,
            "uploadedAt": "2024-08-27T09:00:00Z",
            "status": "ready"
        }
    ]

    return mock_documents

# Mock feedback endpoint
@app.post("/api/documents/analysis/{document_id}/feedback", tags=["feedback"])
async def submit_feedback(document_id: str, feedback: FeedbackData) -> Dict[str, Any]:
    """Submit feedback for document analysis."""
    from datetime import datetime

    # Log the feedback (in a real app, this would go to a database)
    logger.info(f"Feedback received for document {document_id}: rating={feedback.rating}, helpful={feedback.helpful}")

    return {
        "message": "Feedback submitted successfully",
        "document_id": document_id,
        "feedback_id": f"feedback_{document_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "submitted_at": datetime.now().isoformat(),
        "status": "received"
    }

# Load document intake router
def load_document_intake_router():
    """Load document intake router directly from file without triggering package imports."""
    import importlib.util
    router_path = os.path.join(os.path.dirname(__file__), "..", "api", "routes", "document_intake.py")
    if os.path.exists(router_path):
        spec = importlib.util.spec_from_file_location("document_intake_router", router_path)
        document_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(document_module)
        return document_module.router
    return None

try:
    document_intake_router = load_document_intake_router()
    if document_intake_router:
        app.include_router(document_intake_router, prefix="/api/documents")
        logger.info("Document intake router included successfully")
    else:
        logger.warning("Document intake router not found")
except Exception as e:
    logger.error(f"Failed to load document intake router: {e}")

# Include PACER router
logger.info(f"About to include router with {len(pacer_router.routes)} routes")
logger.info(f"Router routes: {[route.path for route in pacer_router.routes]}")
app.include_router(pacer_router, prefix="/api/pacer")
print(f'PACER router registered: {pacer_router}')
print(f'App routes: {app.routes}')
logger.info(f"After including router, app has {len(app.routes)} total routes")
for route in app.routes:
    if hasattr(route, 'path'):
        logger.info(f"App route: {route.path} ({type(route).__name__})")
logger.info("PACER router included from pacer_gateway.router")

logger.info(f"FastAPI app created - Debug: {settings.DEBUG}")

# Ensure the app with registered routes is available to uvicorn
app = app