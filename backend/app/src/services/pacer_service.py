# -*- coding: utf-8 -*-
"""
PACER Service Layer

Integrates PACER API with user authentication and database.
Handles credential management, cost tracking, and search history.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
import os

# PACER integration imports
# Import from backend/src/pacer (deployed with backend)
try:
    from src.pacer.auth.authenticator import (
        PACERAuthenticator,
        PACERAuthenticationError,
        PACERMFARequiredError,
        PACERInvalidCredentialsError,
        PACERRateLimitError
    )
    from src.pacer.auth.token_manager import TokenManager
    from src.pacer.auth.mfa_handler import MFAHandler
    from src.pacer.api.pcl_client import PCLClient, PCLAuthenticationError
    from src.pacer.downloads.cost_tracker import CostTracker, PACEROperation
    from src.pacer.downloads.document_fetcher import DocumentFetcher, DocumentFetchError
except ImportError as e:
    # Fallback: Stub classes for when PACER module not available
    import logging
    logging.warning(f"PACER integration modules not available - using stubs. Error: {e}")

    class PACERAuthenticationError(Exception): pass
    class PACERMFARequiredError(Exception): pass
    class PACERInvalidCredentialsError(Exception): pass
    class PACERRateLimitError(Exception): pass
    class PCLAuthenticationError(Exception): pass
    class DocumentFetchError(Exception): pass

    class PACERAuthenticator:
        def __init__(self, *args, **kwargs): pass
        async def authenticate(self, *args, **kwargs): return {'nextGenCSO': 'stub_token'}

    class TokenManager:
        async def get_token(self, *args, **kwargs): return None
        async def store_token(self, *args, **kwargs): pass
        async def invalidate_token(self, *args, **kwargs): pass

    class MFAHandler:
        pass

    class PCLClient:
        pass

    class CostTracker:
        def __init__(self, *args, **kwargs): pass

    class PACEROperation:
        pass

    class DocumentFetcher:
        def __init__(self, *args, **kwargs): pass

# Database models
from app.models.pacer_credentials import (
    UserPACERCredentials,
    PACERSearchHistory,
    PACERDocument,
    PACERCostTracking
)
from app.models.user import User

logger = logging.getLogger(__name__)


class PACERServiceError(Exception):
    """Base exception for PACER service errors"""
    pass


class PACERService:
    """
    Service layer for PACER integration.

    SaaS Model: Uses app-level PACER credentials for all users.
    Users don't need their own PACER account - access is controlled via subscription tiers/credits.

    Handles:
    - App-level authentication (single PACER account for all users)
    - Per-user cost tracking and limits
    - Search history per user
    - Document downloads with credit deduction
    """

    def __init__(self, db: Session):
        """
        Initialize PACER service.

        Args:
            db: Database session
        """
        self.db = db
        self.token_manager = TokenManager()

        # Initialize encryption for credentials (kept for backwards compatibility)
        self._init_encryption()

        # Cost tracker (will be instantiated per user with their limits)
        self.cost_trackers: Dict[int, CostTracker] = {}

        # Load app-level credentials
        self._app_credentials = self._load_app_credentials()

    def _load_app_credentials(self) -> Optional[Dict[str, str]]:
        """
        Load app-level PACER credentials from environment.

        SaaS model: The app has one PACER account that serves all users.
        Users pay via subscription tiers and credits, not their own PACER accounts.
        """
        username = os.getenv('PACER_USERNAME')
        password = os.getenv('PACER_PASSWORD')

        if username and password:
            logger.info("App-level PACER credentials loaded from environment")
            return {
                'username': username,
                'password': password,
                'client_code': os.getenv('PACER_CLIENT_CODE'),
                'environment': os.getenv('PACER_ENVIRONMENT', 'production')
            }
        else:
            logger.warning("No app-level PACER credentials configured - PACER features disabled")
            return None

    def has_app_credentials(self) -> bool:
        """Check if app-level PACER credentials are configured"""
        return self._app_credentials is not None

    def get_pacer_status(self) -> Dict[str, Any]:
        """Get PACER service status for frontend"""
        return {
            "enabled": self.has_app_credentials(),
            "mode": "app_managed",  # Users don't need their own PACER account
            "message": "PACER access is managed by the platform. Use your subscription credits to download documents." if self.has_app_credentials() else "PACER service not configured"
        }

    def _init_encryption(self):
        """Initialize Fernet encryption for credentials"""
        try:
            # Define persistent key file path
            # Store alongside the database in the backend directory
            import os
            key_file = Path(os.getcwd()) / "backend" / ".pacer_encryption_key"

            # Ensure the directory exists
            key_file.parent.mkdir(parents=True, exist_ok=True)

            # Try to load existing key first
            if key_file.exists():
                with open(key_file, 'rb') as kf:
                    encryption_key = kf.read()
                self.fernet = Fernet(encryption_key)
                logger.info("Loaded PACER encryption key from persistent file")
                return

            # Fallback to environment variable
            encryption_key = os.getenv('PACER_ENCRYPTION_KEY')
            if encryption_key:
                if isinstance(encryption_key, str):
                    encryption_key = encryption_key.encode()
                self.fernet = Fernet(encryption_key)
                # Save to file for persistence
                key_file.parent.mkdir(parents=True, exist_ok=True)
                with open(key_file, 'wb') as kf:
                    kf.write(encryption_key)
                logger.info("Loaded PACER encryption key from environment and saved to file")
                return

            # Generate and persist new key
            logger.info("Generating new PACER encryption key and saving to file")
            encryption_key = Fernet.generate_key()
            self.fernet = Fernet(encryption_key)

            # Save key to persistent file
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, 'wb') as kf:
                kf.write(encryption_key)
            logger.info("PACER encryption key saved to persistent file")

        except Exception as e:
            logger.error(f"Error initializing PACER encryption: {e}")
            # Fallback to temporary key only as last resort
            self.fernet = Fernet(Fernet.generate_key())
            logger.warning("Using temporary encryption key - credentials may not persist!")

    async def save_user_credentials(
        self,
        user_id: int,
        pacer_username: str,
        pacer_password: str,
        client_code: Optional[str] = None,
        environment: str = "production",
        daily_limit: float = 100.0,
        monthly_limit: float = 1000.0
    ) -> UserPACERCredentials:
        """
        Save or update user PACER credentials.

        Args:
            user_id: User ID
            pacer_username: PACER username
            pacer_password: PACER password (will be encrypted)
            client_code: Optional client code
            environment: PACER environment
            daily_limit: Daily spending limit
            monthly_limit: Monthly spending limit

        Returns:
            UserPACERCredentials object
        """
        # Encrypt password
        encrypted_password = self.fernet.encrypt(pacer_password.encode()).decode()

        # Check if credentials exist
        credentials = self.db.query(UserPACERCredentials).filter(
            UserPACERCredentials.user_id == user_id
        ).first()

        if credentials:
            # Check if username changed (account switching)
            username_changed = credentials.pacer_username != pacer_username

            # Update existing
            credentials.pacer_username = pacer_username
            credentials.pacer_password_encrypted = encrypted_password
            credentials.pacer_client_code = client_code
            credentials.environment = environment
            credentials.daily_cost_limit = daily_limit
            credentials.monthly_cost_limit = monthly_limit
            credentials.updated_at = datetime.utcnow()

            # Reset verification status if account changed
            if username_changed:
                credentials.is_verified = False
                credentials.last_verified_at = None
                # Clear any cached tokens for the old account
                if hasattr(self, 'token_manager') and credentials.pacer_username:
                    try:
                        self.token_manager.clear_tokens(credentials.pacer_username)
                    except:
                        pass  # Token clearing is best-effort
                logger.info(f"PACER account switched to {pacer_username}, reset verification status")
        else:
            # Create new
            credentials = UserPACERCredentials(
                user_id=user_id,
                pacer_username=pacer_username,
                pacer_password_encrypted=encrypted_password,
                pacer_client_code=client_code,
                environment=environment,
                daily_cost_limit=daily_limit,
                monthly_cost_limit=monthly_limit
            )
            self.db.add(credentials)

        self.db.commit()
        self.db.refresh(credentials)

        logger.info(f"Saved PACER credentials for user {user_id}")
        return credentials

    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt PACER password"""
        try:
            return self.fernet.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            logger.error(f"Error decrypting PACER password: {e}")
            raise PACERServiceError("Failed to decrypt credentials")

    async def authenticate_app(
        self,
        force_refresh: bool = False
    ) -> str:
        """
        Authenticate using app-level PACER credentials.

        SaaS Model: All users share the app's PACER account.
        This is the primary authentication method.

        Args:
            force_refresh: Force new authentication even if cached token exists

        Returns:
            PACER authentication token

        Raises:
            PACERServiceError: If authentication fails or no app credentials configured
        """
        if not self._app_credentials:
            raise PACERServiceError("PACER service not configured. Please contact support.")

        # Check for cached token first
        cached_token = await self.token_manager.get_token(self._app_credentials['username'])
        if cached_token and not force_refresh:
            logger.debug("Using cached app-level PACER token")
            return cached_token

        # Authenticate with app credentials
        authenticator = PACERAuthenticator(environment=self._app_credentials['environment'])

        try:
            logger.info(f"[PACER AUTH] Authenticating with app-level credentials")

            result = await authenticator.authenticate(
                username=self._app_credentials['username'],
                password=self._app_credentials['password'],
                client_code=self._app_credentials['client_code'],
                force_refresh=force_refresh
            )

            token = result['nextGenCSO']

            # Store token in manager
            await self.token_manager.store_token(
                username=self._app_credentials['username'],
                token=token
            )

            logger.info("[PACER AUTH] App-level authentication successful")
            return token

        except PACERInvalidCredentialsError:
            logger.error("[PACER AUTH] Invalid app-level PACER credentials")
            raise PACERServiceError("PACER service configuration error. Please contact support.")
        except PACERRateLimitError:
            logger.error("[PACER AUTH] App-level PACER rate limited")
            raise PACERServiceError("Service temporarily unavailable. Please try again later.")
        except PACERAuthenticationError as e:
            logger.error(f"[PACER AUTH] App-level authentication failed: {e}")
            raise PACERServiceError(f"PACER service error: {str(e)}")

    async def authenticate_user(
        self,
        user_id: int,
        force_refresh: bool = False,
        otp: Optional[str] = None,
        test_mode: bool = False
    ) -> str:
        """
        Authenticate user with PACER and return token.

        Args:
            user_id: User ID
            force_refresh: Force new authentication even if cached token exists
            otp: Optional one-time password for MFA
            test_mode: If True, bypass real PACER authentication for testing

        Returns:
            PACER authentication token

        Raises:
            PACERServiceError: If authentication fails
        """
        # Get user credentials
        credentials = self.db.query(UserPACERCredentials).filter(
            UserPACERCredentials.user_id == user_id,
            UserPACERCredentials.is_active == True
        ).first()

        if not credentials:
            raise PACERServiceError("PACER credentials not found. Please add your credentials first.")

        # TEST MODE: Bypass real PACER authentication
        if test_mode:
            logger.info(f"TEST MODE: Bypassing real PACER authentication for user {user_id}")
            # Mark credentials as verified
            credentials.is_verified = True
            credentials.last_authenticated = datetime.utcnow()
            self.db.commit()
            # Return a fake test token
            return "TEST_TOKEN_" + "x" * 40

        # Decrypt password
        password = self._decrypt_password(credentials.pacer_password_encrypted)

        # Authenticate
        authenticator = PACERAuthenticator(environment=credentials.environment)

        try:
            logger.info(f"[PACER AUTH] Starting authentication for user {user_id}, username: {credentials.pacer_username}, test_mode: {test_mode}")

            try:
                result = await authenticator.authenticate(
                    username=credentials.pacer_username,
                    password=password,
                    client_code=credentials.pacer_client_code,
                    otp=otp,
                    force_refresh=force_refresh
                )
                logger.info(f"[PACER AUTH] Authentication result: {result}")
            except Exception as auth_err:
                logger.error(f"[PACER AUTH] Exception during authenticate() call: {type(auth_err).__name__}: {str(auth_err)}")
                import traceback
                logger.error(f"[PACER AUTH] Traceback: {traceback.format_exc()}")
                raise

            token = result['nextGenCSO']
            logger.info(f"[PACER AUTH] Token extracted successfully")

            # Store token in manager (for backwards compatibility)
            await self.token_manager.store_token(
                username=credentials.pacer_username,
                token=token
            )

            # Update credentials status
            credentials.is_verified = True
            credentials.last_verified_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Authenticated user {user_id} with PACER (cached: {result.get('cached', False)})")
            return token

        except PACERRateLimitError as e:
            # Rate limit - provide user-friendly message with retry time
            logger.warning(f"Rate limit exceeded for user {user_id}: {e}")
            raise PACERServiceError(f"Too many authentication attempts. {str(e)}")
        except PACERInvalidCredentialsError:
            # Invalid credentials - mark as not verified
            credentials.is_verified = False
            self.db.commit()
            logger.error(f"Invalid PACER credentials for user {user_id}")
            raise PACERServiceError("Invalid PACER credentials. Please check your username and password.")
        except PACERMFARequiredError:
            # MFA required - let user know they need to provide OTP
            logger.info(f"MFA required for user {user_id}")
            raise PACERServiceError("Multi-factor authentication required. Please provide your one-time password.")
        except PACERAuthenticationError as e:
            # General authentication error
            logger.error(f"[PACER AUTH] PACER authentication failed for user {user_id}: {e}")
            logger.error(f"[PACER AUTH] Error type: {type(e).__name__}, Message: {str(e)}")
            raise PACERServiceError(f"Authentication failed: {str(e)}")
        finally:
            # Always cleanup authenticator resources
            await authenticator.close()

    def _get_cost_tracker(self, user_id: int) -> CostTracker:
        """Get or create cost tracker for user"""
        if user_id not in self.cost_trackers:
            # Get user's cost limits
            credentials = self.db.query(UserPACERCredentials).filter(
                UserPACERCredentials.user_id == user_id
            ).first()

            daily_limit = credentials.daily_cost_limit if credentials else 100.0
            monthly_limit = credentials.monthly_cost_limit if credentials else 1000.0

            self.cost_trackers[user_id] = CostTracker(
                daily_limit=daily_limit,
                monthly_limit=monthly_limit
            )

        return self.cost_trackers[user_id]

    async def search_cases(
        self,
        user_id: int,
        **search_params
    ) -> Dict[str, Any]:
        """
        Search PACER cases for user.

        Args:
            user_id: User ID
            **search_params: Search parameters (court, case_number, etc.)

        Returns:
            Search results dictionary
        """
        # Authenticate user
        token = await self.authenticate_user(user_id)

        # Create PCL client
        client = PCLClient(auth_token=token)

        try:
            # Perform search
            results = await client.search_cases(**search_params)

            # Save search history
            search_history = PACERSearchHistory(
                user_id=user_id,
                search_type="case",
                search_criteria=search_params,
                results_count=results.total_count,
                results_summary={
                    "total": results.total_count,
                    "page": results.page,
                    "has_more": results.has_more
                },
                search_cost=0.0,  # Case searches are free
                court=search_params.get('court'),
                timestamp=datetime.utcnow()
            )
            self.db.add(search_history)

            # Update user stats
            credentials = self.db.query(UserPACERCredentials).filter(
                UserPACERCredentials.user_id == user_id
            ).first()
            if credentials:
                credentials.total_searches += 1
                credentials.last_used_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"User {user_id} searched cases: {results.total_count} results")

            return {
                "success": True,
                "results": results.results,
                "total_count": results.total_count,
                "page": results.page,
                "page_size": results.page_size,
                "has_more": results.has_more,
                "search_id": search_history.id
            }

        except Exception as e:
            logger.error(f"Case search error for user {user_id}: {e}")
            raise PACERServiceError(f"Search failed: {str(e)}")

    async def search_parties(
        self,
        user_id: int,
        party_name: str,
        **search_params
    ) -> Dict[str, Any]:
        """
        Search PACER parties for user.

        Args:
            user_id: User ID
            party_name: Party name to search
            **search_params: Additional search parameters

        Returns:
            Search results dictionary
        """
        # Authenticate user
        token = await self.authenticate_user(user_id)

        # Create PCL client
        client = PCLClient(auth_token=token)

        try:
            # Perform search
            results = await client.search_parties(
                party_name=party_name,
                **search_params
            )

            # Save search history
            search_history = PACERSearchHistory(
                user_id=user_id,
                search_type="party",
                search_criteria={"party_name": party_name, **search_params},
                results_count=results.total_count,
                results_summary={
                    "total": results.total_count,
                    "page": results.page
                },
                search_cost=0.0,  # Party searches are free
                court=search_params.get('court'),
                timestamp=datetime.utcnow()
            )
            self.db.add(search_history)

            # Update user stats
            credentials = self.db.query(UserPACERCredentials).filter(
                UserPACERCredentials.user_id == user_id
            ).first()
            if credentials:
                credentials.total_searches += 1
                credentials.last_used_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"User {user_id} searched parties: {results.total_count} results")

            return {
                "success": True,
                "results": results.results,
                "total_count": results.total_count,
                "page": results.page,
                "page_size": results.page_size,
                "has_more": results.has_more
            }

        except Exception as e:
            logger.error(f"Party search error for user {user_id}: {e}")
            raise PACERServiceError(f"Search failed: {str(e)}")

    async def download_document(
        self,
        user_id: int,
        document_url: str,
        case_id: str,
        document_id: str,
        court: Optional[str] = None,
        estimated_pages: int = 1,
        save_to_disk: bool = True
    ) -> Dict[str, Any]:
        """
        Download a document from PACER.

        Args:
            user_id: User ID
            document_url: PACER document URL
            case_id: Case identifier
            document_id: Document identifier
            court: Court identifier
            estimated_pages: Estimated document pages
            save_to_disk: Whether to save document to disk

        Returns:
            Download result with document data

        Raises:
            PACERServiceError: If download fails
        """
        # Get user credentials
        credentials = self.db.query(UserPACERCredentials).filter(
            UserPACERCredentials.user_id == user_id,
            UserPACERCredentials.is_active == True
        ).first()

        if not credentials:
            raise PACERServiceError("PACER credentials not found")

        # Ensure user is authenticated
        token = await self.token_manager.get_token(credentials.pacer_username)
        if not token:
            # Authenticate if no cached token
            token = await self.authenticate_user(user_id)

        # Initialize cost tracker
        cost_tracker = self._get_cost_tracker(user_id)

        # Initialize document fetcher
        fetcher = DocumentFetcher(
            auth_token=token,
            cost_tracker=cost_tracker,
            storage_path=Path(settings.DOCUMENT_STORAGE_PATH) if hasattr(settings, 'DOCUMENT_STORAGE_PATH') else None
        )

        try:
            # Download document
            result = await fetcher.fetch_document(
                document_url=document_url,
                case_id=case_id,
                document_id=document_id,
                user_id=str(user_id),
                court=court,
                estimated_pages=estimated_pages,
                save_to_disk=save_to_disk
            )

            # Save download record to database
            pacer_doc = PACERDocument(
                user_id=user_id,
                document_id=document_id,
                case_id=case_id,
                document_number=document_id.split('-')[-1] if '-' in document_id else document_id,
                title=f"Document {document_id}",
                file_path=result.get("file_path"),
                file_size=result.get("size_bytes"),
                page_count=result.get("pages"),
                file_hash=result.get("checksum"),
                pacer_url=document_url,
                court=court,
                download_cost=result.get("cost", 0.0),
                download_status="completed",
                is_available=True
            )
            self.db.add(pacer_doc)

            # Update credentials usage stats
            credentials.total_downloads += 1
            credentials.total_cost += result.get("cost", 0.0)
            credentials.last_used_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"User {user_id} downloaded document {document_id} (${result.get('cost', 0):.2f})")

            return {
                "success": True,
                "document_id": document_id,
                "case_id": case_id,
                "file_path": result.get("file_path"),
                "size_bytes": result.get("size_bytes"),
                "pages": result.get("pages"),
                "cost": result.get("cost"),
                "downloaded_at": result.get("downloaded_at"),
                "checksum": result.get("checksum")
            }

        except DocumentFetchError as e:
            logger.error(f"Document download failed for user {user_id}: {e}")
            raise PACERServiceError(f"Document download failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error downloading document: {e}")
            raise PACERServiceError(f"Download error: {str(e)}")

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get PACER usage statistics for user"""
        credentials = self.db.query(UserPACERCredentials).filter(
            UserPACERCredentials.user_id == user_id
        ).first()

        if not credentials:
            # Return proper structure with defaults so frontend doesn't crash
            return {
                "credentials": None,
                "usage": {
                    "total_searches": 0,
                    "total_downloads": 0,
                    "total_cost": 0.0
                },
                "limits": {
                    "daily_limit": 50.0,
                    "monthly_limit": 500.0,
                    "daily_spending": 0.0,
                    "monthly_spending": 0.0,
                    "daily_remaining": 50.0,
                    "monthly_remaining": 500.0
                },
                "recent_searches": [],
                "error": "No PACER credentials configured"
            }

        # Get cost tracker
        tracker = self._get_cost_tracker(user_id)
        cost_report = tracker.get_usage_report(user_id=str(user_id))

        return {
            "credentials": {
                "username": credentials.pacer_username,
                "environment": credentials.environment,
                "is_verified": credentials.is_verified,
                "last_used": credentials.last_used_at.isoformat() if credentials.last_used_at else None
            },
            "usage": {
                "total_searches": credentials.total_searches,
                "total_downloads": credentials.total_downloads,
                "total_cost": credentials.total_cost
            },
            "limits": {
                "daily_limit": credentials.daily_cost_limit,
                "monthly_limit": credentials.monthly_cost_limit,
                "daily_spending": cost_report['daily_spending'],
                "monthly_spending": cost_report['monthly_spending'],
                "daily_remaining": cost_report['daily_remaining'],
                "monthly_remaining": cost_report['monthly_remaining']
            },
            "recent_searches": self._get_recent_searches(user_id, limit=10)
        }

    def _get_recent_searches(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent searches for user"""
        searches = self.db.query(PACERSearchHistory).filter(
            PACERSearchHistory.user_id == user_id
        ).order_by(PACERSearchHistory.timestamp.desc()).limit(limit).all()

        return [{
            "id": s.id,
            "type": s.search_type,
            "criteria": s.search_criteria,
            "results_count": s.results_count,
            "court": s.court,
            "timestamp": s.timestamp.isoformat()
        } for s in searches]

    def get_user_credentials_status(self, user_id: int) -> Dict[str, Any]:
        """Check if user has PACER credentials configured"""
        credentials = self.db.query(UserPACERCredentials).filter(
            UserPACERCredentials.user_id == user_id
        ).first()

        return {
            "has_credentials": credentials is not None,
            "is_verified": credentials.is_verified if credentials else False,
            "username": credentials.pacer_username if credentials else None,
            "environment": credentials.environment if credentials else None
        }

    async def get_rate_limit_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get rate limit status for user.

        Returns:
            Dictionary with rate limit information
        """
        # Get user credentials
        credentials = self.db.query(UserPACERCredentials).filter(
            UserPACERCredentials.user_id == user_id
        ).first()

        if not credentials:
            return {
                "error": "No PACER credentials found",
                "rate_limited": False
            }

        # Create temporary authenticator to check rate limit
        authenticator = PACERAuthenticator(environment=credentials.environment)

        try:
            # Try to initialize Redis
            redis_client = await authenticator._init_redis()
            if redis_client is None:
                return {
                    "redis_available": False,
                    "rate_limited": False,
                    "message": "Rate limiting not active (Redis unavailable)"
                }

            # Get username hash
            username_hash = authenticator._hash_username(credentials.pacer_username)
            key = f"pacer:ratelimit:{username_hash}"

            # Check attempts
            attempts = await redis_client.get(key)
            if attempts:
                attempts = int(attempts)
                ttl = await redis_client.ttl(key)

                return {
                    "redis_available": True,
                    "rate_limited": attempts >= authenticator.max_auth_attempts,
                    "attempts": attempts,
                    "max_attempts": authenticator.max_auth_attempts,
                    "remaining_attempts": max(0, authenticator.max_auth_attempts - attempts),
                    "reset_in_seconds": ttl if ttl > 0 else 0,
                    "window_seconds": authenticator.rate_limit_window
                }
            else:
                return {
                    "redis_available": True,
                    "rate_limited": False,
                    "attempts": 0,
                    "max_attempts": authenticator.max_auth_attempts,
                    "remaining_attempts": authenticator.max_auth_attempts,
                    "reset_in_seconds": 0,
                    "window_seconds": authenticator.rate_limit_window
                }

        except Exception as e:
            logger.error(f"Error checking rate limit status: {e}")
            return {
                "error": f"Failed to check rate limit: {str(e)}",
                "rate_limited": False
            }
        finally:
            await authenticator.close()

    async def clear_rate_limit(self, user_id: int) -> Dict[str, Any]:
        """
        Clear rate limit for user (admin function).

        Args:
            user_id: User ID

        Returns:
            Status dictionary
        """
        # Get user credentials
        credentials = self.db.query(UserPACERCredentials).filter(
            UserPACERCredentials.user_id == user_id
        ).first()

        if not credentials:
            return {
                "success": False,
                "error": "No PACER credentials found"
            }

        # Create temporary authenticator
        authenticator = PACERAuthenticator(environment=credentials.environment)

        try:
            # Initialize Redis
            redis_client = await authenticator._init_redis()
            if redis_client is None:
                return {
                    "success": False,
                    "error": "Redis unavailable"
                }

            # Clear rate limit
            username_hash = authenticator._hash_username(credentials.pacer_username)
            key = f"pacer:ratelimit:{username_hash}"
            deleted = await redis_client.delete(key)

            logger.info(f"Cleared rate limit for user {user_id}")

            return {
                "success": True,
                "message": "Rate limit cleared successfully",
                "keys_deleted": deleted
            }

        except Exception as e:
            logger.error(f"Error clearing rate limit: {e}")
            return {
                "success": False,
                "error": f"Failed to clear rate limit: {str(e)}"
            }
        finally:
            await authenticator.close()

    async def logout_user(self, user_id: int) -> Dict[str, Any]:
        """
        Logout user from PACER by invalidating cached token.

        Args:
            user_id: User ID

        Returns:
            Status dictionary
        """
        # Get user credentials
        credentials = self.db.query(UserPACERCredentials).filter(
            UserPACERCredentials.user_id == user_id
        ).first()

        if not credentials:
            return {
                "success": False,
                "error": "No PACER credentials found"
            }

        # Create temporary authenticator
        authenticator = PACERAuthenticator(environment=credentials.environment)

        try:
            # Invalidate token in authenticator cache
            await authenticator.invalidate_token(credentials.pacer_username)

            # Also invalidate in token manager (for backwards compatibility)
            await self.token_manager.invalidate_token(credentials.pacer_username)

            logger.info(f"User {user_id} logged out from PACER")

            return {
                "success": True,
                "message": "Successfully logged out from PACER"
            }

        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return {
                "success": False,
                "error": f"Logout failed: {str(e)}"
            }
        finally:
            await authenticator.close()
