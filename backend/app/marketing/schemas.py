"""
Marketing Pydantic Schemas

Request/response models for marketing API endpoints.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ Contact Schemas ============

class ContactBase(BaseModel):
    """Base contact fields"""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    firm_name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class ContactCreate(ContactBase):
    """Create contact request"""
    contact_type: str = "other"
    source: str = "manual"
    tags: Optional[List[str]] = None


class ContactUpdate(BaseModel):
    """Update contact request"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    firm_name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    tags: Optional[List[str]] = None


class ContactResponse(ContactBase):
    """Contact response"""
    id: int
    contact_type: str
    source: str
    is_subscribed: bool
    engagement_score: int
    created_at: datetime
    last_contacted_at: Optional[datetime]

    class Config:
        from_attributes = True


class ContactDetailResponse(ContactResponse):
    """Detailed contact response with cases"""
    cases: List[Dict[str, Any]] = []
    case_count: int = 0
    emails_received_count: int = 0


class ContactListResponse(BaseModel):
    """Paginated contact list"""
    contacts: List[ContactResponse]
    total: int
    page: int
    page_size: int


# ============ Campaign Schemas ============

class CampaignBase(BaseModel):
    """Base campaign fields"""
    name: str
    description: Optional[str] = None
    campaign_type: str


class CampaignCreate(CampaignBase):
    """Create campaign request"""
    target_contact_types: Optional[List[str]] = None
    target_case_types: Optional[List[str]] = None
    target_courts: Optional[List[str]] = None
    target_states: Optional[List[str]] = None
    daily_send_limit: int = 100
    from_email: Optional[str] = None
    from_name: Optional[str] = None


class CampaignUpdate(BaseModel):
    """Update campaign request"""
    name: Optional[str] = None
    description: Optional[str] = None
    target_contact_types: Optional[List[str]] = None
    target_case_types: Optional[List[str]] = None
    target_states: Optional[List[str]] = None
    daily_send_limit: Optional[int] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None


class CampaignResponse(CampaignBase):
    """Campaign response"""
    id: int
    status: str
    total_sent: int
    total_opened: int
    total_clicked: int
    total_converted: int
    created_at: datetime
    activated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CampaignStats(BaseModel):
    """Campaign statistics"""
    campaign_id: int
    name: str
    status: str
    metrics: Dict[str, int]
    rates: Dict[str, float]
    sequences: List[Dict[str, Any]]
    created_at: str
    activated_at: Optional[str]


class SequenceCreate(BaseModel):
    """Create email sequence request"""
    subject_line: str
    body_html: str
    body_text: Optional[str] = None
    delay_days: int = 0
    delay_hours: int = 0
    use_ai_personalization: bool = True
    personalization_prompt: Optional[str] = None


class SequenceResponse(BaseModel):
    """Email sequence response"""
    id: int
    campaign_id: int
    sequence_order: int
    subject_line: str
    delay_days: int
    delay_hours: int
    is_active: bool
    total_sent: int
    total_opened: int

    class Config:
        from_attributes = True


# ============ Newsletter Schemas ============

class SubscribeRequest(BaseModel):
    """Newsletter subscribe request"""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    interests: Optional[List[str]] = None
    jurisdictions: Optional[List[str]] = None


class SubscriberResponse(BaseModel):
    """Newsletter subscriber response"""
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    company: Optional[str]
    is_confirmed: bool
    is_active: bool
    frequency: str
    emails_received: int
    emails_opened: int
    created_at: datetime

    class Config:
        from_attributes = True


class NewsletterEditionResponse(BaseModel):
    """Newsletter edition response"""
    id: int
    edition_number: Optional[int]
    edition_date: datetime
    subject_line: Optional[str]
    status: str
    total_sent: int
    total_opened: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Analytics Schemas ============

class DashboardMetrics(BaseModel):
    """Dashboard metrics response"""
    contacts: Dict[str, int]
    campaigns: Dict[str, int]
    emails: Dict[str, Any]
    newsletter: Dict[str, int]
    conversions: Dict[str, int]
    generated_at: str


class FunnelMetrics(BaseModel):
    """Funnel metrics response"""
    period_days: int
    funnel: Dict[str, int]
    rates: Dict[str, float]


class DailyMetricsResponse(BaseModel):
    """Daily metrics response"""
    date: str
    new_contacts: int
    emails_sent: int
    emails_opened: int
    open_rate: float
    conversions: int

    class Config:
        from_attributes = True


# ============ Monitor Schemas ============

class MonitorStatusResponse(BaseModel):
    """Monitor status response"""
    last_poll_started: Optional[str]
    last_poll_completed: Optional[str]
    last_status: Optional[str]
    last_error: Optional[str]
    dockets_found: int
    dockets_processed: int
    contacts_created: int
    rate_limit_remaining: Optional[int]
    config: Dict[str, Any]


class MonitorTriggerResponse(BaseModel):
    """Monitor trigger response"""
    status: str
    message: str


# ============ Landing Flow Schemas ============

class LandingPageData(BaseModel):
    """Data for zero-friction landing page"""
    email: str
    contact_name: Optional[str]
    case_name: Optional[str]
    case_number: Optional[str]
    court: Optional[str]
    nature_of_suit: Optional[str]
    token: str
    campaign_id: Optional[int]


class ConversionRequest(BaseModel):
    """Track conversion request"""
    token: str
    conversion_type: str = "signup"
    user_id: Optional[str] = None
    revenue: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


# ============ Email Template Schemas ============

class EmailTemplateCreate(BaseModel):
    """Create email template request"""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    subject_line: str
    preview_text: Optional[str] = None
    body_html: str
    body_text: Optional[str] = None


class EmailTemplateResponse(BaseModel):
    """Email template response"""
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    subject_line: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Utility Schemas ============

class OptOutRequest(BaseModel):
    """Opt-out request"""
    email: Optional[EmailStr] = None
    reason: Optional[str] = None


class TestEmailRequest(BaseModel):
    """Test email request"""
    to_email: EmailStr
    subject: Optional[str] = "Test Email from CourtCase-Search"
    body: Optional[str] = "This is a test email."
