"""
Case Monitoring Background Service
Polls monitored cases for new documents and broadcasts notifications
"""
import asyncio
import logging
import os
from typing import Set, Dict, Any, List, Optional
from datetime import datetime
from fastapi import WebSocket

from app.src.services.courtlistener_service import CourtListenerService
from app.models.case_notification_history import CaseNotification
from app.services.email_notification_service import email_notification_service
from app.services.document_download_service import DocumentDownloadService

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Force DEBUG level for this module


class CaseMonitorService:
    """Background service that monitors cases for new documents"""

    def __init__(self):
        self.running = False
        self.poll_interval = 900  # 15 minutes default (safer for CourtListener rate limits)
        self.rate_limit_retry_after = 0  # Seconds to wait if rate limited (0 = not rate limited)
        self.websocket_clients: Set[WebSocket] = set()
        self._task = None
        self._check_lock = asyncio.Lock()  # Prevent concurrent checks
        self._last_check_time = None  # Track last check to prevent rapid-fire calls

    def set_poll_interval(self, seconds: int):
        """Set how often to check for updates (in seconds)"""
        self.poll_interval = max(60, seconds)  # Minimum 1 minute
        logger.info(f"Poll interval set to {self.poll_interval} seconds")

    def set_rate_limit_retry(self, seconds: int):
        """Set a shorter retry interval when rate limited"""
        self.rate_limit_retry_after = max(30, seconds)  # Minimum 30 seconds
        logger.info(f"[MONITOR] Rate limit hit - will retry in {self.rate_limit_retry_after} seconds")

    def register_websocket(self, websocket: WebSocket):
        """Register a WebSocket client for notifications"""
        self.websocket_clients.add(websocket)
        logger.info(f"WebSocket client registered. Total clients: {len(self.websocket_clients)}")

    def unregister_websocket(self, websocket: WebSocket):
        """Unregister a WebSocket client"""
        self.websocket_clients.discard(websocket)
        logger.info(f"WebSocket client unregistered. Total clients: {len(self.websocket_clients)}")

    async def broadcast_notification(self, notification: Dict[str, Any]):
        """Broadcast notification to all connected WebSocket clients"""
        if not self.websocket_clients:
            return

        disconnected = set()
        for client in self.websocket_clients:
            try:
                await client.send_json(notification)
            except Exception as e:
                logger.error(f"Failed to send notification to client: {e}")
                disconnected.add(client)

        # Remove disconnected clients
        for client in disconnected:
            self.unregister_websocket(client)

    async def check_monitored_cases(self, db):
        """Check all monitored cases for new documents for all users"""
        # Prevent concurrent checks with a lock
        if self._check_lock.locked():
            logger.info("[MONITOR] Check already in progress, skipping")
            return

        # Rate limit: prevent checks more often than every 30 seconds
        from datetime import timedelta
        now = datetime.utcnow()
        if self._last_check_time and (now - self._last_check_time) < timedelta(seconds=30):
            logger.info(f"[MONITOR] Check called too soon (last: {self._last_check_time}), skipping")
            return

        async with self._check_lock:
            self._last_check_time = now
            await self._do_check_monitored_cases(db)

    async def _do_check_monitored_cases(self, db):
        """Internal method that actually performs the check"""
        try:
            from shared.database.models import UserDocketMonitor, TrackedDocket

            # Query database for all active monitors with notifications enabled
            # Both is_active AND notifications_enabled must be True
            active_monitors = db.query(UserDocketMonitor).filter(
                UserDocketMonitor.is_active == True,
                UserDocketMonitor.notifications_enabled == True
            ).all()

            if not active_monitors:
                logger.debug("No active case monitors in database")
                return

            logger.info(f"[MONITOR] Checking {len(active_monitors)} active case monitors from database")
            print(f"[MONITOR] DEBUG: Checking {len(active_monitors)} active case monitors")

            # Group monitors by user
            user_monitors: Dict[int, List[Any]] = {}
            for monitor in active_monitors:
                if monitor.user_id not in user_monitors:
                    user_monitors[monitor.user_id] = []
                user_monitors[monitor.user_id].append(monitor)

            # Check for updates using CourtListener service (with API key)
            api_key = os.getenv("COURTLISTENER_API_KEY")
            logger.info(f"[MONITOR] CourtListener API key available: {bool(api_key)}")
            if api_key:
                logger.info(f"[MONITOR] API key starts with: {api_key[:10]}...")
            service = CourtListenerService(db=db, api_key=api_key)
            all_updates = []

            # Check each user's monitored cases
            for user_id, monitors in user_monitors.items():
                try:
                    for monitor in monitors:
                        docket_id = monitor.courtlistener_docket_id
                        if not docket_id:
                            continue

                        logger.info(f"[MONITOR] Checking docket {docket_id} ({monitor.case_name}) for user {user_id}")
                        logger.info(f"[MONITOR] Last checked at: {monitor.last_checked_at}")

                        # Check this specific docket for new documents
                        try:
                            result = await service.get_docket_with_documents(docket_id)

                            if not result.get("success"):
                                logger.warning(f"[MONITOR] Failed to fetch docket {docket_id}: {result.get('error', 'Unknown error')}")
                                continue

                            documents = result.get("documents", [])
                            logger.info(f"[MONITOR] Fetched {len(documents)} total documents from docket {docket_id}")
                            print(f"[MONITOR] DEBUG: Fetched {len(documents)} documents, last_checked: {monitor.last_checked_at}")

                            # Filter for documents we haven't seen yet
                            # FIXED: Use entry_number comparison instead of timestamps
                            # This correctly detects documents we haven't processed, regardless of when they were filed
                            new_docs = []
                            seen_entry_numbers = set()  # Deduplicate by entry_number
                            last_known_entry = getattr(monitor, 'last_known_entry_number', 0) or 0
                            max_entry_seen = last_known_entry

                            logger.info(f"[MONITOR] Comparing {len(documents)} docs against last_known_entry_number: {last_known_entry}")

                            # Debug: Log first 5 document entry numbers
                            for i, doc in enumerate(documents[:5]):
                                logger.info(f"[MONITOR] DEBUG: Doc {i+1} entry_number={doc.get('entry_number')}, date_filed={doc.get('entry_date_filed')}")

                            for doc in documents:
                                entry_number = doc.get("entry_number")

                                # Try to get entry_number as int
                                try:
                                    entry_num_int = int(entry_number) if entry_number else 0
                                except (ValueError, TypeError):
                                    entry_num_int = 0

                                # Track max entry number seen
                                if entry_num_int > max_entry_seen:
                                    max_entry_seen = entry_num_int

                                # Document is new if its entry_number > last known
                                # Also deduplicate by entry_number (CourtListener may return duplicates)
                                if entry_num_int > last_known_entry:
                                    if entry_num_int not in seen_entry_numbers:
                                        seen_entry_numbers.add(entry_num_int)
                                        logger.info(f"[MONITOR] NEW DOC: Entry #{entry_number} > last known #{last_known_entry}")
                                        new_docs.append(doc)
                                    else:
                                        logger.debug(f"[MONITOR] Skipping duplicate entry #{entry_number}")

                            # Update the max entry number we've seen (will be saved later)
                            monitor._max_entry_seen = max_entry_seen

                            if new_docs:
                                logger.info(f"[MONITOR] *** FOUND {len(new_docs)} NEW DOCUMENTS for user {user_id}, docket {docket_id} ***")

                                # DEDUPLICATION: Check if we already notified for these exact documents recently
                                # Get document entry numbers to create a unique signature
                                new_doc_ids = sorted([str(d.get('entry_number', d.get('id', ''))) for d in new_docs])
                                doc_signature = ','.join(new_doc_ids)

                                # Check for recent duplicate notification (within last 10 minutes)
                                # Get ALL notifications for this docket, then filter by user_id
                                from datetime import timedelta
                                recent_cutoff = datetime.utcnow() - timedelta(minutes=10)
                                recent_notifications = db.query(CaseNotification).filter(
                                    CaseNotification.docket_id == int(docket_id),
                                    CaseNotification.sent_at > recent_cutoff,
                                    CaseNotification.notification_type == "new_documents"
                                ).all()

                                # Check if any notification matches this user and has the same documents
                                is_duplicate = False
                                for existing_notification in recent_notifications:
                                    existing_extra = existing_notification.extra_data or {}
                                    if str(existing_extra.get('user_id')) == str(user_id):
                                        # Check if same documents
                                        existing_doc_ids = sorted([str(d.get('entry_number', d.get('id', ''))) for d in (existing_notification.documents or [])])
                                        existing_signature = ','.join(existing_doc_ids)
                                        if doc_signature == existing_signature:
                                            logger.info(f"[MONITOR] Skipping duplicate notification for user {user_id}, docket {docket_id} - already sent within 10 minutes (notification #{existing_notification.id})")
                                            is_duplicate = True
                                            break

                                if is_duplicate:
                                    # Still update the entry number even though we skip notification
                                    # This prevents repeated duplicate detection on next check
                                    monitor.last_checked_at = datetime.utcnow()
                                    if hasattr(monitor, '_max_entry_seen') and monitor._max_entry_seen > 0:
                                        monitor.last_known_entry_number = monitor._max_entry_seen
                                        logger.info(f"[MONITOR] Updated last_known_entry_number to {monitor._max_entry_seen} (duplicate skipped)")
                                    db.commit()
                                    continue

                                update_data = {
                                    "docket_id": docket_id,
                                    "case_name": monitor.case_name,
                                    "court": monitor.court_name,
                                    "documents": new_docs,
                                    "count": len(new_docs)
                                }
                                all_updates.append(update_data)

                                # Send notifications
                                notification_data = {
                                    "type": "case_update",
                                    "user_id": user_id,
                                    "docket_id": docket_id,
                                    "case_name": monitor.case_name,
                                    "new_documents": new_docs,
                                    "timestamp": datetime.now().isoformat()
                                }

                                # Save notification to database for persistence
                                try:
                                    notification_record = CaseNotification(
                                        docket_id=int(docket_id),
                                        case_name=monitor.case_name,
                                        court=monitor.court_name,
                                        notification_type="new_documents",
                                        document_count=len(new_docs),
                                        documents=new_docs,
                                        websocket_sent=False,
                                        email_sent=False,
                                        extra_data={"user_id": user_id}
                                    )
                                    db.add(notification_record)
                                    db.flush()  # Get ID for logging
                                    logger.info(f"[MONITOR] Saved notification ID {notification_record.id} to database")
                                except Exception as e:
                                    logger.error(f"[MONITOR] Failed to save notification to database: {e}")

                                # Broadcast to WebSocket clients
                                logger.info(f"[MONITOR] Broadcasting WebSocket notification for {len(new_docs)} new docs")
                                await self.broadcast_notification(notification_data)
                                
                                # Update websocket_sent flag
                                try:
                                    if notification_record:
                                        notification_record.websocket_sent = True
                                        db.flush()
                                except Exception as ws_flag_err:
                                    logger.warning(f"[MONITOR] Failed to update websocket_sent flag: {ws_flag_err}")

                                # Send email notification with case details
                                # Try to use Celery for reliability with retry support
                                logger.info(f"[MONITOR] Queueing email notification for {len(new_docs)} new docs")
                                try:
                                    from app.marketing.workers.tasks import send_case_notification_email
                                    # Queue email via Celery for reliability with retries
                                    send_case_notification_email.delay(notification_record.id)
                                    logger.info(f"[MONITOR] Email queued via Celery for notification {notification_record.id}")
                                except Exception as celery_err:
                                    # Fallback to direct send if Celery unavailable
                                    logger.warning(f"[MONITOR] Celery unavailable, sending directly: {celery_err}")
                                    email_result = await email_notification_service.send_case_update_email(
                                        user_id=user_id,
                                        docket_id=docket_id,
                                        new_documents=new_docs,
                                        case_name=monitor.case_name,
                                        court=monitor.court_name
                                    )

                                    # Update email_sent flag based on result
                                    try:
                                        if notification_record and email_result.get('success'):
                                            notification_record.email_sent = True
                                            db.flush()
                                            logger.info(f"[MONITOR] Email sent successfully to user {user_id}")
                                        elif email_result:
                                            logger.warning(f"[MONITOR] Email send failed: {email_result.get('error', 'Unknown error')}")
                                    except Exception as email_flag_err:
                                        logger.warning(f"[MONITOR] Failed to update email_sent flag: {email_flag_err}")

                                # Auto-download documents if enabled for this monitor
                                if monitor.auto_download_enabled:
                                    logger.info(f"[MONITOR] Auto-download enabled - starting downloads for {len(new_docs)} docs")
                                    try:
                                        download_service = DocumentDownloadService(db)
                                        downloads = await download_service.auto_download_new_documents(
                                            user_id=user_id,
                                            docket_id=docket_id,
                                            documents=new_docs
                                        )
                                        completed = [d for d in downloads if d.status.value == "completed"]
                                        logger.info(f"[MONITOR] Auto-download: {len(completed)}/{len(downloads)} documents downloaded successfully")
                                    except Exception as download_err:
                                        logger.error(f"[MONITOR] Auto-download error: {download_err}")
                                else:
                                    logger.debug(f"[MONITOR] Auto-download not enabled for monitor {monitor.id}")
                            else:
                                logger.info(f"[MONITOR] No new documents for docket {docket_id} (checked {len(documents)} docs)")

                            # Update last_checked_at and last_known_entry_number
                            monitor.last_checked_at = datetime.utcnow()
                            # Save the max entry number we saw (from _max_entry_seen set during detection)
                            if hasattr(monitor, '_max_entry_seen') and monitor._max_entry_seen > 0:
                                monitor.last_known_entry_number = monitor._max_entry_seen
                                logger.info(f"[MONITOR] Updated last_known_entry_number to {monitor._max_entry_seen}")
                            db.commit()

                        except Exception as e:
                            error_str = str(e)
                            logger.error(f"[MONITOR] Error checking docket {docket_id}: {e}")

                            # Check if this is a rate limit error (429)
                            if '429' in error_str or 'rate limit' in error_str.lower() or 'throttled' in error_str.lower():
                                # CourtListener returns: "Expected available in X seconds"
                                # Parse the actual wait time from the response
                                import re
                                retry_after = 60  # Default 60 seconds

                                # Try to match "Expected available in X seconds" (CourtListener format)
                                match = re.search(r'available in (\d+) seconds', error_str.lower())
                                if match:
                                    retry_after = int(match.group(1)) + 5  # Add 5 sec buffer
                                    logger.info(f"[MONITOR] Parsed retry-after from response: {retry_after} seconds")
                                elif 'retry-after' in error_str.lower():
                                    # Try to extract retry-after header value
                                    match = re.search(r'retry-after[:\s]+(\d+)', error_str.lower())
                                    if match:
                                        retry_after = int(match.group(1))

                                self.set_rate_limit_retry(retry_after)
                                logger.warning(f"[MONITOR] Rate limited by CourtListener for docket {docket_id} - skipping this monitor, continuing with others")
                                # Continue with other monitors instead of stopping all processing
                                # The rate limit retry will be handled on the next full check cycle
                                continue

                            import traceback
                            logger.error(f"[MONITOR] Traceback: {traceback.format_exc()}")

                except Exception as e:
                    logger.error(f"[MONITOR] Error checking updates for user {user_id}: {e}")

            if all_updates:
                logger.info(f"[MONITOR] *** Total updates found across all users: {len(all_updates)} ***")
            else:
                logger.info(f"[MONITOR] No new documents found in monitored cases")

        except Exception as e:
            logger.error(f"[MONITOR] Error in check_monitored_cases: {e}")
            import traceback
            logger.error(f"[MONITOR] Traceback: {traceback.format_exc()}")

    async def monitoring_loop(self):
        """Main monitoring loop - creates fresh DB sessions for each cycle"""
        from app.src.core.database import SessionLocal

        logger.info("Case monitoring service started")

        while self.running:
            db = None
            try:
                # Check if we're still rate limited from a previous 429
                if self.rate_limit_retry_after > 0:
                    wait_time = self.rate_limit_retry_after
                    logger.info(f"[MONITOR] Still rate limited - waiting {wait_time} seconds before retry")
                    self.rate_limit_retry_after = 0  # Reset after using
                    await asyncio.sleep(wait_time)
                    continue  # Check again after waiting

                # Create fresh DB session for each check cycle to avoid stale connections
                db = SessionLocal()
                await self.check_monitored_cases(db)

                # Determine wait time: use rate limit retry if set during check, otherwise normal poll interval
                if self.rate_limit_retry_after > 0:
                    wait_time = self.rate_limit_retry_after
                    logger.info(f"[MONITOR] Rate limited - waiting {wait_time} seconds before retry")
                    # Don't reset here - let the next iteration handle it
                else:
                    wait_time = self.poll_interval
                    logger.debug(f"[MONITOR] Next check in {wait_time} seconds")

                await asyncio.sleep(wait_time)

            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                # Wait a bit before retrying on error
                await asyncio.sleep(60)
            finally:
                # Always close the DB session
                if db:
                    try:
                        db.close()
                    except Exception:
                        pass

        logger.info("Case monitoring service stopped")

    def start(self, db=None):
        """Start the monitoring service (db parameter kept for backward compatibility but not used)"""
        if self.running:
            logger.warning("Monitoring service already running")
            return

        self.running = True
        self._task = asyncio.create_task(self.monitoring_loop())
        logger.info("Case monitoring service starting...")

    def stop(self):
        """Stop the monitoring service"""
        if not self.running:
            return

        self.running = False
        if self._task:
            self._task.cancel()
        logger.info("Case monitoring service stopping...")


# Global instance
case_monitor_service = CaseMonitorService()
