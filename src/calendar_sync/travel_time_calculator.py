"""
Advanced Travel Time Calculator for Legal Calendar Management

Provides sophisticated travel time calculations using multiple data sources,
real-time traffic, historical patterns, and legal-specific considerations.
"""

from typing import List, Dict, Any, Optional, Union, Tuple, Set
from datetime import datetime, timedelta, time
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
import json
import re
from abc import ABC, abstractmethod
import aiohttp
import hashlib
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import numpy as np

logger = logging.getLogger(__name__)


class TransportMode(Enum):
    """Transportation modes."""
    DRIVING = "driving"
    WALKING = "walking"
    PUBLIC_TRANSIT = "public_transit"
    BICYCLE = "bicycle"
    RIDE_SHARE = "ride_share"
    TAXI = "taxi"


class TrafficCondition(Enum):
    """Traffic conditions."""
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    SEVERE = "severe"


class TravelProvider(Enum):
    """Travel time data providers."""
    GOOGLE_MAPS = "google_maps"
    MAPBOX = "mapbox"
    HERE_MAPS = "here_maps"
    BING_MAPS = "bing_maps"
    OPEN_ROUTE_SERVICE = "open_route_service"
    HISTORICAL_DATA = "historical_data"


@dataclass
class Location:
    """Enhanced location with geocoding support."""
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    building_type: str = "courthouse"  # courthouse, law_firm, office
    parking_availability: str = "unknown"  # good, limited, poor, none
    security_screening_time: int = 0  # minutes
    accessibility_notes: Optional[str] = None
    
    def full_address(self) -> str:
        """Get formatted full address."""
        parts = [self.address, self.city, self.state, self.zip_code]
        return ", ".join(filter(None, parts))
    
    def coordinates(self) -> Optional[Tuple[float, float]]:
        """Get coordinates tuple."""
        if self.latitude is not None and self.longitude is not None:
            return (self.latitude, self.longitude)
        return None


@dataclass
class TravelTimeResult:
    """Result of travel time calculation."""
    origin: Location
    destination: Location
    transport_mode: TransportMode
    provider: TravelProvider
    
    # Core travel data
    distance_miles: float
    travel_time_minutes: int
    traffic_delay_minutes: int = 0
    
    # Legal-specific considerations
    parking_time_minutes: int = 10
    security_screening_minutes: int = 0
    walking_to_courtroom_minutes: int = 5
    prep_time_minutes: int = 15  # Time to prepare after arrival
    
    # Reliability and metadata
    confidence: float = 0.8
    calculated_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=1))
    traffic_condition: TrafficCondition = TrafficCondition.MODERATE
    alternative_routes: List[Dict[str, Any]] = field(default_factory=list)
    
    # Error handling
    error_message: Optional[str] = None
    fallback_used: bool = False
    
    @property
    def total_time_minutes(self) -> int:
        """Calculate total time including all overhead."""
        return (self.travel_time_minutes + 
                self.traffic_delay_minutes + 
                self.parking_time_minutes + 
                self.security_screening_minutes + 
                self.walking_to_courtroom_minutes + 
                self.prep_time_minutes)
    
    @property
    def is_valid(self) -> bool:
        """Check if result is still valid."""
        return datetime.now() < self.expires_at and self.error_message is None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'origin': {
                'name': self.origin.name,
                'address': self.origin.full_address(),
                'coordinates': self.origin.coordinates()
            },
            'destination': {
                'name': self.destination.name,
                'address': self.destination.full_address(),
                'coordinates': self.destination.coordinates()
            },
            'transport_mode': self.transport_mode.value,
            'provider': self.provider.value,
            'distance_miles': self.distance_miles,
            'travel_time_minutes': self.travel_time_minutes,
            'traffic_delay_minutes': self.traffic_delay_minutes,
            'parking_time_minutes': self.parking_time_minutes,
            'security_screening_minutes': self.security_screening_minutes,
            'walking_to_courtroom_minutes': self.walking_to_courtroom_minutes,
            'prep_time_minutes': self.prep_time_minutes,
            'total_time_minutes': self.total_time_minutes,
            'confidence': self.confidence,
            'traffic_condition': self.traffic_condition.value,
            'calculated_at': self.calculated_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'error_message': self.error_message,
            'fallback_used': self.fallback_used
        }


@dataclass
class TravelTimeRequest:
    """Request for travel time calculation."""
    origin: Location
    destination: Location
    departure_time: datetime
    transport_mode: TransportMode = TransportMode.DRIVING
    preferred_providers: List[TravelProvider] = field(default_factory=lambda: [TravelProvider.GOOGLE_MAPS])
    include_alternatives: bool = True
    consider_traffic: bool = True
    consider_parking: bool = True
    buffer_percentage: float = 0.2  # 20% buffer for uncertainty


class TravelTimeProvider(ABC):
    """Abstract base class for travel time providers."""
    
    @abstractmethod
    async def calculate_travel_time(self, request: TravelTimeRequest) -> TravelTimeResult:
        """Calculate travel time between locations."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass
    
    @abstractmethod
    def get_rate_limit(self) -> Dict[str, int]:
        """Get rate limit information."""
        pass


class GoogleMapsProvider(TravelTimeProvider):
    """Google Maps travel time provider."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.requests_today = 0
        self.daily_limit = 2500  # Typical free tier limit
        
    async def calculate_travel_time(self, request: TravelTimeRequest) -> TravelTimeResult:
        """Calculate travel time using Google Maps API."""
        try:
            # Geocode locations if needed
            origin_coords = await self._ensure_geocoded(request.origin)
            dest_coords = await self._ensure_geocoded(request.destination)
            
            if not origin_coords or not dest_coords:
                raise ValueError("Failed to geocode locations")
            
            # Prepare API request
            params = {
                'origins': f"{origin_coords[0]},{origin_coords[1]}",
                'destinations': f"{dest_coords[0]},{dest_coords[1]}",
                'mode': self._map_transport_mode(request.transport_mode),
                'departure_time': int(request.departure_time.timestamp()),
                'traffic_model': 'best_guess',
                'key': self.api_key
            }
            
            if request.consider_traffic:
                params['departure_time'] = 'now'  # For real-time traffic
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/distancematrix/json"
                async with session.get(url, params=params) as response:
                    data = await response.json()
            
            self.requests_today += 1
            
            # Parse response
            if data.get('status') == 'OK' and data.get('rows'):
                element = data['rows'][0]['elements'][0]
                
                if element.get('status') == 'OK':
                    return self._parse_google_response(element, request)
                else:
                    raise ValueError(f"Google Maps API error: {element.get('status')}")
            else:
                raise ValueError(f"Google Maps API error: {data.get('status')}")
        
        except Exception as e:
            logger.error(f"Google Maps provider error: {str(e)}")
            return self._create_error_result(request, str(e))
    
    async def _ensure_geocoded(self, location: Location) -> Optional[Tuple[float, float]]:
        """Ensure location has coordinates."""
        if location.coordinates():
            return location.coordinates()
        
        # Use Google Geocoding API
        if not location.full_address():
            return None
        
        try:
            params = {
                'address': location.full_address(),
                'key': self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/geocode/json"
                async with session.get(url, params=params) as response:
                    data = await response.json()
            
            if data.get('status') == 'OK' and data.get('results'):
                result = data['results'][0]
                geometry = result['geometry']['location']
                coords = (geometry['lat'], geometry['lng'])
                
                # Update location with coordinates
                location.latitude, location.longitude = coords
                return coords
        
        except Exception as e:
            logger.warning(f"Geocoding failed for {location.name}: {str(e)}")
        
        return None
    
    def _map_transport_mode(self, mode: TransportMode) -> str:
        """Map transport mode to Google Maps mode."""
        mapping = {
            TransportMode.DRIVING: 'driving',
            TransportMode.WALKING: 'walking',
            TransportMode.PUBLIC_TRANSIT: 'transit',
            TransportMode.BICYCLE: 'bicycling'
        }
        return mapping.get(mode, 'driving')
    
    def _parse_google_response(self, element: Dict[str, Any], 
                             request: TravelTimeRequest) -> TravelTimeResult:
        """Parse Google Maps API response."""
        # Extract basic data
        distance_meters = element['distance']['value']
        duration_seconds = element['duration']['value']
        
        # Check for traffic data
        traffic_duration_seconds = duration_seconds
        traffic_delay_minutes = 0
        
        if 'duration_in_traffic' in element:
            traffic_duration_seconds = element['duration_in_traffic']['value']
            traffic_delay_minutes = max(0, (traffic_duration_seconds - duration_seconds) // 60)
        
        # Calculate legal-specific overheads
        parking_time = self._calculate_parking_time(request.destination)
        security_time = self._calculate_security_time(request.destination)
        walking_time = self._calculate_walking_time(request.destination)
        
        # Determine traffic condition
        traffic_condition = self._assess_traffic_condition(traffic_delay_minutes)
        
        # Apply buffer
        base_travel_minutes = traffic_duration_seconds // 60
        buffered_travel_minutes = int(base_travel_minutes * (1 + request.buffer_percentage))
        
        return TravelTimeResult(
            origin=request.origin,
            destination=request.destination,
            transport_mode=request.transport_mode,
            provider=TravelProvider.GOOGLE_MAPS,
            distance_miles=distance_meters * 0.000621371,  # Convert to miles
            travel_time_minutes=buffered_travel_minutes,
            traffic_delay_minutes=traffic_delay_minutes,
            parking_time_minutes=parking_time,
            security_screening_minutes=security_time,
            walking_to_courtroom_minutes=walking_time,
            confidence=0.85,
            traffic_condition=traffic_condition,
            expires_at=datetime.now() + timedelta(minutes=30)  # Google data is relatively fresh
        )
    
    def _calculate_parking_time(self, location: Location) -> int:
        """Calculate expected parking time."""
        if location.building_type == "courthouse":
            parking_times = {
                "good": 5,
                "limited": 15,
                "poor": 25,
                "none": 0  # Street parking or walking from distant lot
            }
            return parking_times.get(location.parking_availability, 10)
        elif location.building_type == "law_firm":
            return 5  # Usually have dedicated parking
        else:
            return 8  # General office building
    
    def _calculate_security_time(self, location: Location) -> int:
        """Calculate security screening time."""
        if location.building_type == "courthouse":
            return max(location.security_screening_time, 10)  # Minimum 10 minutes for courthouse security
        else:
            return location.security_screening_time
    
    def _calculate_walking_time(self, location: Location) -> int:
        """Calculate walking time within building."""
        if location.building_type == "courthouse":
            return 8  # Time to walk to specific courtroom
        elif location.building_type == "law_firm":
            return 3  # Smaller building
        else:
            return 5  # General office
    
    def _assess_traffic_condition(self, delay_minutes: int) -> TrafficCondition:
        """Assess traffic condition from delay."""
        if delay_minutes < 5:
            return TrafficCondition.LIGHT
        elif delay_minutes < 15:
            return TrafficCondition.MODERATE
        elif delay_minutes < 30:
            return TrafficCondition.HEAVY
        else:
            return TrafficCondition.SEVERE
    
    def _create_error_result(self, request: TravelTimeRequest, error: str) -> TravelTimeResult:
        """Create error result."""
        return TravelTimeResult(
            origin=request.origin,
            destination=request.destination,
            transport_mode=request.transport_mode,
            provider=TravelProvider.GOOGLE_MAPS,
            distance_miles=0.0,
            travel_time_minutes=60,  # Conservative fallback
            confidence=0.3,
            error_message=error,
            fallback_used=True
        )
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        return self.requests_today < self.daily_limit and bool(self.api_key)
    
    def get_rate_limit(self) -> Dict[str, int]:
        """Get rate limit information."""
        return {
            'daily_limit': self.daily_limit,
            'used_today': self.requests_today,
            'remaining': max(0, self.daily_limit - self.requests_today)
        }


class HistoricalTravelProvider(TravelTimeProvider):
    """Provider using historical travel time data and patterns."""
    
    def __init__(self):
        self.historical_data: Dict[str, List[Dict[str, Any]]] = {}
        self.geocoder = Nominatim(user_agent="legal_calendar_system")
        
    async def calculate_travel_time(self, request: TravelTimeRequest) -> TravelTimeResult:
        """Calculate travel time using historical data and heuristics."""
        try:
            # Create route key
            route_key = self._create_route_key(request.origin, request.destination)
            
            # Check historical data
            historical_time = self._get_historical_time(route_key, request.departure_time)
            
            if historical_time:
                return historical_time
            
            # Fall back to distance-based calculation
            return await self._calculate_from_distance(request)
        
        except Exception as e:
            logger.error(f"Historical provider error: {str(e)}")
            return self._create_fallback_result(request)
    
    def _create_route_key(self, origin: Location, destination: Location) -> str:
        """Create a unique key for the route."""
        origin_str = f"{origin.name}|{origin.full_address()}"
        dest_str = f"{destination.name}|{destination.full_address()}"
        return hashlib.md5(f"{origin_str}->{dest_str}".encode()).hexdigest()[:16]
    
    def _get_historical_time(self, route_key: str, departure_time: datetime) -> Optional[TravelTimeResult]:
        """Get travel time from historical data."""
        if route_key not in self.historical_data:
            return None
        
        records = self.historical_data[route_key]
        
        # Filter by similar time of day and day of week
        departure_hour = departure_time.hour
        departure_dow = departure_time.weekday()
        
        relevant_records = [
            r for r in records
            if abs(r['hour'] - departure_hour) <= 1 and r['day_of_week'] == departure_dow
        ]
        
        if not relevant_records:
            relevant_records = records  # Use all data if no specific match
        
        if relevant_records:
            # Calculate average with recent data weighted more heavily
            weights = []
            values = []
            
            for record in relevant_records:
                age_days = (datetime.now() - datetime.fromisoformat(record['recorded_at'])).days
                weight = max(0.1, 1.0 / (1.0 + age_days * 0.1))  # Decay over time
                weights.append(weight)
                values.append(record['travel_time_minutes'])
            
            weighted_avg = np.average(values, weights=weights)
            
            # Use the first record as template and update with calculated average
            template = relevant_records[0]
            
            # This would return a proper TravelTimeResult based on the template
            # For now, return None to trigger fallback
            return None
        
        return None
    
    async def _calculate_from_distance(self, request: TravelTimeRequest) -> TravelTimeResult:
        """Calculate travel time based on straight-line distance and speed assumptions."""
        try:
            # Ensure both locations have coordinates
            origin_coords = await self._get_coordinates(request.origin)
            dest_coords = await self._get_coordinates(request.destination)
            
            if not origin_coords or not dest_coords:
                return self._create_fallback_result(request)
            
            # Calculate straight-line distance
            distance_miles = geodesic(origin_coords, dest_coords).miles
            
            # Apply route factor (actual driving distance vs straight line)
            route_factor = self._get_route_factor(distance_miles)
            actual_distance = distance_miles * route_factor
            
            # Calculate travel time based on mode
            travel_speed = self._get_travel_speed(request.transport_mode, request.departure_time)
            base_travel_minutes = (actual_distance / travel_speed) * 60
            
            # Add traffic adjustment
            traffic_factor = self._get_traffic_factor(request.departure_time)
            adjusted_travel_minutes = int(base_travel_minutes * traffic_factor)
            
            # Apply buffer
            buffered_minutes = int(adjusted_travel_minutes * (1 + request.buffer_percentage))
            
            # Calculate overheads
            parking_time = self._calculate_parking_time(request.destination)
            security_time = self._calculate_security_time(request.destination)
            walking_time = self._calculate_walking_time(request.destination)
            
            return TravelTimeResult(
                origin=request.origin,
                destination=request.destination,
                transport_mode=request.transport_mode,
                provider=TravelProvider.HISTORICAL_DATA,
                distance_miles=actual_distance,
                travel_time_minutes=buffered_minutes,
                traffic_delay_minutes=int(adjusted_travel_minutes - base_travel_minutes),
                parking_time_minutes=parking_time,
                security_screening_minutes=security_time,
                walking_to_courtroom_minutes=walking_time,
                confidence=0.6,  # Lower confidence for estimated data
                traffic_condition=self._estimate_traffic_condition(request.departure_time),
                fallback_used=True
            )
        
        except Exception as e:
            logger.error(f"Distance-based calculation failed: {str(e)}")
            return self._create_fallback_result(request)
    
    async def _get_coordinates(self, location: Location) -> Optional[Tuple[float, float]]:
        """Get coordinates for location."""
        if location.coordinates():
            return location.coordinates()
        
        # Try geocoding with address
        if location.full_address():
            try:
                geocoded = self.geocoder.geocode(location.full_address())
                if geocoded:
                    coords = (geocoded.latitude, geocoded.longitude)
                    location.latitude, location.longitude = coords
                    return coords
            except Exception as e:
                logger.warning(f"Geocoding failed: {str(e)}")
        
        return None
    
    def _get_route_factor(self, straight_distance_miles: float) -> float:
        """Get factor to convert straight-line distance to actual route distance."""
        # Longer distances typically have lower route factors (highways are more direct)
        if straight_distance_miles < 1:
            return 1.4  # Short distances have many turns
        elif straight_distance_miles < 5:
            return 1.3
        elif straight_distance_miles < 20:
            return 1.25
        else:
            return 1.2  # Highway travel is more direct
    
    def _get_travel_speed(self, transport_mode: TransportMode, departure_time: datetime) -> float:
        """Get travel speed in mph based on mode and time."""
        hour = departure_time.hour
        
        if transport_mode == TransportMode.DRIVING:
            # Adjust speed based on time of day
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
                return 25  # mph
            elif 22 <= hour or hour <= 6:  # Late night/early morning
                return 45  # mph
            else:
                return 35  # mph
        elif transport_mode == TransportMode.WALKING:
            return 3  # mph
        elif transport_mode == TransportMode.BICYCLE:
            return 12  # mph
        elif transport_mode == TransportMode.PUBLIC_TRANSIT:
            return 20  # mph (including stops)
        else:
            return 30  # mph (default)
    
    def _get_traffic_factor(self, departure_time: datetime) -> float:
        """Get traffic adjustment factor."""
        hour = departure_time.hour
        day_of_week = departure_time.weekday()
        
        # Weekend traffic is lighter
        if day_of_week >= 5:  # Saturday, Sunday
            return 0.9
        
        # Weekday traffic patterns
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
            return 1.5
        elif 10 <= hour <= 16:  # Mid-day
            return 1.1
        else:
            return 1.0  # Off-peak
    
    def _calculate_parking_time(self, location: Location) -> int:
        """Calculate parking time (same logic as Google provider)."""
        if location.building_type == "courthouse":
            parking_times = {
                "good": 5,
                "limited": 15,
                "poor": 25,
                "none": 0
            }
            return parking_times.get(location.parking_availability, 10)
        elif location.building_type == "law_firm":
            return 5
        else:
            return 8
    
    def _calculate_security_time(self, location: Location) -> int:
        """Calculate security screening time."""
        if location.building_type == "courthouse":
            return max(location.security_screening_time, 10)
        else:
            return location.security_screening_time
    
    def _calculate_walking_time(self, location: Location) -> int:
        """Calculate walking time within building."""
        if location.building_type == "courthouse":
            return 8
        elif location.building_type == "law_firm":
            return 3
        else:
            return 5
    
    def _estimate_traffic_condition(self, departure_time: datetime) -> TrafficCondition:
        """Estimate traffic condition based on time."""
        hour = departure_time.hour
        day_of_week = departure_time.weekday()
        
        if day_of_week >= 5:  # Weekend
            return TrafficCondition.LIGHT
        
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
            return TrafficCondition.HEAVY
        elif 10 <= hour <= 16:  # Mid-day
            return TrafficCondition.MODERATE
        else:
            return TrafficCondition.LIGHT
    
    def _create_fallback_result(self, request: TravelTimeRequest) -> TravelTimeResult:
        """Create conservative fallback result."""
        return TravelTimeResult(
            origin=request.origin,
            destination=request.destination,
            transport_mode=request.transport_mode,
            provider=TravelProvider.HISTORICAL_DATA,
            distance_miles=10.0,  # Conservative estimate
            travel_time_minutes=45,  # Conservative estimate
            confidence=0.3,
            fallback_used=True,
            error_message="Unable to calculate precise travel time, using conservative estimate"
        )
    
    def add_historical_data(self, route_key: str, travel_data: Dict[str, Any]):
        """Add historical travel time data."""
        if route_key not in self.historical_data:
            self.historical_data[route_key] = []
        
        self.historical_data[route_key].append(travel_data)
        
        # Keep only recent data (last 90 days)
        cutoff_date = datetime.now() - timedelta(days=90)
        self.historical_data[route_key] = [
            data for data in self.historical_data[route_key]
            if datetime.fromisoformat(data['recorded_at']) > cutoff_date
        ]
    
    def is_available(self) -> bool:
        """Historical provider is always available."""
        return True
    
    def get_rate_limit(self) -> Dict[str, int]:
        """No rate limits for historical provider."""
        return {'daily_limit': -1, 'used_today': 0, 'remaining': -1}


class TravelTimeCalculator:
    """Main travel time calculator with multiple providers and smart fallback."""
    
    def __init__(self):
        self.providers: Dict[TravelProvider, TravelTimeProvider] = {}
        self.cache: Dict[str, TravelTimeResult] = {}
        self.cache_duration_hours = 1
        self.request_count = 0
        
        # Initialize historical provider as default fallback
        self.providers[TravelProvider.HISTORICAL_DATA] = HistoricalTravelProvider()
        
    def register_provider(self, provider_type: TravelProvider, provider: TravelTimeProvider):
        """Register a travel time provider."""
        self.providers[provider_type] = provider
        logger.info(f"Registered travel time provider: {provider_type.value}")
    
    async def calculate_travel_time(self, request: TravelTimeRequest) -> TravelTimeResult:
        """Calculate travel time using the best available provider."""
        # Check cache first
        cache_key = self._create_cache_key(request)
        cached_result = self._get_cached_result(cache_key)
        
        if cached_result and cached_result.is_valid:
            logger.debug(f"Using cached travel time result")
            return cached_result
        
        # Try providers in order of preference
        for provider_type in request.preferred_providers:
            if provider_type in self.providers:
                provider = self.providers[provider_type]
                
                if provider.is_available():
                    try:
                        result = await provider.calculate_travel_time(request)
                        
                        if result.error_message is None:
                            # Cache successful result
                            self._cache_result(cache_key, result)
                            self.request_count += 1
                            
                            logger.info(f"Travel time calculated via {provider_type.value}: "
                                       f"{result.total_time_minutes} minutes")
                            return result
                        else:
                            logger.warning(f"Provider {provider_type.value} returned error: "
                                          f"{result.error_message}")
                    
                    except Exception as e:
                        logger.error(f"Provider {provider_type.value} failed: {str(e)}")
                        continue
                else:
                    logger.warning(f"Provider {provider_type.value} not available")
        
        # Fallback to historical/distance-based calculation
        historical_provider = self.providers.get(TravelProvider.HISTORICAL_DATA)
        if historical_provider:
            logger.info("Using fallback historical provider")
            result = await historical_provider.calculate_travel_time(request)
            self._cache_result(cache_key, result)
            return result
        
        # Ultimate fallback - very conservative estimate
        logger.warning("All providers failed, using ultimate fallback")
        return self._create_ultimate_fallback(request)
    
    async def calculate_multiple_routes(self, origin: Location, 
                                      destinations: List[Location],
                                      departure_time: datetime,
                                      transport_mode: TransportMode = TransportMode.DRIVING) -> List[TravelTimeResult]:
        """Calculate travel times to multiple destinations."""
        results = []
        
        # Create requests for all destinations
        requests = []
        for destination in destinations:
            request = TravelTimeRequest(
                origin=origin,
                destination=destination,
                departure_time=departure_time,
                transport_mode=transport_mode
            )
            requests.append(request)
        
        # Calculate in parallel
        tasks = [self.calculate_travel_time(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to calculate travel time to {destinations[i].name}: {str(result)}")
                # Create fallback result
                fallback_request = requests[i]
                fallback_result = self._create_ultimate_fallback(fallback_request)
                valid_results.append(fallback_result)
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def find_optimal_departure_time(self, origin: Location, destination: Location,
                                        arrival_time: datetime, 
                                        transport_mode: TransportMode = TransportMode.DRIVING,
                                        search_window_minutes: int = 120) -> Tuple[datetime, TravelTimeResult]:
        """Find the optimal departure time to arrive by a specific time."""
        
        # Start with simple calculation
        initial_request = TravelTimeRequest(
            origin=origin,
            destination=destination,
            departure_time=arrival_time - timedelta(hours=2),  # Initial guess
            transport_mode=transport_mode
        )
        
        initial_result = await self.calculate_travel_time(initial_request)
        
        # Calculate initial departure time
        total_time_needed = timedelta(minutes=initial_result.total_time_minutes)
        optimal_departure = arrival_time - total_time_needed
        
        # Refine with different times around rush hours
        candidate_times = []
        
        # Generate candidate departure times
        base_time = optimal_departure
        for offset_minutes in range(-search_window_minutes//2, search_window_minutes//2, 15):
            candidate_time = base_time + timedelta(minutes=offset_minutes)
            candidate_times.append(candidate_time)
        
        # Test each candidate time
        best_departure = optimal_departure
        best_result = initial_result
        
        for candidate_time in candidate_times:
            request = TravelTimeRequest(
                origin=origin,
                destination=destination,
                departure_time=candidate_time,
                transport_mode=transport_mode
            )
            
            result = await self.calculate_travel_time(request)
            
            # Calculate arrival time
            estimated_arrival = candidate_time + timedelta(minutes=result.total_time_minutes)
            
            # Check if this gets us there on time with better reliability
            if (estimated_arrival <= arrival_time and 
                result.confidence > best_result.confidence):
                best_departure = candidate_time
                best_result = result
        
        return best_departure, best_result
    
    def _create_cache_key(self, request: TravelTimeRequest) -> str:
        """Create cache key for request."""
        key_parts = [
            request.origin.name,
            request.destination.name,
            request.transport_mode.value,
            request.departure_time.strftime("%Y-%m-%d-%H")  # Hour-level caching
        ]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()[:16]
    
    def _get_cached_result(self, cache_key: str) -> Optional[TravelTimeResult]:
        """Get cached result if valid."""
        if cache_key in self.cache:
            result = self.cache[cache_key]
            if result.is_valid:
                return result
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
        
        return None
    
    def _cache_result(self, cache_key: str, result: TravelTimeResult):
        """Cache travel time result."""
        self.cache[cache_key] = result
        
        # Clean up old cache entries (simple cleanup)
        if len(self.cache) > 1000:  # Arbitrary limit
            # Remove oldest entries (this is simplified - in production use LRU cache)
            old_keys = list(self.cache.keys())[:100]
            for key in old_keys:
                if not self.cache[key].is_valid:
                    del self.cache[key]
    
    def _create_ultimate_fallback(self, request: TravelTimeRequest) -> TravelTimeResult:
        """Create ultimate fallback result when all else fails."""
        return TravelTimeResult(
            origin=request.origin,
            destination=request.destination,
            transport_mode=request.transport_mode,
            provider=TravelProvider.HISTORICAL_DATA,
            distance_miles=15.0,  # Very conservative
            travel_time_minutes=60,  # Very conservative
            parking_time_minutes=15,
            security_screening_minutes=10,
            walking_to_courtroom_minutes=10,
            prep_time_minutes=15,
            confidence=0.2,  # Very low confidence
            fallback_used=True,
            error_message="All travel time providers failed, using conservative estimate"
        )
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        valid_entries = sum(1 for result in self.cache.values() if result.is_valid)
        total_entries = len(self.cache)
        
        return {
            'total_cache_entries': total_entries,
            'valid_cache_entries': valid_entries,
            'cache_hit_rate': valid_entries / max(total_entries, 1),
            'total_requests': self.request_count,
            'provider_status': {
                provider_type.value: {
                    'available': provider.is_available(),
                    'rate_limits': provider.get_rate_limit()
                }
                for provider_type, provider in self.providers.items()
            }
        }
    
    def clear_cache(self):
        """Clear travel time cache."""
        self.cache.clear()
        logger.info("Travel time cache cleared")


# Example usage and testing
async def example_travel_time_usage():
    """Example usage of the travel time calculator."""
    
    # Create locations
    downtown_courthouse = Location(
        name="Downtown Federal Courthouse",
        address="123 Federal Plaza",
        city="Los Angeles",
        state="CA",
        zip_code="90012",
        building_type="courthouse",
        parking_availability="limited",
        security_screening_time=15
    )
    
    law_firm_office = Location(
        name="Smith & Associates",
        address="456 Wilshire Blvd",
        city="Los Angeles", 
        state="CA",
        zip_code="90017",
        building_type="law_firm",
        parking_availability="good"
    )
    
    uptown_courthouse = Location(
        name="Superior Court of California",
        address="789 Temple Street",
        city="Los Angeles",
        state="CA", 
        zip_code="90012",
        building_type="courthouse",
        parking_availability="poor",
        security_screening_time=20
    )
    
    # Initialize calculator
    calculator = TravelTimeCalculator()
    
    # Add Google Maps provider (would need real API key)
    # google_provider = GoogleMapsProvider("your-api-key-here")
    # calculator.register_provider(TravelProvider.GOOGLE_MAPS, google_provider)
    
    print("Testing Travel Time Calculator")
    print("=" * 40)
    
    # Test single route calculation
    departure_time = datetime(2024, 1, 15, 14, 0)  # 2 PM
    
    request = TravelTimeRequest(
        origin=law_firm_office,
        destination=downtown_courthouse,
        departure_time=departure_time,
        transport_mode=TransportMode.DRIVING,
        consider_traffic=True,
        buffer_percentage=0.25
    )
    
    result = await calculator.calculate_travel_time(request)
    
    print(f"Route: {result.origin.name} → {result.destination.name}")
    print(f"Transport Mode: {result.transport_mode.value}")
    print(f"Provider: {result.provider.value}")
    print(f"Distance: {result.distance_miles:.1f} miles")
    print(f"Base Travel Time: {result.travel_time_minutes} minutes")
    print(f"Traffic Delay: {result.traffic_delay_minutes} minutes")
    print(f"Parking Time: {result.parking_time_minutes} minutes")
    print(f"Security Screening: {result.security_screening_minutes} minutes")
    print(f"Walking to Courtroom: {result.walking_to_courtroom_minutes} minutes")
    print(f"Prep Time: {result.prep_time_minutes} minutes")
    print(f"Total Time: {result.total_time_minutes} minutes")
    print(f"Confidence: {result.confidence:.1%}")
    print(f"Traffic Condition: {result.traffic_condition.value}")
    
    if result.error_message:
        print(f"Error: {result.error_message}")
    if result.fallback_used:
        print("⚠️  Fallback method used")
    
    print("\n" + "=" * 40)
    
    # Test multiple destinations
    print("Testing multiple destinations...")
    destinations = [downtown_courthouse, uptown_courthouse]
    
    multi_results = await calculator.calculate_multiple_routes(
        origin=law_firm_office,
        destinations=destinations,
        departure_time=departure_time
    )
    
    print(f"\nRoutes from {law_firm_office.name}:")
    for i, result in enumerate(multi_results):
        print(f"{i+1}. To {result.destination.name}: {result.total_time_minutes} minutes")
    
    print("\n" + "=" * 40)
    
    # Test optimal departure time
    print("Finding optimal departure time...")
    target_arrival = datetime(2024, 1, 15, 15, 0)  # Must arrive by 3 PM
    
    optimal_departure, optimal_result = await calculator.find_optimal_departure_time(
        origin=law_firm_office,
        destination=downtown_courthouse,
        arrival_time=target_arrival,
        search_window_minutes=60
    )
    
    print(f"To arrive by {target_arrival.strftime('%I:%M %p')}:")
    print(f"Optimal departure: {optimal_departure.strftime('%I:%M %p')}")
    print(f"Travel time: {optimal_result.total_time_minutes} minutes")
    print(f"Confidence: {optimal_result.confidence:.1%}")
    
    # Get statistics
    stats = calculator.get_cache_statistics()
    print(f"\nCache Statistics:")
    print(f"Total requests: {stats['total_requests']}")
    print(f"Cache entries: {stats['total_cache_entries']}")
    print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
    
    print("\n" + json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    asyncio.run(example_travel_time_usage())