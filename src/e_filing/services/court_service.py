"""
Court Service

Service for managing court information, configurations, and
integration with multiple court systems.
"""

import logging
from datetime import datetime, time
from typing import Dict, List, Optional
from uuid import UUID

from ..models import (
    CourtInfo,
    CourtType,
    FilingConfiguration,
    EFilingCredentials
)

logger = logging.getLogger(__name__)


class CourtService:
    """
    Service for managing court information and system configurations
    """
    
    def __init__(self):
        self.courts: Dict[str, CourtInfo] = {}
        self.configurations: Dict[str, FilingConfiguration] = {}
        self.system_status: Dict[str, Dict] = {}
        
        # Initialize with sample court data
        self._initialize_sample_courts()
        
        logger.info("Court service initialized")
    
    def _initialize_sample_courts(self):
        """Initialize with sample court data for major jurisdictions"""
        
        # Federal District Courts
        federal_courts = [
            {
                "name": "United States District Court for the Southern District of New York",
                "court_type": CourtType.FEDERAL_DISTRICT,
                "jurisdiction": "Southern District of New York",
                "address": "500 Pearl Street",
                "city": "New York",
                "state": "NY", 
                "zip_code": "10007",
                "cm_ecf_url": "https://ecf.nysd.uscourts.gov",
                "pacer_site": "https://pacer.nysd.uscourts.gov",
                "efiling_system": "CM/ECF",
                "local_rules_url": "https://nysd.uscourts.gov/rules",
                "filing_fee_schedule": {
                    "case_opening": "402.00",
                    "motion": "0.00",
                    "appeal": "505.00"
                },
                "max_file_size_mb": 50,
                "business_hours": {
                    "monday": "9:00 AM - 5:00 PM",
                    "tuesday": "9:00 AM - 5:00 PM",
                    "wednesday": "9:00 AM - 5:00 PM",
                    "thursday": "9:00 AM - 5:00 PM",
                    "friday": "9:00 AM - 5:00 PM"
                }
            },
            {
                "name": "United States District Court for the Central District of California",
                "court_type": CourtType.FEDERAL_DISTRICT,
                "jurisdiction": "Central District of California",
                "address": "350 West 1st Street",
                "city": "Los Angeles",
                "state": "CA",
                "zip_code": "90012",
                "cm_ecf_url": "https://ecf.cacd.uscourts.gov",
                "pacer_site": "https://pacer.cacd.uscourts.gov",
                "efiling_system": "CM/ECF",
                "filing_fee_schedule": {
                    "case_opening": "402.00",
                    "motion": "0.00"
                },
                "max_file_size_mb": 50
            },
            {
                "name": "United States Bankruptcy Court for the Southern District of New York",
                "court_type": CourtType.FEDERAL_BANKRUPTCY,
                "jurisdiction": "Southern District of New York",
                "address": "300 Quarropas Street",
                "city": "White Plains",
                "state": "NY",
                "zip_code": "10601",
                "cm_ecf_url": "https://ecf.nysb.uscourts.gov",
                "efiling_system": "CM/ECF",
                "filing_fee_schedule": {
                    "case_opening": "338.00",
                    "motion": "0.00"
                }
            }
        ]
        
        # State Courts
        state_courts = [
            {
                "name": "Los Angeles Superior Court",
                "court_type": CourtType.STATE_SUPERIOR,
                "jurisdiction": "Los Angeles County",
                "address": "111 North Hill Street",
                "city": "Los Angeles",
                "state": "CA",
                "zip_code": "90012",
                "efiling_system": "California Courts E-Filing",
                "local_rules_url": "https://www.lacourt.org/rules",
                "filing_fee_schedule": {
                    "case_opening": "435.00",
                    "motion": "60.00"
                },
                "business_hours": {
                    "monday": "8:00 AM - 4:30 PM",
                    "tuesday": "8:00 AM - 4:30 PM",
                    "wednesday": "8:00 AM - 4:30 PM",
                    "thursday": "8:00 AM - 4:30 PM",
                    "friday": "8:00 AM - 4:30 PM"
                }
            },
            {
                "name": "New York Supreme Court - New York County",
                "court_type": CourtType.STATE_SUPERIOR,
                "jurisdiction": "New York County",
                "address": "60 Centre Street",
                "city": "New York",
                "state": "NY",
                "zip_code": "10007",
                "efiling_system": "NYSCEF",
                "filing_fee_schedule": {
                    "case_opening": "210.00",
                    "motion": "45.00"
                },
                "business_hours": {
                    "monday": "9:00 AM - 5:00 PM",
                    "tuesday": "9:00 AM - 5:00 PM",
                    "wednesday": "9:00 AM - 5:00 PM",
                    "thursday": "9:00 AM - 5:00 PM",
                    "friday": "9:00 AM - 5:00 PM"
                }
            },
            {
                "name": "Cook County Circuit Court",
                "court_type": CourtType.STATE_SUPERIOR,
                "jurisdiction": "Cook County",
                "address": "50 West Washington Street",
                "city": "Chicago",
                "state": "IL",
                "zip_code": "60602",
                "efiling_system": "Illinois E-File",
                "filing_fee_schedule": {
                    "case_opening": "337.00",
                    "motion": "55.00"
                }
            }
        ]
        
        # Add courts to system
        all_courts = federal_courts + state_courts
        for court_data in all_courts:
            court = CourtInfo(**court_data)
            court_id = str(court.id)
            self.courts[court_id] = court
            
            # Create basic configuration
            self.configurations[court_id] = self._create_default_configuration(court)
        
        logger.info(f"Initialized {len(all_courts)} courts")
    
    def _create_default_configuration(self, court: CourtInfo) -> FilingConfiguration:
        """Create default filing configuration for a court"""
        
        base_url = court.cm_ecf_url or "https://example-court.gov"
        
        return FilingConfiguration(
            court_id=court.id,
            filing_endpoint=f"{base_url}/cgi-bin/iquery.pl",
            query_endpoint=f"{base_url}/cgi-bin/possible.pl", 
            authentication_endpoint=f"{base_url}/cgi-bin/login.pl",
            required_formats=["PDF"],
            max_file_size_mb=court.max_file_size_mb,
            max_documents_per_filing=99,
            validation_rules={
                "require_signature": True,
                "require_certificate_of_service": True,
                "max_document_pages": 500
            },
            required_fields=[
                "case_number",
                "document_title", 
                "filing_attorney",
                "document_type"
            ],
            business_hours=court.business_hours,
            supports_electronic_service=True,
            supports_fee_waiver=True,
            supports_sealed_documents=True,
            requires_certificate_of_service=True
        )
    
    async def get_court_by_id(self, court_id: str) -> Optional[CourtInfo]:
        """Get court information by ID"""
        return self.courts.get(court_id)
    
    async def search_courts(
        self,
        state: Optional[str] = None,
        court_type: Optional[CourtType] = None,
        jurisdiction: Optional[str] = None,
        name_search: Optional[str] = None
    ) -> List[CourtInfo]:
        """Search courts by various criteria"""
        
        results = list(self.courts.values())
        
        if state:
            results = [c for c in results if c.state.upper() == state.upper()]
        
        if court_type:
            results = [c for c in results if c.court_type == court_type]
        
        if jurisdiction:
            jurisdiction_lower = jurisdiction.lower()
            results = [c for c in results if jurisdiction_lower in c.jurisdiction.lower()]
        
        if name_search:
            name_lower = name_search.lower()
            results = [c for c in results if name_lower in c.name.lower()]
        
        return results
    
    async def get_court_configuration(self, court_id: str) -> Optional[FilingConfiguration]:
        """Get filing configuration for a court"""
        return self.configurations.get(court_id)
    
    async def update_court_configuration(
        self,
        court_id: str,
        config_updates: Dict
    ) -> bool:
        """Update court filing configuration"""
        try:
            if court_id not in self.configurations:
                return False
            
            config = self.configurations[court_id]
            
            # Update configuration fields
            for field, value in config_updates.items():
                if hasattr(config, field):
                    setattr(config, field, value)
            
            logger.info(f"Updated configuration for court {court_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update court configuration: {str(e)}")
            return False
    
    async def check_court_system_status(self, court_id: str) -> Dict[str, any]:
        """Check the status of a court's e-filing system"""
        try:
            court = self.courts.get(court_id)
            if not court:
                return {
                    "status": "error",
                    "message": "Court not found",
                    "available": False
                }
            
            # In production, this would make actual HTTP requests to court systems
            # For now, simulate status checks
            
            current_time = datetime.now().time()
            is_business_hours = self._is_during_business_hours(court, current_time)
            
            # Simulate system status (in production, would check actual endpoints)
            system_status = {
                "status": "operational",
                "available": True,
                "is_business_hours": is_business_hours,
                "system_version": "4.6.1",
                "last_maintenance": "2024-01-01T02:00:00Z",
                "response_time_ms": 150,
                "filing_queue_length": 3,
                "estimated_processing_time": "2-5 minutes"
            }
            
            # Cache the status
            self.system_status[court_id] = system_status
            
            return system_status
            
        except Exception as e:
            logger.error(f"Court system status check failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "available": False,
                "error_time": datetime.utcnow().isoformat()
            }
    
    async def get_filing_requirements(self, court_id: str) -> Dict[str, any]:
        """Get detailed filing requirements for a court"""
        try:
            court = self.courts.get(court_id)
            config = self.configurations.get(court_id)
            
            if not court or not config:
                return {"error": "Court or configuration not found"}
            
            requirements = {
                "court_name": court.name,
                "court_type": court.court_type.value,
                "efiling_system": court.efiling_system,
                
                # Document requirements
                "accepted_formats": config.required_formats,
                "max_file_size_mb": config.max_file_size_mb,
                "max_documents_per_filing": config.max_documents_per_filing,
                
                # Required fields
                "required_fields": config.required_fields,
                "validation_rules": config.validation_rules,
                
                # Business rules
                "supports_electronic_service": config.supports_electronic_service,
                "requires_certificate_of_service": config.requires_certificate_of_service,
                "supports_sealed_documents": config.supports_sealed_documents,
                
                # Timing
                "business_hours": config.business_hours,
                "maintenance_windows": config.maintenance_windows,
                
                # Fees
                "filing_fee_schedule": court.filing_fee_schedule,
                "supports_fee_waiver": config.supports_fee_waiver,
                
                # Contact
                "local_rules_url": court.local_rules_url,
                "cm_ecf_url": court.cm_ecf_url
            }
            
            return requirements
            
        except Exception as e:
            logger.error(f"Failed to get filing requirements: {str(e)}")
            return {"error": str(e)}
    
    async def validate_court_credentials(
        self,
        court_id: str,
        credentials: EFilingCredentials
    ) -> Dict[str, any]:
        """Validate e-filing credentials for a specific court"""
        try:
            court = self.courts.get(court_id)
            if not court:
                return {
                    "valid": False,
                    "error": "Court not found"
                }
            
            # Basic credential validation
            if not credentials.username or not credentials.password_hash:
                return {
                    "valid": False,
                    "error": "Username and password required"
                }
            
            if not credentials.bar_number:
                return {
                    "valid": False,
                    "error": "Bar number required"
                }
            
            # Check if credentials match court type requirements
            if court.court_type.value.startswith("federal"):
                if not credentials.pacer_id:
                    return {
                        "valid": False,
                        "error": "PACER ID required for federal courts"
                    }
            
            # Check expiration
            if credentials.expires_at and credentials.expires_at < datetime.utcnow():
                return {
                    "valid": False,
                    "error": "Credentials have expired"
                }
            
            # Check account status
            if credentials.account_locked:
                return {
                    "valid": False,
                    "error": "Account is locked"
                }
            
            # In production, would validate against actual court system
            return {
                "valid": True,
                "message": "Credentials appear valid",
                "requires_2fa": credentials.two_factor_enabled
            }
            
        except Exception as e:
            logger.error(f"Credential validation failed: {str(e)}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    def _is_during_business_hours(self, court: CourtInfo, current_time: time) -> bool:
        """Check if current time is during court business hours"""
        try:
            current_day = datetime.now().strftime('%A').lower()
            
            if current_day not in court.business_hours:
                return False
            
            hours_str = court.business_hours[current_day]
            if not hours_str or hours_str.lower() == 'closed':
                return False
            
            # Parse business hours (e.g., "9:00 AM - 5:00 PM")
            start_str, end_str = hours_str.split(' - ')
            start_time = datetime.strptime(start_str.strip(), '%I:%M %p').time()
            end_time = datetime.strptime(end_str.strip(), '%I:%M %p').time()
            
            return start_time <= current_time <= end_time
            
        except Exception as e:
            logger.error(f"Business hours check failed: {str(e)}")
            return False
    
    async def get_system_health(self) -> Dict[str, any]:
        """Get overall court systems health status"""
        try:
            total_courts = len(self.courts)
            operational_courts = 0
            
            # Check status of all court systems
            for court_id in self.courts.keys():
                status = await self.check_court_system_status(court_id)
                if status.get("available", False):
                    operational_courts += 1
            
            health_percentage = (operational_courts / total_courts) * 100 if total_courts > 0 else 0
            
            return {
                "overall_status": "healthy" if health_percentage >= 90 else "degraded" if health_percentage >= 50 else "unhealthy",
                "total_courts": total_courts,
                "operational_courts": operational_courts,
                "health_percentage": round(health_percentage, 1),
                "last_checked": datetime.utcnow().isoformat(),
                "federal_courts": len([c for c in self.courts.values() if c.court_type.value.startswith("federal")]),
                "state_courts": len([c for c in self.courts.values() if not c.court_type.value.startswith("federal")])
            }
            
        except Exception as e:
            logger.error(f"System health check failed: {str(e)}")
            return {
                "overall_status": "error",
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat()
            }
    
    async def add_court(self, court_info: CourtInfo) -> str:
        """Add a new court to the system"""
        try:
            court_id = str(court_info.id)
            self.courts[court_id] = court_info
            self.configurations[court_id] = self._create_default_configuration(court_info)
            
            logger.info(f"Added court: {court_info.name}")
            return court_id
            
        except Exception as e:
            logger.error(f"Failed to add court: {str(e)}")
            raise
    
    async def update_court(self, court_id: str, updates: Dict) -> bool:
        """Update court information"""
        try:
            if court_id not in self.courts:
                return False
            
            court = self.courts[court_id]
            
            # Update court fields
            for field, value in updates.items():
                if hasattr(court, field):
                    setattr(court, field, value)
            
            logger.info(f"Updated court {court_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update court: {str(e)}")
            return False
    
    async def remove_court(self, court_id: str) -> bool:
        """Remove a court from the system"""
        try:
            if court_id not in self.courts:
                return False
            
            court_name = self.courts[court_id].name
            del self.courts[court_id]
            del self.configurations[court_id]
            self.system_status.pop(court_id, None)
            
            logger.info(f"Removed court: {court_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove court: {str(e)}")
            return False