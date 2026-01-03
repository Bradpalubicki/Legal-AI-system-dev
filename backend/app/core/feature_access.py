"""
Feature Access Configuration for Tiered Pricing
Defines what features are available to each user tier/role
"""
from enum import Enum
from typing import Dict, Any, Optional
from app.models.user import UserRole


class FeatureTier(str, Enum):
    """Feature tier levels - aligned with Stripe subscription tiers"""
    FREE = "free"                    # $0 - No subscription
    BASIC = "basic"                  # $9.99/month - Basic features
    INDIVIDUAL_PRO = "individual_pro"  # $29.99/month - Advanced features
    PROFESSIONAL = "professional"    # $99/month - Complete toolkit
    PREMIUM = "premium"              # $199/month - Maximum power
    ENTERPRISE = "enterprise"        # Custom - Organizations
    ADMIN = "admin"                  # Full access - admins always get everything


class Feature(str, Enum):
    """Available features in the system"""
    # Case Management
    CASE_MONITORING = "case_monitoring"
    CASE_CREATION = "case_creation"
    CASE_NOTES = "case_notes"

    # Document Features
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DOWNLOAD = "document_download"
    DOCUMENT_EXPORT = "document_export"
    DOCUMENT_COMPARISON = "document_comparison"
    DOCUMENT_BATCH_PROCESSING = "document_batch_processing"

    # AI Features
    AI_ANALYSIS = "ai_analysis"
    AI_SUMMARIZATION = "ai_summarization"
    AI_CLAUSE_EXTRACTION = "ai_clause_extraction"
    AI_RISK_ASSESSMENT = "ai_risk_assessment"
    AI_ASSISTANT = "ai_assistant"

    # Research Features
    PACER_SEARCH = "pacer_search"
    PACER_DOWNLOAD = "pacer_download"
    COURTLISTENER_SEARCH = "courtlistener_search"
    LEGAL_RESEARCH = "legal_research"
    CITATION_VALIDATION = "citation_validation"

    # Notifications
    EMAIL_NOTIFICATIONS = "email_notifications"
    SMS_NOTIFICATIONS = "sms_notifications"
    WEBHOOK_NOTIFICATIONS = "webhook_notifications"

    # Collaboration
    TEAM_COLLABORATION = "team_collaboration"
    CLIENT_PORTAL = "client_portal"
    MATTER_MANAGEMENT = "matter_management"

    # API & Integration
    API_ACCESS = "api_access"
    WEBHOOK_INTEGRATION = "webhook_integration"
    ZAPIER_INTEGRATION = "zapier_integration"

    # Admin
    AUDIT_LOGS = "audit_logs"
    COMPLIANCE_REPORTS = "compliance_reports"

    # Defense Builder Advanced Features
    ADVERSARIAL_SIMULATION = "adversarial_simulation"


# Feature access configuration by tier - aligned with Stripe subscription tiers
# From pricing.py: FREE, BASIC ($9.99), INDIVIDUAL_PRO ($29.99), PROFESSIONAL ($99), PREMIUM ($199), ENTERPRISE
TIER_FEATURES: Dict[FeatureTier, Dict[str, Dict[str, Any]]] = {
    # ===========================================================================
    # FREE TIER - $0/month - Basic access to search
    # ===========================================================================
    FeatureTier.FREE: {
        Feature.CASE_MONITORING: {
            "enabled": True,
            "limit": 1,  # 1 case monitoring for free
            "description": "Monitor 1 case"
        },
        Feature.DOCUMENT_VIEW: {
            "enabled": True,
            "limit": 5,  # 5 document previews per month
            "description": "Limited document previews"
        },
        Feature.COURTLISTENER_SEARCH: {
            "enabled": True,
            "limit": None,  # Unlimited free searches
            "description": "Free court searches"
        },
        Feature.EMAIL_NOTIFICATIONS: {
            "enabled": False,
            "description": "Upgrade to Basic for email notifications"
        },
        Feature.AI_ANALYSIS: {
            "enabled": False,
            "description": "Upgrade to Basic for AI analysis"
        },
        Feature.ADVERSARIAL_SIMULATION: {
            "enabled": False,
            "description": "Upgrade to Basic for opposing counsel simulation"
        },
    },

    # ===========================================================================
    # BASIC TIER - $9.99/month - 20 document credits
    # ===========================================================================
    FeatureTier.BASIC: {
        Feature.CASE_MONITORING: {
            "enabled": True,
            "limit": 5,  # 5 case monitoring
            "description": "Monitor up to 5 cases"
        },
        Feature.CASE_CREATION: {
            "enabled": True,
            "limit": 5,
            "description": "Create up to 5 cases"
        },
        Feature.CASE_NOTES: {
            "enabled": True,
            "description": "Add notes to cases"
        },
        Feature.DOCUMENT_VIEW: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited document viewing"
        },
        Feature.DOCUMENT_DOWNLOAD: {
            "enabled": True,
            "limit": 20,  # 20 document credits
            "description": "20 document downloads/month"
        },
        Feature.DOCUMENT_UPLOAD: {
            "enabled": True,
            "limit": 20,
            "description": "Upload up to 20 documents"
        },
        Feature.COURTLISTENER_SEARCH: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited CourtListener searches"
        },
        Feature.EMAIL_NOTIFICATIONS: {
            "enabled": True,
            "description": "Email notifications for case updates"
        },
        Feature.AI_ANALYSIS: {
            "enabled": True,
            "limit": 20,  # Matches document credits
            "description": "Basic AI analysis (20/month)"
        },
        Feature.AI_SUMMARIZATION: {
            "enabled": True,
            "limit": 20,
            "description": "AI summaries (20/month)"
        },
        Feature.SMS_NOTIFICATIONS: {
            "enabled": False,
            "description": "Upgrade to Individual Pro for SMS"
        },
        Feature.API_ACCESS: {
            "enabled": False,
            "description": "Upgrade to Individual Pro for API access"
        },
        Feature.DOCUMENT_EXPORT: {
            "enabled": False,
            "description": "Upgrade to Individual Pro for exports"
        },
        Feature.ADVERSARIAL_SIMULATION: {
            "enabled": True,
            "counter_arguments": 3,
            "weakness_analysis": False,
            "priority_processing": False,
            "description": "3 counter-arguments with 3-level debate tree"
        },
    },

    # ===========================================================================
    # INDIVIDUAL PRO TIER - $29.99/month - 75 document credits
    # ===========================================================================
    FeatureTier.INDIVIDUAL_PRO: {
        Feature.CASE_MONITORING: {
            "enabled": True,
            "limit": 25,  # 25 case monitoring
            "description": "Monitor up to 25 cases"
        },
        Feature.CASE_CREATION: {
            "enabled": True,
            "limit": 25,
            "description": "Create up to 25 cases"
        },
        Feature.CASE_NOTES: {
            "enabled": True,
            "description": "Full case notes"
        },
        Feature.DOCUMENT_VIEW: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited document viewing"
        },
        Feature.DOCUMENT_DOWNLOAD: {
            "enabled": True,
            "limit": 75,  # 75 document credits
            "description": "75 document downloads/month"
        },
        Feature.DOCUMENT_UPLOAD: {
            "enabled": True,
            "limit": 75,
            "description": "Upload up to 75 documents"
        },
        Feature.DOCUMENT_EXPORT: {
            "enabled": True,
            "formats": ["pdf", "docx", "txt"],
            "description": "Export to multiple formats"
        },
        Feature.COURTLISTENER_SEARCH: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited CourtListener searches"
        },
        Feature.EMAIL_NOTIFICATIONS: {
            "enabled": True,
            "description": "Email notifications"
        },
        Feature.AI_ANALYSIS: {
            "enabled": True,
            "limit": 75,  # Advanced AI - matches credits
            "description": "Advanced AI analysis (75/month)"
        },
        Feature.AI_SUMMARIZATION: {
            "enabled": True,
            "limit": 75,
            "description": "AI summaries (75/month)"
        },
        Feature.AI_CLAUSE_EXTRACTION: {
            "enabled": True,
            "description": "Extract key clauses with AI"
        },
        Feature.AI_RISK_ASSESSMENT: {
            "enabled": True,
            "description": "AI risk assessment"
        },
        Feature.AI_ASSISTANT: {
            "enabled": True,
            "limit": 100,
            "description": "AI assistant queries"
        },
        Feature.API_ACCESS: {
            "enabled": True,
            "rate_limit": 1000,  # 1k requests per day
            "description": "API access"
        },
        Feature.SMS_NOTIFICATIONS: {
            "enabled": False,
            "description": "Upgrade to Professional for SMS"
        },
        Feature.TEAM_COLLABORATION: {
            "enabled": False,
            "description": "Upgrade to Professional for team features"
        },
        Feature.ADVERSARIAL_SIMULATION: {
            "enabled": True,
            "counter_arguments": 5,
            "weakness_analysis": False,
            "priority_processing": False,
            "description": "5 counter-arguments with 3-level debate tree"
        },
    },

    # ===========================================================================
    # PROFESSIONAL TIER - $99/month - 200 document credits
    # ===========================================================================
    FeatureTier.PROFESSIONAL: {
        Feature.CASE_MONITORING: {
            "enabled": True,
            "limit": 100,  # 100 case monitoring
            "description": "Monitor up to 100 cases"
        },
        Feature.CASE_CREATION: {
            "enabled": True,
            "limit": 100,
            "description": "Create up to 100 cases"
        },
        Feature.CASE_NOTES: {
            "enabled": True,
            "description": "Full case management"
        },
        Feature.DOCUMENT_VIEW: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited document viewing"
        },
        Feature.DOCUMENT_DOWNLOAD: {
            "enabled": True,
            "limit": 200,  # 200 document credits
            "description": "200 document downloads/month"
        },
        Feature.DOCUMENT_UPLOAD: {
            "enabled": True,
            "limit": 200,
            "description": "Upload up to 200 documents"
        },
        Feature.DOCUMENT_EXPORT: {
            "enabled": True,
            "formats": ["pdf", "docx", "txt", "rtf"],
            "description": "Export to all formats"
        },
        Feature.DOCUMENT_COMPARISON: {
            "enabled": True,
            "limit": 50,
            "description": "Compare documents with AI"
        },
        Feature.DOCUMENT_BATCH_PROCESSING: {
            "enabled": True,
            "description": "Batch process documents"
        },
        Feature.COURTLISTENER_SEARCH: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited searches"
        },
        Feature.PACER_SEARCH: {
            "enabled": True,
            "description": "PACER searches"
        },
        Feature.PACER_DOWNLOAD: {
            "enabled": True,
            "description": "Download PACER documents"
        },
        Feature.LEGAL_RESEARCH: {
            "enabled": True,
            "description": "Full legal research tools"
        },
        Feature.CITATION_VALIDATION: {
            "enabled": True,
            "description": "Validate legal citations"
        },
        Feature.EMAIL_NOTIFICATIONS: {
            "enabled": True,
            "description": "Email notifications"
        },
        Feature.SMS_NOTIFICATIONS: {
            "enabled": True,
            "limit": 100,
            "description": "SMS notifications (100/month)"
        },
        Feature.AI_ANALYSIS: {
            "enabled": True,
            "limit": 200,
            "description": "Advanced AI analysis (200/month)"
        },
        Feature.AI_SUMMARIZATION: {
            "enabled": True,
            "limit": 200,
            "description": "AI summaries (200/month)"
        },
        Feature.AI_CLAUSE_EXTRACTION: {
            "enabled": True,
            "description": "AI clause extraction"
        },
        Feature.AI_RISK_ASSESSMENT: {
            "enabled": True,
            "description": "AI risk assessment"
        },
        Feature.AI_ASSISTANT: {
            "enabled": True,
            "limit": 500,
            "description": "AI assistant queries"
        },
        Feature.API_ACCESS: {
            "enabled": True,
            "rate_limit": 5000,
            "description": "API access (5k/day)"
        },
        Feature.TEAM_COLLABORATION: {
            "enabled": False,
            "description": "Upgrade to Premium for team collaboration"
        },
        Feature.ADVERSARIAL_SIMULATION: {
            "enabled": True,
            "counter_arguments": 8,
            "weakness_analysis": True,
            "priority_processing": False,
            "description": "8 counter-arguments with weakness analysis"
        },
    },

    # ===========================================================================
    # PREMIUM TIER - $199/month - 500 document credits
    # ===========================================================================
    FeatureTier.PREMIUM: {
        Feature.CASE_MONITORING: {
            "enabled": True,
            "limit": None,  # Unlimited
            "description": "Unlimited case monitoring"
        },
        Feature.CASE_CREATION: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited cases"
        },
        Feature.CASE_NOTES: {
            "enabled": True,
            "description": "Full case management"
        },
        Feature.DOCUMENT_VIEW: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited document viewing"
        },
        Feature.DOCUMENT_DOWNLOAD: {
            "enabled": True,
            "limit": 500,  # 500 document credits
            "description": "500 document downloads/month"
        },
        Feature.DOCUMENT_UPLOAD: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited document uploads"
        },
        Feature.DOCUMENT_EXPORT: {
            "enabled": True,
            "formats": ["pdf", "docx", "txt", "rtf"],
            "description": "Export to all formats"
        },
        Feature.DOCUMENT_COMPARISON: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited document comparisons"
        },
        Feature.DOCUMENT_BATCH_PROCESSING: {
            "enabled": True,
            "description": "Batch process documents"
        },
        Feature.COURTLISTENER_SEARCH: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited searches"
        },
        Feature.PACER_SEARCH: {
            "enabled": True,
            "description": "PACER searches"
        },
        Feature.PACER_DOWNLOAD: {
            "enabled": True,
            "description": "Download PACER documents"
        },
        Feature.LEGAL_RESEARCH: {
            "enabled": True,
            "description": "Full research suite"
        },
        Feature.CITATION_VALIDATION: {
            "enabled": True,
            "description": "Citation validation"
        },
        Feature.EMAIL_NOTIFICATIONS: {
            "enabled": True,
            "description": "Unlimited email notifications"
        },
        Feature.SMS_NOTIFICATIONS: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited SMS"
        },
        Feature.WEBHOOK_NOTIFICATIONS: {
            "enabled": True,
            "description": "Webhook notifications"
        },
        Feature.AI_ANALYSIS: {
            "enabled": True,
            "limit": 500,
            "description": "AI analysis (500/month)"
        },
        Feature.AI_SUMMARIZATION: {
            "enabled": True,
            "limit": 500,
            "description": "AI summaries (500/month)"
        },
        Feature.AI_CLAUSE_EXTRACTION: {
            "enabled": True,
            "description": "AI clause extraction"
        },
        Feature.AI_RISK_ASSESSMENT: {
            "enabled": True,
            "description": "AI risk assessment"
        },
        Feature.AI_ASSISTANT: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited AI assistant queries"
        },
        Feature.API_ACCESS: {
            "enabled": True,
            "rate_limit": 10000,
            "description": "API access (10k/day)"
        },
        Feature.TEAM_COLLABORATION: {
            "enabled": False,
            "description": "Upgrade to Enterprise for team collaboration"
        },
        Feature.AUDIT_LOGS: {
            "enabled": True,
            "retention_days": 180,
            "description": "Audit logs (6 months)"
        },
        Feature.ADVERSARIAL_SIMULATION: {
            "enabled": True,
            "counter_arguments": 15,
            "weakness_analysis": True,
            "priority_processing": True,
            "description": "15 counter-arguments with priority processing"
        },
    },

    # ===========================================================================
    # ENTERPRISE TIER - Custom pricing
    # ===========================================================================
    FeatureTier.ENTERPRISE: {
        Feature.CASE_MONITORING: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited case monitoring"
        },
        Feature.CASE_CREATION: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited cases"
        },
        Feature.CASE_NOTES: {
            "enabled": True,
            "description": "Full case management"
        },
        Feature.DOCUMENT_VIEW: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited document viewing"
        },
        Feature.DOCUMENT_DOWNLOAD: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited document downloads"
        },
        Feature.DOCUMENT_UPLOAD: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited document uploads"
        },
        Feature.DOCUMENT_EXPORT: {
            "enabled": True,
            "formats": ["pdf", "docx", "txt", "rtf"],
            "description": "Export to all formats"
        },
        Feature.DOCUMENT_COMPARISON: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited document comparisons"
        },
        Feature.DOCUMENT_BATCH_PROCESSING: {
            "enabled": True,
            "description": "Batch process documents"
        },
        Feature.COURTLISTENER_SEARCH: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited searches"
        },
        Feature.PACER_SEARCH: {
            "enabled": True,
            "description": "PACER searches"
        },
        Feature.PACER_DOWNLOAD: {
            "enabled": True,
            "description": "Download PACER documents"
        },
        Feature.LEGAL_RESEARCH: {
            "enabled": True,
            "description": "Full research suite"
        },
        Feature.CITATION_VALIDATION: {
            "enabled": True,
            "description": "Citation validation"
        },
        Feature.EMAIL_NOTIFICATIONS: {
            "enabled": True,
            "description": "Unlimited email notifications"
        },
        Feature.SMS_NOTIFICATIONS: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited SMS"
        },
        Feature.WEBHOOK_NOTIFICATIONS: {
            "enabled": True,
            "description": "Webhook notifications"
        },
        Feature.AI_ANALYSIS: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited AI analysis"
        },
        Feature.AI_SUMMARIZATION: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited AI summaries"
        },
        Feature.AI_CLAUSE_EXTRACTION: {
            "enabled": True,
            "description": "AI clause extraction"
        },
        Feature.AI_RISK_ASSESSMENT: {
            "enabled": True,
            "description": "AI risk assessment"
        },
        Feature.AI_ASSISTANT: {
            "enabled": True,
            "limit": None,
            "description": "Unlimited AI assistant queries"
        },
        Feature.TEAM_COLLABORATION: {
            "enabled": True,
            "max_users": None,  # Unlimited
            "description": "Unlimited team collaboration"
        },
        Feature.CLIENT_PORTAL: {
            "enabled": True,
            "description": "Client portal access"
        },
        Feature.MATTER_MANAGEMENT: {
            "enabled": True,
            "description": "Full matter management"
        },
        Feature.API_ACCESS: {
            "enabled": True,
            "rate_limit": None,  # Custom
            "description": "Custom API access"
        },
        Feature.WEBHOOK_INTEGRATION: {
            "enabled": True,
            "description": "Webhook integrations"
        },
        Feature.ZAPIER_INTEGRATION: {
            "enabled": True,
            "description": "Zapier integration"
        },
        Feature.AUDIT_LOGS: {
            "enabled": True,
            "retention_days": 365,
            "description": "Full audit logs (1 year)"
        },
        Feature.COMPLIANCE_REPORTS: {
            "enabled": True,
            "description": "Compliance reporting"
        },
        Feature.ADVERSARIAL_SIMULATION: {
            "enabled": True,
            "counter_arguments": 20,
            "weakness_analysis": True,
            "priority_processing": True,
            "description": "20 counter-arguments with full analysis"
        },
    },

    # ===========================================================================
    # ADMIN TIER - Full access to everything (for admin users)
    # ===========================================================================
    FeatureTier.ADMIN: {
        # Admins get unlimited access to everything
        Feature.CASE_MONITORING: {"enabled": True, "limit": None, "description": "Unlimited"},
        Feature.CASE_CREATION: {"enabled": True, "limit": None, "description": "Unlimited"},
        Feature.CASE_NOTES: {"enabled": True, "description": "Full access"},
        Feature.DOCUMENT_VIEW: {"enabled": True, "limit": None, "description": "Unlimited"},
        Feature.DOCUMENT_DOWNLOAD: {"enabled": True, "limit": None, "description": "Unlimited"},
        Feature.DOCUMENT_UPLOAD: {"enabled": True, "limit": None, "description": "Unlimited"},
        Feature.DOCUMENT_EXPORT: {"enabled": True, "formats": ["pdf", "docx", "txt", "rtf"], "description": "All formats"},
        Feature.DOCUMENT_COMPARISON: {"enabled": True, "limit": None, "description": "Unlimited"},
        Feature.DOCUMENT_BATCH_PROCESSING: {"enabled": True, "description": "Full access"},
        Feature.COURTLISTENER_SEARCH: {"enabled": True, "limit": None, "description": "Unlimited"},
        Feature.PACER_SEARCH: {"enabled": True, "description": "Full access"},
        Feature.PACER_DOWNLOAD: {"enabled": True, "description": "Full access"},
        Feature.LEGAL_RESEARCH: {"enabled": True, "description": "Full access"},
        Feature.CITATION_VALIDATION: {"enabled": True, "description": "Full access"},
        Feature.EMAIL_NOTIFICATIONS: {"enabled": True, "description": "Full access"},
        Feature.SMS_NOTIFICATIONS: {"enabled": True, "limit": None, "description": "Unlimited"},
        Feature.WEBHOOK_NOTIFICATIONS: {"enabled": True, "description": "Full access"},
        Feature.AI_ANALYSIS: {"enabled": True, "limit": None, "description": "Unlimited"},
        Feature.AI_SUMMARIZATION: {"enabled": True, "limit": None, "description": "Unlimited"},
        Feature.AI_CLAUSE_EXTRACTION: {"enabled": True, "description": "Full access"},
        Feature.AI_RISK_ASSESSMENT: {"enabled": True, "description": "Full access"},
        Feature.AI_ASSISTANT: {"enabled": True, "limit": None, "description": "Unlimited"},
        Feature.TEAM_COLLABORATION: {"enabled": True, "max_users": None, "description": "Unlimited"},
        Feature.CLIENT_PORTAL: {"enabled": True, "description": "Full access"},
        Feature.MATTER_MANAGEMENT: {"enabled": True, "description": "Full access"},
        Feature.API_ACCESS: {"enabled": True, "rate_limit": None, "description": "Unlimited"},
        Feature.WEBHOOK_INTEGRATION: {"enabled": True, "description": "Full access"},
        Feature.ZAPIER_INTEGRATION: {"enabled": True, "description": "Full access"},
        Feature.AUDIT_LOGS: {"enabled": True, "retention_days": 365, "description": "Full access"},
        Feature.COMPLIANCE_REPORTS: {"enabled": True, "description": "Full access"},
        Feature.ADVERSARIAL_SIMULATION: {
            "enabled": True,
            "counter_arguments": 50,
            "weakness_analysis": True,
            "priority_processing": True,
            "description": "Full adversarial simulation access"
        },
    },
}


# Map UserRole to FeatureTier (fallback when no subscription exists)
# Note: Subscription tier takes priority over role-based tier
ROLE_TO_TIER: Dict[UserRole, FeatureTier] = {
    UserRole.GUEST: FeatureTier.FREE,
    UserRole.USER: FeatureTier.FREE,      # New users start at FREE, subscription upgrades them
    UserRole.CLIENT: FeatureTier.FREE,    # Clients start at FREE
    UserRole.ATTORNEY: FeatureTier.FREE,  # Attorneys start at FREE (subscription determines features)
    UserRole.ADMIN: FeatureTier.ADMIN,    # Admins ALWAYS get full access regardless of subscription
}


def get_tier_for_role(role: UserRole) -> FeatureTier:
    """Get the feature tier for a user role"""
    return ROLE_TO_TIER.get(role, FeatureTier.FREE)


def get_feature_config(tier: FeatureTier, feature: Feature) -> Dict[str, Any]:
    """
    Get feature configuration for a specific tier

    Args:
        tier: The user's tier
        feature: The feature to check

    Returns:
        Feature configuration dict with enabled, limit, description, etc.
    """
    tier_config = TIER_FEATURES.get(tier, {})
    feature_config = tier_config.get(feature, {
        "enabled": False,
        "description": "Feature not available in this tier"
    })

    return feature_config


def has_feature_access(tier: FeatureTier, feature: Feature) -> bool:
    """
    Check if a tier has access to a feature

    Args:
        tier: The user's tier
        feature: The feature to check

    Returns:
        True if feature is enabled for this tier
    """
    config = get_feature_config(tier, feature)
    return config.get("enabled", False)


def get_feature_limit(tier: FeatureTier, feature: Feature) -> Optional[int]:
    """
    Get the usage limit for a feature in a tier

    Args:
        tier: The user's tier
        feature: The feature to check

    Returns:
        Usage limit (None means unlimited, 0 means disabled)
    """
    config = get_feature_config(tier, feature)
    return config.get("limit")


def get_upgrade_message(feature: Feature, current_tier: FeatureTier) -> Dict[str, Any]:
    """
    Get upgrade messaging for a locked feature

    Args:
        feature: The locked feature
        current_tier: User's current tier

    Returns:
        Dict with upgrade message and target tier
    """
    # Tier names and prices aligned with Stripe subscription tiers
    tier_names = {
        FeatureTier.FREE: "Free",
        FeatureTier.BASIC: "Basic",
        FeatureTier.INDIVIDUAL_PRO: "Individual Pro",
        FeatureTier.PROFESSIONAL: "Professional",
        FeatureTier.PREMIUM: "Premium",
        FeatureTier.ENTERPRISE: "Enterprise",
        FeatureTier.ADMIN: "Admin"
    }

    tier_prices = {
        FeatureTier.FREE: "$0",
        FeatureTier.BASIC: "$9.99/month",
        FeatureTier.INDIVIDUAL_PRO: "$29.99/month",
        FeatureTier.PROFESSIONAL: "$99/month",
        FeatureTier.PREMIUM: "$199/month",
        FeatureTier.ENTERPRISE: "Custom pricing"
    }

    # Find the lowest tier that has this feature
    tier_order = [
        FeatureTier.BASIC,
        FeatureTier.INDIVIDUAL_PRO,
        FeatureTier.PROFESSIONAL,
        FeatureTier.PREMIUM,
        FeatureTier.ENTERPRISE
    ]

    for tier in tier_order:
        if has_feature_access(tier, feature):
            config = get_feature_config(tier, feature)

            return {
                "feature": feature.value,
                "description": config.get("description", ""),
                "target_tier": tier.value,
                "tier_name": tier_names.get(tier, tier.value),
                "price": tier_prices.get(tier, ""),
                "message": f"Upgrade to {tier_names.get(tier, tier.value)} to unlock this feature",
                "cta": f"Upgrade to {tier_names.get(tier, tier.value)}",
                "upgrade_url": f"/settings?tab=subscription&upgrade={tier.value}"
            }

    return {
        "feature": feature.value,
        "message": "This feature is not available",
        "target_tier": None
    }
