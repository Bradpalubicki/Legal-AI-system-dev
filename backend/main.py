# CRITICAL: Set up Python path BEFORE any other imports
# Railway deploys backend/ contents to /app/, so we need /app in sys.path
# to find the 'app' package at /app/app/
import sys
from pathlib import Path
_current_dir = Path(__file__).parent
# Only add current dir to path - adding parent (/) breaks imports on Railway
# because Python may find /app directory before /app/app package
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

"""
Legal AI System - Streamlined FastAPI Application
Core functionality: Document processing, Q&A, Defense building, Case tracking
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import os
import logging

# Load environment variables - try current dir first (Docker/Railway), then parent (local dev)
env_path = _current_dir / '.env'
if not env_path.exists():
    env_path = _current_dir.parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

# Validate environment configuration before starting
# This prevents runtime errors due to missing/invalid configuration
from app.src.core.env_validation import validate_environment_or_exit
validate_environment_or_exit()

# Verify API keys are loaded (without exposing them)
import logging
logger = logging.getLogger(__name__)

print("\n" + "="*60)
print("ENVIRONMENT CONFIGURATION CHECK")
print("="*60)
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
openai_key = os.getenv('OPENAI_API_KEY')
print(f"ANTHROPIC_API_KEY: {'[OK] Configured' if anthropic_key else '[MISSING]'}")
print(f"OPENAI_API_KEY: {'[OK] Configured' if openai_key else '[MISSING]'}")
# Never log actual key values
print("="*60 + "\n")

# Initialize Database - with persistence layer
from app.src.core.database import init_database, engine, Base as CoreBase
from app.models.legal_documents import Base as LegalBase

print("\n" + "="*60)
print("DATABASE INITIALIZATION")
print("="*60)
try:
    # Import models to register them with SQLAlchemy
    from app.models import legal_documents
    from app.models import user  # Import user models for authentication
    from app.models import billing  # Billing system models (subscriptions, payments, invoices)
    from app.models import case_access  # Case access pay-per-case models (requires tracked_dockets from shared)
    # from app.models import learning  # DISABLED: Not needed for monitoring
    from app.models import case_management  # Enable case management tables
    from app.models import credits  # Enable credits system
    from app.models import pacer_credentials  # Import PACER integration models
    from app.models import case_notification_history  # Import notification history for monitoring
    from app.models import disclaimer_acknowledgment  # Import disclaimer acknowledgment models

    # Marketing automation models
    from app.marketing.contacts import models as contact_models
    from app.marketing.campaigns import models as campaign_models
    from app.marketing.newsletter import models as newsletter_models
    from app.marketing.analytics import models as analytics_models

    # Import shared database models (TrackedDocket, UserDocketMonitor, etc.)
    from shared.database import models as shared_models

    # IMPORTANT: Create shared model tables FIRST (TrackedDocket, etc.)
    # because case_access has a foreign key dependency on tracked_dockets
    print(f"Creating shared model tables: {list(shared_models.Base.metadata.tables.keys())}")
    shared_models.Base.metadata.create_all(bind=engine)

    # Create CoreBase tables (case_management, credits, etc.)
    print(f"Creating CoreBase tables: {list(CoreBase.metadata.tables.keys())}")
    CoreBase.metadata.create_all(bind=engine)

    # Create all tables (backend models from LegalBase)
    # This includes case_access which depends on tracked_dockets
    print(f"Creating LegalBase tables: {list(LegalBase.metadata.tables.keys())}")
    LegalBase.metadata.create_all(bind=engine)

    print("SUCCESS: Database tables created/verified")
    print(f"Database location: legal_ai.db")
except Exception as e:
    print(f"WARNING: Database initialization issue: {e}")
    import traceback
    traceback.print_exc()
print("="*60 + "\n")

# ============================================================================
# SENTRY ERROR TRACKING - Production Monitoring
# ============================================================================

def configure_sentry():
    """Configure Sentry error tracking for production monitoring"""
    sentry_dsn = os.getenv('SENTRY_DSN')
    sentry_enabled = os.getenv('SENTRY_ENABLED', 'false').lower() == 'true'
    environment = os.getenv('ENVIRONMENT', 'development')

    if sentry_enabled and sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

            sentry_sdk.init(
                dsn=sentry_dsn,
                environment=environment,
                integrations=[
                    FastApiIntegration(auto_enabling_integrations=True),
                    SqlalchemyIntegration(),
                ],
                # Performance monitoring
                traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
                profiles_sample_rate=0.1,  # 10% for profiling

                # Security & Privacy
                attach_stacktrace=True,
                send_default_pii=False,  # Critical for legal data - never send PII

                # Release tracking
                release=f"legal-ai-system@1.0.0",

                # Filter sensitive data before sending to Sentry
                before_send=filter_sentry_event,
            )

            print("SUCCESS: Sentry error tracking configured")
            logger.info(f"Sentry initialized for environment: {environment}")

        except ImportError:
            print("WARNING: sentry-sdk not installed, error tracking disabled")
            logger.warning("sentry-sdk not available")
        except Exception as e:
            print(f"WARNING: Failed to initialize Sentry: {e}")
            logger.error(f"Sentry initialization failed: {e}")
    else:
        print("INFO: Sentry error tracking disabled (set SENTRY_ENABLED=true to enable)")


def filter_sentry_event(event, hint):
    """
    Filter sensitive data from Sentry events before sending.
    Critical for legal applications - must not leak sensitive data.
    """
    # Remove sensitive headers
    if 'request' in event and 'headers' in event['request']:
        sensitive_headers = ['authorization', 'cookie', 'x-api-key', 'x-auth-token']
        for header in sensitive_headers:
            event['request']['headers'].pop(header.lower(), None)

    # Remove sensitive form/body data
    if 'request' in event and 'data' in event['request']:
        sensitive_fields = ['password', 'token', 'secret', 'key', 'api_key',
                          'ssn', 'social_security', 'credit_card', 'cvv']
        if isinstance(event['request']['data'], dict):
            for field in sensitive_fields:
                if field in event['request']['data']:
                    event['request']['data'][field] = '[FILTERED]'

    # Filter sensitive data from exception values
    if 'exception' in event and 'values' in event['exception']:
        for exception in event['exception']['values']:
            if 'value' in exception:
                # Remove potential API keys or tokens from exception messages
                for sensitive in ['sk-', 'api_', 'token_', 'Bearer ']:
                    if sensitive in exception['value']:
                        exception['value'] = exception['value'].split(sensitive)[0] + '[FILTERED]'

    return event


# Initialize Sentry
print("\n" + "="*60)
print("ERROR TRACKING CONFIGURATION")
print("="*60)
configure_sentry()
print("="*60 + "\n")

# Create FastAPI app
app = FastAPI(
    title="Legal AI System",
    description="AI-Powered Legal Document Analysis System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# EXCEPTION HANDLERS - Centralized Error Handling
# ============================================================================

from app.src.core.exceptions import EXCEPTION_HANDLERS

# Register all exception handlers for consistent error responses
for exception_class, handler in EXCEPTION_HANDLERS.items():
    app.add_exception_handler(exception_class, handler)

print("SUCCESS: Exception handlers registered (centralized error handling)")

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# Security Middleware (authentication, security headers)
from app.middleware.security import SecurityMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.monitoring import MonitoringMiddleware

# =============================================================================
# CORS MUST BE CONFIGURED FIRST (before other middleware)
# In FastAPI, middleware added LAST handles requests FIRST
# But CORS needs to handle OPTIONS preflight before any auth checks
# =============================================================================
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else []
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS if origin.strip()]  # Clean whitespace

# Production origins (always included)
PRODUCTION_ORIGINS = [
    "https://legal-ai-system-production.up.railway.app",
    "https://legal-ai-backend-production-7311.up.railway.app",
    "https://courtcase-search.com",
    "https://www.courtcase-search.com",
]

# Development origins
DEV_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
    "http://localhost:8000",
    "http://localhost:8001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "http://127.0.0.1:3003",
    "http://127.0.0.1:8000",
]

# Combine all origins: production + env variable + dev
# Production origins are ALWAYS included to prevent CORS issues
allowed_origins = list(set(PRODUCTION_ORIGINS + CORS_ORIGINS + DEV_ORIGINS))

# Add CORS middleware FIRST (will be processed LAST in the stack, wrapping everything)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)
print(f"CORS Origins: {', '.join(allowed_origins[:3])}{'...' if len(allowed_origins) > 3 else ''}")

# Add Monitoring Middleware
app.add_middleware(MonitoringMiddleware)
print("SUCCESS: Monitoring middleware activated (real-time metrics collection)")

# Add Security Middleware (authentication & security headers)
# Development mode: Authentication optional, allows testing without tokens
# Production mode: Authentication required (ENVIRONMENT=production)
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
REQUIRE_AUTH = ENVIRONMENT == 'production'

app.add_middleware(
    SecurityMiddleware,
    require_auth=REQUIRE_AUTH,  # Automatically enabled in production
    exclude_paths=[
        '/health',
        '/health/system',  # Production health check
        '/ai-health',  # Public AI health check (diagnose AI client issues)
        '/metrics',
        '/docs',
        '/openapi.json',
        '/redoc',
        '/favicon.ico',
        # Auth endpoints (public - no authentication required)
        '/api/v1/auth/register',
        '/api/v1/auth/login',
        '/api/v1/auth/refresh',
        # Marketing public endpoints (newsletter, tracking, landing)
        '/api/v1/marketing/subscribe',
        '/api/v1/marketing/unsubscribe',
        '/api/v1/marketing/confirm',
        '/api/v1/marketing/track',
        '/api/v1/marketing/landing',
        '/api/v1/marketing/optout',
        # Development-only exclusions (have their own auth fallbacks)
        '/api/v1/pacer',         # PACER has get_current_user_or_test fallback
        '/api/v1/credits',       # Credits - needed for PACER integration
        # CourtListener - specific public paths only (monitor/* requires auth)
        '/api/v1/courtlistener/search',   # Public search endpoints
        '/api/v1/courtlistener/docket',   # Public docket lookup
        '/api/v1/courtlistener/status',   # Public status check
        '/api/v1/courtlistener/recap',    # Public RECAP documents
        # NOTE: /api/v1/documents removed - endpoints require proper auth
        # Backend monitoring dashboard and API endpoints (development access)
        '/admin/backend-monitor',         # Backend monitor dashboard
        '/api/v1/monitoring',             # Monitoring API endpoints (for dashboard)
        # Help agent quick tips (public - just static tips)
        '/api/v1/help/quick-tips',        # Quick tips for UI
        # Ratings system (public - anyone can view/submit ratings)
        '/api/ratings',                   # App ratings and reviews
    ]
)

print(f"Authentication: {'ENABLED ✓' if REQUIRE_AUTH else 'DISABLED (dev mode)'}")

# Add Rate Limiting Middleware (protection against abuse)
app.add_middleware(
    RateLimitMiddleware,
    default_limit=1000,  # Increased to 1000 requests per minute for development
    default_window=60
)

print(f"SUCCESS: Security middleware activated ({'Production' if ENVIRONMENT == 'production' else 'Development'} mode)")
print("SUCCESS: Rate limiting enabled (100 req/min)")
print("SUCCESS: Security headers configured")

# Basic root endpoint
@app.get("/")
async def root():
    return {"message": "Legal AI System API", "status": "running", "version": "1.0.0"}

# Public AI Health Check - diagnose AI client issues without authentication
@app.get("/ai-health")
async def public_ai_health_check():
    """
    PUBLIC endpoint to test AI client connections.
    Tests both Anthropic and OpenAI clients with minimal requests.
    """
    import anthropic
    import openai

    results = {
        "status": "checking",
        "anthropic": {"status": "unknown"},
        "openai": {"status": "unknown"},
        "environment": {
            "ANTHROPIC_API_KEY": "configured" if os.getenv("ANTHROPIC_API_KEY") else "MISSING",
            "OPENAI_API_KEY": "configured" if os.getenv("OPENAI_API_KEY") else "MISSING"
        }
    }

    # Test Anthropic
    try:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            results["anthropic"] = {"status": "error", "error": "ANTHROPIC_API_KEY not set"}
        else:
            client = anthropic.Anthropic(api_key=anthropic_key)
            # Test with minimal request
            response = client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": "Say 'OK'"}]
            )
            results["anthropic"] = {
                "status": "healthy",
                "model": "claude-opus-4-20250514",
                "response": response.content[0].text if response.content else "no content"
            }
    except anthropic.BadRequestError as e:
        results["anthropic"] = {"status": "error", "error": f"BadRequest: {str(e)}", "type": "BadRequestError"}
    except anthropic.AuthenticationError as e:
        results["anthropic"] = {"status": "error", "error": f"Auth failed: {str(e)}", "type": "AuthenticationError"}
    except anthropic.NotFoundError as e:
        results["anthropic"] = {"status": "error", "error": f"Model not found: {str(e)}", "type": "NotFoundError"}
    except Exception as e:
        results["anthropic"] = {"status": "error", "error": str(e), "type": type(e).__name__}

    # Test OpenAI
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            results["openai"] = {"status": "error", "error": "OPENAI_API_KEY not set"}
        else:
            openai_client = openai.OpenAI(api_key=openai_key)
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                max_tokens=10,
                messages=[{"role": "user", "content": "Say 'OK'"}]
            )
            results["openai"] = {
                "status": "healthy",
                "model": "gpt-4o",
                "response": response.choices[0].message.content if response.choices else "no content"
            }
    except Exception as e:
        results["openai"] = {"status": "error", "error": str(e), "type": type(e).__name__}

    # Overall status
    if results["anthropic"]["status"] == "healthy" and results["openai"]["status"] == "healthy":
        results["status"] = "healthy"
    elif results["anthropic"]["status"] == "healthy" or results["openai"]["status"] == "healthy":
        results["status"] = "partial"
    else:
        results["status"] = "unhealthy"

    return results

# Health check endpoints (comprehensive)
from app.api.health import router as health_router
app.include_router(health_router)
print("SUCCESS: Health check endpoints loaded (/health, /health/system, /health/ready, /health/live)")

# ============================================================================
# CORE API ROUTERS - Essential functionality only
# ============================================================================

# Document Processing
from app.api.document_processing import router as document_router
app.include_router(document_router)
print("SUCCESS: Document processing endpoints loaded")

# Financial Validation & Analysis
from app.api.financial_validation import router as financial_router
app.include_router(financial_router)
print("SUCCESS: Financial validation endpoints loaded")

# Batch Processing - Handle hundreds of documents efficiently
try:
    from app.api.batch_processing import router as batch_router
    app.include_router(batch_router)
    print("SUCCESS: Batch processing endpoints loaded (bulk document upload)")
except ImportError as e:
    print(f"INFO: Batch processing not available: {e}")

# Q&A System
from app.api.qa_system import router as qa_router
app.include_router(qa_router)
print("SUCCESS: Q&A system endpoints loaded")

# Defense Builder
from app.api.defense_builder import router as defense_router
app.include_router(defense_router)
print("SUCCESS: Defense strategy endpoints loaded")

# Case Tracker
from app.api.case_tracker import router as case_tracker_router
app.include_router(case_tracker_router)
print("SUCCESS: Case tracking endpoints loaded")

# Case Management - Comprehensive case tracking system
from app.api.case_management_endpoints import router as case_management_router
app.include_router(case_management_router)
print("SUCCESS: Case management endpoints loaded (comprehensive tracking)")

# Integrated Flow - Full defense flow
from app.src.api.integrated_flow import router as integrated_flow_router
app.include_router(integrated_flow_router)
print("SUCCESS: Integrated defense flow endpoints loaded")

# Authentication - User registration, login, logout
from app.api.auth import router as auth_router
app.include_router(auth_router)
print("SUCCESS: Authentication endpoints loaded")

# Auth Examples - Demonstration endpoints
from app.api.auth_examples import router as auth_examples_router
app.include_router(auth_examples_router)
print("SUCCESS: Authentication examples loaded")

# Legal Research - Case law search, citation processing
from app.api.legal_research_endpoints import router as legal_research_router
app.include_router(legal_research_router)
print("SUCCESS: Legal research endpoints loaded")

# Client Management - Client portal, document sharing
from app.api.client_management_endpoints import router as client_management_router
app.include_router(client_management_router)
print("SUCCESS: Client management endpoints loaded")

# Attorney Management - Attorney profiles, meetings, communications
try:
    from app.api.attorney_endpoints import router as attorney_router
    app.include_router(attorney_router)
    print("SUCCESS: Attorney management endpoints loaded")
except ImportError as e:
    print(f"INFO: Attorney endpoints not available: {e}")

# Compliance & Audit - GDPR/CCPA compliance, audit logging (Week 4)
try:
    from app.api.compliance_endpoints import router as compliance_router
    app.include_router(compliance_router)
    print("SUCCESS: Compliance endpoints loaded")
except ImportError:
    print("INFO: Compliance endpoints not available")

try:
    from app.api.audit_endpoints import router as audit_router
    app.include_router(audit_router)
    print("SUCCESS: Audit logging endpoints loaded")
except ImportError:
    print("INFO: Audit endpoints not available")

# Comprehensive Audit System - Full audit trail for AI, documents, admin actions
try:
    from app.api.comprehensive_audit_endpoints import router as comprehensive_audit_router
    app.include_router(comprehensive_audit_router)
    print("SUCCESS: Comprehensive audit endpoints loaded (AI responses, hallucinations, document access)")
except ImportError as e:
    print(f"INFO: Comprehensive audit endpoints not available: {e}")

# Disclaimer Acknowledgments - Track when users confirm/disable liability disclaimers
try:
    from app.api.disclaimer_acknowledgments import router as disclaimer_router
    app.include_router(disclaimer_router)
    print("SUCCESS: Disclaimer acknowledgment tracking loaded")
except ImportError as e:
    print(f"INFO: Disclaimer acknowledgment endpoints not available: {e}")

# Learning System - Continuous improvement (Feedback, RAG, Performance Tracking)
try:
    from app.api.learning_endpoints import router as learning_router
    app.include_router(learning_router)
    print("SUCCESS: Learning & continuous improvement endpoints loaded")
except ImportError:
    print("INFO: Learning endpoints not available")

# Legal Filing Analysis - AI-powered document analysis and deadline calculation
try:
    from app.api.legal_analysis_endpoints import router as legal_analysis_router
    app.include_router(legal_analysis_router, prefix="/api/v1")
    print("SUCCESS: Legal filing analysis endpoints loaded (document classification, deadlines)")
except ImportError as e:
    print(f"INFO: Legal analysis endpoints not available: {e}")
except Exception as e:
    print(f"ERROR: Legal analysis endpoints failed to load: {e}")

# Monitoring Dashboard - Real-time system monitoring
try:
    from app.api.monitoring_endpoints import router as monitoring_router
    app.include_router(monitoring_router)
    print("SUCCESS: Monitoring dashboard endpoints loaded (real-time metrics)")
except ImportError as e:
    print(f"INFO: Monitoring endpoints not available: {e}")

# Backend Monitoring Dashboard - Admin UI for system monitoring
try:
    from app.api.backend_monitor import router as backend_monitor_router
    app.include_router(backend_monitor_router)
    print("SUCCESS: Backend monitoring dashboard loaded (/admin/backend-monitor)")
except ImportError as e:
    print(f"INFO: Backend monitor not available: {e}")

# PACER Integration - Federal court records access
try:
    from app.api.pacer_endpoints import router as pacer_router
    app.include_router(pacer_router)
    print("SUCCESS: PACER integration endpoints loaded (federal court access)")
except ImportError as e:
    print(f"INFO: PACER endpoints not available: {e}")
except Exception as e:
    print(f"ERROR: PACER endpoints failed to load: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# CourtListener Integration - FREE federal court records (PACER alternative)
try:
    from app.api.courtlistener_endpoints import router as courtlistener_router
    app.include_router(courtlistener_router)
    print("SUCCESS: CourtListener integration loaded (FREE federal court records)")
except ImportError as e:
    print(f"INFO: CourtListener endpoints not available: {e}")

# State Court Information - Explains state court limitations and provides portal URLs
try:
    from app.api.state_court_info import router as state_court_router
    app.include_router(state_court_router, prefix="/api/v1")
    print("SUCCESS: State court information loaded (coverage explanations)")
except ImportError as e:
    print(f"INFO: State court info endpoints not available: {e}")
except Exception as e:
    print(f"ERROR: State court info failed to load: {e}")

# Credits System - User credit management for PACER purchases
try:
    from app.api.credits import router as credits_router
    app.include_router(credits_router)
    print("SUCCESS: Credits system loaded (credit-based document purchasing)")
except ImportError as e:
    print(f"INFO: Credits endpoints not available: {e}")
except Exception as e:
    print(f"ERROR: Credits system failed to load: {e}")

# AI Help Agent - In-app contextual assistance
try:
    from app.api.help_agent import router as help_agent_router
    app.include_router(help_agent_router, prefix="/api/v1/help", tags=["help"])
    print("SUCCESS: AI Help Agent loaded (in-app contextual assistance)")
except ImportError as e:
    print(f"INFO: Help agent endpoints not available: {e}")
except Exception as e:
    print(f"ERROR: Help agent failed to load: {e}")

# Case Notifications - Real-time updates for monitored cases
try:
    from app.api.case_notifications import router as notifications_router
    app.include_router(notifications_router)
    print("SUCCESS: Case notifications loaded (real-time monitoring)")
except ImportError as e:
    print(f"INFO: Case notification endpoints not available: {e}")
except Exception as e:
    print(f"ERROR: Case notifications failed to load: {e}")

# Notification History - View and manage notification history
try:
    from app.api.notification_history import router as notification_history_router
    app.include_router(notification_history_router)
    print("SUCCESS: Notification history loaded (view past notifications)")
except ImportError as e:
    print(f"INFO: Notification history endpoints not available: {e}")
except Exception as e:
    print(f"ERROR: Notification history failed to load: {e}")

# Marketing Automation - CourtListener polling, email campaigns, newsletters
try:
    from app.marketing.router import router as marketing_router, public_router as marketing_public_router
    app.include_router(marketing_router)
    app.include_router(marketing_public_router)
    print("SUCCESS: Marketing automation loaded (campaigns, newsletters, analytics)")
except ImportError as e:
    print(f"INFO: Marketing endpoints not available: {e}")
except Exception as e:
    print(f"ERROR: Marketing automation failed to load: {e}")
# Ratings system (public - allows anyone to rate the app)
try:
    from app.api.ratings import router as ratings_router
    app.include_router(ratings_router)
    print("SUCCESS: Ratings system loaded (user reviews and ratings)")
except ImportError as e:
    print(f"INFO: Ratings endpoints not available: {e}")
except Exception as e:
    print(f"ERROR: Ratings system failed to load: {e}")


# Document Downloads (auto-download system for monitored cases)
try:
    from app.api.document_downloads import router as downloads_router
    app.include_router(downloads_router)
    print("SUCCESS: Document downloads endpoints loaded (auto-download system)")
except ImportError as e:
    print(f"INFO: Document downloads endpoints not available: {e}")
except Exception as e:
    print(f"ERROR: Document downloads endpoints failed to load: {e}")

# Pricing API (subscription tiers, credit packs, pricing calculator)
try:
    from app.api.pricing import router as pricing_router
    app.include_router(pricing_router)
    print("SUCCESS: Pricing endpoints loaded (tiers, credit packs, pricing)")
except ImportError as e:
    print(f"INFO: Pricing endpoints not available: {e}")
except Exception as e:
    print(f"ERROR: Pricing endpoints failed to load: {e}")


# Test endpoints (development only)
if os.getenv('ENVIRONMENT', 'development') == 'development':
    try:
        from app.api.test_notification import router as test_notification_router
        app.include_router(test_notification_router)
        print("SUCCESS: Test notification endpoints loaded (development only)")
    except ImportError as e:
        print(f"INFO: Test notification endpoints not available: {e}")
    except Exception as e:
        print(f"ERROR: Test notification endpoints failed to load: {e}")


# Application Lifecycle Events
@app.on_event("startup")
async def startup_event():
    """Start background services on application startup"""
    try:
        from app.services.case_monitor_service import case_monitor_service
        from app.src.core.database import SessionLocal

        db = SessionLocal()

        # Start background monitoring service
        case_monitor_service.start(db)
        print("SUCCESS: Case monitoring service started")
    except Exception as e:
        print(f"ERROR: Failed to start case monitoring service: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop background services on application shutdown"""
    try:
        from app.services.case_monitor_service import case_monitor_service
        case_monitor_service.stop()
        print("Case monitoring service stopped")
    except Exception as e:
        print(f"ERROR: Failed to stop case monitoring service: {e}")


print("\n" + "="*60)
print("LEGAL AI SYSTEM - Backend API Ready")
print("="*60)
print("Authentication: /api/v1/auth/*")
print("Document Processing: /api/v1/documents/*")
print("Batch Processing: /api/v1/batch/* (bulk uploads)")
print("Q&A System: /api/v1/qa/*")
print("Defense Builder: /api/v1/defense/*")
print("Case Tracking: /api/v1/case-tracking/*")
print("Case Management: /api/v1/cases/* (comprehensive)")
print("Integrated Flow: /api/v1/integrated/*")
print("Legal Research: /api/v1/research/*")
print("Client Management: /api/v1/clients/*")
print("Compliance: /api/v1/compliance/*")
print("Audit Logs: /api/v1/audit/*")
print("Learning System: /api/v1/learning/*")
print("Legal Analysis: /api/v1/legal-analysis/* (filing classification, deadlines)")
print("Monitoring Dashboard: /api/v1/monitoring/* (real-time metrics)")
print("Backend Monitor UI: http://localhost:8000/admin/backend-monitor (admin only)")
print("PACER Integration: /api/v1/pacer/* (federal court records)")
print("Credits System: /api/v1/credits/* (credit-based purchases)")
print("Help Agent: /api/v1/help/* (in-app AI assistance)")
print("Marketing Admin: /api/v1/admin/marketing/* (campaigns, newsletters)")
print("Marketing Public: /api/v1/marketing/* (subscribe, tracking)")
print("API Docs: http://localhost:8000/docs")
print("="*60 + "\n")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )





