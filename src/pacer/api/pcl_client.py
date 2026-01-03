# -*- coding: utf-8 -*-
"""
PACER Case Locator (PCL) API Client

Comprehensive client for searching cases and parties across all PACER courts.

Features:
- Case search with advanced filters
- Party search across courts
- Batch search operations
- Pagination support
- Comprehensive error handling
- Retry logic with exponential backoff
- Cost tracking integration
"""

import httpx
import logging
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator
from enum import Enum
from datetime import datetime, date
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class SearchType(Enum):
    """Types of PACER searches"""
    CASE = "cases"
    PARTY = "parties"


class CourtType(Enum):
    """PACER court types"""
    DISTRICT = "district"
    BANKRUPTCY = "bankruptcy"
    APPELLATE = "appellate"


@dataclass
class SearchResult:
    """Container for search results with metadata"""
    results: List[Dict[str, Any]]
    total_count: int
    page: int
    page_size: int
    has_more: bool
    query: Dict[str, Any]
    search_type: SearchType
    timestamp: datetime


class PCLAPIError(Exception):
    """Base exception for PCL API errors"""
    pass


class PCLAuthenticationError(PCLAPIError):
    """Raised when authentication token is invalid or expired"""
    pass


class PCLRateLimitError(PCLAPIError):
    """Raised when rate limit is exceeded"""
    pass


class PCLClient:
    """
    Client for PACER Case Locator API.

    Provides comprehensive search capabilities across all PACER courts
    with robust error handling and automatic retries.
    """

    def __init__(
        self,
        auth_token: str,
        environment: str = "production",
        max_retries: int = 3,
        timeout: float = 60.0
    ):
        """
        Initialize PCL client.

        Args:
            auth_token: nextGenCSO authentication token
            environment: PACER environment ('production' or 'qa')
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.auth_token = auth_token
        self.env = environment
        self.base_url = self._get_base_url()
        self.max_retries = max_retries
        self.timeout = httpx.Timeout(timeout, connect=10.0)

        # Track request statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retries": 0
        }

        logger.info(f"PCLClient initialized for {environment} environment")

    def _get_base_url(self) -> str:
        """Get PCL API base URL for environment"""
        if self.env.lower() == "qa":
            return "https://qa-pcl.uscourts.gov"
        return "https://pcl.uscourts.gov"

    def _get_headers(self) -> Dict[str, str]:
        """Get required headers for PCL API requests"""
        # Note: PCL public API may not require authentication
        # Authentication is handled differently for public vs authenticated APIs
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "PACER-Legal-AI-System/1.0"
        }
        # Only add authentication if token is provided and not a test token
        if self.auth_token and not self.auth_token.startswith("TEST_TOKEN"):
            # Try Cookie format for authenticated PCL access
            headers["Cookie"] = f"nextGenCSO={self.auth_token}"
        return headers

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            payload: Request payload (for POST requests)

        Returns:
            Response data as dictionary

        Raises:
            PCLAPIError: On API errors
            PCLAuthenticationError: On authentication failures
            PCLRateLimitError: On rate limit errors
        """
        url = f"{self.base_url}/{endpoint}"
        last_error = None

        headers = self._get_headers()
        logger.info(f"[PCL DEBUG] Making request to: {url}")
        logger.info(f"[PCL DEBUG] Headers: {headers}")
        logger.info(f"[PCL DEBUG] Payload: {payload}")

        for attempt in range(self.max_retries):
            self.stats["total_requests"] += 1

            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method.upper() == "POST":
                        response = await client.post(
                            url,
                            json=payload,
                            headers=headers
                        )
                    else:
                        response = await client.get(
                            url,
                            headers=headers
                        )

                    logger.info(f"[PCL DEBUG] Response status: {response.status_code}")
                    logger.info(f"[PCL DEBUG] Response headers: {response.headers}")

                    # Handle specific HTTP status codes
                    if response.status_code == 401:
                        self.stats["failed_requests"] += 1
                        raise PCLAuthenticationError(
                            "Authentication token expired or invalid. Please re-authenticate."
                        )

                    elif response.status_code == 429:
                        # Rate limited
                        self.stats["retries"] += 1
                        retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
                        logger.warning(f"Rate limited, waiting {retry_after}s")

                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(retry_after)
                            continue
                        else:
                            self.stats["failed_requests"] += 1
                            raise PCLRateLimitError("Rate limit exceeded, please try again later")

                    elif response.status_code >= 500:
                        # Server error, retry with exponential backoff
                        self.stats["retries"] += 1
                        wait_time = 2 ** attempt

                        logger.warning(
                            f"Server error (HTTP {response.status_code}), "
                            f"attempt {attempt + 1}/{self.max_retries}, "
                            f"waiting {wait_time}s"
                        )

                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(wait_time)
                            continue

                    # Raise for other error status codes
                    response.raise_for_status()

                    # Parse response
                    data = response.json()

                    self.stats["successful_requests"] += 1
                    return data

            except httpx.TimeoutException as e:
                last_error = e
                self.stats["retries"] += 1
                logger.warning(f"Request timeout, attempt {attempt + 1}/{self.max_retries}")

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

            except httpx.NetworkError as e:
                last_error = e
                self.stats["retries"] += 1
                logger.warning(f"Network error, attempt {attempt + 1}/{self.max_retries}")

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

            except (PCLAuthenticationError, PCLRateLimitError):
                # Don't retry on these
                raise

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error: {e}")

                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

        # All retries exhausted
        self.stats["failed_requests"] += 1
        raise PCLAPIError(f"Request failed after {self.max_retries} attempts: {last_error}")

    async def search_cases(
        self,
        case_number: Optional[str] = None,
        case_title: Optional[str] = None,
        court: Optional[str] = None,
        filed_from: Optional[str] = None,
        filed_to: Optional[str] = None,
        closed_from: Optional[str] = None,
        closed_to: Optional[str] = None,
        nature_of_suit: Optional[str] = None,
        case_status: Optional[str] = None,
        judge_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResult:
        """
        Search for cases using PCL API.

        Args:
            case_number: Full or partial case number
            case_title: Case title to search
            court: Court identifier (e.g., 'nysd', 'cacb')
            filed_from: Cases filed after this date (YYYY-MM-DD)
            filed_to: Cases filed before this date
            closed_from: Cases closed after this date
            closed_to: Cases closed before this date
            nature_of_suit: Nature of suit code
            case_status: Case status (e.g., 'open', 'closed')
            judge_name: Name of judge
            page: Page number (1-indexed)
            page_size: Results per page (max 100)

        Returns:
            SearchResult object with results and metadata
        """
        endpoint = "pcl-public-api/rest/cases/find"

        # Build search criteria
        search_criteria = {}

        if case_number:
            search_criteria["caseNumberFull"] = case_number
        if case_title:
            search_criteria["caseTitle"] = case_title
        if court:
            search_criteria["courtId"] = court.lower()
        if filed_from or filed_to:
            search_criteria["dateFiledFrom"] = filed_from
            search_criteria["dateFiledTo"] = filed_to
        if closed_from or closed_to:
            search_criteria["dateClosedFrom"] = closed_from
            search_criteria["dateClosedTo"] = closed_to
        if nature_of_suit:
            search_criteria["natureOfSuit"] = nature_of_suit
        if case_status:
            search_criteria["caseStatus"] = case_status
        if judge_name:
            search_criteria["judgeName"] = judge_name

        # PCL API expects search criteria at root level, not wrapped in "caseSearch"
        # Merge search criteria with pagination parameters
        payload = {
            **search_criteria,
            "page": page,
            "pageSize": min(page_size, 100)  # Cap at 100
        }

        logger.info(f"Searching cases: {search_criteria}")

        data = await self._make_request("POST", endpoint, payload)

        # Extract results and metadata
        results = data.get("results", data.get("cases", []))
        total = data.get("totalCount", data.get("total", len(results)))
        has_more = data.get("hasMore", (page * page_size) < total)

        return SearchResult(
            results=results,
            total_count=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
            query=search_criteria,
            search_type=SearchType.CASE,
            timestamp=datetime.utcnow()
        )

    async def search_parties(
        self,
        party_name: str,
        court: Optional[str] = None,
        party_role: Optional[str] = None,
        case_filed_from: Optional[str] = None,
        case_filed_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResult:
        """
        Search for parties across cases.

        Args:
            party_name: Name of party to search
            court: Limit to specific court
            party_role: Party role (e.g., 'plaintiff', 'defendant', 'debtor')
            case_filed_from: Limit to cases filed after this date
            case_filed_to: Limit to cases filed before this date
            page: Page number (1-indexed)
            page_size: Results per page

        Returns:
            SearchResult object with party search results
        """
        endpoint = "pcl-public-api/rest/parties/find"

        search_criteria = {
            "partyName": party_name
        }

        if court:
            search_criteria["courtId"] = court.lower()
        if party_role:
            search_criteria["partyRole"] = party_role
        if case_filed_from:
            search_criteria["caseFiledFrom"] = case_filed_from
        if case_filed_to:
            search_criteria["caseFiledTo"] = case_filed_to

        # PCL API expects search criteria at root level, not wrapped in "partySearch"
        payload = {
            **search_criteria,
            "page": page,
            "pageSize": min(page_size, 100)
        }

        logger.info(f"Searching parties: {search_criteria}")

        data = await self._make_request("POST", endpoint, payload)

        results = data.get("results", data.get("parties", []))
        total = data.get("totalCount", data.get("total", len(results)))
        has_more = data.get("hasMore", (page * page_size) < total)

        return SearchResult(
            results=results,
            total_count=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
            query=search_criteria,
            search_type=SearchType.PARTY,
            timestamp=datetime.utcnow()
        )

    async def search_cases_all_pages(
        self,
        max_pages: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Search cases with automatic pagination.

        Yields individual case results across all pages.

        Args:
            max_pages: Maximum number of pages to fetch (None for all)
            **kwargs: Arguments passed to search_cases()

        Yields:
            Individual case dictionaries
        """
        page = 1
        while True:
            if max_pages and page > max_pages:
                break

            result = await self.search_cases(page=page, **kwargs)

            for case in result.results:
                yield case

            if not result.has_more:
                break

            page += 1
            # Small delay between pages to avoid rate limiting
            await asyncio.sleep(0.5)

    async def batch_search_cases(
        self,
        searches: List[Dict[str, Any]],
        delay_between: float = 1.0
    ) -> List[SearchResult]:
        """
        Perform multiple case searches in batch.

        Args:
            searches: List of search parameter dictionaries
            delay_between: Delay between searches to avoid rate limiting

        Returns:
            List of SearchResult objects
        """
        results = []

        for i, search_params in enumerate(searches):
            try:
                result = await self.search_cases(**search_params)
                results.append(result)
                logger.info(f"Batch search {i+1}/{len(searches)} completed: {result.total_count} results")

                # Delay between requests
                if i < len(searches) - 1:
                    await asyncio.sleep(delay_between)

            except Exception as e:
                logger.error(f"Batch search {i+1} failed: {e}")
                # Append error result
                results.append(SearchResult(
                    results=[],
                    total_count=0,
                    page=1,
                    page_size=0,
                    has_more=False,
                    query=search_params,
                    search_type=SearchType.CASE,
                    timestamp=datetime.utcnow()
                ))

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        success_rate = (
            self.stats["successful_requests"] / self.stats["total_requests"] * 100
            if self.stats["total_requests"] > 0
            else 0
        )

        return {
            **self.stats,
            "success_rate": round(success_rate, 2),
            "environment": self.env
        }


# Example usage
async def main():
    """Test PCL client"""
    import os

    # Get auth token (you'd get this from PACERAuthenticator)
    token = os.getenv("PACER_TOKEN")
    if not token:
        print("❌ PACER_TOKEN must be set. Authenticate first with PACERAuthenticator.")
        return

    client = PCLClient(auth_token=token, environment="production")

    try:
        # Search for cases
        print("🔍 Searching for cases in NYSD...")
        results = await client.search_cases(
            court="nysd",
            filed_from="2024-01-01",
            page_size=5
        )

        print(f"✅ Found {results.total_count} cases")
        print(f"   Page {results.page}, showing {len(results.results)} results")

        for case in results.results[:3]:
            print(f"   - {case.get('caseNumber')}: {case.get('caseTitle')}")

        # Get stats
        stats = client.get_stats()
        print(f"\n📊 Client Statistics:")
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Success rate: {stats['success_rate']}%")

    except PCLAuthenticationError:
        print("❌ Authentication failed - token may be expired")
    except PCLAPIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
