"""
Documents System
Complete document processing with comparison, templates, and generation capabilities.
"""

from .comparison import (
    DocumentComparison,
    DocumentChange,
    Comment,
    DocumentVersion,
    ComparisonResult,
    ApprovalWorkflow,
    RedlineDocument,
    ChangeType,
    ComparisonMode,
    ApprovalStatus,
    CommentType,
    document_comparison,
    get_comparison_endpoints,
    initialize_document_comparison
)

from .templates import (
    TemplateManager,
    Template,
    TemplateSection,
    TemplateField,
    TemplateInstance,
    AutoFillMapping,
    TemplateLibrary,
    TemplateType,
    TemplateCategory,
    FieldType,
    ValidationRule,
    JurisdictionLevel,
    template_manager,
    get_template_endpoints,
    initialize_template_system
)

from .generator import (
    DocumentGenerator,
    GeneratedDocument,
    DocumentPacket,
    CourtFormatting,
    BulkGenerationJob,
    MergeField,
    SignaturePlacement,
    Watermark,
    DocumentFormat,
    WatermarkType,
    SignatureType,
    CourtFormat,
    FilingType,
    document_generator,
    get_generation_endpoints,
    initialize_document_generation
)

__all__ = [
    # Document Comparison
    "DocumentComparison",
    "DocumentChange",
    "Comment",
    "DocumentVersion",
    "ComparisonResult",
    "ApprovalWorkflow",
    "RedlineDocument",
    "ChangeType",
    "ComparisonMode",
    "ApprovalStatus",
    "CommentType",
    "document_comparison",
    "get_comparison_endpoints",
    "initialize_document_comparison",

    # Template System
    "TemplateManager",
    "Template",
    "TemplateSection",
    "TemplateField",
    "TemplateInstance",
    "AutoFillMapping",
    "TemplateLibrary",
    "TemplateType",
    "TemplateCategory",
    "FieldType",
    "ValidationRule",
    "JurisdictionLevel",
    "template_manager",
    "get_template_endpoints",
    "initialize_template_system",

    # Document Generation
    "DocumentGenerator",
    "GeneratedDocument",
    "DocumentPacket",
    "CourtFormatting",
    "BulkGenerationJob",
    "MergeField",
    "SignaturePlacement",
    "Watermark",
    "DocumentFormat",
    "WatermarkType",
    "SignatureType",
    "CourtFormat",
    "FilingType",
    "document_generator",
    "get_generation_endpoints",
    "initialize_document_generation",

    # Unified functions
    "get_document_endpoints",
    "initialize_document_system"
]


async def get_document_endpoints():
    """Get all document processing endpoints from all modules"""
    endpoints = []

    # Collect endpoints from all modules
    comparison_endpoints = await get_comparison_endpoints()
    template_endpoints = await get_template_endpoints()
    generation_endpoints = await get_generation_endpoints()

    endpoints.extend(comparison_endpoints)
    endpoints.extend(template_endpoints)
    endpoints.extend(generation_endpoints)

    return endpoints


async def initialize_document_system():
    """Initialize the complete document processing system"""
    print("Initializing Document Processing System...")

    results = []

    # Initialize all subsystems
    comparison_init = await initialize_document_comparison()
    results.append(("Document Comparison", comparison_init))

    template_init = await initialize_template_system()
    results.append(("Template Library", template_init))

    generation_init = await initialize_document_generation()
    results.append(("Document Generation", generation_init))

    # Check results
    failed_systems = [name for name, success in results if not success]
    successful_systems = [name for name, success in results if success]

    if failed_systems:
        print(f"WARNING: Failed to initialize: {', '.join(failed_systems)}")

    if successful_systems:
        print(f"SUCCESS: Successfully initialized: {', '.join(successful_systems)}")

    # Get total endpoint count
    all_endpoints = await get_document_endpoints()
    total_endpoints = len(all_endpoints)

    print(f"Document Processing System initialized with {total_endpoints} endpoints")
    print("=" * 60)
    print("DOCUMENT PROCESSING SYSTEM READY")
    print("=" * 60)
    print("Features Available:")
    print("- Side-by-side document comparison with change tracking")
    print("- Version history and collaborative review workflows")
    print("- Comprehensive template library with auto-fill")
    print("- Court-ready document generation and formatting")
    print("- Multi-document packets and bulk processing")
    print("- Electronic filing preparation and watermarking")
    print("=" * 60)

    return len(failed_systems) == 0


async def trigger_system_wide_updates(operation_type: str, document_id: str, metadata: dict = None):
    """Trigger system-wide updates when document operations occur"""
    try:
        from datetime import datetime
        from decimal import Decimal

        # This function would integrate with analytics, notifications, and audit systems
        print(f"System-wide update triggered: {operation_type} for document {document_id}")

        # Update analytics
        try:
            from ..analytics import user_metrics_analyzer, business_analytics_engine

            if operation_type == "document_generated":
                await user_metrics_analyzer.track_engagement(
                    user_id=metadata.get("user_id", "unknown"),
                    activity_type="document_generation",
                    duration_minutes=metadata.get("duration", 0),
                    feature_used="document_generator"
                )
            elif operation_type == "template_used":
                await user_metrics_analyzer.track_engagement(
                    user_id=metadata.get("user_id", "unknown"),
                    activity_type="template_usage",
                    feature_used="template_library"
                )
            elif operation_type == "comparison_performed":
                await user_metrics_analyzer.track_engagement(
                    user_id=metadata.get("user_id", "unknown"),
                    activity_type="document_comparison",
                    feature_used="document_comparison"
                )

            # Track business metrics
            if metadata and metadata.get("billable_time"):
                await business_analytics_engine.track_customer_lifecycle(
                    firm_id=metadata.get("firm_id", "unknown"),
                    event_type="billable_activity",
                    value=Decimal(str(metadata.get("billable_amount", 0)))
                )

        except ImportError:
            # Analytics system not available
            pass
        except Exception as e:
            print(f"Analytics update failed: {e}")

        # Audit trail
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation_type,
            "document_id": document_id,
            "metadata": metadata or {},
            "system": "document_processing"
        }
        print(f"Audit entry: {audit_entry}")

        # Notification system (placeholder)
        if operation_type in ["approval_requested", "comment_added", "document_shared"]:
            print(f"Notification would be sent for: {operation_type}")

        return True

    except Exception as e:
        print(f"Error triggering system-wide updates: {e}")
        return False