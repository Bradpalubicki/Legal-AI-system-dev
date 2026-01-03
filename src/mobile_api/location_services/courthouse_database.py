"""
Courthouse Database Module

Manages courthouse information, location data, and provides
search and filtering capabilities for courthouse detection.
"""

import json
import logging
import math
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from .location_models import (
    CourthouseInfo,
    CourthouseType,
    LocationCoordinates,
    LocationAccuracy
)

logger = logging.getLogger(__name__)


class CourthouseDatabase:
    """
    Database manager for courthouse information with geographic search capabilities
    """
    
    def __init__(self, database_file: Optional[str] = None):
        self.courthouses: Dict[str, CourthouseInfo] = {}
        self.location_index: Dict[str, List[str]] = {}  # Grid-based spatial index
        self.database_file = database_file
        self.last_updated = datetime.utcnow()
        
        # Initialize with sample courthouse data
        self._initialize_sample_data()
        
        # Load from file if provided
        if database_file:
            self._load_from_file()
    
    def _initialize_sample_data(self):
        """Initialize database with sample courthouse data for major US cities"""
        sample_courthouses = [
            # Federal Courts - Major Cities
            {
                "name": "United States District Court for the Southern District of New York",
                "court_type": CourthouseType.FEDERAL_DISTRICT,
                "address": "500 Pearl Street",
                "city": "New York",
                "state": "NY",
                "zip_code": "10007",
                "coordinates": LocationCoordinates(
                    latitude=40.7128, longitude=-74.0060,
                    accuracy=LocationAccuracy.HIGH
                ),
                "phone": "(212) 805-0136",
                "jurisdiction": "Southern District of New York",
                "judges": ["Alison J. Nathan", "Lewis A. Kaplan", "Jesse M. Furman"],
                "departments": ["Civil", "Criminal", "Magistrate"],
                "case_types": ["Civil Rights", "Criminal", "Securities", "Contract Disputes"],
                "business_hours": {
                    "monday": "9:00 AM - 5:00 PM",
                    "tuesday": "9:00 AM - 5:00 PM",
                    "wednesday": "9:00 AM - 5:00 PM",
                    "thursday": "9:00 AM - 5:00 PM",
                    "friday": "9:00 AM - 5:00 PM"
                },
                "efiling_system": "CM/ECF",
                "security_requirements": ["Photo ID Required", "Metal Detector", "X-ray Screening"],
                "local_rules_url": "https://nysd.uscourts.gov/rules"
            },
            {
                "name": "United States District Court for the Central District of California",
                "court_type": CourthouseType.FEDERAL_DISTRICT,
                "address": "350 West 1st Street",
                "city": "Los Angeles",
                "state": "CA",
                "zip_code": "90012",
                "coordinates": LocationCoordinates(
                    latitude=34.0522, longitude=-118.2437,
                    accuracy=LocationAccuracy.HIGH
                ),
                "phone": "(213) 894-1565",
                "jurisdiction": "Central District of California",
                "judges": ["Dolly M. Gee", "John F. Walter", "Virginia A. Phillips"],
                "departments": ["Civil", "Criminal", "Bankruptcy"],
                "case_types": ["Intellectual Property", "Employment", "Immigration", "Criminal"],
                "business_hours": {
                    "monday": "8:30 AM - 4:30 PM",
                    "tuesday": "8:30 AM - 4:30 PM",
                    "wednesday": "8:30 AM - 4:30 PM",
                    "thursday": "8:30 AM - 4:30 PM",
                    "friday": "8:30 AM - 4:30 PM"
                },
                "efiling_system": "CM/ECF"
            },
            # State Courts
            {
                "name": "Los Angeles Superior Court - Central District",
                "court_type": CourthouseType.STATE_SUPERIOR,
                "address": "111 North Hill Street",
                "city": "Los Angeles",
                "state": "CA",
                "zip_code": "90012",
                "coordinates": LocationCoordinates(
                    latitude=34.0569, longitude=-118.2441,
                    accuracy=LocationAccuracy.HIGH
                ),
                "phone": "(213) 830-0800",
                "jurisdiction": "Los Angeles County",
                "judges": ["Multiple Departments"],
                "departments": ["Civil", "Criminal", "Family", "Probate", "Small Claims"],
                "case_types": ["Personal Injury", "Contract", "Family Law", "Probate", "Criminal"],
                "business_hours": {
                    "monday": "8:00 AM - 4:30 PM",
                    "tuesday": "8:00 AM - 4:30 PM",
                    "wednesday": "8:00 AM - 4:30 PM",
                    "thursday": "8:00 AM - 4:30 PM",
                    "friday": "8:00 AM - 4:30 PM"
                },
                "local_rules_url": "https://www.lacourt.org/rules"
            },
            {
                "name": "New York Supreme Court - New York County",
                "court_type": CourthouseType.STATE_SUPERIOR,
                "address": "60 Centre Street",
                "city": "New York",
                "state": "NY",
                "zip_code": "10007",
                "coordinates": LocationCoordinates(
                    latitude=40.7148, longitude=-74.0021,
                    accuracy=LocationAccuracy.HIGH
                ),
                "phone": "(646) 386-3730",
                "jurisdiction": "New York County",
                "judges": ["Multiple Departments"],
                "departments": ["Civil", "Commercial", "Tax Certiorari"],
                "case_types": ["Commercial", "Real Estate", "Tort", "Contract"],
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
                "court_type": CourthouseType.STATE_SUPERIOR,
                "address": "50 West Washington Street",
                "city": "Chicago",
                "state": "IL",
                "zip_code": "60602",
                "coordinates": LocationCoordinates(
                    latitude=41.8781, longitude=-87.6298,
                    accuracy=LocationAccuracy.HIGH
                ),
                "phone": "(312) 603-5030",
                "jurisdiction": "Cook County",
                "departments": ["Civil", "Criminal", "Domestic Relations", "Probate"],
                "case_types": ["Civil", "Criminal", "Family", "Probate", "Traffic"],
                "business_hours": {
                    "monday": "8:30 AM - 4:30 PM",
                    "tuesday": "8:30 AM - 4:30 PM",
                    "wednesday": "8:30 AM - 4:30 PM",
                    "thursday": "8:30 AM - 4:30 PM",
                    "friday": "8:30 AM - 4:30 PM"
                }
            }
        ]
        
        for courthouse_data in sample_courthouses:
            courthouse = CourthouseInfo(**courthouse_data)
            self.add_courthouse(courthouse)
        
        logger.info(f"Initialized courthouse database with {len(sample_courthouses)} entries")
    
    def add_courthouse(self, courthouse: CourthouseInfo) -> str:
        """Add a courthouse to the database"""
        courthouse_id = str(courthouse.id)
        self.courthouses[courthouse_id] = courthouse
        
        # Add to spatial index
        grid_key = self._get_grid_key(
            courthouse.coordinates.latitude,
            courthouse.coordinates.longitude
        )
        
        if grid_key not in self.location_index:
            self.location_index[grid_key] = []
        
        self.location_index[grid_key].append(courthouse_id)
        
        logger.debug(f"Added courthouse: {courthouse.name}")
        return courthouse_id
    
    def get_courthouse(self, courthouse_id: str) -> Optional[CourthouseInfo]:
        """Get courthouse by ID"""
        return self.courthouses.get(courthouse_id)
    
    def find_nearby_courthouses(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        max_results: int = 10
    ) -> List[Tuple[CourthouseInfo, float]]:
        """
        Find courthouses within a specified radius
        Returns list of (courthouse, distance_km) tuples sorted by distance
        """
        nearby_courthouses = []
        
        # Get grid cells to search
        grid_keys = self._get_nearby_grid_keys(latitude, longitude, radius_km)
        
        # Search in relevant grid cells
        for grid_key in grid_keys:
            if grid_key in self.location_index:
                for courthouse_id in self.location_index[grid_key]:
                    courthouse = self.courthouses[courthouse_id]
                    
                    # Calculate distance
                    distance_km = self._haversine_distance(
                        latitude, longitude,
                        courthouse.coordinates.latitude,
                        courthouse.coordinates.longitude
                    )
                    
                    if distance_km <= radius_km:
                        nearby_courthouses.append((courthouse, distance_km))
        
        # Sort by distance and limit results
        nearby_courthouses.sort(key=lambda x: x[1])
        return nearby_courthouses[:max_results]
    
    def find_courthouse_by_name(self, name: str, fuzzy: bool = True) -> List[CourthouseInfo]:
        """Find courthouse by name with optional fuzzy matching"""
        results = []
        name_lower = name.lower()
        
        for courthouse in self.courthouses.values():
            courthouse_name_lower = courthouse.name.lower()
            
            if fuzzy:
                # Simple fuzzy matching - check if any words match
                name_words = name_lower.split()
                courthouse_words = courthouse_name_lower.split()
                
                if any(word in courthouse_words for word in name_words):
                    results.append(courthouse)
            else:
                # Exact match
                if name_lower in courthouse_name_lower:
                    results.append(courthouse)
        
        return results
    
    def find_courthouses_by_jurisdiction(self, jurisdiction: str) -> List[CourthouseInfo]:
        """Find courthouses by jurisdiction"""
        results = []
        jurisdiction_lower = jurisdiction.lower()
        
        for courthouse in self.courthouses.values():
            if jurisdiction_lower in courthouse.jurisdiction.lower():
                results.append(courthouse)
        
        return results
    
    def find_courthouses_by_type(self, court_type: CourthouseType) -> List[CourthouseInfo]:
        """Find courthouses by type"""
        return [
            courthouse for courthouse in self.courthouses.values()
            if courthouse.court_type == court_type
        ]
    
    def find_courthouses_by_state(self, state: str) -> List[CourthouseInfo]:
        """Find courthouses by state"""
        results = []
        state_upper = state.upper()
        
        for courthouse in self.courthouses.values():
            if courthouse.state.upper() == state_upper:
                results.append(courthouse)
        
        return results
    
    def is_courthouse_open(self, courthouse: CourthouseInfo, check_time: datetime = None) -> bool:
        """Check if courthouse is currently open"""
        if check_time is None:
            check_time = datetime.now()
        
        # Get day of week (monday=0)
        day_name = check_time.strftime('%A').lower()
        
        if day_name not in courthouse.business_hours:
            return False
        
        hours_str = courthouse.business_hours[day_name]
        if not hours_str or hours_str.lower() == 'closed':
            return False
        
        try:
            # Parse hours (e.g., "9:00 AM - 5:00 PM")
            start_str, end_str = hours_str.split(' - ')
            start_time = datetime.strptime(start_str.strip(), '%I:%M %p').time()
            end_time = datetime.strptime(end_str.strip(), '%I:%M %p').time()
            current_time = check_time.time()
            
            return start_time <= current_time <= end_time
            
        except (ValueError, AttributeError):
            # If parsing fails, assume closed
            return False
    
    def get_next_business_day(self, courthouse: CourthouseInfo, from_date: datetime = None) -> Optional[str]:
        """Get the next business day for the courthouse"""
        if from_date is None:
            from_date = datetime.now()
        
        # Check next 7 days
        for i in range(1, 8):
            check_date = from_date.replace(hour=12, minute=0, second=0, microsecond=0)
            check_date = check_date + timedelta(days=i)
            
            day_name = check_date.strftime('%A').lower()
            if day_name in courthouse.business_hours:
                hours_str = courthouse.business_hours[day_name]
                if hours_str and hours_str.lower() != 'closed':
                    return check_date.strftime('%A, %B %d')
        
        return None
    
    def update_courthouse(self, courthouse_id: str, updates: Dict) -> bool:
        """Update courthouse information"""
        if courthouse_id not in self.courthouses:
            return False
        
        courthouse = self.courthouses[courthouse_id]
        
        # Update fields
        for field, value in updates.items():
            if hasattr(courthouse, field):
                setattr(courthouse, field, value)
        
        courthouse.last_updated = datetime.utcnow()
        return True
    
    def delete_courthouse(self, courthouse_id: str) -> bool:
        """Delete courthouse from database"""
        if courthouse_id not in self.courthouses:
            return False
        
        courthouse = self.courthouses[courthouse_id]
        
        # Remove from spatial index
        grid_key = self._get_grid_key(
            courthouse.coordinates.latitude,
            courthouse.coordinates.longitude
        )
        
        if grid_key in self.location_index:
            self.location_index[grid_key].remove(courthouse_id)
            if not self.location_index[grid_key]:
                del self.location_index[grid_key]
        
        # Remove from main database
        del self.courthouses[courthouse_id]
        return True
    
    def get_statistics(self) -> Dict[str, any]:
        """Get database statistics"""
        stats = {
            "total_courthouses": len(self.courthouses),
            "last_updated": self.last_updated.isoformat(),
            "court_types": {},
            "states": {},
            "grid_cells": len(self.location_index)
        }
        
        # Count by court type
        for courthouse in self.courthouses.values():
            court_type = courthouse.court_type.value
            stats["court_types"][court_type] = stats["court_types"].get(court_type, 0) + 1
            
            state = courthouse.state
            stats["states"][state] = stats["states"].get(state, 0) + 1
        
        return stats
    
    def _get_grid_key(self, latitude: float, longitude: float, grid_size: float = 0.01) -> str:
        """Get grid key for spatial indexing"""
        lat_grid = int(latitude / grid_size)
        lon_grid = int(longitude / grid_size)
        return f"{lat_grid}_{lon_grid}"
    
    def _get_nearby_grid_keys(self, latitude: float, longitude: float, radius_km: float) -> List[str]:
        """Get grid keys for nearby cells within radius"""
        grid_size = 0.01  # Approximately 1.1km at equator
        
        # Calculate grid offset for radius
        lat_offset = int((radius_km / 111.0) / grid_size) + 1  # 111km per degree latitude
        lon_offset = int((radius_km / (111.0 * math.cos(math.radians(latitude)))) / grid_size) + 1
        
        grid_keys = []
        center_lat_grid = int(latitude / grid_size)
        center_lon_grid = int(longitude / grid_size)
        
        for lat_offset_val in range(-lat_offset, lat_offset + 1):
            for lon_offset_val in range(-lon_offset, lon_offset + 1):
                lat_grid = center_lat_grid + lat_offset_val
                lon_grid = center_lon_grid + lon_offset_val
                grid_keys.append(f"{lat_grid}_{lon_grid}")
        
        return grid_keys
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        earth_radius_km = 6371.0
        
        return earth_radius_km * c
    
    def _load_from_file(self):
        """Load courthouse data from file"""
        try:
            with open(self.database_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for courthouse_data in data.get('courthouses', []):
                # Convert coordinates
                coord_data = courthouse_data['coordinates']
                coordinates = LocationCoordinates(**coord_data)
                courthouse_data['coordinates'] = coordinates
                
                # Create courthouse object
                courthouse = CourthouseInfo(**courthouse_data)
                self.add_courthouse(courthouse)
            
            logger.info(f"Loaded {len(data.get('courthouses', []))} courthouses from file")
            
        except FileNotFoundError:
            logger.warning(f"Database file {self.database_file} not found")
        except Exception as e:
            logger.error(f"Failed to load database file: {str(e)}")
    
    def save_to_file(self):
        """Save courthouse data to file"""
        if not self.database_file:
            return False
        
        try:
            data = {
                "last_updated": self.last_updated.isoformat(),
                "courthouses": []
            }
            
            for courthouse in self.courthouses.values():
                courthouse_dict = courthouse.dict()
                data["courthouses"].append(courthouse_dict)
            
            with open(self.database_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Saved {len(self.courthouses)} courthouses to file")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save database file: {str(e)}")
            return False