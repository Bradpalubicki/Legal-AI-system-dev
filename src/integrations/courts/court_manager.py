"""
Court Integration Manager

Unified management system for all court API integrations including
federal courts, state courts, and fallback methods with comprehensive
data aggregation and response handling.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

from .federal_courts import PacerAPIClient, CMECFIntegration, FederalCourtCalendar, JudgeAssignmentAPI, FederalCourtDistrict, CourtCase, CourtDocument
from .state_courts import StateCourtManager, StateJurisdiction, StateCourtCase
from .fallback_methods import FallbackManager, FallbackMethod, FallbackResult

logger = logging.getLogger(__name__)

class CourtSystemType(Enum):
    """Type of court system"""
    FEDERAL = "federal"
    STATE = "state"
    LOCAL = "local"
    TRIBAL = "tribal"
    ADMINISTRATIVE = "administrative"

class CourtLevel(Enum):
    """Level of court"""
    SUPREME = "supreme"
    APPELLATE = "appellate"
    DISTRICT = "district"
    TRIAL = "trial"
    MUNICIPAL = "municipal"
    SPECIALTY = "specialty"

@dataclass
class CourtDataRequest:
    """Request for court data"""
    request_id: str
    court_system: CourtSystemType
    jurisdiction: Union[FederalCourtDistrict, StateJurisdiction, str]
    search_criteria: Dict[str, Any]
    requested_data_types: List[str] = field(default_factory=list)
    priority: str = "normal"  # low, normal, high, urgent
    timeout_seconds: int = 30
    use_fallback: bool = True
    fallback_methods: Optional[List[FallbackMethod]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CourtAPIResponse:
    """Response from court API integration"""
    request_id: str
    success: bool
    court_system: CourtSystemType
    jurisdiction: Union[FederalCourtDistrict, StateJurisdiction, str]
    data_source: str  # API name or fallback method
    response_time_ms: int
    data: List[Union[CourtCase, StateCourtCase, Dict[str, Any]]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    fallback_used: bool = False
    confidence_score: float = 1.0  # 0.0 to 1.0

class CourtIntegrationManager:
    """
    Main manager for all court system integrations
    Coordinates federal, state, and fallback systems
    """

    def __init__(self):
        # Initialize all court system clients
        self.pacer_client = PacerAPIClient()
        self.cmecf_integration = CMECFIntegration()
        self.federal_calendar = FederalCourtCalendar()
        self.judge_assignment = JudgeAssignmentAPI()

        self.state_court_manager = StateCourtManager()
        self.fallback_manager = FallbackManager()

        # Performance tracking
        self.request_history: List[CourtAPIResponse] = []
        self.performance_metrics: Dict[str, Any] = {
            'total_requests': 0,
            'successful_requests': 0,
            'fallback_usage': 0,
            'average_response_time': 0,
            'system_availability': {}
        }

        # Circuit breaker for failed services
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}

    async def search_all_courts(self, request: CourtDataRequest) -> CourtAPIResponse:
        """
        Search across all available court systems based on request parameters
        """
        start_time = datetime.now()

        response = CourtAPIResponse(
            request_id=request.request_id,
            success=False,
            court_system=request.court_system,
            jurisdiction=request.jurisdiction,
            data_source="aggregated",
            response_time_ms=0
        )

        try:
            all_data = []
            primary_success = False

            # Route to appropriate court system
            if request.court_system == CourtSystemType.FEDERAL:
                federal_data = await self._search_federal_courts(request)
                if federal_data.success:
                    all_data.extend(federal_data.data)
                    primary_success = True
                    response.data_source = federal_data.data_source

            elif request.court_system == CourtSystemType.STATE:
                state_data = await self._search_state_courts(request)
                if state_data.success:
                    all_data.extend(state_data.data)
                    primary_success = True
                    response.data_source = state_data.data_source

            # Use fallback methods if primary search failed or no results
            if (not primary_success or not all_data) and request.use_fallback:
                fallback_data = await self._search_fallback_methods(request)
                if fallback_data:
                    all_data.extend(fallback_data)
                    response.fallback_used = True
                    if not primary_success:
                        response.data_source = "fallback_methods"

            # Deduplicate and merge results
            deduplicated_data = self._deduplicate_court_cases(all_data)

            response.success = len(deduplicated_data) > 0
            response.data = deduplicated_data
            response.confidence_score = self._calculate_confidence_score(response)

        except Exception as e:
            logger.error(f"Error in comprehensive court search: {str(e)}")
            response.errors.append(str(e))

        # Calculate response time and update metrics
        end_time = datetime.now()
        response.response_time_ms = int((end_time - start_time).total_seconds() * 1000)

        await self._update_performance_metrics(response)
        self.request_history.append(response)

        return response

    async def _search_federal_courts(self, request: CourtDataRequest) -> CourtAPIResponse:
        """Search federal court systems"""
        start_time = datetime.now()

        response = CourtAPIResponse(
            request_id=request.request_id,
            success=False,
            court_system=CourtSystemType.FEDERAL,
            jurisdiction=request.jurisdiction,
            data_source="federal_courts",
            response_time_ms=0
        )

        try:
            if not isinstance(request.jurisdiction, FederalCourtDistrict):
                # Try to convert string to FederalCourtDistrict
                try:
                    jurisdiction = FederalCourtDistrict(str(request.jurisdiction).lower())
                except ValueError:
                    response.errors.append(f"Invalid federal district: {request.jurisdiction}")
                    return response
            else:
                jurisdiction = request.jurisdiction

            # Check circuit breaker
            if self._is_circuit_breaker_open("federal_courts"):
                response.warnings.append("Federal courts API circuit breaker is open")
                return response

            search_criteria = request.search_criteria

            # Search cases using PACER
            cases = await self.pacer_client.search_cases(
                district=jurisdiction,
                case_name=search_criteria.get('case_name'),
                case_number=search_criteria.get('case_number'),
                party_name=search_criteria.get('party_name'),
                date_range=search_criteria.get('date_range')
            )

            response.success = True
            response.data = cases
            response.metadata['source'] = 'PACER'
            response.metadata['district'] = jurisdiction.value

        except Exception as e:
            logger.error(f"Error searching federal courts: {str(e)}")
            response.errors.append(str(e))
            await self._record_circuit_breaker_failure("federal_courts")

        response.response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        return response

    async def _search_state_courts(self, request: CourtDataRequest) -> CourtAPIResponse:
        """Search state court systems"""
        start_time = datetime.now()

        response = CourtAPIResponse(
            request_id=request.request_id,
            success=False,
            court_system=CourtSystemType.STATE,
            jurisdiction=request.jurisdiction,
            data_source="state_courts",
            response_time_ms=0
        )

        try:
            if not isinstance(request.jurisdiction, StateJurisdiction):
                # Try to convert string to StateJurisdiction
                try:
                    jurisdiction = StateJurisdiction(str(request.jurisdiction).upper())
                except ValueError:
                    response.errors.append(f"Invalid state jurisdiction: {request.jurisdiction}")
                    return response
            else:
                jurisdiction = request.jurisdiction

            # Check circuit breaker
            if self._is_circuit_breaker_open(f"state_courts_{jurisdiction.value}"):
                response.warnings.append(f"State courts API circuit breaker is open for {jurisdiction.value}")
                return response

            search_criteria = request.search_criteria

            # Search using state court manager
            state_cases = await self.state_court_manager.search_jurisdiction_cases(
                jurisdiction=jurisdiction,
                **search_criteria
            )

            response.success = len(state_cases) > 0
            response.data = state_cases
            response.metadata['source'] = f'{jurisdiction.value}_courts'
            response.metadata['jurisdiction'] = jurisdiction.value

        except Exception as e:
            logger.error(f"Error searching state courts: {str(e)}")
            response.errors.append(str(e))
            await self._record_circuit_breaker_failure(f"state_courts_{request.jurisdiction}")

        response.response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        return response

    async def _search_fallback_methods(self, request: CourtDataRequest) -> List[Dict[str, Any]]:
        """Search using fallback methods"""
        try:
            court_identifier = f"{request.court_system.value}_{request.jurisdiction}"
            case_number = request.search_criteria.get('case_number', '')

            fallback_methods = request.fallback_methods
            if not fallback_methods:
                # Use default fallback methods based on availability
                fallback_methods = [
                    FallbackMethod.MANUAL_ENTRY,
                    FallbackMethod.EMAIL_PARSING,
                    FallbackMethod.PDF_EXTRACTION
                ]

            results = await self.fallback_manager.collect_case_data(
                court_identifier=court_identifier,
                case_number=case_number,
                preferred_methods=fallback_methods
            )

            # Convert fallback results to court case format
            fallback_data = []
            for result in results:
                if result.success:
                    fallback_data.append({
                        'case_number': case_number,
                        'case_name': result.data.get('case_name', 'Unknown'),
                        'court_system': request.court_system.value,
                        'jurisdiction': str(request.jurisdiction),
                        'source': f"fallback_{result.method.value}",
                        'confidence': result.confidence,
                        'data': result.data
                    })

            return fallback_data

        except Exception as e:
            logger.error(f"Error in fallback search: {str(e)}")
            return []

    def _deduplicate_court_cases(self, cases: List[Union[CourtCase, StateCourtCase, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Remove duplicate cases from combined results"""
        seen_cases = set()
        deduplicated = []

        for case in cases:
            # Create a unique identifier for the case
            if hasattr(case, 'case_number'):
                case_key = (case.case_number, getattr(case, 'district', None) or getattr(case, 'jurisdiction', None))
            elif isinstance(case, dict):
                case_key = (case.get('case_number'), case.get('jurisdiction') or case.get('district'))
            else:
                continue

            if case_key not in seen_cases:
                seen_cases.add(case_key)

                # Convert to standardized dict format
                if hasattr(case, '__dict__'):
                    case_dict = self._convert_case_to_dict(case)
                else:
                    case_dict = case

                deduplicated.append(case_dict)

        return deduplicated

    def _convert_case_to_dict(self, case: Union[CourtCase, StateCourtCase]) -> Dict[str, Any]:
        """Convert case object to dictionary format"""
        case_dict = {
            'case_number': case.case_number,
            'case_name': case.case_name,
            'filing_date': case.filing_date.isoformat() if hasattr(case.filing_date, 'isoformat') else str(case.filing_date),
            'case_type': case.case_type,
            'status': case.status,
            'judge': case.judge,
            'parties': getattr(case, 'parties', []),
            'attorneys': getattr(case, 'attorneys', [])
        }

        # Add system-specific fields
        if hasattr(case, 'district'):
            case_dict['district'] = case.district.value if hasattr(case.district, 'value') else str(case.district)
            case_dict['court_system'] = 'federal'
        elif hasattr(case, 'jurisdiction'):
            case_dict['jurisdiction'] = case.jurisdiction.value if hasattr(case.jurisdiction, 'value') else str(case.jurisdiction)
            case_dict['court_system'] = 'state'
            case_dict['court_level'] = getattr(case, 'court_level', None)

        return case_dict

    def _calculate_confidence_score(self, response: CourtAPIResponse) -> float:
        """Calculate confidence score for response"""
        base_score = 1.0

        # Reduce score if fallback was used
        if response.fallback_used:
            base_score *= 0.7

        # Reduce score for slow responses
        if response.response_time_ms > 10000:  # > 10 seconds
            base_score *= 0.8
        elif response.response_time_ms > 5000:  # > 5 seconds
            base_score *= 0.9

        # Reduce score if there were warnings
        if response.warnings:
            base_score *= (1.0 - (len(response.warnings) * 0.1))

        # Reduce score if circuit breaker was involved
        if any('circuit breaker' in warning.lower() for warning in response.warnings):
            base_score *= 0.5

        return max(0.0, min(1.0, base_score))

    async def get_court_calendar(self, court_system: CourtSystemType,
                                jurisdiction: Union[FederalCourtDistrict, StateJurisdiction],
                                judge: Optional[str] = None,
                                date_range: Optional[Tuple[datetime, datetime]] = None) -> List[Dict[str, Any]]:
        """Get court calendar across systems"""
        try:
            calendar_events = []

            if court_system == CourtSystemType.FEDERAL and isinstance(jurisdiction, FederalCourtDistrict):
                events = await self.federal_calendar.get_court_calendar(jurisdiction, judge, date_range)
                calendar_events.extend(events)

            elif court_system == CourtSystemType.STATE and isinstance(jurisdiction, StateJurisdiction):
                # State court calendars would be handled by individual state APIs
                # This would be implemented based on available state court APIs
                logger.info(f"State court calendar for {jurisdiction} not yet implemented")

            return calendar_events

        except Exception as e:
            logger.error(f"Error getting court calendar: {str(e)}")
            return []

    async def submit_electronic_filing(self, court_system: CourtSystemType,
                                     jurisdiction: Union[FederalCourtDistrict, StateJurisdiction],
                                     case_number: str,
                                     document_data: Dict[str, Any]) -> bool:
        """Submit electronic filing to appropriate court system"""
        try:
            if court_system == CourtSystemType.FEDERAL and isinstance(jurisdiction, FederalCourtDistrict):
                return await self.cmecf_integration.submit_filing(jurisdiction, case_number, document_data)

            elif court_system == CourtSystemType.STATE:
                # State e-filing would be handled by individual state systems
                logger.warning(f"Electronic filing for state court {jurisdiction} not yet implemented")
                return False

            return False

        except Exception as e:
            logger.error(f"Error submitting electronic filing: {str(e)}")
            return False

    def _is_circuit_breaker_open(self, service_name: str) -> bool:
        """Check if circuit breaker is open for service"""
        if service_name not in self.circuit_breakers:
            return False

        breaker = self.circuit_breakers[service_name]

        # Check if breaker should be reset
        if datetime.now() > breaker.get('reset_time', datetime.min):
            breaker['failures'] = 0
            breaker['is_open'] = False
            return False

        return breaker.get('is_open', False)

    async def _record_circuit_breaker_failure(self, service_name: str):
        """Record failure for circuit breaker"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = {
                'failures': 0,
                'is_open': False,
                'failure_threshold': 5,
                'reset_timeout_minutes': 5
            }

        breaker = self.circuit_breakers[service_name]
        breaker['failures'] += 1

        # Open circuit breaker if threshold exceeded
        if breaker['failures'] >= breaker['failure_threshold']:
            breaker['is_open'] = True
            breaker['reset_time'] = datetime.now() + timedelta(minutes=breaker['reset_timeout_minutes'])
            logger.warning(f"Circuit breaker opened for service {service_name}")

    async def _update_performance_metrics(self, response: CourtAPIResponse):
        """Update performance metrics"""
        metrics = self.performance_metrics

        metrics['total_requests'] += 1
        if response.success:
            metrics['successful_requests'] += 1

        if response.fallback_used:
            metrics['fallback_usage'] += 1

        # Update average response time
        current_avg = metrics['average_response_time']
        total_requests = metrics['total_requests']

        metrics['average_response_time'] = (
            (current_avg * (total_requests - 1)) + response.response_time_ms
        ) / total_requests

        # Update system availability
        system_key = f"{response.court_system.value}_{response.jurisdiction}"
        if system_key not in metrics['system_availability']:
            metrics['system_availability'][system_key] = {'total': 0, 'successful': 0}

        metrics['system_availability'][system_key]['total'] += 1
        if response.success:
            metrics['system_availability'][system_key]['successful'] += 1

    async def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        metrics = self.performance_metrics

        # Calculate availability percentages
        availability_percentages = {}
        for system, counts in metrics['system_availability'].items():
            if counts['total'] > 0:
                availability_percentages[system] = (counts['successful'] / counts['total']) * 100

        return {
            'summary': {
                'total_requests': metrics['total_requests'],
                'success_rate': (metrics['successful_requests'] / metrics['total_requests'] * 100)
                               if metrics['total_requests'] > 0 else 0,
                'fallback_usage_rate': (metrics['fallback_usage'] / metrics['total_requests'] * 100)
                                      if metrics['total_requests'] > 0 else 0,
                'average_response_time_ms': metrics['average_response_time']
            },
            'system_availability': availability_percentages,
            'circuit_breakers': {
                name: {
                    'is_open': breaker['is_open'],
                    'failure_count': breaker['failures'],
                    'reset_time': breaker.get('reset_time', '').isoformat() if breaker.get('reset_time') else None
                }
                for name, breaker in self.circuit_breakers.items()
            },
            'recent_requests': [
                {
                    'request_id': r.request_id,
                    'success': r.success,
                    'court_system': r.court_system.value,
                    'jurisdiction': str(r.jurisdiction),
                    'response_time_ms': r.response_time_ms,
                    'fallback_used': r.fallback_used,
                    'confidence_score': r.confidence_score
                }
                for r in self.request_history[-10:]  # Last 10 requests
            ]
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all integrated systems"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'systems': {}
        }

        try:
            # Check PACER/Federal systems
            try:
                # Simple connectivity test
                await asyncio.wait_for(
                    self.pacer_client.authenticate(),
                    timeout=10.0
                )
                health_status['systems']['federal_pacer'] = 'healthy'
            except asyncio.TimeoutError:
                health_status['systems']['federal_pacer'] = 'timeout'
                health_status['overall_status'] = 'degraded'
            except Exception:
                health_status['systems']['federal_pacer'] = 'unhealthy'
                health_status['overall_status'] = 'degraded'

            # Check state court systems
            state_systems_healthy = 0
            total_state_systems = len(StateJurisdiction)

            for jurisdiction in StateJurisdiction:
                try:
                    # Simple test search
                    test_result = await asyncio.wait_for(
                        self.state_court_manager.search_jurisdiction_cases(
                            jurisdiction=jurisdiction,
                            case_number='test'
                        ),
                        timeout=5.0
                    )
                    health_status['systems'][f'state_{jurisdiction.value}'] = 'healthy'
                    state_systems_healthy += 1
                except asyncio.TimeoutError:
                    health_status['systems'][f'state_{jurisdiction.value}'] = 'timeout'
                except Exception:
                    health_status['systems'][f'state_{jurisdiction.value}'] = 'unhealthy'

            # Determine overall state system health
            if state_systems_healthy == 0:
                health_status['overall_status'] = 'unhealthy'
            elif state_systems_healthy < total_state_systems * 0.5:
                health_status['overall_status'] = 'degraded'

            # Check fallback systems
            try:
                fallback_healthy = await self.fallback_manager.health_check()
                health_status['systems']['fallback_methods'] = 'healthy' if fallback_healthy else 'unhealthy'
                if not fallback_healthy and health_status['overall_status'] == 'healthy':
                    health_status['overall_status'] = 'degraded'
            except Exception:
                health_status['systems']['fallback_methods'] = 'unhealthy'
                if health_status['overall_status'] == 'healthy':
                    health_status['overall_status'] = 'degraded'

        except Exception as e:
            logger.error(f"Error in health check: {str(e)}")
            health_status['overall_status'] = 'error'
            health_status['error'] = str(e)

        return health_status