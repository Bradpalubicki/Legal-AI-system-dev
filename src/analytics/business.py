"""
Business Analytics System
Tracks revenue metrics, growth analytics, business performance, and financial insights.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import asyncio
from decimal import Decimal
import json


class RevenueType(str, Enum):
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage_based"
    PROFESSIONAL_SERVICES = "professional_services"
    LICENSING = "licensing"
    MARKETPLACE = "marketplace"


class GrowthMetric(str, Enum):
    MRR = "monthly_recurring_revenue"
    ARR = "annual_recurring_revenue"
    USER_ACQUISITION = "user_acquisition"
    CHURN_RATE = "churn_rate"
    LTV = "lifetime_value"
    CAC = "customer_acquisition_cost"
    EXPANSION_REVENUE = "expansion_revenue"


class BusinessSegment(str, Enum):
    SMALL_FIRM = "small_firm"
    MEDIUM_FIRM = "medium_firm"
    LARGE_FIRM = "large_firm"
    ENTERPRISE = "enterprise"
    SOLO_PRACTITIONER = "solo_practitioner"


class PricingTier(str, Enum):
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class PlanType(str, Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"
    USAGE_BASED = "usage_based"
    CUSTOM = "custom"


@dataclass
class RevenueMetrics:
    firm_id: str
    monthly_recurring_revenue: Decimal
    annual_recurring_revenue: Decimal
    one_time_revenue: Decimal
    usage_based_revenue: Decimal
    total_revenue: Decimal
    revenue_growth_rate: float
    revenue_by_segment: Dict[str, Decimal]
    revenue_by_tier: Dict[str, Decimal]
    billing_period: str
    payment_method_distribution: Dict[str, float]
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class GrowthAnalytics:
    period_start: datetime
    period_end: datetime
    new_customers: int
    churned_customers: int
    net_customer_growth: int
    churn_rate: float
    retention_rate: float
    expansion_rate: float
    contraction_rate: float
    customer_lifetime_value: Decimal
    customer_acquisition_cost: Decimal
    payback_period_months: float
    growth_rate_percentage: float
    market_penetration: float
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class CustomerSegmentAnalysis:
    segment: BusinessSegment
    customer_count: int
    total_revenue: Decimal
    average_revenue_per_user: Decimal
    churn_rate: float
    satisfaction_score: float
    usage_intensity: float
    expansion_potential: float
    preferred_pricing_tier: PricingTier
    avg_contract_value: Decimal
    support_ticket_ratio: float
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class ProfitabilityAnalysis:
    firm_id: str
    total_revenue: Decimal
    cost_of_goods_sold: Decimal
    gross_profit: Decimal
    gross_margin: float
    operating_expenses: Decimal
    operating_profit: Decimal
    operating_margin: float
    net_profit: Decimal
    net_margin: float
    break_even_point: Decimal
    contribution_margin: float
    roi_percentage: float
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class MarketAnalysis:
    total_addressable_market: Decimal
    serviceable_addressable_market: Decimal
    serviceable_obtainable_market: Decimal
    market_share: float
    competitive_position: str
    growth_opportunity_score: float
    market_trends: List[str]
    competitor_analysis: Dict[str, Any]
    pricing_benchmarks: Dict[str, Decimal]
    demand_forecast: Dict[str, Any]
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class SalesMetrics:
    total_deals: int
    won_deals: int
    lost_deals: int
    pipeline_value: Decimal
    average_deal_size: Decimal
    sales_cycle_days: float
    win_rate: float
    quota_attainment: float
    lead_conversion_rate: float
    sales_velocity: float
    upsell_rate: float
    cross_sell_rate: float
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class BusinessAnalyticsReport:
    report_period_start: datetime
    report_period_end: datetime
    revenue_metrics: RevenueMetrics
    growth_analytics: GrowthAnalytics
    customer_segments: List[CustomerSegmentAnalysis]
    profitability: ProfitabilityAnalysis
    market_analysis: MarketAnalysis
    sales_metrics: SalesMetrics
    key_insights: List[str]
    strategic_recommendations: List[str]
    risk_factors: List[str]
    opportunities: List[str]
    executive_summary: str
    generated_at: datetime = None

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.utcnow()


class BusinessAnalyticsEngine:
    def __init__(self):
        self.revenue_data = {}
        self.customer_data = {}
        self.sales_data = {}
        self.market_data = {}

    async def track_revenue(self, firm_id: str, amount: Decimal, revenue_type: RevenueType,
                          billing_period: str = "monthly", tier: PricingTier = PricingTier.PROFESSIONAL) -> bool:
        """Track revenue data for a firm"""
        try:
            if firm_id not in self.revenue_data:
                self.revenue_data[firm_id] = {
                    'total_revenue': Decimal('0'),
                    'monthly_revenue': Decimal('0'),
                    'annual_revenue': Decimal('0'),
                    'usage_revenue': Decimal('0'),
                    'one_time_revenue': Decimal('0'),
                    'revenue_by_type': {},
                    'revenue_by_tier': {},
                    'billing_periods': [],
                    'payment_methods': {}
                }

            firm_revenue = self.revenue_data[firm_id]
            firm_revenue['total_revenue'] += amount

            # Track by revenue type
            if revenue_type == RevenueType.SUBSCRIPTION:
                if billing_period == "monthly":
                    firm_revenue['monthly_revenue'] += amount
                    firm_revenue['annual_revenue'] += amount * 12
                elif billing_period == "annual":
                    firm_revenue['annual_revenue'] += amount
                    firm_revenue['monthly_revenue'] += amount / 12
            elif revenue_type == RevenueType.USAGE_BASED:
                firm_revenue['usage_revenue'] += amount
            else:
                firm_revenue['one_time_revenue'] += amount

            # Track by tier
            if tier.value not in firm_revenue['revenue_by_tier']:
                firm_revenue['revenue_by_tier'][tier.value] = Decimal('0')
            firm_revenue['revenue_by_tier'][tier.value] += amount

            # Track by type
            if revenue_type.value not in firm_revenue['revenue_by_type']:
                firm_revenue['revenue_by_type'][revenue_type.value] = Decimal('0')
            firm_revenue['revenue_by_type'][revenue_type.value] += amount

            firm_revenue['billing_periods'].append({
                'amount': amount,
                'type': revenue_type.value,
                'tier': tier.value,
                'period': billing_period,
                'date': datetime.utcnow()
            })

            return True

        except Exception as e:
            print(f"Error tracking revenue: {e}")
            return False

    async def track_customer_lifecycle(self, firm_id: str, event_type: str,
                                     value: Optional[Decimal] = None, segment: BusinessSegment = BusinessSegment.SMALL_FIRM) -> bool:
        """Track customer lifecycle events"""
        try:
            if firm_id not in self.customer_data:
                self.customer_data[firm_id] = {
                    'acquisition_date': datetime.utcnow(),
                    'segment': segment,
                    'lifecycle_events': [],
                    'total_value': Decimal('0'),
                    'is_active': True,
                    'satisfaction_score': 8.5,
                    'support_tickets': 0
                }

            customer = self.customer_data[firm_id]
            customer['lifecycle_events'].append({
                'event': event_type,
                'value': value,
                'date': datetime.utcnow()
            })

            if value:
                customer['total_value'] += value

            if event_type == "churn":
                customer['is_active'] = False
            elif event_type == "reactivation":
                customer['is_active'] = True
            elif event_type == "support_ticket":
                customer['support_tickets'] += 1

            return True

        except Exception as e:
            print(f"Error tracking customer lifecycle: {e}")
            return False

    async def calculate_revenue_metrics(self, firm_id: Optional[str] = None) -> Optional[RevenueMetrics]:
        """Calculate comprehensive revenue metrics"""
        try:
            if firm_id and firm_id in self.revenue_data:
                firm_revenue = self.revenue_data[firm_id]
            else:
                # Aggregate all firms
                firm_revenue = {
                    'total_revenue': Decimal('0'),
                    'monthly_revenue': Decimal('0'),
                    'annual_revenue': Decimal('0'),
                    'usage_revenue': Decimal('0'),
                    'one_time_revenue': Decimal('0'),
                    'revenue_by_type': {},
                    'revenue_by_tier': {}
                }

                for fid, data in self.revenue_data.items():
                    firm_revenue['total_revenue'] += data['total_revenue']
                    firm_revenue['monthly_revenue'] += data['monthly_revenue']
                    firm_revenue['annual_revenue'] += data['annual_revenue']
                    firm_revenue['usage_revenue'] += data['usage_revenue']
                    firm_revenue['one_time_revenue'] += data['one_time_revenue']

                    for rtype, amount in data['revenue_by_type'].items():
                        if rtype not in firm_revenue['revenue_by_type']:
                            firm_revenue['revenue_by_type'][rtype] = Decimal('0')
                        firm_revenue['revenue_by_type'][rtype] += amount

                    for tier, amount in data['revenue_by_tier'].items():
                        if tier not in firm_revenue['revenue_by_tier']:
                            firm_revenue['revenue_by_tier'][tier] = Decimal('0')
                        firm_revenue['revenue_by_tier'][tier] += amount

            # Calculate growth rate (placeholder)
            growth_rate = 15.7  # 15.7% month-over-month growth

            # Sample payment method distribution
            payment_methods = {
                "credit_card": 65.0,
                "bank_transfer": 25.0,
                "check": 8.0,
                "other": 2.0
            }

            return RevenueMetrics(
                firm_id=firm_id or "aggregate",
                monthly_recurring_revenue=firm_revenue['monthly_revenue'],
                annual_recurring_revenue=firm_revenue['annual_revenue'],
                one_time_revenue=firm_revenue['one_time_revenue'],
                usage_based_revenue=firm_revenue['usage_revenue'],
                total_revenue=firm_revenue['total_revenue'],
                revenue_growth_rate=growth_rate,
                revenue_by_segment=firm_revenue['revenue_by_type'],
                revenue_by_tier=firm_revenue['revenue_by_tier'],
                billing_period="monthly",
                payment_method_distribution=payment_methods
            )

        except Exception as e:
            print(f"Error calculating revenue metrics: {e}")
            return None

    async def calculate_growth_analytics(self, period_days: int = 30) -> Optional[GrowthAnalytics]:
        """Calculate growth analytics for specified period"""
        try:
            period_end = datetime.utcnow()
            period_start = period_end - timedelta(days=period_days)

            # Calculate metrics from customer data
            new_customers = 0
            churned_customers = 0
            total_customers = len(self.customer_data)

            for firm_id, customer in self.customer_data.items():
                # Check if acquired in period
                if customer['acquisition_date'] >= period_start:
                    new_customers += 1

                # Check for churn events in period
                for event in customer['lifecycle_events']:
                    if event['event'] == 'churn' and event['date'] >= period_start:
                        churned_customers += 1

            net_growth = new_customers - churned_customers
            churn_rate = (churned_customers / max(total_customers, 1)) * 100
            retention_rate = 100 - churn_rate

            # Calculate LTV and CAC (sample calculations)
            avg_monthly_revenue = Decimal('2500')
            avg_customer_lifespan_months = 24
            ltv = avg_monthly_revenue * avg_customer_lifespan_months

            cac = Decimal('850')  # Average customer acquisition cost
            payback_months = float(cac / avg_monthly_revenue) if avg_monthly_revenue > 0 else 0

            return GrowthAnalytics(
                period_start=period_start,
                period_end=period_end,
                new_customers=new_customers,
                churned_customers=churned_customers,
                net_customer_growth=net_growth,
                churn_rate=churn_rate,
                retention_rate=retention_rate,
                expansion_rate=12.4,  # 12.4% expansion revenue
                contraction_rate=3.2,   # 3.2% contraction
                customer_lifetime_value=ltv,
                customer_acquisition_cost=cac,
                payback_period_months=payback_months,
                growth_rate_percentage=18.7,
                market_penetration=2.3
            )

        except Exception as e:
            print(f"Error calculating growth analytics: {e}")
            return None

    async def analyze_customer_segments(self) -> List[CustomerSegmentAnalysis]:
        """Analyze customer segments and their performance"""
        try:
            segments = {}

            for firm_id, customer in self.customer_data.items():
                segment = customer['segment']
                if segment not in segments:
                    segments[segment] = {
                        'customers': [],
                        'total_revenue': Decimal('0'),
                        'total_satisfaction': 0,
                        'total_support_tickets': 0
                    }

                segments[segment]['customers'].append(customer)
                segments[segment]['total_revenue'] += customer['total_value']
                segments[segment]['total_satisfaction'] += customer['satisfaction_score']
                segments[segment]['total_support_tickets'] += customer['support_tickets']

            analyses = []
            for segment, data in segments.items():
                customer_count = len(data['customers'])
                if customer_count > 0:
                    arpu = data['total_revenue'] / customer_count
                    avg_satisfaction = data['total_satisfaction'] / customer_count
                    support_ratio = data['total_support_tickets'] / customer_count

                    # Calculate churn rate for segment
                    churned = sum(1 for c in data['customers'] if not c['is_active'])
                    segment_churn_rate = (churned / customer_count) * 100

                    analyses.append(CustomerSegmentAnalysis(
                        segment=BusinessSegment(segment),
                        customer_count=customer_count,
                        total_revenue=data['total_revenue'],
                        average_revenue_per_user=arpu,
                        churn_rate=segment_churn_rate,
                        satisfaction_score=avg_satisfaction,
                        usage_intensity=7.8,  # Placeholder
                        expansion_potential=8.2,  # Placeholder
                        preferred_pricing_tier=PricingTier.PROFESSIONAL,
                        avg_contract_value=arpu * 12,
                        support_ticket_ratio=support_ratio
                    ))

            return analyses

        except Exception as e:
            print(f"Error analyzing customer segments: {e}")
            return []

    async def calculate_profitability(self, firm_id: Optional[str] = None) -> Optional[ProfitabilityAnalysis]:
        """Calculate profitability analysis"""
        try:
            revenue_metrics = await self.calculate_revenue_metrics(firm_id)
            if not revenue_metrics:
                return None

            total_revenue = revenue_metrics.total_revenue

            # Sample cost calculations (in real implementation, these would be tracked)
            cogs = total_revenue * Decimal('0.25')  # 25% COGS
            gross_profit = total_revenue - cogs
            gross_margin = float(gross_profit / total_revenue * 100) if total_revenue > 0 else 0

            operating_expenses = total_revenue * Decimal('0.45')  # 45% OpEx
            operating_profit = gross_profit - operating_expenses
            operating_margin = float(operating_profit / total_revenue * 100) if total_revenue > 0 else 0

            net_profit = operating_profit * Decimal('0.85')  # After taxes/interest
            net_margin = float(net_profit / total_revenue * 100) if total_revenue > 0 else 0

            break_even = operating_expenses / Decimal('0.75')  # Break-even revenue
            contribution_margin = float(gross_margin)
            roi = float(net_profit / (total_revenue * Decimal('0.6')) * 100)  # ROI on invested capital

            return ProfitabilityAnalysis(
                firm_id=firm_id or "aggregate",
                total_revenue=total_revenue,
                cost_of_goods_sold=cogs,
                gross_profit=gross_profit,
                gross_margin=gross_margin,
                operating_expenses=operating_expenses,
                operating_profit=operating_profit,
                operating_margin=operating_margin,
                net_profit=net_profit,
                net_margin=net_margin,
                break_even_point=break_even,
                contribution_margin=contribution_margin,
                roi_percentage=roi
            )

        except Exception as e:
            print(f"Error calculating profitability: {e}")
            return None

    async def generate_market_analysis(self) -> Optional[MarketAnalysis]:
        """Generate market analysis and competitive positioning"""
        try:
            # Sample market analysis data
            return MarketAnalysis(
                total_addressable_market=Decimal('45000000000'),  # $45B legal tech market
                serviceable_addressable_market=Decimal('8500000000'),  # $8.5B AI legal tools
                serviceable_obtainable_market=Decimal('425000000'),  # $425M realistic market
                market_share=2.3,  # 2.3% market share
                competitive_position="Strong contender in AI-powered legal analysis",
                growth_opportunity_score=8.7,
                market_trends=[
                    "Increasing adoption of AI in legal workflows",
                    "Growing demand for document automation",
                    "Expansion into mid-market law firms",
                    "Integration with existing legal software",
                    "Focus on compliance and security"
                ],
                competitor_analysis={
                    "primary_competitors": ["LegalZoom", "Clio", "Thomson Reuters"],
                    "competitive_advantages": ["Advanced AI capabilities", "Comprehensive analytics", "White-label options"],
                    "market_positioning": "Premium AI-first legal technology platform"
                },
                pricing_benchmarks={
                    "basic_tier": Decimal('99'),
                    "professional_tier": Decimal('299'),
                    "enterprise_tier": Decimal('599'),
                    "market_average": Decimal('350')
                },
                demand_forecast={
                    "next_quarter": "25% growth expected",
                    "next_year": "180% growth projected",
                    "key_drivers": ["AI adoption", "Remote work trends", "Efficiency demands"]
                }
            )

        except Exception as e:
            print(f"Error generating market analysis: {e}")
            return None

    async def calculate_sales_metrics(self) -> Optional[SalesMetrics]:
        """Calculate sales performance metrics"""
        try:
            # Sample sales metrics calculation
            total_deals = 45
            won_deals = 28
            lost_deals = 12
            pipeline_deals = total_deals - won_deals - lost_deals

            pipeline_value = Decimal('125000')
            avg_deal_size = pipeline_value / max(total_deals, 1)
            win_rate = (won_deals / max(total_deals - pipeline_deals, 1)) * 100
            sales_cycle = 35.5  # Average days to close

            return SalesMetrics(
                total_deals=total_deals,
                won_deals=won_deals,
                lost_deals=lost_deals,
                pipeline_value=pipeline_value,
                average_deal_size=avg_deal_size,
                sales_cycle_days=sales_cycle,
                win_rate=win_rate,
                quota_attainment=112.4,  # 112.4% of quota
                lead_conversion_rate=18.7,  # 18.7% conversion
                sales_velocity=2.8,  # Deals per day
                upsell_rate=23.5,  # 23.5% upsell rate
                cross_sell_rate=15.2   # 15.2% cross-sell rate
            )

        except Exception as e:
            print(f"Error calculating sales metrics: {e}")
            return None

    async def generate_business_report(self, period_days: int = 30) -> Optional[BusinessAnalyticsReport]:
        """Generate comprehensive business analytics report"""
        try:
            period_end = datetime.utcnow()
            period_start = period_end - timedelta(days=period_days)

            # Get all analytics components
            revenue_metrics = await self.calculate_revenue_metrics()
            growth_analytics = await self.calculate_growth_analytics(period_days)
            customer_segments = await self.analyze_customer_segments()
            profitability = await self.calculate_profitability()
            market_analysis = await self.generate_market_analysis()
            sales_metrics = await self.calculate_sales_metrics()

            if not all([revenue_metrics, growth_analytics, profitability, market_analysis, sales_metrics]):
                return None

            # Generate insights
            key_insights = [
                f"Monthly recurring revenue of ${revenue_metrics.monthly_recurring_revenue:,.2f} with {revenue_metrics.revenue_growth_rate}% growth",
                f"Customer retention rate of {growth_analytics.retention_rate:.1f}% indicates strong product-market fit",
                f"Average customer lifetime value of ${growth_analytics.customer_lifetime_value:,.2f} vs acquisition cost of ${growth_analytics.customer_acquisition_cost:,.2f}",
                f"Gross margin of {profitability.gross_margin:.1f}% demonstrates healthy unit economics",
                f"Market opportunity of ${market_analysis.serviceable_obtainable_market:,.0f} with current {market_analysis.market_share}% share"
            ]

            # Generate recommendations
            strategic_recommendations = [
                "Focus on reducing customer acquisition cost through improved conversion funnels",
                "Expand into enterprise segment to increase average contract value",
                "Develop strategic partnerships to accelerate market penetration",
                "Invest in product features that drive expansion revenue from existing customers",
                "Optimize pricing strategy based on competitive benchmarking analysis"
            ]

            # Identify risks
            risk_factors = [
                "Competitive pressure from established legal software providers",
                "Potential economic downturn affecting legal industry spending",
                "Regulatory changes impacting AI usage in legal practice",
                "Customer concentration risk in specific legal practice areas"
            ]

            # Identify opportunities
            opportunities = [
                "International expansion into European and APAC markets",
                "Development of specialized solutions for niche legal practices",
                "Integration marketplace for third-party legal tools",
                "White-label partnerships with established legal service providers"
            ]

            # Executive summary
            executive_summary = f"""
            Business performance for the {period_days}-day period shows strong growth momentum with ${revenue_metrics.total_revenue:,.2f} in total revenue
            and {growth_analytics.net_customer_growth} net new customers. The business demonstrates healthy unit economics with a
            {profitability.gross_margin:.1f}% gross margin and {growth_analytics.retention_rate:.1f}% customer retention rate.
            Key growth drivers include expanding market adoption of AI legal tools and successful penetration into the mid-market segment.
            """

            return BusinessAnalyticsReport(
                report_period_start=period_start,
                report_period_end=period_end,
                revenue_metrics=revenue_metrics,
                growth_analytics=growth_analytics,
                customer_segments=customer_segments,
                profitability=profitability,
                market_analysis=market_analysis,
                sales_metrics=sales_metrics,
                key_insights=key_insights,
                strategic_recommendations=strategic_recommendations,
                risk_factors=risk_factors,
                opportunities=opportunities,
                executive_summary=executive_summary.strip()
            )

        except Exception as e:
            print(f"Error generating business report: {e}")
            return None

    async def get_business_analytics_summary(self, time_range: str = "month") -> Dict[str, Any]:
        """Get high-level business analytics summary"""
        try:
            revenue_metrics = await self.calculate_revenue_metrics()
            growth_analytics = await self.calculate_growth_analytics()

            summary = {
                "revenue": {
                    "mrr": float(revenue_metrics.monthly_recurring_revenue) if revenue_metrics else 0,
                    "arr": float(revenue_metrics.annual_recurring_revenue) if revenue_metrics else 0,
                    "growth_rate": revenue_metrics.revenue_growth_rate if revenue_metrics else 0
                },
                "customers": {
                    "total": len(self.customer_data),
                    "new": growth_analytics.new_customers if growth_analytics else 0,
                    "churned": growth_analytics.churned_customers if growth_analytics else 0,
                    "churn_rate": growth_analytics.churn_rate if growth_analytics else 0
                },
                "metrics": {
                    "ltv": float(growth_analytics.customer_lifetime_value) if growth_analytics else 0,
                    "cac": float(growth_analytics.customer_acquisition_cost) if growth_analytics else 0,
                    "ltv_cac_ratio": float(growth_analytics.customer_lifetime_value / growth_analytics.customer_acquisition_cost) if growth_analytics and growth_analytics.customer_acquisition_cost > 0 else 0
                }
            }

            return summary

        except Exception as e:
            print(f"Error generating business summary: {e}")
            return {}

    async def export_business_data(self, format_type: str = "json", include_sensitive: bool = False) -> Optional[str]:
        """Export business analytics data"""
        try:
            export_data = {
                "revenue_data": {k: {
                    "total_revenue": float(v["total_revenue"]),
                    "monthly_revenue": float(v["monthly_revenue"]),
                    "annual_revenue": float(v["annual_revenue"])
                } for k, v in self.revenue_data.items()},
                "customer_count": len(self.customer_data),
                "export_timestamp": datetime.utcnow().isoformat()
            }

            if include_sensitive:
                export_data["detailed_revenue"] = self.revenue_data
                export_data["customer_data"] = self.customer_data

            if format_type.lower() == "json":
                return json.dumps(export_data, indent=2, default=str)
            elif format_type.lower() == "csv":
                # Simple CSV for revenue data
                csv_lines = ["firm_id,total_revenue,monthly_revenue,annual_revenue"]
                for firm_id, data in export_data["revenue_data"].items():
                    line = f"{firm_id},{data['total_revenue']},{data['monthly_revenue']},{data['annual_revenue']}"
                    csv_lines.append(line)
                return "\n".join(csv_lines)

            return json.dumps(export_data, indent=2, default=str)

        except Exception as e:
            print(f"Error exporting business data: {e}")
            return None


# Global instance
business_analytics_engine = BusinessAnalyticsEngine()


# FastAPI endpoints configuration
async def get_business_analytics_endpoints():
    """Return FastAPI endpoint configurations for business analytics"""
    return [
        {
            "path": "/analytics/business/revenue",
            "method": "GET",
            "handler": "get_revenue_metrics",
            "description": "Get comprehensive revenue metrics"
        },
        {
            "path": "/analytics/business/growth",
            "method": "GET",
            "handler": "get_growth_analytics",
            "description": "Get growth and customer analytics"
        },
        {
            "path": "/analytics/business/segments",
            "method": "GET",
            "handler": "get_customer_segment_analysis",
            "description": "Get customer segment analysis"
        },
        {
            "path": "/analytics/business/profitability",
            "method": "GET",
            "handler": "get_profitability_analysis",
            "description": "Get profitability and margin analysis"
        },
        {
            "path": "/analytics/business/market",
            "method": "GET",
            "handler": "get_market_analysis",
            "description": "Get market analysis and competitive positioning"
        },
        {
            "path": "/analytics/business/sales",
            "method": "GET",
            "handler": "get_sales_metrics",
            "description": "Get sales performance metrics"
        },
        {
            "path": "/analytics/business/report",
            "method": "GET",
            "handler": "generate_business_analytics_report",
            "description": "Generate comprehensive business analytics report"
        },
        {
            "path": "/analytics/business/summary",
            "method": "GET",
            "handler": "get_business_analytics_summary",
            "description": "Get high-level business metrics summary"
        },
        {
            "path": "/analytics/business/track/revenue",
            "method": "POST",
            "handler": "track_business_revenue",
            "description": "Track revenue data"
        },
        {
            "path": "/analytics/business/track/customer",
            "method": "POST",
            "handler": "track_customer_lifecycle",
            "description": "Track customer lifecycle events"
        },
        {
            "path": "/analytics/business/export",
            "method": "POST",
            "handler": "export_business_analytics",
            "description": "Export business analytics data"
        }
    ]


async def initialize_business_analytics_system():
    """Initialize the business analytics system"""
    print("Business Analytics System initialized successfully")
    print(f"Available endpoints: {len(await get_business_analytics_endpoints())}")
    return True