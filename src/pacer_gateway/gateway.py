"""
PACER Gateway Main Service

High-level gateway service that orchestrates PACER operations including
account management, cost tracking, compliance monitoring, and request routing.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass

from ..shared.utils.cache_manager import cache_manager
from .client import PacerClient, PacerResponse, PacerError
from .account_manager import account_manager, AccountPool
from .cost_tracker import cost_tracker, CostCategory, BillingPeriod
from .models import (
    PacerAccount, CourtInfo, SearchCriteria, CaseInfo, DocketEntry,
    DocumentInfo, RequestLog, QueuedRequest, RequestStatus, 
    get_court_info, FEDERAL_COURTS
)


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class GatewayConfig:
    """PACER Gateway configuration"""
    max_concurrent_requests: int = 10
    request_timeout_seconds: int = 120
    enable_cost_tracking: bool = True
    enable_compliance_monitoring: bool = True
    enable_request_caching: bool = True
    cache_ttl_hours: int = 24
    retry_failed_requests: bool = True
    max_retries: int = 2
    queue_batch_size: int = 50


class PacerGateway:
    """Main PACER Gateway service"""
    
    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig()
        self.active_clients: Dict[str, PacerClient] = {}
        self.request_queue: List[QueuedRequest] = []
        self.request_logs: List[RequestLog] = []
        
        # Service instances
        self.account_manager = account_manager
        self.cost_tracker = cost_tracker
        
        # Semaphore for concurrent request limiting
        self.request_semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        logger.info("PACER Gateway initialized")
    
    async def search_cases(
        self,
        search_criteria: SearchCriteria,
        court_ids: List[str] = None,
        user_id: int = None,
        client_request_id: str = None
    ) -> Dict[str, Any]:
        """Search for cases across one or more courts"""
        
        try:
            if not court_ids:
                court_ids = search_criteria.court_ids or list(FEDERAL_COURTS.keys())[:5]  # Limit default search
            
            logger.info(f"Starting case search across {len(court_ids)} courts")
            
            # Validate courts
            valid_courts = []
            for court_id in court_ids:
                court_info = get_court_info(court_id)
                if court_info:
                    valid_courts.append(court_info)
                else:
                    logger.warning(f"Unknown court ID: {court_id}")
            
            if not valid_courts:
                return {
                    "success": False,
                    "error": "No valid courts specified",
                    "results": []
                }
            
            # Estimate cost
            estimated_cost = await self._estimate_search_cost(len(valid_courts))
            
            # Execute searches concurrently
            search_tasks = []
            for court_info in valid_courts:
                task = self._search_court(
                    court_info,
                    search_criteria,
                    user_id,
                    client_request_id,
                    estimated_cost // len(valid_courts)
                )
                search_tasks.append(task)
            
            # Wait for all searches to complete
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Process results
            successful_results = []
            failed_courts = []
            total_cost_cents = 0
            
            for i, result in enumerate(search_results):
                court_id = valid_courts[i].court_id
                
                if isinstance(result, Exception):
                    failed_courts.append({
                        "court_id": court_id,
                        "error": str(result)
                    })
                    logger.error(f"Search failed for court {court_id}: {str(result)}")
                else:
                    successful_results.extend(result.get("cases", []))
                    total_cost_cents += result.get("cost_cents", 0)
            
            return {
                "success": len(successful_results) > 0,
                "total_results": len(successful_results),
                "results": successful_results,
                "cost_dollars": total_cost_cents / 100.0,
                "courts_searched": len(valid_courts),
                "successful_courts": len(valid_courts) - len(failed_courts),
                "failed_courts": failed_courts,
                "search_criteria": search_criteria.__dict__,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Case search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    async def get_docket_report(
        self,
        case_number: str,
        court_id: str,
        include_documents: bool = True,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Get docket report for a specific case"""
        
        try:
            logger.info(f"Getting docket report for case {case_number} in court {court_id}")
            
            # Get court info
            court_info = get_court_info(court_id)
            if not court_info:
                return {
                    "success": False,
                    "error": f"Unknown court ID: {court_id}",
                    "docket_entries": []
                }
            
            # Check cache first
            cache_key = f"pacer:docket:{court_id}:{case_number}"
            if self.config.enable_request_caching:
                cached_result = await cache_manager.get(cache_key)
                if cached_result:
                    logger.info(f"Returning cached docket report for {case_number}")
                    return cached_result
            
            # Estimate cost
            estimated_cost = await self._estimate_docket_cost(include_documents)
            
            # Get client
            client = await self._get_court_client(court_info, user_id)
            if not client:
                return {
                    "success": False,
                    "error": f"Could not get PACER client for court {court_id}",
                    "docket_entries": []
                }
            
            try:
                # Make request with cost approval
                async with self.request_semaphore:
                    # Check cost approval
                    approved, reason, _ = await cost_tracker.check_cost_approval(
                        client.account.account_id,
                        estimated_cost,
                        court_id,
                        user_id
                    )
                    
                    if not approved:
                        return {
                            "success": False,
                            "error": f"Cost limit exceeded: {reason}",
                            "docket_entries": []
                        }
                    
                    # Make PACER request
                    response = await client.get_docket_report(
                        case_number,
                        include_documents,
                        date_from,
                        date_to
                    )
                    
                    # Process response
                    result = await self._process_docket_response(
                        response, 
                        case_number,
                        court_id,
                        client.account.account_id,
                        user_id
                    )
                    
                    # Cache result
                    if self.config.enable_request_caching and result["success"]:
                        await cache_manager.set(
                            cache_key,
                            result,
                            ttl=self.config.cache_ttl_hours * 3600
                        )
                    
                    return result
                    
            finally:
                await self._release_client(client)
        
        except Exception as e:
            logger.error(f"Docket report failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "docket_entries": []
            }
    
    async def download_document(
        self,
        document_url: str,
        case_number: str,
        court_id: str,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Download a document from PACER"""
        
        try:
            logger.info(f"Downloading document for case {case_number}")
            
            # Get court info
            court_info = get_court_info(court_id)
            if not court_info:
                return {
                    "success": False,
                    "error": f"Unknown court ID: {court_id}",
                    "document_data": None
                }
            
            # Estimate cost (rough estimate)
            estimated_cost = await self._estimate_document_cost()
            
            # Get client
            client = await self._get_court_client(court_info, user_id)
            if not client:
                return {
                    "success": False,
                    "error": f"Could not get PACER client for court {court_id}",
                    "document_data": None
                }
            
            try:
                async with self.request_semaphore:
                    # Check cost approval
                    approved, reason, _ = await cost_tracker.check_cost_approval(
                        client.account.account_id,
                        estimated_cost,
                        court_id,
                        user_id
                    )
                    
                    if not approved:
                        return {
                            "success": False,
                            "error": f"Cost limit exceeded: {reason}",
                            "document_data": None
                        }
                    
                    # Download document
                    response = await client.get_document(document_url, case_number)
                    
                    # Process response
                    result = await self._process_document_response(
                        response,
                        case_number,
                        court_id,
                        client.account.account_id,
                        user_id
                    )
                    
                    return result
                    
            finally:
                await self._release_client(client)
        
        except Exception as e:
            logger.error(f"Document download failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "document_data": None
            }
    
    async def queue_bulk_request(
        self,
        request_type: str,
        requests: List[Dict[str, Any]],
        priority: int = 1,
        user_id: int = None
    ) -> str:
        """Queue bulk requests for batch processing"""
        
        try:
            queued_requests = []
            
            for i, request_data in enumerate(requests):
                queued_request = QueuedRequest(
                    request_id=f"bulk_{request_type}_{int(datetime.now().timestamp())}_{i}",
                    account_id="",  # Will be assigned during processing
                    priority=priority,
                    request_type=request_type,
                    request_data=request_data
                )
                
                queued_requests.append(queued_request)
                self.request_queue.append(queued_request)
            
            logger.info(f"Queued {len(queued_requests)} bulk {request_type} requests")
            
            # Start background processing
            asyncio.create_task(self._process_request_queue())
            
            return f"bulk_{request_type}_{int(datetime.now().timestamp())}"
            
        except Exception as e:
            logger.error(f"Failed to queue bulk requests: {str(e)}")
            raise
    
    async def get_cost_analysis(
        self,
        account_id: str = None,
        period: BillingPeriod = BillingPeriod.MONTHLY,
        court_id: str = None
    ) -> Dict[str, Any]:
        """Get cost analysis and billing information"""
        
        try:
            analysis = await cost_tracker.get_cost_analysis(
                account_id=account_id,
                court_id=court_id,
                period=period
            )
            
            return {
                "success": True,
                "analysis": {
                    "period": period.value,
                    "start_date": analysis.period_start.isoformat(),
                    "end_date": analysis.period_end.isoformat(),
                    "total_cost_dollars": analysis.total_cost_dollars,
                    "total_requests": analysis.total_requests,
                    "total_pages": analysis.total_pages,
                    "total_documents": analysis.total_documents,
                    "average_cost_per_request": analysis.average_cost_per_request_cents / 100.0,
                    "cost_by_court": {k: v/100.0 for k, v in analysis.cost_by_court.items()},
                    "peak_cost_day": analysis.peak_cost_day.isoformat() if analysis.peak_cost_day else None,
                    "peak_cost_amount": analysis.peak_cost_amount_cents / 100.0
                }
            }
            
        except Exception as e:
            logger.error(f"Cost analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_account_status(self, account_id: str = None) -> Dict[str, Any]:
        """Get account status and usage information"""
        
        try:
            if account_id:
                account_summary = await self.account_manager.get_account_summary(account_id)
                return {
                    "success": True,
                    "account_summary": account_summary
                }
            else:
                # Get all pool statuses
                pool_statuses = {}
                for pool_name in self.account_manager.account_pools.keys():
                    pool_statuses[pool_name] = await self.account_manager.get_pool_status(pool_name)
                
                return {
                    "success": True,
                    "pool_statuses": pool_statuses
                }
                
        except Exception as e:
            logger.error(f"Account status check failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _search_court(
        self,
        court_info: CourtInfo,
        search_criteria: SearchCriteria,
        user_id: int,
        client_request_id: str,
        estimated_cost: int
    ) -> Dict[str, Any]:
        """Search a specific court"""
        
        try:
            # Get client
            client = await self._get_court_client(court_info, user_id)
            if not client:
                raise PacerError(f"Could not get client for court {court_info.court_id}")
            
            try:
                # Check cost approval
                approved, reason, _ = await cost_tracker.check_cost_approval(
                    client.account.account_id,
                    estimated_cost,
                    court_info.court_id,
                    user_id
                )
                
                if not approved:
                    raise PacerError(f"Cost limit exceeded: {reason}")
                
                # Build search parameters
                search_params = self._build_search_params(search_criteria)
                
                # Make search request
                response = await client.search_cases(search_params, search_criteria.max_results)
                
                # Process results
                cases = self._parse_search_results(response.data, court_info.court_id)
                
                # Track cost
                await self._track_request_cost(
                    client.account.account_id,
                    court_info.court_id,
                    "case_search",
                    response.cost_cents,
                    user_id,
                    len(cases)
                )
                
                return {
                    "court_id": court_info.court_id,
                    "cases": cases,
                    "cost_cents": response.cost_cents,
                    "total_found": len(cases)
                }
                
            finally:
                await self._release_client(client)
                
        except Exception as e:
            logger.error(f"Court search failed for {court_info.court_id}: {str(e)}")
            raise
    
    async def _get_court_client(
        self,
        court_info: CourtInfo,
        user_id: int = None
    ) -> Optional[PacerClient]:
        """Get or create a PACER client for a court"""
        
        try:
            # Check for existing client
            client_key = f"{court_info.court_id}_{user_id or 'default'}"
            
            if client_key in self.active_clients:
                client = self.active_clients[client_key]
                if client.session.is_valid():
                    return client
                else:
                    # Clean up expired client
                    await client.logout()
                    del self.active_clients[client_key]
            
            # Get available account
            account_result = await self.account_manager.get_available_account(
                court_id=court_info.court_id,
                selection_strategy="least_used"
            )
            
            if not account_result:
                logger.warning(f"No available accounts for court {court_info.court_id}")
                return None
            
            account, pool_name = account_result
            
            # Create new client
            client = PacerClient(account, court_info, timeout=self.config.request_timeout_seconds)
            
            # Authenticate
            if not await client.authenticate():
                logger.error(f"Authentication failed for court {court_info.court_id}")
                await self.account_manager.release_account(account.account_id, pool_name)
                return None
            
            # Store active client
            self.active_clients[client_key] = client
            
            logger.info(f"Created PACER client for court {court_info.court_id}")
            return client
            
        except Exception as e:
            logger.error(f"Failed to get court client: {str(e)}")
            return None
    
    async def _release_client(self, client: PacerClient):
        """Release a client back to the pool"""
        
        try:
            # Find and remove from active clients
            client_key = None
            for key, active_client in self.active_clients.items():
                if active_client == client:
                    client_key = key
                    break
            
            if client_key:
                del self.active_clients[client_key]
            
            # Release account
            await self.account_manager.release_account(client.account.account_id)
            
        except Exception as e:
            logger.error(f"Failed to release client: {str(e)}")
    
    async def _estimate_search_cost(self, court_count: int) -> int:
        """Estimate cost for case searches"""
        return court_count * 30  # $0.30 per search
    
    async def _estimate_docket_cost(self, include_documents: bool) -> int:
        """Estimate cost for docket report"""
        base_cost = 0  # Docket sheets are free
        if include_documents:
            base_cost += 500  # Estimate $5.00 for documents
        return base_cost
    
    async def _estimate_document_cost(self) -> int:
        """Estimate cost for document download"""
        return 300  # Estimate $3.00 per document
    
    def _build_search_params(self, criteria: SearchCriteria) -> Dict[str, Any]:
        """Build search parameters from criteria"""
        
        params = {}
        
        if criteria.case_number:
            params['case_number'] = criteria.case_number
        if criteria.case_title:
            params['case_title'] = criteria.case_title
        if criteria.party_name:
            params['party_name'] = criteria.party_name
        if criteria.attorney_name:
            params['attorney_name'] = criteria.attorney_name
        if criteria.judge_name:
            params['judge_name'] = criteria.judge_name
        if criteria.nature_of_suit:
            params['nature_of_suit'] = criteria.nature_of_suit
        if criteria.date_filed_from:
            params['date_filed_from'] = criteria.date_filed_from
        if criteria.date_filed_to:
            params['date_filed_to'] = criteria.date_filed_to
        
        return params
    
    def _parse_search_results(self, search_data: Any, court_id: str) -> List[Dict[str, Any]]:
        """Parse search results into standardized format"""
        
        cases = []
        
        if isinstance(search_data, list):
            for case_data in search_data:
                if isinstance(case_data, dict):
                    parsed_case = {
                        'case_number': case_data.get('case_number', ''),
                        'case_title': case_data.get('case_title', ''),
                        'court_id': court_id,
                        'filed_date': case_data.get('filed_date', ''),
                        'case_link': case_data.get('case_link', ''),
                        'metadata': case_data
                    }
                    cases.append(parsed_case)
        
        return cases
    
    async def _process_docket_response(
        self,
        response: PacerResponse,
        case_number: str,
        court_id: str,
        account_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """Process docket report response"""
        
        try:
            if not response.is_success:
                return {
                    "success": False,
                    "error": f"PACER request failed: {response.status_code}",
                    "docket_entries": []
                }
            
            # Extract docket data
            docket_data = response.data if isinstance(response.data, dict) else {}
            case_info = docket_data.get('case_info', {})
            entries = docket_data.get('docket_entries', [])
            
            # Track cost
            await self._track_request_cost(
                account_id,
                court_id,
                "docket_report",
                response.cost_cents,
                user_id,
                len(entries)
            )
            
            return {
                "success": True,
                "case_number": case_number,
                "court_id": court_id,
                "case_info": case_info,
                "docket_entries": entries,
                "total_entries": len(entries),
                "cost_dollars": response.cost_dollars,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to process docket response: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "docket_entries": []
            }
    
    async def _process_document_response(
        self,
        response: PacerResponse,
        case_number: str,
        court_id: str,
        account_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """Process document download response"""
        
        try:
            if not response.is_success:
                return {
                    "success": False,
                    "error": f"Document download failed: {response.status_code}",
                    "document_data": None
                }
            
            # Track cost
            await self._track_request_cost(
                account_id,
                court_id,
                "document_download",
                response.cost_cents,
                user_id,
                1
            )
            
            return {
                "success": True,
                "case_number": case_number,
                "court_id": court_id,
                "document_data": response.raw_content,
                "page_count": response.page_count,
                "cost_dollars": response.cost_dollars,
                "content_type": "application/pdf",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to process document response: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "document_data": None
            }
    
    async def _track_request_cost(
        self,
        account_id: str,
        court_id: str,
        request_type: str,
        cost_cents: int,
        user_id: int = None,
        item_count: int = 0
    ):
        """Track request cost and usage"""
        
        try:
            # Record billing
            await cost_tracker.record_cost(
                account_id=account_id,
                court_id=court_id,
                description=f"{request_type} request",
                cost_cents=cost_cents,
                document_count=item_count if request_type == "document_download" else 0,
                category=CostCategory.SEARCH_FEES if "search" in request_type else CostCategory.DOCUMENT_ACCESS
            )
            
            # Track account usage
            await self.account_manager.track_usage(
                account_id=account_id,
                court_id=court_id,
                request_type=request_type,
                cost_cents=cost_cents,
                document_count=item_count
            )
            
        except Exception as e:
            logger.error(f"Failed to track request cost: {str(e)}")
    
    async def _process_request_queue(self):
        """Process queued requests in batches"""
        
        try:
            while self.request_queue:
                # Get batch of requests
                batch = self.request_queue[:self.config.queue_batch_size]
                self.request_queue = self.request_queue[self.config.queue_batch_size:]
                
                # Process batch concurrently
                tasks = []
                for request in batch:
                    if request.status == RequestStatus.PENDING:
                        task = self._process_queued_request(request)
                        tasks.append(task)
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Wait before processing next batch
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Request queue processing failed: {str(e)}")
    
    async def _process_queued_request(self, request: QueuedRequest):
        """Process a single queued request"""
        
        try:
            request.status = RequestStatus.PROCESSING
            request.started_at = datetime.now(timezone.utc)
            
            # Process based on request type
            if request.request_type == "case_search":
                # Process case search request
                pass
            elif request.request_type == "docket_report":
                # Process docket report request
                pass
            elif request.request_type == "document_download":
                # Process document download request
                pass
            
            request.status = RequestStatus.COMPLETED
            request.completed_at = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Queued request processing failed: {str(e)}")
            request.status = RequestStatus.FAILED
            request.error_message = str(e)
            request.retry_count += 1
            
            # Retry if allowed
            if request.can_retry():
                request.status = RequestStatus.PENDING
                self.request_queue.append(request)


# Global gateway instance
pacer_gateway = PacerGateway()