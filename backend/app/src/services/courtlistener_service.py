"""
CourtListener Service - Federal Court Records Integration

Provides free access to federal court records through CourtListener API.
Auto-monitors cases for new document filings.
"""

import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone, date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import asyncio

# Import models from shared database
from shared.database.models import TrackedDocket, UserDocketMonitor

logger = logging.getLogger(__name__)


def parse_date_to_naive_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse a date string from CourtListener API into a timezone-naive datetime.

    CourtListener returns dates in ISO format (e.g., "2023-05-04").
    We need timezone-naive datetimes for SQLite compatibility.

    Args:
        date_str: Date string in ISO format or None

    Returns:
        Timezone-naive datetime object or None
    """
    if not date_str:
        return None

    try:
        # Parse ISO date string
        if 'T' in date_str:
            # Full datetime format: "2023-05-04T14:30:00Z"
            parsed = datetime.fromisoformat(date_str.replace('Z', '').replace('+00:00', ''))
        else:
            # Date-only format: "2023-05-04"
            parsed_date = date.fromisoformat(date_str)
            parsed = datetime.combine(parsed_date, datetime.min.time())

        # Ensure timezone-naive (remove any timezone info)
        return parsed.replace(tzinfo=None)
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return None


class CourtListenerServiceError(Exception):
    """Base exception for CourtListener service errors"""
    pass


class CourtListenerService:
    """
    Service for CourtListener API integration.

    Provides:
    - Case and docket search
    - Document retrieval
    - Auto-monitoring for case updates
    - Free alternative to PACER
    """

    def __init__(self, db: Session, api_key: Optional[str] = None):
        """
        Initialize CourtListener service.

        Args:
            db: Database session
            api_key: Optional CourtListener API key (5000 queries/hour with key)
        """
        self.db = db
        self.api_key = api_key
        self.base_url = "https://www.courtlistener.com/api/rest/v4"
        self.timeout = httpx.Timeout(60.0, connect=15.0)  # Increased timeout for slower API responses

        # Monitored cases are now stored in database (TrackedDocket + UserDocketMonitor tables)
        # This ensures persistence across server restarts

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including authentication if available"""
        headers = {
            "User-Agent": "Legal-AI-System/1.0",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Token {self.api_key}"
        return headers

    def _get_courts_by_type(self, court_type: str) -> List[str]:
        """
        Get list of court codes for a given court type.

        Args:
            court_type: 'bankruptcy', 'district', or 'circuit'

        Returns:
            List of CourtListener court codes
        """
        # Bankruptcy courts (end with 'b')
        bankruptcy_courts = [
            'almb', 'alnb', 'alsb',  # Alabama
            'akb',                    # Alaska
            'azb',                    # Arizona
            'areb', 'arwb',           # Arkansas
            'cacb', 'caeb', 'canb', 'casb',  # California
            'cob',                    # Colorado
            'ctb',                    # Connecticut
            'deb',                    # Delaware
            'dcb',                    # District of Columbia
            'flmb', 'flnb', 'flsb',   # Florida
            'gamb', 'ganb', 'gasb',   # Georgia
            'hib',                    # Hawaii
            'idb',                    # Idaho
            'ilcb', 'ilnb', 'ilsb',   # Illinois
            'innb', 'insb',           # Indiana
            'ianb', 'iasb',           # Iowa
            'ksb',                    # Kansas
            'kyeb', 'kywb',           # Kentucky
            'laeb', 'lamb', 'lawb',   # Louisiana
            'meb',                    # Maine
            'mdb',                    # Maryland
            'mab',                    # Massachusetts
            'mieb', 'miwb',           # Michigan
            'mnb',                    # Minnesota
            'msnb', 'mssb',           # Mississippi
            'moeb', 'mowb',           # Missouri
            'mtb',                    # Montana
            'neb',                    # Nebraska
            'nvb',                    # Nevada
            'nhb',                    # New Hampshire
            'njb',                    # New Jersey
            'nmb',                    # New Mexico
            'nyeb', 'nynb', 'nysb', 'nywb',  # New York
            'nceb', 'ncmb', 'ncwb',   # North Carolina
            'ndb',                    # North Dakota
            'ohnb', 'ohsb',           # Ohio
            'okeb', 'oknb', 'okwb',   # Oklahoma
            'orb',                    # Oregon
            'paeb', 'pamb', 'pawb',   # Pennsylvania
            'rib',                    # Rhode Island
            'scb',                    # South Carolina
            'sdb',                    # South Dakota
            'tneb', 'tnmb', 'tnwb',   # Tennessee
            'txeb', 'txnb', 'txsb', 'txwb',  # Texas
            'utb',                    # Utah
            'vtb',                    # Vermont
            'vaeb', 'vawb',           # Virginia
            'waeb', 'wawb',           # Washington
            'wvnb', 'wvsb',           # West Virginia
            'wieb', 'wiwb',           # Wisconsin
            'wyb',                    # Wyoming
            'prb', 'vib', 'gub', 'nmib'  # Territories
        ]

        # District courts (end with 'd')
        district_courts = [
            'almd', 'alnd', 'alsd',   # Alabama
            'akd',                    # Alaska
            'azd',                    # Arizona
            'ared', 'arwd',           # Arkansas
            'cacd', 'caed', 'cand', 'casd',  # California
            'cod',                    # Colorado
            'ctd',                    # Connecticut
            'ded',                    # Delaware
            'dcd',                    # District of Columbia
            'flmd', 'flnd', 'flsd',   # Florida
            'gamd', 'gand', 'gasd',   # Georgia
            'hid',                    # Hawaii
            'idd',                    # Idaho
            'ilcd', 'ilnd', 'ilsd',   # Illinois
            'innd', 'insd',           # Indiana
            'iand', 'iasd',           # Iowa
            'ksd',                    # Kansas
            'kyed', 'kywd',           # Kentucky
            'laed', 'lamd', 'lawd',   # Louisiana
            'med',                    # Maine
            'mdd',                    # Maryland
            'mad',                    # Massachusetts
            'mied', 'miwd',           # Michigan
            'mnd',                    # Minnesota
            'msnd', 'mssd',           # Mississippi
            'moed', 'mowd',           # Missouri
            'mtd',                    # Montana
            'ned',                    # Nebraska
            'nvd',                    # Nevada
            'nhd',                    # New Hampshire
            'njd',                    # New Jersey
            'nmd',                    # New Mexico
            'nyed', 'nynd', 'nysd', 'nywd',  # New York
            'nced', 'ncmd', 'ncwd',   # North Carolina
            'ndd',                    # North Dakota
            'ohnd', 'ohsd',           # Ohio
            'oked', 'oknd', 'okwd',   # Oklahoma
            'ord',                    # Oregon
            'paed', 'pamd', 'pawd',   # Pennsylvania
            'rid',                    # Rhode Island
            'scd',                    # South Carolina
            'sdd',                    # South Dakota
            'tned', 'tnmd', 'tnwd',   # Tennessee
            'txed', 'txnd', 'txsd', 'txwd',  # Texas
            'utd',                    # Utah
            'vtd',                    # Vermont
            'vaed', 'vawd',           # Virginia
            'waed', 'wawd',           # Washington
            'wvnd', 'wvsd',           # West Virginia
            'wied', 'wiwd',           # Wisconsin
            'wyd',                    # Wyoming
            'prd', 'vid', 'gud', 'nmid'  # Territories
        ]

        # Circuit courts (Courts of Appeals)
        circuit_courts = [
            'ca1', 'ca2', 'ca3', 'ca4', 'ca5', 'ca6',
            'ca7', 'ca8', 'ca9', 'ca10', 'ca11',
            'cadc', 'cafc'  # DC Circuit and Federal Circuit
        ]

        if court_type == 'bankruptcy':
            return bankruptcy_courts
        elif court_type == 'district':
            return district_courts
        elif court_type == 'circuit':
            return circuit_courts
        else:
            return []

    async def search_dockets(
        self,
        query: Optional[str] = None,
        court_id: Optional[str] = None,
        court_type: Optional[str] = None,
        case_number: Optional[str] = None,
        party_name: Optional[str] = None,
        filed_after: Optional[str] = None,
        filed_before: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Search for dockets (cases) in CourtListener.

        Args:
            query: General search query
            court_id: Court identifier (e.g., 'ca9', 'nysd')
            court_type: Court type filter ('bankruptcy', 'district', 'circuit')
            case_number: Case number
            party_name: Name of party in case
            filed_after: Date filed after (YYYY-MM-DD)
            filed_before: Date filed before (YYYY-MM-DD)
            page: Page number
            page_size: Results per page

        Returns:
            Search results with dockets
        """
        try:
            # Build search parameters
            params = {
                "type": "r",  # RECAP (dockets)
                "page": page,
                "page_size": min(page_size, 100)
            }

            # Build query string
            query_parts = []
            if query:
                query_parts.append(query)
            if case_number:
                query_parts.append(f"docketNumber:{case_number}")
            if party_name:
                query_parts.append(f'party:"{party_name}"')
            if court_id:
                # Single specific court
                params["court"] = court_id
            elif court_type:
                # Filter by court type - use CourtListener's court parameter
                # This filters server-side for better results
                court_codes = self._get_courts_by_type(court_type)
                if court_codes:
                    params["court"] = " ".join(court_codes)
                    logger.info(f"Filtering by court type '{court_type}' with {len(court_codes)} courts")
            if filed_after:
                query_parts.append(f"dateFiled:[{filed_after} TO *]")
            elif filed_before:
                query_parts.append(f"dateFiled:[* TO {filed_before}]")

            if query_parts:
                params["q"] = " AND ".join(query_parts)

            logger.info(f"CourtListener search: {params}")
            logger.info(f"CourtListener search URL: {self.base_url}/search/")

            async with httpx.AsyncClient(
                timeout=self.timeout,
                trust_env=True,  # Trust system proxy settings
                follow_redirects=True
            ) as client:
                logger.info("Making request to CourtListener...")
                response = await client.get(
                    f"{self.base_url}/search/",
                    params=params,
                    headers=self._get_headers()
                )
                logger.info(f"Response received: {response.status_code}")

                response.raise_for_status()
                data = response.json()

                return {
                    "success": True,
                    "count": data.get("count", 0),
                    "results": data.get("results", []),
                    "next": data.get("next"),
                    "previous": data.get("previous")
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"CourtListener API error: {e.response.status_code}")
            raise CourtListenerServiceError(f"Search failed: {e.response.status_code}")
        except httpx.TimeoutException as e:
            logger.error(f"CourtListener API timeout: {e}")
            raise CourtListenerServiceError("CourtListener API request timed out. The service may be slow or unavailable. Please try again.")
        except Exception as e:
            import traceback
            logger.error(f"CourtListener search error: {type(e).__name__}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            error_msg = str(e) if str(e) else f"{type(e).__name__}"
            raise CourtListenerServiceError(f"Search failed: {error_msg}")

    async def get_docket_details(self, docket_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific docket.

        Args:
            docket_id: CourtListener docket ID

        Returns:
            Detailed docket information including entries and documents
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/dockets/{docket_id}/",
                    headers=self._get_headers()
                )

                response.raise_for_status()
                return {
                    "success": True,
                    "docket": response.json()
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"CourtListener API error: {e.response.status_code}")
            raise CourtListenerServiceError(f"Failed to get docket: {e.response.status_code}")
        except Exception as e:
            logger.error(f"CourtListener error: {e}")
            raise CourtListenerServiceError(f"Failed to get docket: {str(e)}")

    async def monitor_case(self, docket_id: int, user_id: str, case_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start monitoring a case for new documents for a specific user.
        Persists to database so monitoring survives server restarts.

        Args:
            docket_id: CourtListener docket ID to monitor
            user_id: User ID who is monitoring this case (will be converted to integer)
            case_metadata: Optional case metadata (if provided, bypasses CourtListener API fetch)

        Returns:
            Dictionary with case details
        """
        # Convert user_id to integer if it's a string (for database consistency)
        # This handles both JWT tokens that send integer IDs and legacy string IDs
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid user_id format: {user_id}, cannot monitor case")
            raise ValueError(f"User ID must be an integer or convertible to integer, got: {user_id}")

        # Use provided case metadata OR fetch from CourtListener
        if case_metadata:
            logger.info(f"Using provided case metadata for docket {docket_id}")
            docket = case_metadata
        else:
            logger.info(f"Fetching case details from CourtListener API for docket {docket_id}")
            docket_result = await self.get_docket_details(docket_id)
            docket = docket_result.get("docket", {})

        # Find or create TrackedDocket
        tracked_docket = self.db.query(TrackedDocket).filter(
            TrackedDocket.courtlistener_docket_id == docket_id
        ).first()

        if not tracked_docket:
            # Create new TrackedDocket entry
            tracked_docket = TrackedDocket(
                docket_number=docket.get("docket_number", ""),
                court_id=docket.get("court_id", "unknown"),
                court_name=docket.get("court", "Unknown Court"),
                case_name=docket.get("case_name", ""),
                courtlistener_docket_id=docket_id,
                courtlistener_last_fetch=datetime.utcnow(),
                date_filed=parse_date_to_naive_datetime(docket.get("date_filed")),
            )
            self.db.add(tracked_docket)
            self.db.flush()  # Get the ID without committing

        # Find or create UserDocketMonitor
        monitor = self.db.query(UserDocketMonitor).filter(
            UserDocketMonitor.user_id == user_id_int,  # Use integer user_id
            UserDocketMonitor.tracked_docket_id == tracked_docket.id
        ).first()

        if monitor:
            # Reactivate if it was stopped
            # IMPORTANT: Don't reset last_checked_at - preserve the tracking baseline
            # so we can detect all documents filed since monitoring started.
            # The background monitoring service will update last_checked_at after checking.
            monitor.is_active = True
            monitor.stopped_monitoring_at = None
        else:
            # Create new monitor entry
            monitor = UserDocketMonitor(
                user_id=user_id_int,  # Use integer user_id
                tracked_docket_id=tracked_docket.id,
                case_name=docket.get("case_name", ""),
                docket_number=docket.get("docket_number", ""),
                court_name=docket.get("court", ""),
                date_filed=parse_date_to_naive_datetime(docket.get("date_filed")),
                courtlistener_docket_id=docket_id,
                courtlistener_absolute_url=docket.get("absolute_url", ""),
                started_monitoring_at=datetime.utcnow(),
                last_checked_at=datetime.utcnow()
            )
            self.db.add(monitor)

        self.db.commit()

        logger.info(f"User {user_id_int} started monitoring docket {docket_id}: {docket.get('case_name', 'Unknown')}")

        # Return case details in expected format
        case_details = {
            "docket_id": docket_id,
            "case_name": docket.get("case_name", ""),
            "docket_number": docket.get("docket_number", ""),
            "court": docket.get("court_id", ""),
            "date_filed": docket.get("date_filed"),
            "absolute_url": docket.get("absolute_url", ""),
            "started_monitoring": monitor.started_monitoring_at.isoformat()
        }

        return case_details

    async def check_for_updates(self, docket_id: int, user_id: str) -> Dict[str, Any]:
        """
        Check if a monitored case has new documents for a specific user.
        Uses database persistence for reliable tracking across server restarts.

        Args:
            docket_id: CourtListener docket ID
            user_id: User ID who is monitoring this case

        Returns:
            Dictionary with new_documents flag and list of new documents
        """
        try:
            # Convert user_id to integer for database consistency
            try:
                user_id_int = int(user_id)
            except (ValueError, TypeError):
                logger.error(f"Invalid user_id format: {user_id}")
                return {"new_documents": False, "documents": []}

            # Query database for user's monitor of this docket
            monitor = self.db.query(UserDocketMonitor).join(TrackedDocket).filter(
                UserDocketMonitor.user_id == user_id_int,
                TrackedDocket.courtlistener_docket_id == docket_id,
                UserDocketMonitor.is_active == True
            ).first()

            if not monitor:
                return {"new_documents": False, "documents": [], "message": "Not monitoring this case"}

            last_check = monitor.last_checked_at

            # Get current docket state from CourtListener
            result = await self.get_docket_details(docket_id)
            docket = result.get("docket", {})

            # Check for documents added after last check
            new_docs = []
            for entry in docket.get("docket_entries", []):
                entry_date = entry.get("date_filed")
                if entry_date:
                    entry_datetime = parse_date_to_naive_datetime(entry_date)
                    if entry_datetime and last_check and entry_datetime > last_check:
                        new_docs.extend(entry.get("recap_documents", []))

            # Update last check time in database
            monitor.last_checked_at = datetime.utcnow()
            self.db.commit()

            return {
                "new_documents": len(new_docs) > 0,
                "documents": new_docs,
                "count": len(new_docs)
            }

        except Exception as e:
            logger.error(f"Error checking updates for docket {docket_id} (user {user_id}): {e}")
            return {"new_documents": False, "documents": [], "error": str(e)}

    async def get_monitored_cases_updates(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Check all monitored cases for updates for a specific user.
        Uses database persistence for reliable tracking across server restarts.

        Args:
            user_id: User ID to check updates for

        Returns:
            List of cases with new documents
        """
        updates = []

        # Convert user_id to integer for database consistency
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid user_id format: {user_id}")
            return []

        # Query database for all active monitors for this user
        monitors = self.db.query(UserDocketMonitor).filter(
            UserDocketMonitor.user_id == user_id_int,
            UserDocketMonitor.is_active == True
        ).all()

        if not monitors:
            return []

        for monitor in monitors:
            try:
                docket_id = monitor.courtlistener_docket_id
                if docket_id:
                    result = await self.check_for_updates(docket_id, user_id)

                    if result.get("new_documents"):
                        updates.append({
                            "docket_id": docket_id,
                            "case_name": monitor.case_name,
                            "docket_number": monitor.docket_number,
                            **result
                        })

            except Exception as e:
                logger.error(f"Error checking docket {monitor.courtlistener_docket_id} for user {user_id}: {e}")

        return updates

    async def search_opinions(
        self,
        query: str,
        court_id: Optional[str] = None,
        filed_after: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Search for court opinions/case law.

        Args:
            query: Search query
            court_id: Court identifier
            filed_after: Date filed after
            page: Page number
            page_size: Results per page

        Returns:
            Search results with opinions
        """
        try:
            params = {
                "type": "o",  # Opinions
                "q": query,
                "page": page,
                "page_size": min(page_size, 100)
            }

            if court_id:
                params["q"] += f" court:{court_id}"
            if filed_after:
                params["q"] += f" dateFiled:[{filed_after} TO *]"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/search/",
                    params=params,
                    headers=self._get_headers()
                )

                response.raise_for_status()
                data = response.json()

                return {
                    "success": True,
                    "count": data.get("count", 0),
                    "results": data.get("results", []),
                    "next": data.get("next"),
                    "previous": data.get("previous")
                }

        except Exception as e:
            logger.error(f"CourtListener opinion search error: {e}")
            raise CourtListenerServiceError(f"Opinion search failed: {str(e)}")

    async def get_monitored_cases_list(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get list of currently monitored cases with full details for a specific user.
        Reads from database for persistence across server restarts.

        Args:
            user_id: User ID to get monitored cases for (will be converted to integer)

        Returns:
            List of monitored cases with case details and monitoring info
        """
        # Convert user_id to integer for database consistency
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid user_id format: {user_id}, cannot get monitored cases")
            return []  # Return empty list for invalid user IDs

        # Query database for active monitors
        monitors = self.db.query(UserDocketMonitor).filter(
            UserDocketMonitor.user_id == user_id_int,
            UserDocketMonitor.is_active == True
        ).all()

        logger.info(f"get_monitored_cases_list called for user {user_id_int}. Total monitored: {len(monitors)}")

        result = []
        for monitor in monitors:
            monitoring_duration = (datetime.utcnow() - monitor.started_monitoring_at).total_seconds() / 3600

            result.append({
                "docket_id": monitor.courtlistener_docket_id,
                "case_name": monitor.case_name or "Unknown Case",
                "docket_number": monitor.docket_number or "",
                "court": monitor.court_name or "",
                "date_filed": monitor.date_filed.isoformat() if monitor.date_filed else None,
                "absolute_url": monitor.courtlistener_absolute_url or "",
                "last_checked": monitor.last_checked_at.isoformat(),
                "started_monitoring": monitor.started_monitoring_at.isoformat(),
                "monitoring_duration_hours": round(monitoring_duration, 2)
            })

        logger.info(f"Returning {len(result)} monitored cases for user {user_id}")
        return result

    def stop_monitoring(self, docket_id: int, user_id: str) -> bool:
        """
        Stop monitoring a case for a specific user.
        Updates database to deactivate monitoring.

        Args:
            docket_id: Docket ID to stop monitoring
            user_id: User ID who wants to stop monitoring (will be converted to integer)

        Returns:
            True if stopped, False if wasn't being monitored
        """
        # Convert user_id to integer for database consistency
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid user_id format: {user_id}, cannot stop monitoring")
            return False

        # Find the monitor entry
        monitor = self.db.query(UserDocketMonitor).join(TrackedDocket).filter(
            UserDocketMonitor.user_id == user_id_int,
            TrackedDocket.courtlistener_docket_id == docket_id,
            UserDocketMonitor.is_active == True
        ).first()

        if monitor:
            monitor.is_active = False
            monitor.stopped_monitoring_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"User {user_id_int} stopped monitoring docket {docket_id}")
            return True

        return False

    async def get_docket_with_documents(self, docket_id: int, max_retries: int = 3) -> Dict[str, Any]:
        """
        Get docket details with full document information from RECAP.

        CORRECT APPROACH - Using Docket-Entries Endpoint:
        ==================================================
        The CourtListener /dockets/{id}/ endpoint does NOT include docket_entries.
        The correct way to get all documents is:
        1. Call /dockets/{docket_id}/ to get docket metadata
        2. Call /docket-entries/?docket={docket_id} to get all entries
        3. Each entry has a "recap_documents" field containing documents
        4. Flatten all recap_documents from all entries into a single list

        Args:
            docket_id: CourtListener docket ID
            max_retries: Maximum number of retry attempts for transient errors (502, 503, 504)

        Returns:
            Dictionary with docket info and documents list

        Raises:
            CourtListenerServiceError: If API call fails after all retries
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching docket {docket_id} with all documents (attempt {attempt + 1}/{max_retries})")

                # Step 1: Get the docket metadata
                docket_result = await self.get_docket_details(docket_id)
                docket = docket_result.get("docket", {})

                # Step 2: Get all docket entries from the docket-entries endpoint
                all_documents = []
                page = 1
                max_pages = 50

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # Fetch docket entries - use docket= parameter (not docket_id=)
                    # Use -date_filed to get newest entries first (more efficient for monitoring)
                    # Note: -entry_number doesn't work correctly with CourtListener API
                    url = f"{self.base_url}/docket-entries/?docket={docket_id}&order_by=-date_filed"

                    while url and page <= max_pages:
                        logger.info(f"Fetching docket entries page {page}: {url}")

                        response = await client.get(url, headers=self._get_headers())
                        response.raise_for_status()

                        data = response.json()
                        entries = data.get("results", [])

                        # Log API's reported count on first page
                        if page == 1:
                            api_count = data.get("count")
                            logger.info(f"⚠️ API reports {api_count} total entries for this docket")

                        if not entries:
                            logger.info(f"No more entries found at page {page}")
                            break

                        logger.info(f"Page {page}: Found {len(entries)} docket entries")

                        # Log how many documents in these entries
                        docs_in_page = sum(len(e.get("recap_documents", [])) for e in entries)
                        logger.info(f"Page {page}: These entries contain {docs_in_page} documents")

                        # Process each entry's documents
                        for entry in entries:
                            entry_number = entry.get("entry_number")
                            entry_date_filed = entry.get("date_filed")
                            entry_date_created = entry.get("date_created")  # Full timestamp when added to CourtListener
                            recap_documents = entry.get("recap_documents", [])

                            # Process each document in this entry
                            for doc in recap_documents:
                                # Add availability info
                                doc["is_available"] = bool(doc.get("filepath_local") or doc.get("ia_upload_failure_count") == 0)
                                doc["cost_estimate"] = 0.0 if doc["is_available"] else ((doc.get("page_count") or 10) * 0.10)

                                # Add entry information for context
                                doc["entry_number"] = entry_number
                                doc["entry_date_filed"] = entry_date_filed
                                doc["entry_date_created"] = entry_date_created  # Full timestamp for accurate monitoring

                                # Add to final list
                                all_documents.append(doc)

                        # Get next page URL
                        url = data.get("next")
                        page += 1

                logger.info(f"✓ Extracted {len(all_documents)} total documents from docket {docket_id}")

                # Validation: Warn if we got 0 documents
                if len(all_documents) == 0:
                    logger.warning(f"⚠️ WARNING: Got 0 documents for docket {docket_id}")
                    logger.warning(f"⚠️ This may indicate:")
                    logger.warning(f"   1. Docket has no documents filed")
                    logger.warning(f"   2. API endpoint is not working correctly")
                    logger.warning(f"   3. Wrong API endpoint being used")
                    logger.warning(f"⚠️ Expected endpoint: /docket-entries/?docket={docket_id}")

                return {
                    "success": True,
                    "docket": docket,
                    "documents": all_documents,
                    "total_documents": len(all_documents),
                    "free_documents": sum(1 for d in all_documents if d["is_available"]),
                    "estimated_total_cost": sum(d["cost_estimate"] for d in all_documents)
                }

            except httpx.HTTPStatusError as e:
                last_error = e
                status_code = e.response.status_code

                # Retry on transient server errors (502, 503, 504)
                if status_code in (502, 503, 504) and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2  # Exponential backoff: 2s, 4s, 8s
                    logger.warning(f"Docket API error {status_code} for docket {docket_id}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue

                logger.error(f"Docket API error: {status_code} for docket {docket_id} (after {attempt + 1} attempts)")

                # Build CourtListener web URL for viewing documents
                absolute_url = f"/docket/{docket_id}/"
                courtlistener_url = f"https://www.courtlistener.com{absolute_url}"

                return {
                    "success": False,
                    "docket": {},
                    "documents": [],
                    "error": f"Failed to fetch docket: HTTP {status_code}",
                    "api_limitation": True,
                    "courtlistener_url": courtlistener_url,
                    "message": "To view documents for this case, please visit CourtListener's website"
                }

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                # Retry on network errors
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    logger.warning(f"Network error for docket {docket_id}: {type(e).__name__}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue

                logger.error(f"Network error fetching docket {docket_id} after {max_retries} attempts: {e}")
                return {
                    "success": False,
                    "docket": {},
                    "documents": [],
                    "error": f"Network error: {type(e).__name__}",
                    "message": "Unable to connect to CourtListener. Please try again later."
                }

            except Exception as e:
                logger.error(f"Error fetching docket with documents: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise CourtListenerServiceError(f"Failed to get documents: {str(e)}")

        # Should not reach here, but just in case
        logger.error(f"All {max_retries} attempts failed for docket {docket_id}")
        return {
            "success": False,
            "docket": {},
            "documents": [],
            "error": f"All retry attempts failed",
            "message": "CourtListener API is currently unavailable. Please try again later."
        }

    async def download_recap_document(self, document_id: int) -> Dict[str, Any]:
        """
        Download a free document from RECAP archive.

        Args:
            document_id: RECAP document ID

        Returns:
            Dictionary with download URL and document info
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get document details first
                response = await client.get(
                    f"{self.base_url}/recap-documents/{document_id}/",
                    headers=self._get_headers()
                )

                response.raise_for_status()
                doc = response.json()

                # Check if document is available
                if not (doc.get("filepath_local") or doc.get("is_available")):
                    return {
                        "success": False,
                        "error": "Document not available in RECAP archive",
                        "pacer_doc_id": doc.get("pacer_doc_id"),
                        "cost_estimate": ((doc.get("page_count") or 10) * 0.10)
                    }

                # Build download URL
                filepath = doc.get('filepath_local', '')
                # Ensure leading slash
                if filepath and not filepath.startswith('/'):
                    filepath = '/' + filepath
                download_url = f"https://www.courtlistener.com{filepath}"

                return {
                    "success": True,
                    "document_id": document_id,
                    "description": doc.get("description") or doc.get("short_description", ""),
                    "page_count": doc.get("page_count"),
                    "download_url": download_url,
                    "is_free": True,
                    "cost": 0.0,
                    "source": "RECAP"
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"RECAP document fetch error: {e.response.status_code}")
            raise CourtListenerServiceError(f"Document not found: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error downloading RECAP document: {e}")
            raise CourtListenerServiceError(f"Download failed: {str(e)}")

    async def download_recap_to_storage(self, document_id: int, save_path: str) -> Dict[str, Any]:
        """
        Download a FREE RECAP document directly to app storage.

        This is the bridge method that:
        1. Fetches document metadata from CourtListener API
        2. Downloads the actual PDF file from PUBLIC URL (no auth required!)
        3. Saves to local storage
        4. Returns file info for analysis pipeline

        Args:
            document_id: RECAP document ID from CourtListener
            save_path: Local path to save the downloaded PDF

        Returns:
            Dictionary with file path, size, metadata, and success status
        """
        try:
            logger.info(f"Starting RECAP document download to storage: ID={document_id}")

            # Create client with trust environment enabled for Windows compatibility
            async with httpx.AsyncClient(
                timeout=self.timeout,
                trust_env=True,  # Trust system proxy settings
                follow_redirects=True
            ) as client:
                # Step 1: Get document metadata from API
                response = await client.get(
                    f"{self.base_url}/recap-documents/{document_id}/",
                    headers=self._get_headers()
                )

                response.raise_for_status()
                doc = response.json()

                # Check if document is available for free download
                filepath_local = doc.get("filepath_local")
                if not filepath_local:
                    logger.warning(f"Document {document_id} not available in RECAP archive")
                    return {
                        "success": False,
                        "error": "Document not available in RECAP archive - may need to purchase from PACER",
                        "pacer_doc_id": doc.get("pacer_doc_id"),
                        "cost_estimate": ((doc.get("page_count") or 10) * 0.10),
                        "can_purchase": True
                    }

                # Step 2: Download the actual PDF from CourtListener
                # These are PUBLIC documents - download as a browser would (no API auth)
                # Ensure leading slash for proper URL construction
                if filepath_local and not filepath_local.startswith('/'):
                    filepath_local = '/' + filepath_local
                download_url = f"https://www.courtlistener.com{filepath_local}"
                logger.info(f"Downloading PDF as browser (public access): {download_url}")

                # Use browser-like headers for public PDF download (no API token)
                browser_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/pdf,*/*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Referer": "https://www.courtlistener.com/",
                    "Connection": "keep-alive"
                }

                try:
                    pdf_response = await client.get(download_url, headers=browser_headers, follow_redirects=True)
                    pdf_response.raise_for_status()
                except Exception as download_error:
                    logger.error(f"Failed to download PDF from {download_url}: {type(download_error).__name__}: {download_error}")
                    raise

                # Step 3: Save to local storage
                import os
                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                with open(save_path, 'wb') as f:
                    f.write(pdf_response.content)

                file_size = len(pdf_response.content)
                logger.info(f"Successfully downloaded RECAP document to {save_path} ({file_size} bytes)")

                # Step 4: Return complete metadata
                return {
                    "success": True,
                    "document_id": document_id,
                    "file_path": save_path,
                    "file_size": file_size,
                    "description": doc.get("description") or doc.get("short_description", ""),
                    "page_count": doc.get("page_count"),
                    "docket_id": doc.get("docket_id"),
                    "document_number": doc.get("document_number"),
                    "attachment_number": doc.get("attachment_number"),
                    "pacer_doc_id": doc.get("pacer_doc_id"),
                    "date_filed": doc.get("date_filed"),
                    "content_type": pdf_response.headers.get("content-type"),
                    "is_free": True,
                    "cost": 0.0,
                    "source": "RECAP",
                    "message": "Document downloaded successfully and ready for analysis"
                }

        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.json()
            except:
                error_detail = e.response.text[:200] if hasattr(e.response, 'text') else ""

            logger.error(f"HTTP error downloading RECAP document {document_id}: {e.response.status_code}")
            logger.error(f"Error details: {error_detail}")

            if e.response.status_code == 403:
                raise CourtListenerServiceError(
                    "ACCESS_RESTRICTED: This document requires a paid CourtListener API subscription for bulk downloads. "
                    f"You can view it FREE on the website: https://www.courtlistener.com/recap-documents/{document_id}/ "
                    "To download many documents, consider upgrading your CourtListener API subscription at https://www.courtlistener.com/donate/"
                )
            else:
                raise CourtListenerServiceError(f"Failed to download document: {e.response.status_code} - {error_detail}")
        except Exception as e:
            import traceback
            logger.error(f"Error downloading RECAP document {document_id} to storage: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")

            # Provide more helpful error messages
            error_msg = str(e)
            if "getaddrinfo failed" in error_msg or "11001" in error_msg:
                raise CourtListenerServiceError(
                    "Network DNS resolution error. Please check your internet connection and try again. "
                    f"If the problem persists, the document may need to be accessed directly at: "
                    f"https://www.courtlistener.com/recap-documents/{document_id}/"
                )
            else:
                raise CourtListenerServiceError(f"Download failed: {error_msg}")

    async def purchase_pacer_document(
        self,
        pacer_case_id: Optional[str] = None,
        pacer_doc_id: Optional[str] = None,
        docket_number: Optional[str] = None,
        court: Optional[str] = None,
        document_number: Optional[int] = None,
        attachment_number: Optional[int] = None,
        request_type: int = 2,  # 1=docket, 2=pdf, 3=attachment_page
        pacer_username: Optional[str] = None,
        pacer_password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Purchase and download a document from PACER using CourtListener's RECAP Fetch API.

        This is an asynchronous operation that:
        1. Submits a purchase request to CourtListener
        2. CourtListener uses your PACER credentials to buy the document
        3. Returns a request ID for polling status

        Args:
            pacer_case_id: PACER case ID
            pacer_doc_id: PACER document ID
            docket_number: Docket number
            court: Court identifier (e.g., 'cand', 'nysd')
            document_number: Document number on docket
            attachment_number: Attachment number (if any)
            request_type: 1=docket report, 2=PDF download, 3=attachment page
            pacer_username: PACER account username
            pacer_password: PACER account password

        Returns:
            Dictionary with request ID and status
        """
        try:
            if not self.api_key:
                raise CourtListenerServiceError("CourtListener API key required for RECAP Fetch API")

            if not pacer_username or not pacer_password:
                raise CourtListenerServiceError("PACER credentials required to purchase documents")

            # Build request payload
            payload = {
                "request_type": request_type,
                "pacer_username": pacer_username,
                "pacer_password": pacer_password
            }

            # Add document identifiers
            if pacer_case_id:
                payload["pacer_case_id"] = pacer_case_id
            if pacer_doc_id:
                payload["pacer_doc_id"] = pacer_doc_id
            if docket_number:
                payload["docket_number"] = docket_number
            if court:
                payload["court"] = court
            if document_number:
                payload["document_number"] = document_number
            if attachment_number:
                payload["attachment_number"] = attachment_number

            logger.info(f"Submitting RECAP Fetch request: type={request_type}, court={court}, doc={document_number}")

            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                response = await client.post(
                    f"{self.base_url}/recap-fetch/",
                    json=payload,
                    headers=self._get_headers()
                )

                response.raise_for_status()
                data = response.json()

                logger.info(f"RECAP Fetch request submitted: ID={data.get('id')}")

                return {
                    "success": True,
                    "request_id": data.get("id"),
                    "status": data.get("status"),
                    "message": "Document purchase request submitted. Use request_id to check status.",
                    "request_type": request_type
                }

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            logger.error(f"RECAP Fetch API error {e.response.status_code}: {error_detail}")
            raise CourtListenerServiceError(f"Failed to submit purchase request: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error submitting RECAP Fetch request: {e}")
            raise CourtListenerServiceError(f"Purchase request failed: {str(e)}")

    async def check_fetch_status(self, request_id: int) -> Dict[str, Any]:
        """
        Check the status of a RECAP Fetch request.

        Args:
            request_id: The ID returned from purchase_pacer_document

        Returns:
            Dictionary with status, document URL if complete, and error info if failed
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/recap-fetch/{request_id}/",
                    headers=self._get_headers()
                )

                response.raise_for_status()
                data = response.json()

                status = data.get("status")
                result = {
                    "success": True,
                    "request_id": request_id,
                    "status": status,
                    "message": data.get("message", "")
                }

                # Status codes: 1=processing, 2=success, 3=failed, 4=queued
                if status == 2:  # Completed successfully
                    result["completed"] = True
                    result["document_url"] = data.get("filepath_local")
                    result["pacer_case_id"] = data.get("pacer_case_id")
                    result["pacer_doc_id"] = data.get("pacer_doc_id")
                    result["cost"] = data.get("cost")
                elif status == 3:  # Failed
                    result["completed"] = True
                    result["failed"] = True
                    result["error"] = data.get("error_message")
                else:  # Still processing or queued
                    result["completed"] = False
                    result["message"] = "Request is still processing"

                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"Error checking fetch status: {e.response.status_code}")
            raise CourtListenerServiceError(f"Failed to check status: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error checking fetch status: {e}")
            raise CourtListenerServiceError(f"Status check failed: {str(e)}")

    async def check_document_availability(
        self,
        court: str,
        pacer_doc_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Check if PACER documents are already available for free in the RECAP Archive.

        This should be called BEFORE purchasing to avoid charging users for documents
        that have become freely available.

        Uses the RECAP Query API: /api/rest/v4/recap-query/

        Args:
            court: Court identifier (e.g., 'cand', 'nysd', 'dcd')
            pacer_doc_ids: List of PACER document IDs to check

        Returns:
            Dictionary mapping pacer_doc_id -> availability info:
            {
                "pacer_doc_id": {
                    "is_available": bool,  # True if free in RECAP
                    "filepath_local": str,  # If available, path to download
                    "recap_document_id": int  # CourtListener document ID
                }
            }
        """
        try:
            if not self.api_key:
                logger.warning("No API key - RECAP Query may have limited access")

            # Build query parameters
            doc_ids_str = ",".join(pacer_doc_ids)

            logger.info(f"Checking RECAP availability for {len(pacer_doc_ids)} documents in court {court}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/recap-query/",
                    params={
                        "court": court,
                        "pacer_doc_id__in": doc_ids_str
                    },
                    headers=self._get_headers()
                )

                response.raise_for_status()
                data = response.json()

                # Parse results into a lookup dictionary
                results = {}

                # The API returns a list of available documents
                for doc in data.get("results", []):
                    pacer_doc_id = str(doc.get("pacer_doc_id", ""))

                    results[pacer_doc_id] = {
                        "is_available": doc.get("is_available", False),
                        "filepath_local": doc.get("filepath_local"),
                        "recap_document_id": doc.get("id"),
                        "page_count": doc.get("page_count"),
                        "description": doc.get("description")
                    }

                # For documents not in results, mark as not available
                for doc_id in pacer_doc_ids:
                    if doc_id not in results:
                        results[doc_id] = {
                            "is_available": False,
                            "filepath_local": None,
                            "recap_document_id": None
                        }

                logger.info(
                    f"RECAP Query results: {sum(1 for r in results.values() if r['is_available'])} "
                    f"of {len(pacer_doc_ids)} documents are freely available"
                )

                return {
                    "success": True,
                    "court": court,
                    "results": results,
                    "checked_count": len(pacer_doc_ids),
                    "available_count": sum(1 for r in results.values() if r["is_available"])
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"RECAP Query API error {e.response.status_code}: {e.response.text}")
            # Don't fail the purchase if this check fails - just log and continue
            return {
                "success": False,
                "error": f"Availability check failed: {e.response.status_code}",
                "results": {doc_id: {"is_available": False} for doc_id in pacer_doc_ids}
            }
        except Exception as e:
            logger.error(f"Error checking document availability: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": {doc_id: {"is_available": False} for doc_id in pacer_doc_ids}
            }

    async def download_purchased_document(self, filepath_local: str, save_path: str) -> Dict[str, Any]:
        """
        Download a purchased document from CourtListener to local storage.

        Args:
            filepath_local: The filepath_local returned from check_fetch_status
            save_path: Local path to save the downloaded file

        Returns:
            Dictionary with download info
        """
        try:
            # Ensure leading slash for proper URL construction
            if filepath_local and not filepath_local.startswith('/'):
                filepath_local = '/' + filepath_local
            download_url = f"https://www.courtlistener.com{filepath_local}"

            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
                response = await client.get(download_url, headers=self._get_headers())
                response.raise_for_status()

                # Save to file
                import os
                os.makedirs(os.path.dirname(save_path), exist_ok=True)

                with open(save_path, 'wb') as f:
                    f.write(response.content)

                file_size = len(response.content)
                logger.info(f"Downloaded document to {save_path} ({file_size} bytes)")

                return {
                    "success": True,
                    "file_path": save_path,
                    "file_size": file_size,
                    "content_type": response.headers.get("content-type"),
                    "message": "Document downloaded successfully"
                }

        except Exception as e:
            logger.error(f"Error downloading document: {e}")
            raise CourtListenerServiceError(f"Download failed: {str(e)}")


