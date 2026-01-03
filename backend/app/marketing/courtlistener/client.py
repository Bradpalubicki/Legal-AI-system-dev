"""
CourtListener API Client

REST API v4 client for CourtListener with rate limiting,
pagination support, and retry logic.

API Docs: https://www.courtlistener.com/help/api/rest/
"""

import httpx
import asyncio
import logging
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


class CourtListenerClient:
    """
    CourtListener REST API v4 Client

    Handles authentication, rate limiting, pagination, and retries
    for the CourtListener federal court records API.
    """

    BASE_URL = "https://www.courtlistener.com/api/rest/v4"

    def __init__(self, token: Optional[str] = None):
        """
        Initialize the CourtListener client.

        Args:
            token: API token (defaults to COURTLISTENER_API_KEY env var)
        """
        self.token = token or os.getenv('COURTLISTENER_API_KEY') or os.getenv('COURTLISTENER_TOKEN')
        if not self.token:
            logger.warning("No CourtListener API token provided")

        self.headers = {
            "Authorization": f"Token {self.token}" if self.token else "",
            "Content-Type": "application/json"
        }

        # Rate limit tracking
        self.rate_limit_remaining = 5000  # Default hourly limit
        self.rate_limit_reset = None
        self.last_request_time = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Make API request with rate limiting and retries.

        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            params: Query parameters
            retry_count: Current retry attempt
            max_retries: Maximum retry attempts

        Returns:
            API response as dictionary
        """
        # Ensure minimum delay between requests (100ms)
        if self.last_request_time:
            elapsed = (datetime.utcnow() - self.last_request_time).total_seconds()
            if elapsed < 0.1:
                await asyncio.sleep(0.1 - elapsed)

        # Build URL - ensure trailing slash for CourtListener API
        url = f"{self.BASE_URL}/{endpoint.strip('/')}/"

        async with httpx.AsyncClient() as client:
            try:
                self.last_request_time = datetime.utcnow()

                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )

                # Track rate limits from response headers
                if "X-RateLimit-Remaining" in response.headers:
                    self.rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
                if "X-RateLimit-Reset" in response.headers:
                    self.rate_limit_reset = datetime.fromtimestamp(
                        int(response.headers["X-RateLimit-Reset"])
                    )

                # Handle rate limiting
                if response.status_code == 429:
                    if retry_count < max_retries:
                        wait_time = 60  # Default 1 minute
                        if "Retry-After" in response.headers:
                            wait_time = int(response.headers["Retry-After"])
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                        await asyncio.sleep(wait_time)
                        return await self._request(method, endpoint, params, retry_count + 1)
                    raise Exception("Rate limit exceeded after retries")

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e}")
                if retry_count < max_retries and e.response.status_code >= 500:
                    await asyncio.sleep(2 ** retry_count)
                    return await self._request(method, endpoint, params, retry_count + 1)
                raise

            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                if retry_count < max_retries:
                    await asyncio.sleep(2 ** retry_count)
                    return await self._request(method, endpoint, params, retry_count + 1)
                raise

    def _extract_cursor(self, next_url: str) -> Optional[str]:
        """Extract cursor from pagination URL."""
        if not next_url:
            return None
        parsed = urlparse(next_url)
        params = parse_qs(parsed.query)
        return params.get('cursor', [None])[0]

    # ============ DOCKET METHODS ============

    async def search_dockets(
        self,
        q: Optional[str] = None,
        court: Optional[str] = None,
        case_name: Optional[str] = None,
        date_filed_after: Optional[datetime] = None,
        date_filed_before: Optional[datetime] = None,
        nature_of_suit: Optional[str] = None,
        order_by: str = "-date_filed",
        cursor: Optional[str] = None,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Search dockets with filters.

        Args:
            q: Full-text search query
            court: Court ID filter (e.g., 'cacd' for Central District of California)
            case_name: Case name contains filter
            date_filed_after: Filed on or after this date
            date_filed_before: Filed on or before this date
            nature_of_suit: Nature of suit code (e.g., '440' for Civil Rights)
            order_by: Sort order (prefix with '-' for descending)
            cursor: Pagination cursor
            page_size: Results per page

        Returns:
            Paginated results with next/previous cursors
        """
        params = {
            "order_by": order_by,
            "page_size": page_size
        }

        if q:
            params["q"] = q
        if court:
            params["court"] = court
        if case_name:
            params["case_name__icontains"] = case_name
        if date_filed_after:
            params["date_filed__gte"] = date_filed_after.strftime("%Y-%m-%d")
        if date_filed_before:
            params["date_filed__lte"] = date_filed_before.strftime("%Y-%m-%d")
        if nature_of_suit:
            params["nature_of_suit__startswith"] = nature_of_suit
        if cursor:
            params["cursor"] = cursor

        return await self._request("GET", "dockets", params)

    async def get_docket(self, docket_id: int) -> Dict[str, Any]:
        """Get single docket by ID."""
        return await self._request("GET", f"dockets/{docket_id}")

    async def get_recent_dockets(
        self,
        hours_back: int = 24,
        courts: Optional[List[str]] = None,
        nature_of_suits: Optional[List[str]] = None,
        max_results: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get dockets filed in the last N hours.

        Args:
            hours_back: How many hours to look back
            courts: List of court IDs to filter by
            nature_of_suits: List of nature of suit codes
            max_results: Maximum results to return

        Returns:
            List of docket records
        """
        date_after = datetime.utcnow() - timedelta(hours=hours_back)
        all_results = []
        cursor = None

        while len(all_results) < max_results:
            response = await self.search_dockets(
                date_filed_after=date_after,
                court=",".join(courts) if courts else None,
                cursor=cursor,
                page_size=min(100, max_results - len(all_results))
            )

            results = response.get("results", [])

            # Filter by nature of suit if specified
            if nature_of_suits:
                results = [
                    r for r in results
                    if any(
                        r.get("nature_of_suit", "").startswith(nos)
                        for nos in nature_of_suits
                    )
                ]

            all_results.extend(results)

            # Check for more pages
            if not response.get("next"):
                break

            cursor = self._extract_cursor(response["next"])
            if not cursor:
                break

            # Small delay between pages
            await asyncio.sleep(0.1)

        logger.info(f"Retrieved {len(all_results)} dockets from last {hours_back} hours")
        return all_results[:max_results]

    # ============ PARTY METHODS ============

    async def get_parties_for_docket(
        self,
        docket_id: int,
        include_attorneys: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all parties for a docket.

        Note: Party endpoint may require special access from Free Law Project.

        Args:
            docket_id: Docket ID to get parties for
            include_attorneys: Include attorney info in results

        Returns:
            List of party records
        """
        params = {
            "docket": docket_id,
        }

        try:
            response = await self._request("GET", "parties", params)
            return response.get("results", [])
        except Exception as e:
            logger.warning(f"Could not get parties for docket {docket_id}: {e}")
            return []

    # ============ ATTORNEY METHODS ============

    async def get_attorneys_for_docket(self, docket_id: int) -> List[Dict[str, Any]]:
        """
        Get all attorneys for a specific docket.

        Args:
            docket_id: Docket ID to get attorneys for

        Returns:
            List of attorney records with contact info
        """
        params = {"docket": docket_id}

        try:
            response = await self._request("GET", "attorneys", params)
            return response.get("results", [])
        except Exception as e:
            logger.warning(f"Could not get attorneys for docket {docket_id}: {e}")
            return []

    async def search_attorneys(
        self,
        name: Optional[str] = None,
        email: Optional[str] = None,
        organization: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search attorneys by name, email, or organization.

        Args:
            name: Attorney name (partial match)
            email: Email address (partial match)
            organization: Law firm name (partial match)

        Returns:
            List of matching attorney records
        """
        params = {}
        if name:
            params["name__icontains"] = name
        if email:
            params["email__icontains"] = email
        if organization:
            params["organizations__name__icontains"] = organization

        response = await self._request("GET", "attorneys", params)
        return response.get("results", [])

    # ============ SEARCH API ============

    async def search(
        self,
        q: str,
        search_type: str = "r",  # r=RECAP, o=opinions, oa=oral arguments
        order_by: str = "score desc",
        **filters
    ) -> Dict[str, Any]:
        """
        Use CourtListener's search API.

        Args:
            q: Search query
            search_type: Type of search (r=RECAP, o=opinions, oa=oral arguments)
            order_by: Sort order
            **filters: Additional filters

        Returns:
            Search results
        """
        params = {
            "q": q,
            "type": search_type,
            "order_by": order_by,
            **filters
        }

        return await self._request("GET", "search", params)

    # ============ UTILITY METHODS ============

    async def get_courts(self) -> List[Dict[str, Any]]:
        """Get list of all courts."""
        response = await self._request("GET", "courts")
        return response.get("results", [])

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        return {
            "remaining": self.rate_limit_remaining,
            "reset_at": self.rate_limit_reset.isoformat() if self.rate_limit_reset else None,
            "last_request": self.last_request_time.isoformat() if self.last_request_time else None
        }

    async def health_check(self) -> bool:
        """Check if API is accessible."""
        try:
            await self._request("GET", "courts", {"page_size": 1})
            return True
        except Exception:
            return False
