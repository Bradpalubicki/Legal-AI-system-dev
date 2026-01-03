"""
Case Monitoring Bridge Service
Connects CaseAccess purchases (new system) with CourtListener monitoring (old system)
"""
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.case_access import CaseAccess, CaseAccessStatus
from app.services.case_monitor_service import case_monitor_service
from app.services.case_notification_service import CaseNotificationService
from app.src.services.courtlistener_service import CourtListenerService

logger = logging.getLogger(__name__)


class CaseMonitoringBridge:
    """
    Bridges the gap between:
    - CaseAccess table (new paid case access system)
    - CourtListener monitoring service (old in-memory system)
    - CaseNotificationService (new notification system)
    """

    def __init__(self, db: Session):
        self.db = db
        self.courtlistener = CourtListenerService(db=db)
        self.notification_service = CaseNotificationService(db=db)

    async def sync_monitoring_from_case_access(self):
        """
        Sync monitoring service with active case access purchases.
        This runs every monitoring cycle to restore monitoring from database.
        """
        try:
            # Get all active case accesses with CourtListener docket IDs
            from shared.database.models import TrackedDocket

            active_cases = self.db.query(CaseAccess).join(
                TrackedDocket, CaseAccess.case_id == TrackedDocket.id
            ).filter(
                CaseAccess.status == CaseAccessStatus.ACTIVE,
                CaseAccess.notifications_enabled == True,
                TrackedDocket.courtlistener_docket_id.isnot(None)
            ).all()

            if not active_cases:
                logger.debug("No active case accesses with CourtListener IDs found")
                return

            logger.info(f"Syncing {len(active_cases)} active case accesses")

            # For each active case access, ensure it's being monitored
            for case_access in active_cases:
                # Skip if access has expired
                if not case_access.is_active():
                    case_access.status = CaseAccessStatus.EXPIRED
                    continue

                case = case_access.case
                docket_id = case.courtlistener_docket_id

                # Check if already being monitored in memory
                if str(docket_id) not in self.courtlistener.monitored_cases:
                    # Restore monitoring from database
                    try:
                        await self.courtlistener.monitor_case(docket_id)
                        logger.info(f"✓ Restored monitoring for docket {docket_id} ({case.case_name})")
                    except Exception as e:
                        logger.error(f"Failed to restore monitoring for docket {docket_id}: {e}")

            self.db.commit()
            logger.info(f"Sync complete. Monitoring {len(self.courtlistener.monitored_cases)} cases")

        except Exception as e:
            logger.error(f"Error syncing monitoring: {e}", exc_info=True)
            self.db.rollback()

    async def check_for_updates_and_notify(self):
        """
        Check monitored cases for updates and send notifications to users who purchased access.

        This replaces the old notification system with the new one.
        """
        try:
            # Get updates from CourtListener
            updates = await self.courtlistener.get_monitored_cases_updates()

            if not updates:
                logger.debug("No case updates found")
                return

            logger.info(f"Found {len(updates)} cases with new documents")

            # For each case with updates, notify all users with active access
            for update in updates:
                docket_id = update.get("docket_id")
                new_documents = update.get("documents", [])

                if not new_documents:
                    continue

                logger.info(f"Processing {len(new_documents)} new documents for docket {docket_id}")

                # Find all users with active access to this case
                # We need to map docket_id back to case_id
                # This requires the TrackedDocket model to have courtlistener_docket_id field
                from shared.database.models import TrackedDocket

                case = self.db.query(TrackedDocket).filter(
                    TrackedDocket.courtlistener_docket_id == docket_id
                ).first()

                if not case:
                    logger.warning(f"Could not find case for docket {docket_id}")
                    continue

                # Get all active case accesses for this case
                case_accesses = self.db.query(CaseAccess).filter(
                    CaseAccess.case_id == case.id,
                    CaseAccess.status == CaseAccessStatus.ACTIVE,
                    CaseAccess.notifications_enabled == True
                ).all()

                logger.info(f"Found {len(case_accesses)} users to notify for case {case.id}")

                # Send notifications using the new notification service
                for doc in new_documents:
                    doc_description = doc.get("description", "New document filed")

                    notifications_sent = self.notification_service.notify_case_update(
                        case_id=case.id,
                        event_type="new_filing",
                        event_title=f"New Document: {doc_description[:100]}",
                        event_description=f"A new document was filed in {case.case_name}",
                        event_data={
                            "docket_id": docket_id,
                            "document": doc,
                            "document_number": doc.get("document_number"),
                            "date_filed": doc.get("date_filed")
                        }
                    )

                    logger.info(f"Sent {notifications_sent} notifications for document in case {case.id}")

        except Exception as e:
            logger.error(f"Error checking updates and notifying: {e}")

    async def ensure_case_monitored(self, case_id: int, courtlistener_docket_id: int):
        """
        Ensure a specific case is being monitored.

        Call this when a user purchases case access to immediately start monitoring.

        Args:
            case_id: Internal case ID
            courtlistener_docket_id: CourtListener docket ID
        """
        try:
            # Check if already monitored
            if str(courtlistener_docket_id) in self.courtlistener.monitored_cases:
                logger.info(f"Docket {courtlistener_docket_id} already monitored")
                return True

            # Start monitoring
            logger.info(f"Starting monitoring for case {case_id} (docket {courtlistener_docket_id})")
            await self.courtlistener.monitor_case(courtlistener_docket_id)

            logger.info(f"✓ Successfully started monitoring docket {courtlistener_docket_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to ensure case monitored: {e}")
            return False


# Global singleton instance
_bridge_instance = None

def get_monitoring_bridge(db: Session) -> CaseMonitoringBridge:
    """Get or create monitoring bridge instance"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = CaseMonitoringBridge(db)
    return _bridge_instance
