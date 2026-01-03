"""
Marketing Admin API Routes

Admin-only endpoints for managing marketing automation.
All routes require admin authentication.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from app.src.core.database import get_db
from app.api.deps.auth import get_admin_user, get_optional_user, CurrentUser
from app.marketing import schemas
from app.marketing.contacts.service import ContactService
from app.marketing.campaigns.service import CampaignService
from app.marketing.campaigns.models import CampaignType, CampaignStatus
from app.marketing.newsletter.service import NewsletterService
from app.marketing.analytics.service import AnalyticsService
from app.marketing.email.tracking import EmailTracker
from app.marketing.email.sender import EmailSender

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/marketing", tags=["Marketing Admin"])


# ============ CONTACTS ============

@router.get("/contacts", response_model=schemas.ContactListResponse)
async def list_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    contact_type: Optional[str] = None,
    is_subscribed: Optional[bool] = None,
    state: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """List all marketing contacts with filters."""
    service = ContactService(db)

    contacts = service.list_contacts(
        skip=skip,
        limit=limit,
        contact_type=contact_type,
        is_subscribed=is_subscribed,
        state=state,
        search=search
    )

    total = service.count_contacts(
        is_subscribed=is_subscribed,
        contact_type=contact_type
    )

    return {
        "contacts": contacts,
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit
    }


@router.get("/contacts/{contact_id}", response_model=schemas.ContactDetailResponse)
async def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Get contact details with case history."""
    service = ContactService(db)
    result = service.get_contact_with_cases(contact_id)

    if not result:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact = result["contact"]
    return {
        **contact.__dict__,
        "contact_type": contact.contact_type.value if contact.contact_type else "other",
        "source": contact.source.value if contact.source else "manual",
        "cases": [
            {
                "id": c.id,
                "case_name": c.case_name,
                "case_number": c.case_number,
                "court": c.court,
                "role": c.role,
                "date_filed": c.date_filed.isoformat() if c.date_filed else None
            }
            for c in result["cases"]
        ],
        "case_count": result["case_count"],
        "emails_received_count": len(contact.emails_received) if contact.emails_received else 0
    }


@router.post("/contacts/{contact_id}/opt-out")
async def opt_out_contact(
    contact_id: int,
    request: schemas.OptOutRequest,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Manually opt out a contact."""
    service = ContactService(db)
    success = service.opt_out(contact_id, request.reason)

    if not success:
        raise HTTPException(status_code=404, detail="Contact not found")

    return {"status": "opted_out", "contact_id": contact_id}


@router.get("/contacts/stats/summary")
async def get_contact_stats(
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Get contact statistics summary."""
    service = ContactService(db)
    return service.get_statistics()


# ============ CAMPAIGNS ============

@router.get("/campaigns", response_model=List[schemas.CampaignResponse])
async def list_campaigns(
    status: Optional[str] = None,
    campaign_type: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """List all campaigns."""
    service = CampaignService(db)
    return service.list_campaigns(status=status, campaign_type=campaign_type)


@router.post("/campaigns", response_model=schemas.CampaignResponse)
async def create_campaign(
    campaign: schemas.CampaignCreate,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Create a new campaign."""
    service = CampaignService(db)

    try:
        campaign_type = CampaignType(campaign.campaign_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid campaign type: {campaign.campaign_type}"
        )

    return service.create_campaign(
        name=campaign.name,
        campaign_type=campaign_type,
        description=campaign.description,
        target_contact_types=campaign.target_contact_types,
        target_case_types=campaign.target_case_types,
        target_courts=campaign.target_courts,
        target_states=campaign.target_states,
        daily_send_limit=campaign.daily_send_limit,
        from_email=campaign.from_email,
        from_name=campaign.from_name,
        created_by_user_id=admin.user_id
    )


@router.get("/campaigns/{campaign_id}", response_model=schemas.CampaignResponse)
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Get campaign by ID."""
    service = CampaignService(db)
    campaign = service.get_campaign(campaign_id)

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return campaign


@router.put("/campaigns/{campaign_id}", response_model=schemas.CampaignResponse)
async def update_campaign(
    campaign_id: int,
    updates: schemas.CampaignUpdate,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Update a campaign."""
    service = CampaignService(db)

    try:
        campaign = service.update_campaign(
            campaign_id,
            **updates.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return campaign


@router.post("/campaigns/{campaign_id}/activate")
async def activate_campaign(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Activate a campaign and start sending."""
    service = CampaignService(db)

    try:
        campaign = service.activate_campaign(campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Queue initial batch of emails in background
    background_tasks.add_task(service.queue_campaign_emails, campaign_id)

    return {"status": "activated", "campaign_id": campaign_id}


@router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Pause a running campaign."""
    service = CampaignService(db)

    try:
        service.pause_campaign(campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "paused", "campaign_id": campaign_id}


@router.get("/campaigns/{campaign_id}/stats", response_model=schemas.CampaignStats)
async def get_campaign_stats(
    campaign_id: int,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Get campaign performance statistics."""
    service = CampaignService(db)
    stats = service.get_campaign_stats(campaign_id)

    if not stats:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return stats


@router.post("/campaigns/{campaign_id}/sequences", response_model=schemas.SequenceResponse)
async def add_sequence(
    campaign_id: int,
    sequence: schemas.SequenceCreate,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Add an email sequence to a campaign."""
    service = CampaignService(db)

    try:
        return service.add_sequence(
            campaign_id=campaign_id,
            subject_line=sequence.subject_line,
            body_html=sequence.body_html,
            body_text=sequence.body_text,
            delay_days=sequence.delay_days,
            delay_hours=sequence.delay_hours,
            use_ai_personalization=sequence.use_ai_personalization,
            personalization_prompt=sequence.personalization_prompt
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/campaigns/{campaign_id}/sequences", response_model=List[schemas.SequenceResponse])
async def get_sequences(
    campaign_id: int,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Get all sequences for a campaign."""
    service = CampaignService(db)
    return service.get_sequences(campaign_id)


# ============ NEWSLETTER ============

@router.get("/newsletter/subscribers", response_model=List[schemas.SubscriberResponse])
async def list_subscribers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """List newsletter subscribers."""
    service = NewsletterService(db)
    return service.list_subscribers(skip=skip, limit=limit, is_active=is_active)


@router.get("/newsletter/editions", response_model=List[schemas.NewsletterEditionResponse])
async def list_editions(
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """List newsletter editions."""
    service = NewsletterService(db)
    return service.list_editions()


@router.post("/newsletter/generate")
async def generate_newsletter(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Manually trigger newsletter generation."""
    service = NewsletterService(db)
    edition = service.generate_weekly_digest()

    return {
        "status": "generated",
        "edition_id": edition.id if edition else None
    }


@router.post("/newsletter/send")
async def send_newsletter(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Manually send the latest newsletter."""
    from app.marketing.workers.tasks import send_weekly_newsletter
    background_tasks.add_task(send_weekly_newsletter)
    return {"status": "send_started"}


# ============ ANALYTICS ============

@router.get("/analytics/dashboard", response_model=schemas.DashboardMetrics)
async def get_dashboard_metrics(
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Get marketing dashboard metrics."""
    service = AnalyticsService(db)
    return service.get_dashboard_metrics()


@router.get("/analytics/funnel", response_model=schemas.FunnelMetrics)
async def get_funnel_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Get conversion funnel metrics."""
    service = AnalyticsService(db)
    return service.get_funnel_metrics(days=days)


@router.get("/analytics/history")
async def get_metrics_history(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Get daily metrics history."""
    service = AnalyticsService(db)
    metrics = service.get_metrics_history(days=days)

    return [
        {
            "date": m.date.isoformat(),
            "new_contacts": m.new_contacts,
            "emails_sent": m.emails_sent,
            "emails_opened": m.emails_opened,
            "open_rate": m.open_rate,
            "conversions": m.conversions
        }
        for m in metrics
    ]


# ============ FILING MONITOR ============

@router.post("/monitor/trigger", response_model=schemas.MonitorTriggerResponse)
async def trigger_monitor(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Manually trigger CourtListener polling."""
    from app.marketing.workers.tasks import poll_courtlistener
    background_tasks.add_task(poll_courtlistener)
    return {"status": "triggered", "message": "CourtListener polling started"}


@router.get("/monitor/status", response_model=schemas.MonitorStatusResponse)
async def get_monitor_status(
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Get filing monitor status and recent activity."""
    from app.marketing.courtlistener.monitor import FilingMonitor
    monitor = FilingMonitor(db)
    return monitor.get_status()


# ============ EMAIL TRACKING (Public endpoints) ============

@router.get("/track/open/{email_send_id}")
async def track_email_open(
    email_send_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Track email open via invisible pixel.

    Returns a 1x1 transparent GIF.
    """
    tracker = EmailTracker(db)
    tracker.track_open(
        email_send_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    # Return 1x1 transparent GIF
    gif_data = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'

    return Response(
        content=gif_data,
        media_type="image/gif",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )


@router.get("/track/click/{email_send_id}")
async def track_email_click(
    email_send_id: int,
    url: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Track email link click and redirect.

    Logs the click and redirects to the original URL.
    """
    tracker = EmailTracker(db)
    redirect_url = tracker.track_click(
        email_send_id,
        url=url,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    if not redirect_url:
        raise HTTPException(status_code=404, detail="Invalid tracking link")

    return RedirectResponse(url=redirect_url, status_code=302)


# ============ LANDING FLOW ============

@router.get("/landing/{token}", response_model=schemas.LandingPageData)
async def get_landing_data(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Get pre-loaded case data for zero-friction landing page.

    This endpoint is called when someone clicks through from a marketing email.
    Returns the case data so the frontend can pre-populate the signup form.
    """
    tracker = EmailTracker(db)
    email_send = tracker.get_email_send_by_token(token)

    if not email_send:
        raise HTTPException(status_code=404, detail="Invalid or expired token")

    personalization = email_send.personalization_data or {}

    return {
        "email": email_send.to_email,
        "contact_name": personalization.get("full_name"),
        "case_name": personalization.get("case_name"),
        "case_number": personalization.get("case_number"),
        "court": personalization.get("court"),
        "nature_of_suit": personalization.get("nature_of_suit"),
        "token": token,
        "campaign_id": email_send.campaign_id
    }


@router.post("/landing/convert")
async def track_landing_conversion(
    conversion: schemas.ConversionRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Track conversion from landing page.

    Called when user completes signup after clicking through from email.
    """
    tracker = EmailTracker(db)
    email_send = tracker.get_email_send_by_token(conversion.token)

    if not email_send:
        raise HTTPException(status_code=404, detail="Invalid token")

    # Track conversion
    tracker.track_conversion(
        email_send_id=email_send.id,
        conversion_type=conversion.conversion_type,
        revenue=conversion.revenue,
        metadata=conversion.metadata
    )

    # Also log in analytics
    analytics = AnalyticsService(db)
    analytics.track_conversion(
        email=email_send.to_email,
        conversion_type=conversion.conversion_type,
        revenue=conversion.revenue,
        campaign_id=email_send.campaign_id,
        email_send_id=email_send.id,
        landing_token=conversion.token,
        user_id=conversion.user_id,
        metadata=conversion.metadata
    )

    return {"status": "converted", "email": email_send.to_email}


# ============ UTILITIES ============

@router.post("/email/test")
async def send_test_email(
    request: schemas.TestEmailRequest,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(get_admin_user)
):
    """Send a test email."""
    sender = EmailSender()

    try:
        result = await sender.send_test_email(
            to_email=request.to_email,
            subject=request.subject,
            body=request.body
        )
        return {"status": "sent", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ PUBLIC ENDPOINTS (No auth) ============

public_router = APIRouter(prefix="/api/v1/marketing", tags=["Marketing Public"])


@public_router.post("/subscribe")
async def subscribe_to_newsletter(
    subscribe: schemas.SubscribeRequest,
    db: Session = Depends(get_db)
):
    """Subscribe to newsletter (public endpoint)."""
    service = NewsletterService(db)

    try:
        subscriber = service.subscribe(
            email=subscribe.email,
            first_name=subscribe.first_name,
            last_name=subscribe.last_name,
            company=subscribe.company,
            interests=subscribe.interests,
            jurisdictions=subscribe.jurisdictions
        )
        return {
            "status": "subscribed",
            "email": subscriber.email,
            "confirmation_required": not subscriber.is_confirmed
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@public_router.get("/confirm/{token}")
async def confirm_subscription(
    token: str,
    db: Session = Depends(get_db)
):
    """Confirm newsletter subscription."""
    service = NewsletterService(db)
    success = service.confirm_subscription(token)

    if not success:
        raise HTTPException(status_code=404, detail="Invalid or expired confirmation token")

    return {"status": "confirmed"}


@public_router.post("/unsubscribe")
async def unsubscribe_from_newsletter(
    request: schemas.OptOutRequest,
    db: Session = Depends(get_db)
):
    """Unsubscribe from newsletter (public endpoint)."""
    if not request.email:
        raise HTTPException(status_code=400, detail="Email required")

    service = NewsletterService(db)
    service.unsubscribe(request.email, request.reason)

    # Also opt out of marketing contacts
    contact_service = ContactService(db)
    contact_service.opt_out_by_email(request.email, request.reason)

    return {"status": "unsubscribed", "email": request.email}
