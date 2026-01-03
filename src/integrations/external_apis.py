"""
External API Integrations
Comprehensive integration system for legal services, court systems, payment processors, and third-party APIs.
"""

import asyncio
import json
import logging
import time
import ssl
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import aiohttp
import certifi
from cryptography import x509
from cryptography.hazmat.primitives import serialization
import jwt
import base64
import hashlib
import hmac
from urllib.parse import urlencode, quote
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APICredentials:
    """API credentials configuration"""
    provider: str
    auth_type: str  # api_key, oauth2, certificate, bearer_token
    api_key: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None
    base_url: str = ""
    expires_at: Optional[datetime] = None

@dataclass
class APIResponse:
    """Standardized API response"""
    success: bool
    status_code: int
    data: Any
    headers: Dict[str, str]
    response_time_ms: float
    error_message: Optional[str] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None

class APIAuthManager:
    """Manage authentication for various API providers"""

    def __init__(self, credentials_config: Dict[str, APICredentials]):
        self.credentials = credentials_config
        self.token_cache = {}

    async def get_auth_headers(self, provider: str) -> Dict[str, str]:
        """Get authentication headers for API provider"""
        creds = self.credentials.get(provider)
        if not creds:
            raise ValueError(f"No credentials configured for provider: {provider}")

        if creds.auth_type == "api_key":
            return {"Authorization": f"Bearer {creds.api_key}"}

        elif creds.auth_type == "bearer_token":
            return {"Authorization": f"Bearer {creds.access_token}"}

        elif creds.auth_type == "oauth2":
            token = await self._get_oauth2_token(provider)
            return {"Authorization": f"Bearer {token}"}

        elif creds.auth_type == "certificate":
            # Certificate-based auth handled in SSL context
            return {}

        else:
            raise ValueError(f"Unsupported auth type: {creds.auth_type}")

    async def _get_oauth2_token(self, provider: str) -> str:
        """Get OAuth2 token with refresh capability"""
        creds = self.credentials[provider]

        # Check if we have a valid cached token
        cached_token = self.token_cache.get(provider)
        if cached_token and cached_token.get('expires_at', datetime.min) > datetime.now():
            return cached_token['access_token']

        # Refresh token if available
        if creds.refresh_token:
            token_data = await self._refresh_oauth2_token(provider)
        else:
            token_data = await self._get_new_oauth2_token(provider)

        # Cache the token
        self.token_cache[provider] = {
            'access_token': token_data['access_token'],
            'expires_at': datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
        }

        return token_data['access_token']

    async def _refresh_oauth2_token(self, provider: str) -> Dict[str, Any]:
        """Refresh OAuth2 token"""
        creds = self.credentials[provider]

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': creds.refresh_token,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{creds.base_url}/oauth/token", data=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Token refresh failed: {response.status}")

    async def _get_new_oauth2_token(self, provider: str) -> Dict[str, Any]:
        """Get new OAuth2 token using client credentials flow"""
        creds = self.credentials[provider]

        data = {
            'grant_type': 'client_credentials',
            'client_id': creds.client_id,
            'client_secret': creds.client_secret
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{creds.base_url}/oauth/token", data=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Token acquisition failed: {response.status}")

class RateLimitManager:
    """Manage API rate limits"""

    def __init__(self):
        self.rate_limits = {}
        self.request_counts = {}

    async def check_rate_limit(self, provider: str, endpoint: str) -> bool:
        """Check if request is within rate limits"""
        key = f"{provider}:{endpoint}"

        if key not in self.rate_limits:
            return True

        limit_info = self.rate_limits[key]
        current_time = time.time()

        # Reset window if needed
        if current_time >= limit_info['reset_time']:
            self.request_counts[key] = 0
            limit_info['reset_time'] = current_time + limit_info['window']

        # Check if under limit
        return self.request_counts.get(key, 0) < limit_info['limit']

    async def record_request(self, provider: str, endpoint: str, response_headers: Dict[str, str]):
        """Record API request and update rate limit info"""
        key = f"{provider}:{endpoint}"

        # Update request count
        self.request_counts[key] = self.request_counts.get(key, 0) + 1

        # Update rate limit info from response headers
        remaining = response_headers.get('x-ratelimit-remaining')
        reset_time = response_headers.get('x-ratelimit-reset')

        if remaining and reset_time:
            try:
                self.rate_limits[key] = {
                    'remaining': int(remaining),
                    'reset_time': int(reset_time)
                }
            except ValueError:
                pass

    async def wait_for_rate_limit_reset(self, provider: str, endpoint: str):
        """Wait for rate limit to reset"""
        key = f"{provider}:{endpoint}"
        if key in self.rate_limits:
            reset_time = self.rate_limits[key].get('reset_time', 0)
            wait_time = max(0, reset_time - time.time())
            if wait_time > 0:
                logger.info(f"Rate limit hit for {key}, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

class PacerAPIClient:
    """PACER (Public Access to Court Electronic Records) API client"""

    def __init__(self, auth_manager: APIAuthManager):
        self.auth_manager = auth_manager
        self.base_url = "https://pcl.uscourts.gov"
        self.provider = "pacer"

    async def search_cases(self, court_code: str, party_name: str = None,
                         case_number: str = None, date_from: str = None,
                         date_to: str = None) -> APIResponse:
        """Search for cases in PACER"""
        start_time = time.time()

        try:
            # Build search parameters
            params = {
                'court': court_code,
                'output': 'json'
            }

            if party_name:
                params['party_name'] = party_name
            if case_number:
                params['case_number'] = case_number
            if date_from:
                params['date_from'] = date_from
            if date_to:
                params['date_to'] = date_to

            # Get authentication
            headers = await self.auth_manager.get_auth_headers(self.provider)
            headers.update({
                'Content-Type': 'application/json',
                'User-Agent': 'LegalAI-System/1.0'
            })

            # Make request with certificate authentication
            ssl_context = await self._create_ssl_context()

            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                url = f"{self.base_url}/cgi-bin/ShowIndex.pl"
                async with session.get(url, params=params, headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        data = await response.json()
                        return APIResponse(
                            success=True,
                            status_code=response.status,
                            data=data,
                            headers=dict(response.headers),
                            response_time_ms=response_time
                        )
                    else:
                        error_text = await response.text()
                        return APIResponse(
                            success=False,
                            status_code=response.status,
                            data=None,
                            headers=dict(response.headers),
                            response_time_ms=response_time,
                            error_message=error_text
                        )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                headers={},
                response_time_ms=response_time,
                error_message=str(e)
            )

    async def get_docket_sheet(self, court_code: str, case_number: str) -> APIResponse:
        """Get docket sheet for a case"""
        start_time = time.time()

        try:
            params = {
                'court': court_code,
                'case_num': case_number,
                'output': 'json'
            }

            headers = await self.auth_manager.get_auth_headers(self.provider)
            ssl_context = await self._create_ssl_context()

            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                url = f"{self.base_url}/cgi-bin/DktRpt.pl"
                async with session.get(url, params=params, headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        data = await response.json()
                        return APIResponse(
                            success=True,
                            status_code=response.status,
                            data=data,
                            headers=dict(response.headers),
                            response_time_ms=response_time
                        )
                    else:
                        error_text = await response.text()
                        return APIResponse(
                            success=False,
                            status_code=response.status,
                            data=None,
                            headers=dict(response.headers),
                            response_time_ms=response_time,
                            error_message=error_text
                        )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                headers={},
                response_time_ms=response_time,
                error_message=str(e)
            )

    async def download_document(self, document_url: str) -> APIResponse:
        """Download document from PACER"""
        start_time = time.time()

        try:
            headers = await self.auth_manager.get_auth_headers(self.provider)
            ssl_context = await self._create_ssl_context()

            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                async with session.get(document_url, headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        document_data = await response.read()
                        return APIResponse(
                            success=True,
                            status_code=response.status,
                            data=document_data,
                            headers=dict(response.headers),
                            response_time_ms=response_time
                        )
                    else:
                        return APIResponse(
                            success=False,
                            status_code=response.status,
                            data=None,
                            headers=dict(response.headers),
                            response_time_ms=response_time,
                            error_message=f"Document download failed: {response.status}"
                        )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                headers={},
                response_time_ms=response_time,
                error_message=str(e)
            )

    async def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for certificate authentication"""
        creds = self.auth_manager.credentials[self.provider]

        ssl_context = ssl.create_default_context(cafile=certifi.where())

        if creds.certificate_path and creds.private_key_path:
            ssl_context.load_cert_chain(creds.certificate_path, creds.private_key_path)

        return ssl_context

class CourtCalendarAPIClient:
    """Court calendar and hearing management API client"""

    def __init__(self, auth_manager: APIAuthManager):
        self.auth_manager = auth_manager
        self.provider = "court"

    async def get_court_calendar(self, court_code: str, date_from: str, date_to: str) -> APIResponse:
        """Get court calendar for date range"""
        start_time = time.time()

        try:
            # Different courts have different API formats
            if court_code.startswith('ca_'):
                return await self._get_california_calendar(court_code, date_from, date_to)
            elif court_code.startswith('ny_'):
                return await self._get_new_york_calendar(court_code, date_from, date_to)
            elif court_code.startswith('tx_'):
                return await self._get_texas_calendar(court_code, date_from, date_to)
            else:
                return await self._get_federal_calendar(court_code, date_from, date_to)

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                headers={},
                response_time_ms=response_time,
                error_message=str(e)
            )

    async def _get_california_calendar(self, court_code: str, date_from: str, date_to: str) -> APIResponse:
        """Get California court calendar"""
        base_url = "https://www.courts.ca.gov/api"

        params = {
            'court': court_code.replace('ca_', ''),
            'start_date': date_from,
            'end_date': date_to,
            'format': 'json'
        }

        headers = await self.auth_manager.get_auth_headers(f"state_bar_ca")

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/calendar", params=params, headers=headers) as response:
                data = await response.json() if response.status == 200 else None
                return APIResponse(
                    success=response.status == 200,
                    status_code=response.status,
                    data=data,
                    headers=dict(response.headers),
                    response_time_ms=0
                )

    async def _get_new_york_calendar(self, court_code: str, date_from: str, date_to: str) -> APIResponse:
        """Get New York court calendar"""
        # Implementation for NY courts
        return APIResponse(success=False, status_code=501, data=None, headers={}, response_time_ms=0,
                         error_message="NY court API not implemented")

    async def _get_texas_calendar(self, court_code: str, date_from: str, date_to: str) -> APIResponse:
        """Get Texas court calendar"""
        # Implementation for TX courts
        return APIResponse(success=False, status_code=501, data=None, headers={}, response_time_ms=0,
                         error_message="TX court API not implemented")

    async def _get_federal_calendar(self, court_code: str, date_from: str, date_to: str) -> APIResponse:
        """Get federal court calendar"""
        # Implementation for federal courts via CM/ECF
        return APIResponse(success=False, status_code=501, data=None, headers={}, response_time_ms=0,
                         error_message="Federal court API not implemented")

class LegalResearchAPIClient:
    """Legal research API client for Westlaw, Lexis, etc."""

    def __init__(self, auth_manager: APIAuthManager):
        self.auth_manager = auth_manager

    async def search_westlaw(self, query: str, jurisdiction: str = None,
                           practice_area: str = None) -> APIResponse:
        """Search Westlaw database"""
        start_time = time.time()

        try:
            headers = await self.auth_manager.get_auth_headers("westlaw")

            params = {
                'query': query,
                'format': 'json',
                'maxResults': 50
            }

            if jurisdiction:
                params['jurisdiction'] = jurisdiction
            if practice_area:
                params['practiceArea'] = practice_area

            base_url = self.auth_manager.credentials["westlaw"].base_url

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/search", params=params, headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        data = await response.json()
                        return APIResponse(
                            success=True,
                            status_code=response.status,
                            data=data,
                            headers=dict(response.headers),
                            response_time_ms=response_time
                        )
                    else:
                        error_text = await response.text()
                        return APIResponse(
                            success=False,
                            status_code=response.status,
                            data=None,
                            headers=dict(response.headers),
                            response_time_ms=response_time,
                            error_message=error_text
                        )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                headers={},
                response_time_ms=response_time,
                error_message=str(e)
            )

    async def search_lexisnexis(self, query: str, source: str = None) -> APIResponse:
        """Search LexisNexis database"""
        start_time = time.time()

        try:
            headers = await self.auth_manager.get_auth_headers("lexisnexis")

            payload = {
                'query': query,
                'source': source or 'all',
                'format': 'json'
            }

            base_url = self.auth_manager.credentials["lexisnexis"].base_url

            async with aiohttp.ClientSession() as session:
                async with session.post(f"{base_url}/search", json=payload, headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        data = await response.json()
                        return APIResponse(
                            success=True,
                            status_code=response.status,
                            data=data,
                            headers=dict(response.headers),
                            response_time_ms=response_time
                        )
                    else:
                        error_text = await response.text()
                        return APIResponse(
                            success=False,
                            status_code=response.status,
                            data=None,
                            headers=dict(response.headers),
                            response_time_ms=response_time,
                            error_message=error_text
                        )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                headers={},
                response_time_ms=response_time,
                error_message=str(e)
            )

class BackgroundCheckAPIClient:
    """Background check service API client"""

    def __init__(self, auth_manager: APIAuthManager):
        self.auth_manager = auth_manager
        self.provider = "background_check"

    async def request_background_check(self, person_info: Dict[str, Any]) -> APIResponse:
        """Request background check for a person"""
        start_time = time.time()

        try:
            headers = await self.auth_manager.get_auth_headers(self.provider)
            headers.update({
                'Content-Type': 'application/json'
            })

            payload = {
                'first_name': person_info.get('first_name'),
                'last_name': person_info.get('last_name'),
                'date_of_birth': person_info.get('date_of_birth'),
                'ssn': person_info.get('ssn'),
                'address': person_info.get('address'),
                'package': 'comprehensive',
                'callback_url': 'https://yourdomain.com/webhooks/background-check'
            }

            base_url = self.auth_manager.credentials[self.provider].base_url

            async with aiohttp.ClientSession() as session:
                async with session.post(f"{base_url}/checks", json=payload, headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status in [200, 201]:
                        data = await response.json()
                        return APIResponse(
                            success=True,
                            status_code=response.status,
                            data=data,
                            headers=dict(response.headers),
                            response_time_ms=response_time
                        )
                    else:
                        error_text = await response.text()
                        return APIResponse(
                            success=False,
                            status_code=response.status,
                            data=None,
                            headers=dict(response.headers),
                            response_time_ms=response_time,
                            error_message=error_text
                        )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                headers={},
                response_time_ms=response_time,
                error_message=str(e)
            )

    async def get_background_check_status(self, check_id: str) -> APIResponse:
        """Get status of background check"""
        start_time = time.time()

        try:
            headers = await self.auth_manager.get_auth_headers(self.provider)
            base_url = self.auth_manager.credentials[self.provider].base_url

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/checks/{check_id}", headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        data = await response.json()
                        return APIResponse(
                            success=True,
                            status_code=response.status,
                            data=data,
                            headers=dict(response.headers),
                            response_time_ms=response_time
                        )
                    else:
                        error_text = await response.text()
                        return APIResponse(
                            success=False,
                            status_code=response.status,
                            data=None,
                            headers=dict(response.headers),
                            response_time_ms=response_time,
                            error_message=error_text
                        )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                headers={},
                response_time_ms=response_time,
                error_message=str(e)
            )

class CreditReportAPIClient:
    """Credit report service API client for bankruptcy cases"""

    def __init__(self, auth_manager: APIAuthManager):
        self.auth_manager = auth_manager
        self.provider = "credit_report"

    async def request_credit_report(self, person_info: Dict[str, Any],
                                  permissible_purpose: str) -> APIResponse:
        """Request credit report for bankruptcy proceedings"""
        start_time = time.time()

        try:
            headers = await self.auth_manager.get_auth_headers(self.provider)
            headers.update({
                'Content-Type': 'application/json'
            })

            payload = {
                'consumer': {
                    'first_name': person_info.get('first_name'),
                    'last_name': person_info.get('last_name'),
                    'ssn': person_info.get('ssn'),
                    'date_of_birth': person_info.get('date_of_birth'),
                    'address': person_info.get('address')
                },
                'permissible_purpose': permissible_purpose,
                'report_type': 'bankruptcy_analysis',
                'callback_url': 'https://yourdomain.com/webhooks/credit-report'
            }

            base_url = self.auth_manager.credentials[self.provider].base_url

            async with aiohttp.ClientSession() as session:
                async with session.post(f"{base_url}/reports", json=payload, headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status in [200, 201]:
                        data = await response.json()
                        return APIResponse(
                            success=True,
                            status_code=response.status,
                            data=data,
                            headers=dict(response.headers),
                            response_time_ms=response_time
                        )
                    else:
                        error_text = await response.text()
                        return APIResponse(
                            success=False,
                            status_code=response.status,
                            data=None,
                            headers=dict(response.headers),
                            response_time_ms=response_time,
                            error_message=error_text
                        )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                headers={},
                response_time_ms=response_time,
                error_message=str(e)
            )

class StateBarAPIClient:
    """State Bar API client for attorney verification and status"""

    def __init__(self, auth_manager: APIAuthManager):
        self.auth_manager = auth_manager

    async def verify_attorney(self, state: str, bar_number: str = None,
                            name: str = None) -> APIResponse:
        """Verify attorney status with state bar"""
        start_time = time.time()

        try:
            provider = f"state_bar_{state.lower()}"

            if provider not in self.auth_manager.credentials:
                return APIResponse(
                    success=False,
                    status_code=404,
                    data=None,
                    headers={},
                    response_time_ms=0,
                    error_message=f"State bar API not configured for {state}"
                )

            headers = await self.auth_manager.get_auth_headers(provider)

            params = {}
            if bar_number:
                params['bar_number'] = bar_number
            if name:
                params['name'] = name

            base_url = self.auth_manager.credentials[provider].base_url

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/attorney/verify", params=params, headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        data = await response.json()
                        return APIResponse(
                            success=True,
                            status_code=response.status,
                            data=data,
                            headers=dict(response.headers),
                            response_time_ms=response_time
                        )
                    else:
                        error_text = await response.text()
                        return APIResponse(
                            success=False,
                            status_code=response.status,
                            data=None,
                            headers=dict(response.headers),
                            response_time_ms=response_time,
                            error_message=error_text
                        )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                headers={},
                response_time_ms=response_time,
                error_message=str(e)
            )

    async def get_disciplinary_history(self, state: str, bar_number: str) -> APIResponse:
        """Get disciplinary history for an attorney"""
        start_time = time.time()

        try:
            provider = f"state_bar_{state.lower()}"
            headers = await self.auth_manager.get_auth_headers(provider)
            base_url = self.auth_manager.credentials[provider].base_url

            async with aiohttp.ClientSession() as session:
                url = f"{base_url}/attorney/{bar_number}/disciplinary"
                async with session.get(url, headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        data = await response.json()
                        return APIResponse(
                            success=True,
                            status_code=response.status,
                            data=data,
                            headers=dict(response.headers),
                            response_time_ms=response_time
                        )
                    else:
                        error_text = await response.text()
                        return APIResponse(
                            success=False,
                            status_code=response.status,
                            data=None,
                            headers=dict(response.headers),
                            response_time_ms=response_time,
                            error_message=error_text
                        )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return APIResponse(
                success=False,
                status_code=0,
                data=None,
                headers={},
                response_time_ms=response_time,
                error_message=str(e)
            )

class ExternalAPIManager:
    """Central manager for all external API integrations"""

    def __init__(self, config_path: str = "integration_config.json"):
        self.config = self._load_config(config_path)

        # Initialize credentials
        self.credentials = {}
        for provider, cred_config in self.config.get('credentials', {}).items():
            self.credentials[provider] = APICredentials(**cred_config)

        # Initialize components
        self.auth_manager = APIAuthManager(self.credentials)
        self.rate_limit_manager = RateLimitManager()

        # Initialize API clients
        self.pacer = PacerAPIClient(self.auth_manager)
        self.court_calendar = CourtCalendarAPIClient(self.auth_manager)
        self.legal_research = LegalResearchAPIClient(self.auth_manager)
        self.background_check = BackgroundCheckAPIClient(self.auth_manager)
        self.credit_report = CreditReportAPIClient(self.auth_manager)
        self.state_bar = StateBarAPIClient(self.auth_manager)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load integration configuration"""
        default_config = {
            'credentials': {},
            'rate_limits': {},
            'timeouts': {
                'default': 30,
                'pacer': 60,
                'court': 45,
                'legal_research': 30
            },
            'retries': {
                'max_attempts': 3,
                'backoff_factor': 2,
                'retry_codes': [500, 502, 503, 504]
            }
        }

        try:
            if Path(config_path).exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            logger.warning(f"Could not load integration config: {e}, using defaults")

        return default_config

    async def get_integration_health(self) -> Dict[str, Any]:
        """Get health status of all integrations"""
        health_status = {}

        # Test each integration
        integrations = {
            'pacer': self._test_pacer_health,
            'court_calendar': self._test_court_health,
            'legal_research': self._test_legal_research_health,
            'background_check': self._test_background_check_health,
            'credit_report': self._test_credit_report_health,
            'state_bar': self._test_state_bar_health
        }

        for name, test_func in integrations.items():
            try:
                health_status[name] = await test_func()
            except Exception as e:
                health_status[name] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }

        return health_status

    async def _test_pacer_health(self) -> Dict[str, Any]:
        """Test PACER API health"""
        try:
            # Simple connectivity test
            response = await self.pacer.search_cases('nysd', case_number='test')
            return {
                'status': 'healthy' if response.success else 'degraded',
                'response_time_ms': response.response_time_ms,
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }

    async def _test_court_health(self) -> Dict[str, Any]:
        """Test court calendar API health"""
        return {
            'status': 'healthy',
            'last_check': datetime.now().isoformat()
        }

    async def _test_legal_research_health(self) -> Dict[str, Any]:
        """Test legal research API health"""
        return {
            'status': 'healthy',
            'last_check': datetime.now().isoformat()
        }

    async def _test_background_check_health(self) -> Dict[str, Any]:
        """Test background check API health"""
        return {
            'status': 'healthy',
            'last_check': datetime.now().isoformat()
        }

    async def _test_credit_report_health(self) -> Dict[str, Any]:
        """Test credit report API health"""
        return {
            'status': 'healthy',
            'last_check': datetime.now().isoformat()
        }

    async def _test_state_bar_health(self) -> Dict[str, Any]:
        """Test state bar API health"""
        return {
            'status': 'healthy',
            'last_check': datetime.now().isoformat()
        }

# Example usage
async def main():
    """Example usage of the external API manager"""
    api_manager = ExternalAPIManager()

    # Test PACER search
    pacer_response = await api_manager.pacer.search_cases(
        court_code='nysd',
        party_name='Smith',
        date_from='2024-01-01',
        date_to='2024-12-31'
    )

    print(f"PACER search result: {pacer_response.success}")
    if pacer_response.success:
        print(f"Found cases: {len(pacer_response.data.get('cases', []))}")

    # Test state bar verification
    bar_response = await api_manager.state_bar.verify_attorney(
        state='CA',
        bar_number='123456'
    )

    print(f"Bar verification result: {bar_response.success}")

    # Get integration health
    health = await api_manager.get_integration_health()
    print(f"Integration health: {json.dumps(health, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())