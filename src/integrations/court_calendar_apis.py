"""
Court Calendar API Integration System

Provides comprehensive integration with federal and state court calendar systems
for retrieving hearing schedules, calendar changes, and court availability.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlencode
import hashlib

logger = logging.getLogger(__name__)


class CalendarEventType(Enum):
    """Types of calendar events"""
    HEARING = "hearing"
    TRIAL = "trial"
    MOTION = "motion"
    CONFERENCE = "conference"
    ARRAIGNMENT = "arraignment"
    SENTENCING = "sentencing"
    SETTLEMENT_CONFERENCE = "settlement_conference"
    STATUS_CONFERENCE = "status_conference"
    PRETRIAL_CONFERENCE = "pretrial_conference"
    JURY_SELECTION = "jury_selection"
    PLEA_HEARING = "plea_hearing"
    ORAL_ARGUMENT = "oral_argument"
    CASE_MANAGEMENT = "case_management"
    SCHEDULING = "scheduling"
    OTHER = "other"


class CalendarEventStatus(Enum):
    """Status of calendar events"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    RESCHEDULED = "rescheduled"
    VACATED = "vacated"


@dataclass
class CalendarEvent:
    """Standardized calendar event data structure"""
    event_id: str
    case_number: str
    event_type: CalendarEventType
    title: str
    description: str
    date: datetime
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_minutes: Optional[int]
    location: str
    courtroom: Optional[str]
    judge: Optional[str]
    parties: List[str]
    attorneys: List[str]
    status: CalendarEventStatus
    is_public: bool
    filing_deadline: Optional[datetime]
    conference_type: Optional[str]
    hearing_type: Optional[str]
    estimated_duration: Optional[str]
    notes: Optional[str]
    last_updated: datetime
    source_court: str
    source_url: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for field in ['date', 'start_time', 'end_time', 'filing_deadline', 'last_updated']:
            if data[field]:
                data[field] = data[field].isoformat()
        # Convert enums to values
        data['event_type'] = data['event_type'].value
        data['status'] = data['status'].value
        return data


@dataclass
class CourtAvailability:
    """Court availability information"""
    court_code: str
    court_name: str
    date: datetime
    is_available: bool
    available_slots: List[Dict[str, Any]]
    holidays: List[str]
    special_sessions: List[Dict[str, Any]]
    emergency_contact: Optional[str]
    last_updated: datetime


@dataclass
class JudgeSchedule:
    """Judge's schedule information"""
    judge_id: str
    judge_name: str
    court: str
    date: datetime
    scheduled_events: List[CalendarEvent]
    availability_windows: List[Dict[str, Any]]
    vacation_dates: List[datetime]
    emergency_availability: bool
    last_updated: datetime


class CourtCalendarAPIClient:
    """Universal court calendar API client"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)
        self.cache = {}
        self.cache_ttl = config.get('cache_ttl_seconds', 3600)
        self.rate_limits = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def _get_cache_key(self, court_code: str, operation: str, **params) -> str:
        """Generate cache key for request"""
        param_str = json.dumps(params, sort_keys=True)
        return f"court_calendar:{court_code}:{operation}:{hashlib.md5(param_str.encode()).hexdigest()}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        timestamp, _ = self.cache[cache_key]
        return (datetime.now() - timestamp).seconds < self.cache_ttl

    async def _check_rate_limit(self, court_code: str) -> bool:
        """Check if we're within rate limits"""
        if court_code not in self.rate_limits:
            self.rate_limits[court_code] = []

        now = datetime.now()
        # Remove old requests (older than 1 minute)
        self.rate_limits[court_code] = [
            req_time for req_time in self.rate_limits[court_code]
            if (now - req_time).seconds < 60
        ]

        court_config = self.config['courts'].get(court_code, {})
        max_requests = court_config.get('rate_limit_per_minute', 30)

        if len(self.rate_limits[court_code]) >= max_requests:
            return False

        self.rate_limits[court_code].append(now)
        return True

    async def get_calendar_events(
        self,
        court_code: str,
        start_date: datetime,
        end_date: datetime,
        case_number: Optional[str] = None,
        judge: Optional[str] = None,
        event_type: Optional[CalendarEventType] = None
    ) -> List[CalendarEvent]:
        """Get calendar events for specified criteria"""
        cache_key = self._get_cache_key(
            court_code, 'events',
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            case_number=case_number,
            judge=judge,
            event_type=event_type.value if event_type else None
        )

        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached calendar events for {court_code}")
            return self.cache[cache_key][1]

        if not await self._check_rate_limit(court_code):
            logger.warning(f"Rate limit exceeded for {court_code}")
            raise Exception(f"Rate limit exceeded for {court_code}")

        try:
            court_config = self.config['courts'][court_code]
            events = await self._fetch_calendar_events(
                court_config, start_date, end_date, case_number, judge, event_type
            )

            # Cache the results
            self.cache[cache_key] = (datetime.now(), events)
            logger.info(f"Retrieved {len(events)} calendar events for {court_code}")
            return events

        except Exception as e:
            logger.error(f"Error retrieving calendar events for {court_code}: {str(e)}")
            raise

    async def _fetch_calendar_events(
        self,
        court_config: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        case_number: Optional[str],
        judge: Optional[str],
        event_type: Optional[CalendarEventType]
    ) -> List[CalendarEvent]:
        """Fetch calendar events from specific court API"""
        api_type = court_config.get('api_type', 'rest')

        if api_type == 'rest':
            return await self._fetch_rest_calendar_events(
                court_config, start_date, end_date, case_number, judge, event_type
            )
        elif api_type == 'soap':
            return await self._fetch_soap_calendar_events(
                court_config, start_date, end_date, case_number, judge, event_type
            )
        elif api_type == 'rss':
            return await self._fetch_rss_calendar_events(
                court_config, start_date, end_date, case_number, judge, event_type
            )
        elif api_type == 'web_scraping':
            return await self._fetch_web_scraping_calendar_events(
                court_config, start_date, end_date, case_number, judge, event_type
            )
        else:
            raise ValueError(f"Unsupported API type: {api_type}")

    async def _fetch_rest_calendar_events(
        self,
        court_config: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        case_number: Optional[str],
        judge: Optional[str],
        event_type: Optional[CalendarEventType]
    ) -> List[CalendarEvent]:
        """Fetch events from REST API"""
        base_url = court_config['base_url']
        endpoint = court_config['endpoints']['calendar']

        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }

        if case_number:
            params['case_number'] = case_number
        if judge:
            params['judge'] = judge
        if event_type:
            params['event_type'] = event_type.value

        headers = self._get_auth_headers(court_config)
        url = urljoin(base_url, endpoint)

        response = await self.client.get(url, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()
        return self._parse_rest_calendar_response(data, court_config['court_code'])

    async def _fetch_soap_calendar_events(
        self,
        court_config: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        case_number: Optional[str],
        judge: Optional[str],
        event_type: Optional[CalendarEventType]
    ) -> List[CalendarEvent]:
        """Fetch events from SOAP API"""
        soap_body = self._build_soap_request(
            court_config, start_date, end_date, case_number, judge, event_type
        )

        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': court_config.get('soap_action', ''),
            **self._get_auth_headers(court_config)
        }

        response = await self.client.post(
            court_config['base_url'],
            content=soap_body,
            headers=headers
        )
        response.raise_for_status()

        return self._parse_soap_calendar_response(response.text, court_config['court_code'])

    async def _fetch_rss_calendar_events(
        self,
        court_config: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        case_number: Optional[str],
        judge: Optional[str],
        event_type: Optional[CalendarEventType]
    ) -> List[CalendarEvent]:
        """Fetch events from RSS feed"""
        rss_url = court_config['rss_url']

        if case_number:
            rss_url += f"?case={case_number}"

        response = await self.client.get(rss_url)
        response.raise_for_status()

        return self._parse_rss_calendar_response(response.text, court_config['court_code'])

    async def _fetch_web_scraping_calendar_events(
        self,
        court_config: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        case_number: Optional[str],
        judge: Optional[str],
        event_type: Optional[CalendarEventType]
    ) -> List[CalendarEvent]:
        """Fetch events via web scraping"""
        base_url = court_config['base_url']
        calendar_path = court_config.get('calendar_path', '/calendar')

        params = {
            'date_from': start_date.strftime('%m/%d/%Y'),
            'date_to': end_date.strftime('%m/%d/%Y')
        }

        if case_number:
            params['case'] = case_number
        if judge:
            params['judge'] = judge

        url = f"{base_url}{calendar_path}?{urlencode(params)}"

        response = await self.client.get(url)
        response.raise_for_status()

        return self._parse_html_calendar_response(response.text, court_config['court_code'])

    def _get_auth_headers(self, court_config: Dict[str, Any]) -> Dict[str, str]:
        """Get authentication headers for court API"""
        auth_type = court_config.get('auth_type', 'none')
        headers = {}

        if auth_type == 'api_key':
            api_key = court_config.get('api_key')
            headers['X-API-Key'] = api_key
        elif auth_type == 'bearer':
            token = court_config.get('access_token')
            headers['Authorization'] = f'Bearer {token}'
        elif auth_type == 'basic':
            username = court_config.get('username')
            password = court_config.get('password')
            import base64
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers['Authorization'] = f'Basic {credentials}'

        return headers

    def _parse_rest_calendar_response(self, data: Dict[str, Any], court_code: str) -> List[CalendarEvent]:
        """Parse REST API response into CalendarEvent objects"""
        events = []

        for item in data.get('events', []):
            try:
                event = CalendarEvent(
                    event_id=item.get('id', ''),
                    case_number=item.get('case_number', ''),
                    event_type=CalendarEventType(item.get('event_type', 'other')),
                    title=item.get('title', ''),
                    description=item.get('description', ''),
                    date=datetime.fromisoformat(item.get('date')),
                    start_time=datetime.fromisoformat(item['start_time']) if item.get('start_time') else None,
                    end_time=datetime.fromisoformat(item['end_time']) if item.get('end_time') else None,
                    duration_minutes=item.get('duration_minutes'),
                    location=item.get('location', ''),
                    courtroom=item.get('courtroom'),
                    judge=item.get('judge'),
                    parties=item.get('parties', []),
                    attorneys=item.get('attorneys', []),
                    status=CalendarEventStatus(item.get('status', 'scheduled')),
                    is_public=item.get('is_public', True),
                    filing_deadline=datetime.fromisoformat(item['filing_deadline']) if item.get('filing_deadline') else None,
                    conference_type=item.get('conference_type'),
                    hearing_type=item.get('hearing_type'),
                    estimated_duration=item.get('estimated_duration'),
                    notes=item.get('notes'),
                    last_updated=datetime.now(),
                    source_court=court_code,
                    source_url=item.get('source_url')
                )
                events.append(event)
            except Exception as e:
                logger.warning(f"Failed to parse calendar event: {str(e)}")
                continue

        return events

    def _parse_soap_calendar_response(self, xml_data: str, court_code: str) -> List[CalendarEvent]:
        """Parse SOAP XML response into CalendarEvent objects"""
        events = []

        try:
            root = ET.fromstring(xml_data)
            # Find calendar events in SOAP response
            for event_elem in root.findall('.//CalendarEvent'):
                event = self._parse_xml_calendar_event(event_elem, court_code)
                if event:
                    events.append(event)
        except ET.ParseError as e:
            logger.error(f"Failed to parse SOAP XML response: {str(e)}")

        return events

    def _parse_rss_calendar_response(self, rss_data: str, court_code: str) -> List[CalendarEvent]:
        """Parse RSS feed into CalendarEvent objects"""
        events = []

        try:
            root = ET.fromstring(rss_data)
            for item in root.findall('.//item'):
                event = self._parse_rss_calendar_item(item, court_code)
                if event:
                    events.append(event)
        except ET.ParseError as e:
            logger.error(f"Failed to parse RSS XML: {str(e)}")

        return events

    def _parse_html_calendar_response(self, html_data: str, court_code: str) -> List[CalendarEvent]:
        """Parse HTML calendar page into CalendarEvent objects"""
        events = []

        try:
            soup = BeautifulSoup(html_data, 'html.parser')

            # Look for calendar event containers
            event_containers = soup.find_all(['tr', 'div'], class_=re.compile(r'calendar|event|hearing'))

            for container in event_containers:
                event = self._parse_html_calendar_event(container, court_code)
                if event:
                    events.append(event)
        except Exception as e:
            logger.error(f"Failed to parse HTML calendar: {str(e)}")

        return events

    def _parse_xml_calendar_event(self, event_elem: ET.Element, court_code: str) -> Optional[CalendarEvent]:
        """Parse XML calendar event element"""
        try:
            return CalendarEvent(
                event_id=event_elem.findtext('EventId', ''),
                case_number=event_elem.findtext('CaseNumber', ''),
                event_type=CalendarEventType(event_elem.findtext('EventType', 'other')),
                title=event_elem.findtext('Title', ''),
                description=event_elem.findtext('Description', ''),
                date=datetime.fromisoformat(event_elem.findtext('Date')),
                start_time=datetime.fromisoformat(event_elem.findtext('StartTime')) if event_elem.findtext('StartTime') else None,
                end_time=datetime.fromisoformat(event_elem.findtext('EndTime')) if event_elem.findtext('EndTime') else None,
                duration_minutes=int(event_elem.findtext('Duration', 0)) or None,
                location=event_elem.findtext('Location', ''),
                courtroom=event_elem.findtext('Courtroom'),
                judge=event_elem.findtext('Judge'),
                parties=[p.text for p in event_elem.findall('.//Party')],
                attorneys=[a.text for a in event_elem.findall('.//Attorney')],
                status=CalendarEventStatus(event_elem.findtext('Status', 'scheduled')),
                is_public=event_elem.findtext('IsPublic', 'true').lower() == 'true',
                filing_deadline=datetime.fromisoformat(event_elem.findtext('FilingDeadline')) if event_elem.findtext('FilingDeadline') else None,
                conference_type=event_elem.findtext('ConferenceType'),
                hearing_type=event_elem.findtext('HearingType'),
                estimated_duration=event_elem.findtext('EstimatedDuration'),
                notes=event_elem.findtext('Notes'),
                last_updated=datetime.now(),
                source_court=court_code,
                source_url=event_elem.findtext('SourceUrl')
            )
        except Exception as e:
            logger.warning(f"Failed to parse XML calendar event: {str(e)}")
            return None

    def _parse_rss_calendar_item(self, item_elem: ET.Element, court_code: str) -> Optional[CalendarEvent]:
        """Parse RSS calendar item"""
        try:
            title = item_elem.findtext('title', '')
            description = item_elem.findtext('description', '')
            pub_date = item_elem.findtext('pubDate', '')

            # Extract case number from title or description
            case_match = re.search(r'Case\s*#?\s*:?\s*(\d+[-\w]+)', title + ' ' + description)
            case_number = case_match.group(1) if case_match else ''

            # Extract event type
            event_type = CalendarEventType.OTHER
            for et in CalendarEventType:
                if et.value.lower() in title.lower() or et.value.lower() in description.lower():
                    event_type = et
                    break

            return CalendarEvent(
                event_id=hashlib.md5((title + pub_date).encode()).hexdigest()[:12],
                case_number=case_number,
                event_type=event_type,
                title=title,
                description=description,
                date=datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z') if pub_date else datetime.now(),
                start_time=None,
                end_time=None,
                duration_minutes=None,
                location='',
                courtroom=None,
                judge=None,
                parties=[],
                attorneys=[],
                status=CalendarEventStatus.SCHEDULED,
                is_public=True,
                filing_deadline=None,
                conference_type=None,
                hearing_type=None,
                estimated_duration=None,
                notes=None,
                last_updated=datetime.now(),
                source_court=court_code,
                source_url=item_elem.findtext('link')
            )
        except Exception as e:
            logger.warning(f"Failed to parse RSS calendar item: {str(e)}")
            return None

    def _parse_html_calendar_event(self, container, court_code: str) -> Optional[CalendarEvent]:
        """Parse HTML calendar event container"""
        try:
            # Extract text content
            text = container.get_text(strip=True)

            # Extract case number
            case_match = re.search(r'Case\s*#?\s*:?\s*(\d+[-\w]+)', text)
            case_number = case_match.group(1) if case_match else ''

            # Extract date/time
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
            event_date = datetime.strptime(date_match.group(1), '%m/%d/%Y') if date_match else datetime.now()

            time_match = re.search(r'(\d{1,2}:\d{2}\s*[AP]M)', text)
            if time_match:
                time_str = time_match.group(1)
                event_time = datetime.strptime(time_str, '%I:%M %p').time()
                event_date = datetime.combine(event_date.date(), event_time)

            # Extract judge
            judge_match = re.search(r'Judge\s*:?\s*([^,\n]+)', text)
            judge = judge_match.group(1).strip() if judge_match else None

            # Extract courtroom
            courtroom_match = re.search(r'Courtroom\s*:?\s*([^,\n]+)', text)
            courtroom = courtroom_match.group(1).strip() if courtroom_match else None

            return CalendarEvent(
                event_id=hashlib.md5(text.encode()).hexdigest()[:12],
                case_number=case_number,
                event_type=CalendarEventType.HEARING,
                title=text[:100],
                description=text,
                date=event_date,
                start_time=event_date if time_match else None,
                end_time=None,
                duration_minutes=None,
                location=courtroom or '',
                courtroom=courtroom,
                judge=judge,
                parties=[],
                attorneys=[],
                status=CalendarEventStatus.SCHEDULED,
                is_public=True,
                filing_deadline=None,
                conference_type=None,
                hearing_type=None,
                estimated_duration=None,
                notes=None,
                last_updated=datetime.now(),
                source_court=court_code,
                source_url=None
            )
        except Exception as e:
            logger.warning(f"Failed to parse HTML calendar event: {str(e)}")
            return None

    def _build_soap_request(
        self,
        court_config: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        case_number: Optional[str],
        judge: Optional[str],
        event_type: Optional[CalendarEventType]
    ) -> str:
        """Build SOAP request body"""
        soap_template = court_config.get('soap_template', '''
        <?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <GetCalendarEvents>
                    <StartDate>{start_date}</StartDate>
                    <EndDate>{end_date}</EndDate>
                    {case_filter}
                    {judge_filter}
                    {type_filter}
                </GetCalendarEvents>
            </soap:Body>
        </soap:Envelope>
        ''')

        case_filter = f'<CaseNumber>{case_number}</CaseNumber>' if case_number else ''
        judge_filter = f'<Judge>{judge}</Judge>' if judge else ''
        type_filter = f'<EventType>{event_type.value}</EventType>' if event_type else ''

        return soap_template.format(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            case_filter=case_filter,
            judge_filter=judge_filter,
            type_filter=type_filter
        )

    async def get_court_availability(
        self,
        court_code: str,
        date: datetime,
        duration_hours: Optional[int] = None
    ) -> CourtAvailability:
        """Get court availability for specified date"""
        cache_key = self._get_cache_key(
            court_code, 'availability',
            date=date.isoformat(),
            duration_hours=duration_hours
        )

        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached availability for {court_code}")
            return self.cache[cache_key][1]

        if not await self._check_rate_limit(court_code):
            logger.warning(f"Rate limit exceeded for {court_code}")
            raise Exception(f"Rate limit exceeded for {court_code}")

        try:
            court_config = self.config['courts'][court_code]
            availability = await self._fetch_court_availability(court_config, date, duration_hours)

            # Cache the results
            self.cache[cache_key] = (datetime.now(), availability)
            logger.info(f"Retrieved availability for {court_code} on {date.date()}")
            return availability

        except Exception as e:
            logger.error(f"Error retrieving court availability for {court_code}: {str(e)}")
            raise

    async def _fetch_court_availability(
        self,
        court_config: Dict[str, Any],
        date: datetime,
        duration_hours: Optional[int]
    ) -> CourtAvailability:
        """Fetch court availability from API"""
        base_url = court_config['base_url']
        endpoint = court_config['endpoints'].get('availability', '/availability')

        params = {
            'date': date.strftime('%Y-%m-%d')
        }

        if duration_hours:
            params['duration'] = duration_hours

        headers = self._get_auth_headers(court_config)
        url = urljoin(base_url, endpoint)

        response = await self.client.get(url, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()

        return CourtAvailability(
            court_code=court_config['court_code'],
            court_name=court_config.get('court_name', ''),
            date=date,
            is_available=data.get('is_available', False),
            available_slots=data.get('available_slots', []),
            holidays=data.get('holidays', []),
            special_sessions=data.get('special_sessions', []),
            emergency_contact=data.get('emergency_contact'),
            last_updated=datetime.now()
        )

    async def get_judge_schedule(
        self,
        court_code: str,
        judge_id: str,
        date: datetime
    ) -> JudgeSchedule:
        """Get judge's schedule for specified date"""
        cache_key = self._get_cache_key(
            court_code, 'judge_schedule',
            judge_id=judge_id,
            date=date.isoformat()
        )

        if self._is_cache_valid(cache_key):
            logger.info(f"Returning cached judge schedule for {judge_id}")
            return self.cache[cache_key][1]

        if not await self._check_rate_limit(court_code):
            logger.warning(f"Rate limit exceeded for {court_code}")
            raise Exception(f"Rate limit exceeded for {court_code}")

        try:
            court_config = self.config['courts'][court_code]
            schedule = await self._fetch_judge_schedule(court_config, judge_id, date)

            # Cache the results
            self.cache[cache_key] = (datetime.now(), schedule)
            logger.info(f"Retrieved schedule for judge {judge_id} on {date.date()}")
            return schedule

        except Exception as e:
            logger.error(f"Error retrieving judge schedule: {str(e)}")
            raise

    async def _fetch_judge_schedule(
        self,
        court_config: Dict[str, Any],
        judge_id: str,
        date: datetime
    ) -> JudgeSchedule:
        """Fetch judge schedule from API"""
        base_url = court_config['base_url']
        endpoint = court_config['endpoints'].get('judge_schedule', '/judge/{judge_id}/schedule')
        endpoint = endpoint.format(judge_id=judge_id)

        params = {
            'date': date.strftime('%Y-%m-%d')
        }

        headers = self._get_auth_headers(court_config)
        url = urljoin(base_url, endpoint)

        response = await self.client.get(url, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()

        # Parse scheduled events
        scheduled_events = []
        for event_data in data.get('scheduled_events', []):
            event = self._parse_rest_calendar_response({'events': [event_data]}, court_config['court_code'])
            if event:
                scheduled_events.extend(event)

        return JudgeSchedule(
            judge_id=judge_id,
            judge_name=data.get('judge_name', ''),
            court=court_config['court_code'],
            date=date,
            scheduled_events=scheduled_events,
            availability_windows=data.get('availability_windows', []),
            vacation_dates=[datetime.fromisoformat(d) for d in data.get('vacation_dates', [])],
            emergency_availability=data.get('emergency_availability', False),
            last_updated=datetime.now()
        )


class CourtCalendarManager:
    """High-level court calendar management system"""

    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.clients = {}
        self.initialize_clients()

    def initialize_clients(self):
        """Initialize court calendar API clients"""
        for court_code, court_config in self.config['courts'].items():
            self.clients[court_code] = CourtCalendarAPIClient(self.config)

    async def get_multi_court_calendar(
        self,
        court_codes: List[str],
        start_date: datetime,
        end_date: datetime,
        **filters
    ) -> Dict[str, List[CalendarEvent]]:
        """Get calendar events from multiple courts"""
        results = {}

        tasks = []
        for court_code in court_codes:
            if court_code in self.clients:
                task = self._get_court_calendar_safe(
                    court_code, start_date, end_date, **filters
                )
                tasks.append((court_code, task))

        # Execute all requests concurrently
        for court_code, task in tasks:
            try:
                events = await task
                results[court_code] = events
            except Exception as e:
                logger.error(f"Failed to get calendar for {court_code}: {str(e)}")
                results[court_code] = []

        return results

    async def _get_court_calendar_safe(
        self,
        court_code: str,
        start_date: datetime,
        end_date: datetime,
        **filters
    ) -> List[CalendarEvent]:
        """Safely get calendar events with error handling"""
        try:
            async with self.clients[court_code] as client:
                return await client.get_calendar_events(
                    court_code, start_date, end_date, **filters
                )
        except Exception as e:
            logger.error(f"Error getting calendar for {court_code}: {str(e)}")
            return []

    async def search_calendar_events(
        self,
        query: str,
        court_codes: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CalendarEvent]:
        """Search calendar events across multiple courts"""
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        if not court_codes:
            court_codes = list(self.config['courts'].keys())

        all_events = []

        # Get events from all courts
        court_results = await self.get_multi_court_calendar(
            court_codes, start_date, end_date
        )

        # Flatten results and filter by query
        for events in court_results.values():
            for event in events:
                if self._matches_query(event, query):
                    all_events.append(event)

        # Sort by date
        all_events.sort(key=lambda e: e.date)

        return all_events

    def _matches_query(self, event: CalendarEvent, query: str) -> bool:
        """Check if event matches search query"""
        query_lower = query.lower()

        searchable_fields = [
            event.title,
            event.description,
            event.case_number,
            event.judge or '',
            ' '.join(event.parties),
            ' '.join(event.attorneys),
            event.location,
            event.courtroom or ''
        ]

        search_text = ' '.join(searchable_fields).lower()
        return query_lower in search_text

    async def get_calendar_conflicts(
        self,
        court_codes: List[str],
        judge: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Find scheduling conflicts for a judge across courts"""
        conflicts = []

        # Get judge's schedule from all courts
        judge_events = {}
        for court_code in court_codes:
            try:
                async with self.clients[court_code] as client:
                    events = await client.get_calendar_events(
                        court_code, start_date, end_date, judge=judge
                    )
                    judge_events[court_code] = events
            except Exception as e:
                logger.error(f"Error getting {court_code} calendar for judge {judge}: {str(e)}")
                continue

        # Find overlapping events
        all_events = []
        for court_code, events in judge_events.items():
            for event in events:
                all_events.append((court_code, event))

        # Sort by date/time
        all_events.sort(key=lambda x: x[1].date)

        # Check for overlaps
        for i in range(len(all_events)):
            for j in range(i + 1, len(all_events)):
                court1, event1 = all_events[i]
                court2, event2 = all_events[j]

                if self._events_overlap(event1, event2):
                    conflicts.append({
                        'conflict_type': 'schedule_overlap',
                        'event1': {
                            'court': court1,
                            'event': event1.to_dict()
                        },
                        'event2': {
                            'court': court2,
                            'event': event2.to_dict()
                        },
                        'severity': 'high' if event1.date.date() == event2.date.date() else 'medium'
                    })

        return conflicts

    def _events_overlap(self, event1: CalendarEvent, event2: CalendarEvent) -> bool:
        """Check if two events overlap in time"""
        if not (event1.start_time and event1.end_time and event2.start_time and event2.end_time):
            # If we don't have precise times, check if they're on the same day
            return event1.date.date() == event2.date.date()

        # Check for time overlap
        return (event1.start_time < event2.end_time and event2.start_time < event1.end_time)

    async def close(self):
        """Close all clients"""
        for client in self.clients.values():
            await client.__aexit__(None, None, None)


# Configuration for major court systems
COURT_CALENDAR_CONFIG = {
    "courts": {
        "federal_district": {
            "court_code": "federal_district",
            "court_name": "Federal District Courts",
            "api_type": "rest",
            "base_url": "https://ecf.dcd.uscourts.gov/api/v1",
            "auth_type": "certificate",
            "endpoints": {
                "calendar": "/calendar/events",
                "availability": "/calendar/availability",
                "judge_schedule": "/judges/{judge_id}/schedule"
            },
            "rate_limit_per_minute": 30,
            "cache_ttl_seconds": 1800
        },
        "federal_circuit": {
            "court_code": "federal_circuit",
            "court_name": "Federal Circuit Courts",
            "api_type": "rest",
            "base_url": "https://ecf.ca2.uscourts.gov/api/v1",
            "auth_type": "certificate",
            "endpoints": {
                "calendar": "/calendar/events",
                "availability": "/calendar/availability"
            },
            "rate_limit_per_minute": 20
        },
        "supreme_court": {
            "court_code": "supreme_court",
            "court_name": "Supreme Court of the United States",
            "api_type": "rss",
            "rss_url": "https://www.supremecourt.gov/rss/cases.xml",
            "rate_limit_per_minute": 10
        },
        "ca_superior": {
            "court_code": "ca_superior",
            "court_name": "California Superior Courts",
            "api_type": "soap",
            "base_url": "https://portal.courtinfo.ca.gov/services/CalendarService.asmx",
            "auth_type": "api_key",
            "soap_action": "http://tempuri.org/GetCalendarEvents",
            "endpoints": {
                "calendar": "/GetCalendarEvents"
            },
            "rate_limit_per_minute": 60
        },
        "ny_supreme": {
            "court_code": "ny_supreme",
            "court_name": "New York State Supreme Court",
            "api_type": "web_scraping",
            "base_url": "https://iapps.courts.state.ny.us",
            "calendar_path": "/webcal_Date",
            "rate_limit_per_minute": 15
        },
        "tx_district": {
            "court_code": "tx_district",
            "court_name": "Texas District Courts",
            "api_type": "rest",
            "base_url": "https://card.txcourts.gov/api/v1",
            "auth_type": "api_key",
            "endpoints": {
                "calendar": "/calendar",
                "availability": "/availability"
            },
            "rate_limit_per_minute": 45
        },
        "fl_circuit": {
            "court_code": "fl_circuit",
            "court_name": "Florida Circuit Courts",
            "api_type": "rest",
            "base_url": "https://flclerks.com/api/v2",
            "auth_type": "oauth2",
            "endpoints": {
                "calendar": "/calendar/events",
                "availability": "/calendar/availability"
            },
            "rate_limit_per_minute": 30
        }
    },
    "cache_ttl_seconds": 3600,
    "max_concurrent_requests": 10,
    "request_timeout_seconds": 30,
    "retry_attempts": 3,
    "retry_delay_seconds": 1
}

# Example usage
async def main():
    """Example usage of the court calendar API system"""
    manager = CourtCalendarManager('court_calendar_config.json')

    try:
        # Get calendar events for multiple courts
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)

        court_codes = ['federal_district', 'ca_superior', 'ny_supreme']

        # Get events from multiple courts
        calendar_results = await manager.get_multi_court_calendar(
            court_codes, start_date, end_date
        )

        print(f"Retrieved calendar events:")
        for court_code, events in calendar_results.items():
            print(f"{court_code}: {len(events)} events")
            for event in events[:3]:  # Show first 3 events
                print(f"  - {event.title} on {event.date.strftime('%Y-%m-%d')}")

        # Search for specific case
        search_results = await manager.search_calendar_events(
            "Smith v. Jones", court_codes, start_date, end_date
        )
        print(f"Found {len(search_results)} events matching 'Smith v. Jones'")

        # Check for judge conflicts
        conflicts = await manager.get_calendar_conflicts(
            court_codes, "Judge Smith", start_date, end_date
        )
        print(f"Found {len(conflicts)} scheduling conflicts for Judge Smith")

    finally:
        await manager.close()


if __name__ == "__main__":
    asyncio.run(main())