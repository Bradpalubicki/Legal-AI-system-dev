"""
Legal AI System - Pricing Configuration

Centralized pricing configuration for:
- Document downloads ($0.25/page base)
- Subscription tiers (Free, Basic, Individual Pro, Professional, Premium, Enterprise)
- Credit packs (pay-as-you-go)

Margin targets:
- Document downloads: 56% gross margin against ~$0.11/page blended cost
- Subscription tiers: 72-78% margin when users consume full allocation
"""

from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


# =============================================================================
# DOCUMENT PRICING
# =============================================================================

# Base price per page for document downloads
DOCUMENT_PRICE_PER_PAGE = Decimal("0.25")

# Our blended cost per page (PACER fees, CourtListener, AI processing, infrastructure)
DOCUMENT_COST_PER_PAGE = Decimal("0.11")

# Gross margin: 56%
DOCUMENT_GROSS_MARGIN = Decimal("0.56")


# =============================================================================
# SUBSCRIPTION TIERS
# =============================================================================

class SubscriptionTier(str, Enum):
    """Available subscription tiers"""
    FREE = "free"
    BASIC = "basic"
    INDIVIDUAL_PRO = "individual_pro"
    PROFESSIONAL = "professional"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class TierConfig:
    """Configuration for a subscription tier"""
    tier: SubscriptionTier
    name: str
    description: str
    price_monthly: Decimal
    price_annual: Decimal
    included_credits: int
    features: Dict[str, any]
    stripe_price_id_monthly: Optional[str] = None
    stripe_price_id_annual: Optional[str] = None
    stripe_product_id: Optional[str] = None
    is_active: bool = True
    trial_days: int = 0

    @property
    def annual_savings(self) -> Decimal:
        """Calculate annual savings vs monthly"""
        monthly_annual = self.price_monthly * 12
        return monthly_annual - self.price_annual

    @property
    def effective_monthly_annual(self) -> Decimal:
        """Effective monthly price when paying annually"""
        if self.price_annual == 0:
            return Decimal("0")
        return (self.price_annual / 12).quantize(Decimal("0.01"))

    @property
    def credit_value(self) -> Decimal:
        """Value of included credits at base price"""
        return Decimal(str(self.included_credits)) * DOCUMENT_PRICE_PER_PAGE


# Subscription tier configurations
SUBSCRIPTION_TIERS: Dict[SubscriptionTier, TierConfig] = {
    SubscriptionTier.FREE: TierConfig(
        tier=SubscriptionTier.FREE,
        name="Free",
        description="Get started with basic access",
        price_monthly=Decimal("0.00"),
        price_annual=Decimal("0.00"),
        included_credits=0,
        trial_days=0,
        features={
            "case_search": True,
            "case_monitoring": 1,  # 1 case
            "document_preview": True,
            "email_notifications": False,
            "api_access": False,
            "priority_support": False,
            "bulk_downloads": False,
            "ai_analysis": False,
            "export_reports": False,
        }
    ),
    SubscriptionTier.BASIC: TierConfig(
        tier=SubscriptionTier.BASIC,
        name="Basic",
        description="Essential features for individual users",
        price_monthly=Decimal("9.99"),
        price_annual=Decimal("99.99"),
        included_credits=20,
        trial_days=14,
        stripe_product_id="prod_Tc00UnymQStX6u",
        stripe_price_id_monthly="price_1Sem0xEmfeh92oXxjA4j9iKB",
        stripe_price_id_annual="price_1Sem0xEmfeh92oXx9nxFXdqY",
        features={
            "case_search": True,
            "case_monitoring": 5,  # 5 cases
            "document_preview": True,
            "email_notifications": True,
            "api_access": False,
            "priority_support": False,
            "bulk_downloads": False,
            "ai_analysis": "basic",  # Basic AI summaries
            "export_reports": False,
        }
    ),
    SubscriptionTier.INDIVIDUAL_PRO: TierConfig(
        tier=SubscriptionTier.INDIVIDUAL_PRO,
        name="Individual Pro",
        description="Advanced features for power users",
        price_monthly=Decimal("29.99"),
        price_annual=Decimal("299.99"),
        included_credits=75,
        trial_days=14,
        stripe_product_id="prod_Tc00RpaoI6tDez",
        stripe_price_id_monthly="price_1Sem0yEmfeh92oXxdcw8kEBu",
        stripe_price_id_annual="price_1Sem0yEmfeh92oXxD9mK0aNX",
        features={
            "case_search": True,
            "case_monitoring": 25,  # 25 cases
            "document_preview": True,
            "email_notifications": True,
            "api_access": True,
            "priority_support": False,
            "bulk_downloads": True,
            "ai_analysis": "advanced",  # Full AI analysis
            "export_reports": True,
        }
    ),
    SubscriptionTier.PROFESSIONAL: TierConfig(
        tier=SubscriptionTier.PROFESSIONAL,
        name="Professional",
        description="Complete toolkit for legal professionals",
        price_monthly=Decimal("99.00"),
        price_annual=Decimal("999.00"),
        included_credits=200,
        trial_days=14,
        stripe_product_id="prod_Tc018aSfmtoOxT",
        stripe_price_id_monthly="price_1Sem0yEmfeh92oXxPGycCkFm",
        stripe_price_id_annual="price_1Sem0yEmfeh92oXxi4MlSUe5",
        features={
            "case_search": True,
            "case_monitoring": 100,  # 100 cases
            "document_preview": True,
            "email_notifications": True,
            "api_access": True,
            "priority_support": True,
            "bulk_downloads": True,
            "ai_analysis": "advanced",
            "export_reports": True,
            "team_sharing": False,
        }
    ),
    SubscriptionTier.PREMIUM: TierConfig(
        tier=SubscriptionTier.PREMIUM,
        name="Premium",
        description="Maximum power for high-volume users",
        price_monthly=Decimal("199.00"),
        price_annual=Decimal("1999.00"),
        included_credits=500,
        trial_days=14,
        stripe_product_id="prod_Tc01uKrGHvQLYg",
        stripe_price_id_monthly="price_1Sem0zEmfeh92oXxj1vQgJzu",
        stripe_price_id_annual="price_1Sem0zEmfeh92oXxcel6xdEx",
        features={
            "case_search": True,
            "case_monitoring": "unlimited",
            "document_preview": True,
            "email_notifications": True,
            "api_access": True,
            "priority_support": True,
            "bulk_downloads": True,
            "ai_analysis": "advanced",
            "export_reports": True,
            "team_sharing": False,  # Coming soon
            "custom_integrations": True,
        }
    ),
    SubscriptionTier.ENTERPRISE: TierConfig(
        tier=SubscriptionTier.ENTERPRISE,
        name="Enterprise",
        description="Custom solutions for organizations",
        price_monthly=Decimal("0.00"),  # Custom pricing
        price_annual=Decimal("0.00"),  # Custom pricing
        included_credits=0,  # Custom
        trial_days=30,
        features={
            "case_search": True,
            "case_monitoring": "unlimited",
            "document_preview": True,
            "email_notifications": True,
            "api_access": True,
            "priority_support": True,
            "bulk_downloads": True,
            "ai_analysis": "advanced",
            "export_reports": True,
            "team_sharing": False,  # Coming soon
            "custom_integrations": True,
            "dedicated_support": True,
            "sla_guarantee": True,
            "custom_branding": True,
            "sso_integration": True,
        }
    ),
}


# =============================================================================
# CREDIT PACKS (Pay-As-You-Go)
# =============================================================================

class CreditPackType(str, Enum):
    """Available credit pack types"""
    SINGLE_PAGE = "single_page"
    STARTER = "starter"
    STANDARD = "standard"
    VALUE = "value"
    PRO = "pro"
    POWER = "power"


@dataclass
class CreditPackConfig:
    """Configuration for a credit pack"""
    pack_type: CreditPackType
    name: str
    credits: int
    price: Decimal
    stripe_price_id: Optional[str] = None
    is_active: bool = True

    @property
    def price_per_credit(self) -> Decimal:
        """Price per credit in this pack"""
        return (self.price / self.credits).quantize(Decimal("0.01"))

    @property
    def savings_vs_single(self) -> Decimal:
        """Savings percentage vs single page price"""
        single_price = CREDIT_PACKS[CreditPackType.SINGLE_PAGE].price_per_credit
        if single_price == 0:
            return Decimal("0")
        return ((single_price - self.price_per_credit) / single_price * 100).quantize(Decimal("0.1"))


# Credit pack configurations
CREDIT_PACKS: Dict[CreditPackType, CreditPackConfig] = {
    CreditPackType.SINGLE_PAGE: CreditPackConfig(
        pack_type=CreditPackType.SINGLE_PAGE,
        name="Single Page",
        credits=1,
        price=Decimal("0.35"),
        stripe_price_id="price_1Sem24Emfeh92oXxf651FnM8",
    ),
    CreditPackType.STARTER: CreditPackConfig(
        pack_type=CreditPackType.STARTER,
        name="Starter Pack",
        credits=25,
        price=Decimal("6.25"),
        stripe_price_id="price_1Sem24Emfeh92oXxICNLuWBZ",
    ),
    CreditPackType.STANDARD: CreditPackConfig(
        pack_type=CreditPackType.STANDARD,
        name="Standard Pack",
        credits=50,
        price=Decimal("11.00"),
        stripe_price_id="price_1Sem25Emfeh92oXxgqkJHIfC",
    ),
    CreditPackType.VALUE: CreditPackConfig(
        pack_type=CreditPackType.VALUE,
        name="Value Pack",
        credits=100,
        price=Decimal("20.00"),
        stripe_price_id="price_1Sem25Emfeh92oXx8N6Pd7Cr",
    ),
    CreditPackType.PRO: CreditPackConfig(
        pack_type=CreditPackType.PRO,
        name="Pro Pack",
        credits=250,
        price=Decimal("45.00"),
        stripe_price_id="price_1Sem25Emfeh92oXxAK9Ge14m",
    ),
    CreditPackType.POWER: CreditPackConfig(
        pack_type=CreditPackType.POWER,
        name="Power Pack",
        credits=500,
        price=Decimal("80.00"),
        stripe_price_id="price_1Sem26Emfeh92oXxbLLxZPj5",
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_tier_config(tier: SubscriptionTier) -> TierConfig:
    """Get configuration for a subscription tier"""
    return SUBSCRIPTION_TIERS.get(tier)


def get_credit_pack_config(pack_type: CreditPackType) -> CreditPackConfig:
    """Get configuration for a credit pack"""
    return CREDIT_PACKS.get(pack_type)


def calculate_document_cost(page_count: int, credits_available: int = 0) -> Dict:
    """
    Calculate the cost to download a document.

    Args:
        page_count: Number of pages in the document
        credits_available: User's available credits

    Returns:
        Dict with cost breakdown
    """
    total_credits_needed = page_count  # 1 credit = 1 page
    total_price = Decimal(str(page_count)) * DOCUMENT_PRICE_PER_PAGE

    credits_to_use = min(credits_available, total_credits_needed)
    credits_remaining = total_credits_needed - credits_to_use
    cash_needed = Decimal(str(credits_remaining)) * DOCUMENT_PRICE_PER_PAGE

    return {
        "page_count": page_count,
        "total_credits_needed": total_credits_needed,
        "price_per_page": float(DOCUMENT_PRICE_PER_PAGE),
        "total_price": float(total_price),
        "credits_available": credits_available,
        "credits_to_use": credits_to_use,
        "credits_remaining_needed": credits_remaining,
        "cash_needed": float(cash_needed),
        "is_free": page_count == 0,
    }


def get_best_credit_pack(credits_needed: int) -> Optional[CreditPackConfig]:
    """
    Get the best credit pack for a given number of credits needed.

    Returns the pack that provides the best value (lowest per-credit price)
    while meeting the credit requirement.
    """
    suitable_packs = [
        pack for pack in CREDIT_PACKS.values()
        if pack.credits >= credits_needed and pack.is_active
    ]

    if not suitable_packs:
        # No single pack covers the need, return largest
        return CREDIT_PACKS[CreditPackType.POWER]

    # Sort by price per credit (ascending)
    return min(suitable_packs, key=lambda p: p.price_per_credit)


def get_all_tiers_comparison() -> List[Dict]:
    """Get all tiers in a comparison-friendly format"""
    tiers = []
    for tier in SubscriptionTier:
        config = SUBSCRIPTION_TIERS[tier]
        tiers.append({
            "tier": tier.value,
            "name": config.name,
            "description": config.description,
            "price_monthly": float(config.price_monthly),
            "price_annual": float(config.price_annual),
            "effective_monthly_annual": float(config.effective_monthly_annual),
            "annual_savings": float(config.annual_savings),
            "included_credits": config.included_credits,
            "credit_value": float(config.credit_value),
            "features": config.features,
            "trial_days": config.trial_days,
            "is_enterprise": tier == SubscriptionTier.ENTERPRISE,
        })
    return tiers


def get_all_credit_packs() -> List[Dict]:
    """Get all credit packs in a purchase-friendly format"""
    packs = []
    for pack_type in CreditPackType:
        config = CREDIT_PACKS[pack_type]
        packs.append({
            "pack_type": pack_type.value,
            "name": config.name,
            "credits": config.credits,
            "price": float(config.price),
            "price_per_credit": float(config.price_per_credit),
            "savings_percent": float(config.savings_vs_single) if pack_type != CreditPackType.SINGLE_PAGE else 0,
            "is_active": config.is_active,
        })
    return packs
