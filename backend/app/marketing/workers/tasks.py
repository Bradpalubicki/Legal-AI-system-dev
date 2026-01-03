"""
Celery Task Definitions

Background tasks for marketing automation.
"""

import logging
import asyncio
from typing import Optional

from app.marketing.workers.celery_app import celery_app
from app.src.core.database import SessionLocal

logger = logging.getLogger(__name__)


def get_db():
    """Get database session for tasks."""
    return SessionLocal()


@celery_app.task(bind=True, max_retries=3)
def poll_courtlistener(self):
    """
    Poll CourtListener for new filings.

    Runs every 30 minutes to find new court cases
    and extract contact information.
    """
    logger.info("Starting CourtListener polling task")

    db = get_db()
    try:
        from app.marketing.courtlistener.monitor import FilingMonitor

        monitor = FilingMonitor(db)
        stats = asyncio.run(monitor.poll_for_new_filings())

        logger.info(
            f"CourtListener poll complete: "
            f"{stats.get('dockets_processed', 0)} dockets, "
            f"{stats.get('contacts_created', 0)} new contacts"
        )

        return stats

    except Exception as e:
        logger.error(f"Error polling CourtListener: {e}", exc_info=True)
        self.retry(exc=e, countdown=300)  # Retry in 5 minutes

    finally:
        db.close()


@celery_app.task(bind=True)
def process_email_queue(self):
    """
    Process queued emails for active campaigns.

    Runs every 5 minutes to send emails that are
    queued and ready to be sent.
    """
    logger.info("Processing email queue")

    db = get_db()
    try:
        from app.marketing.campaigns.service import CampaignService
        from app.marketing.email.sender import EmailSender

        campaign_service = CampaignService(db)
        sender = EmailSender()

        # Get emails ready to send
        queued_emails = campaign_service.get_queued_emails(limit=50)

        sent_count = 0
        failed_count = 0

        for email_send in queued_emails:
            try:
                contact = email_send.contact
                success = asyncio.run(sender.send_email(email_send, contact))

                if success:
                    sent_count += 1
                else:
                    failed_count += 1

                db.commit()

            except Exception as e:
                logger.error(f"Error sending email {email_send.id}: {e}")
                failed_count += 1
                db.rollback()

        logger.info(f"Email queue processed: {sent_count} sent, {failed_count} failed")

        return {"sent": sent_count, "failed": failed_count}

    except Exception as e:
        logger.error(f"Error processing email queue: {e}", exc_info=True)
        db.rollback()

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def send_campaign_email(self, email_send_id: int):
    """
    Send a single campaign email.

    Used for individual sends and retries.
    """
    db = get_db()
    try:
        from app.marketing.campaigns.models import EmailSend
        from app.marketing.email.sender import EmailSender

        email_send = db.query(EmailSend).filter(
            EmailSend.id == email_send_id
        ).first()

        if not email_send:
            logger.warning(f"Email send {email_send_id} not found")
            return

        sender = EmailSender()
        asyncio.run(sender.send_email(email_send, email_send.contact))
        db.commit()

    except Exception as e:
        logger.error(f"Error sending email {email_send_id}: {e}")
        self.retry(exc=e, countdown=60)

    finally:
        db.close()


@celery_app.task
def generate_weekly_newsletter():
    """
    Generate content for weekly newsletter.

    Runs Sunday evening to prepare content
    for Monday morning send.
    """
    logger.info("Generating weekly newsletter")

    db = get_db()
    try:
        from app.marketing.newsletter.service import NewsletterService

        newsletter_service = NewsletterService(db)
        edition = newsletter_service.generate_weekly_digest()

        logger.info(f"Newsletter generated: edition {edition.id if edition else 'None'}")

        return {"edition_id": edition.id if edition else None}

    except Exception as e:
        logger.error(f"Error generating newsletter: {e}", exc_info=True)

    finally:
        db.close()


@celery_app.task
def send_weekly_newsletter():
    """
    Send weekly newsletter to all subscribers.

    Runs Monday morning.
    """
    logger.info("Sending weekly newsletter")

    db = get_db()
    try:
        from app.marketing.newsletter.service import NewsletterService

        newsletter_service = NewsletterService(db)
        stats = asyncio.run(newsletter_service.send_latest_edition())

        logger.info(f"Newsletter sent: {stats}")

        return stats

    except Exception as e:
        logger.error(f"Error sending newsletter: {e}", exc_info=True)

    finally:
        db.close()


@celery_app.task
def daily_analytics_rollup():
    """
    Calculate and store daily analytics.

    Runs at midnight to aggregate the day's metrics.
    """
    logger.info("Running daily analytics rollup")

    db = get_db()
    try:
        from app.marketing.analytics.service import AnalyticsService

        analytics_service = AnalyticsService(db)
        analytics_service.calculate_daily_metrics()

        logger.info("Daily analytics rollup complete")

    except Exception as e:
        logger.error(f"Error in analytics rollup: {e}", exc_info=True)

    finally:
        db.close()


@celery_app.task
def update_all_campaign_metrics():
    """
    Update metrics for all active campaigns.

    Runs hourly to keep campaign stats current.
    """
    logger.info("Updating campaign metrics")

    db = get_db()
    try:
        from app.marketing.campaigns.service import CampaignService
        from app.marketing.campaigns.models import Campaign, CampaignStatus

        campaign_service = CampaignService(db)

        # Get all active campaigns
        campaigns = db.query(Campaign).filter(
            Campaign.status == CampaignStatus.ACTIVE
        ).all()

        for campaign in campaigns:
            campaign_service.update_campaign_metrics(campaign.id)

        logger.info(f"Updated metrics for {len(campaigns)} campaigns")

    except Exception as e:
        logger.error(f"Error updating campaign metrics: {e}", exc_info=True)

    finally:
        db.close()


@celery_app.task
def process_opt_outs():
    """
    Process any pending opt-out requests.

    CAN-SPAM requires honoring opt-outs within 10 business days.
    We process them immediately.
    """
    logger.info("Processing opt-outs")

    db = get_db()
    try:
        from app.marketing.contacts.service import ContactService

        contact_service = ContactService(db)
        processed = contact_service.process_pending_opt_outs()

        logger.info(f"Processed {processed} opt-out requests")

        return {"processed": processed}

    except Exception as e:
        logger.error(f"Error processing opt-outs: {e}", exc_info=True)

    finally:
        db.close()


@celery_app.task
def queue_campaign_emails(campaign_id: int):
    """
    Queue emails for a campaign.

    Called when a campaign is activated.
    """
    logger.info(f"Queueing emails for campaign {campaign_id}")

    db = get_db()
    try:
        from app.marketing.campaigns.service import CampaignService

        campaign_service = CampaignService(db)
        queued = campaign_service.queue_campaign_emails(campaign_id)

        logger.info(f"Queued {queued} emails for campaign {campaign_id}")

        return {"campaign_id": campaign_id, "queued": queued}

    except Exception as e:
        logger.error(f"Error queueing campaign emails: {e}", exc_info=True)

    finally:
        db.close()


@celery_app.task
def personalize_email_content(email_send_id: int):
    """
    Use AI to personalize email content.

    Called before sending emails that have AI personalization enabled.
    """
    logger.info(f"Personalizing email {email_send_id}")

    db = get_db()
    try:
        from app.marketing.campaigns.models import EmailSend, EmailSequence
        from app.marketing.campaigns.personalization import EmailPersonalizer

        email_send = db.query(EmailSend).filter(
            EmailSend.id == email_send_id
        ).first()

        if not email_send:
            return

        sequence = db.query(EmailSequence).filter(
            EmailSequence.id == email_send.sequence_id
        ).first()

        if not sequence or not sequence.use_ai_personalization:
            return

        personalizer = EmailPersonalizer()
        personalized_content = asyncio.run(
            personalizer.personalize_email(
                email_send,
                email_send.contact,
                sequence.personalization_prompt
            )
        )

        if personalized_content:
            email_send.body_html = personalized_content.get('body_html', email_send.body_html)
            email_send.subject_line = personalized_content.get('subject', email_send.subject_line)
            db.commit()

        logger.info(f"Personalized email {email_send_id}")

    except Exception as e:
        logger.error(f"Error personalizing email: {e}", exc_info=True)

    finally:
        db.close()


# =============================================================================
# CASE NOTIFICATION TASKS
# =============================================================================

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_case_notification_email(self, notification_id: int):
    """
    Send a case notification email with retry support.

    Called when new documents are detected for a monitored case.
    Retries up to 3 times with 5 minute delay between retries.
    """
    logger.info(f"[CELERY] Sending case notification email for notification {notification_id}")

    db = get_db()
    try:
        from app.models.case_notification_history import CaseNotification
        from app.services.email_notification_service import email_notification_service
        from app.models.user import User

        # Get the notification record
        notification = db.query(CaseNotification).filter(
            CaseNotification.id == notification_id
        ).first()

        if not notification:
            logger.warning(f"[CELERY] Notification {notification_id} not found")
            return {"success": False, "error": "Notification not found"}

        # Already sent? Skip
        if notification.email_sent:
            logger.info(f"[CELERY] Notification {notification_id} email already sent, skipping")
            return {"success": True, "skipped": True}

        # Get user ID from extra_data
        extra_data = notification.extra_data or {}
        user_id = extra_data.get('user_id')

        if not user_id:
            logger.warning(f"[CELERY] No user_id in notification {notification_id}")
            return {"success": False, "error": "No user_id in notification"}

        # Get user email
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.email:
            logger.warning(f"[CELERY] User {user_id} not found or no email")
            return {"success": False, "error": "User not found or no email"}

        # Send the email
        result = email_notification_service.send_new_documents_notification(
            to_email=user.email,
            docket_id=notification.docket_id,
            case_name=notification.case_name or "Unknown Case",
            document_count=notification.document_count or len(notification.documents or []),
            documents=notification.documents or [],
            court=notification.court
        )

        if result.get('success'):
            notification.email_sent = True
            notification.extra_data = {**extra_data, 'email_sent_at': result.get('sent_at')}
            db.commit()
            logger.info(f"[CELERY] Email sent successfully for notification {notification_id}")
            return {"success": True, "sent_to": user.email}
        else:
            # Retry on failure
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"[CELERY] Email send failed for notification {notification_id}: {error_msg}")
            raise self.retry(exc=Exception(error_msg))

    except Exception as e:
        logger.error(f"[CELERY] Error sending notification email {notification_id}: {e}", exc_info=True)
        # Let Celery handle the retry
        raise self.retry(exc=e)

    finally:
        db.close()


@celery_app.task
def retry_failed_notification_emails():
    """
    Find and retry failed notification emails.

    Runs every 15 minutes to find notifications where:
    - email_sent = False
    - websocket_sent = True (notification was created properly)
    - sent_at is within last 24 hours (don't retry very old notifications)
    """
    logger.info("[CELERY] Checking for failed notification emails to retry")

    db = get_db()
    try:
        from app.models.case_notification_history import CaseNotification
        from datetime import datetime, timedelta

        # Find notifications that need email retry (last 24 hours only)
        cutoff = datetime.utcnow() - timedelta(hours=24)

        failed_notifications = db.query(CaseNotification).filter(
            CaseNotification.email_sent == False,
            CaseNotification.websocket_sent == True,  # Was properly created
            CaseNotification.sent_at > cutoff,
            CaseNotification.notification_type == "new_documents"
        ).all()

        if not failed_notifications:
            logger.info("[CELERY] No failed notification emails to retry")
            return {"retried": 0}

        logger.info(f"[CELERY] Found {len(failed_notifications)} failed notification emails to retry")

        retried_count = 0
        for notification in failed_notifications:
            # Queue each one for retry
            send_case_notification_email.delay(notification.id)
            retried_count += 1

        logger.info(f"[CELERY] Queued {retried_count} notification emails for retry")
        return {"retried": retried_count}

    except Exception as e:
        logger.error(f"[CELERY] Error retrying notification emails: {e}", exc_info=True)
        return {"error": str(e)}

    finally:
        db.close()


# =============================================================================
# ADVERSARIAL SIMULATION TASKS
# =============================================================================

@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def run_adversarial_simulation(self, simulation_id: str):
    """
    Run adversarial simulation in background.

    Generates counter-arguments, rebuttals, and weakness analysis.
    Called when interview is complete.
    """
    from datetime import datetime
    logger.info(f"[CELERY] Starting adversarial simulation {simulation_id}")

    db = get_db()
    try:
        from app.models.adversarial import AdversarialSimulation, TIER_ADVERSARIAL_FEATURES
        from app.src.services.adversarial_simulation_service import AdversarialSimulationService

        # Get simulation
        simulation = db.query(AdversarialSimulation).filter(
            AdversarialSimulation.id == simulation_id
        ).first()

        if not simulation:
            logger.warning(f"[CELERY] Simulation {simulation_id} not found")
            return {"success": False, "error": "Simulation not found"}

        # Skip if already completed
        if simulation.status == 'completed':
            logger.info(f"[CELERY] Simulation {simulation_id} already completed, skipping")
            return {"success": True, "skipped": True}

        # Mark as running
        simulation.status = 'running'
        simulation.started_at = datetime.utcnow() if not simulation.started_at else simulation.started_at
        db.commit()

        # Get tier config for weakness analysis
        # Default to basic tier - in production would look up user's actual tier
        tier_config = TIER_ADVERSARIAL_FEATURES.get("basic", {})
        include_weaknesses = tier_config.get("weakness_analysis", False)

        # Run simulation
        service = AdversarialSimulationService(db)
        result = asyncio.run(service.finalize_simulation(
            simulation_id=simulation_id,
            include_weaknesses=include_weaknesses
        ))

        logger.info(
            f"[CELERY] Adversarial simulation {simulation_id} completed with "
            f"{len(result.get('counter_arguments', []))} counter-arguments"
        )

        return {
            "success": True,
            "simulation_id": simulation_id,
            "counter_count": len(result.get('counter_arguments', [])),
            "overall_strength": result.get('overall_strength')
        }

    except Exception as e:
        logger.error(f"[CELERY] Error in adversarial simulation {simulation_id}: {e}", exc_info=True)

        # Mark as failed
        try:
            simulation = db.query(AdversarialSimulation).filter(
                AdversarialSimulation.id == simulation_id
            ).first()
            if simulation:
                simulation.status = 'failed'
                simulation.error_message = str(e)
                db.commit()
        except Exception:
            db.rollback()

        # Retry
        raise self.retry(exc=e)

    finally:
        db.close()


@celery_app.task
def process_adversarial_queue():
    """
    Process pending adversarial simulations.

    Runs every 5 minutes to find simulations that need processing.
    """
    from datetime import datetime, timedelta
    logger.info("[CELERY] Processing adversarial simulation queue")

    db = get_db()
    try:
        from app.models.adversarial import AdversarialSimulation

        # Find pending simulations that have collected facts
        pending = db.query(AdversarialSimulation).filter(
            AdversarialSimulation.status == 'pending',
            AdversarialSimulation.collected_facts != {}
        ).all()

        # Also find running simulations that have been stuck for > 10 minutes
        stuck_cutoff = datetime.utcnow() - timedelta(minutes=10)
        stuck = db.query(AdversarialSimulation).filter(
            AdversarialSimulation.status == 'running',
            AdversarialSimulation.started_at < stuck_cutoff
        ).all()

        queued_count = 0

        # Queue pending simulations
        for simulation in pending:
            run_adversarial_simulation.delay(simulation.id)
            queued_count += 1

        # Retry stuck simulations
        for simulation in stuck:
            logger.warning(f"[CELERY] Retrying stuck simulation {simulation.id}")
            simulation.status = 'pending'  # Reset to pending so it can be picked up
            db.commit()
            run_adversarial_simulation.delay(simulation.id)
            queued_count += 1

        if queued_count:
            logger.info(f"[CELERY] Queued {queued_count} adversarial simulations")

        return {"queued": queued_count}

    except Exception as e:
        logger.error(f"[CELERY] Error processing adversarial queue: {e}", exc_info=True)
        return {"error": str(e)}

    finally:
        db.close()
