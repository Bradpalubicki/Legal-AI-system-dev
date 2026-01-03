"""
Calendar Integration Module for Legal AI System

Provides comprehensive calendar integration capabilities for legal deadlines,
court dates, and task scheduling across multiple calendar platforms.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import json
import asyncio
import logging
from urllib.parse import urlencode

import aiohttp
import icalendar
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import msal
from exchangelib import Credentials as ExchangeCredentials, Account, CalendarItem, EWSDateTime
import pytz

logger = logging.getLogger(__name__)


class CalendarProvider(Enum):
    """Supported calendar providers."""
    GOOGLE = "google"
    OUTLOOK = "outlook"
    EXCHANGE = "exchange"
    ICALENDAR = "icalendar"
    APPLE = "apple"


class EventPriority(Enum):
    """Event priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EventType(Enum):
    """Legal event types."""
    DEADLINE = "deadline"
    HEARING = "hearing"
    FILING = "filing"
    MEETING = "meeting"
    REMINDER = "reminder"
    COURT_DATE = "court_date"
    DISCOVERY = "discovery"
    DEPOSITION = "deposition"


@dataclass
class CalendarEvent:
    """Represents a calendar event for legal matters."""
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    event_type: EventType
    priority: EventPriority
    case_id: Optional[str] = None
    client_id: Optional[str] = None
    deadline_id: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None
    reminders: Optional[List[int]] = None  # Minutes before event
    metadata: Optional[Dict[str, Any]] = None
    external_event_id: Optional[str] = None
    provider: Optional[CalendarProvider] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['end_time'] = self.end_time.isoformat()
        data['event_type'] = self.event_type.value
        data['priority'] = self.priority.value
        if self.provider:
            data['provider'] = self.provider.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalendarEvent':
        """Create from dictionary format."""
        data['start_time'] = datetime.fromisoformat(data['start_time'])
        data['end_time'] = datetime.fromisoformat(data['end_time'])
        data['event_type'] = EventType(data['event_type'])
        data['priority'] = EventPriority(data['priority'])
        if 'provider' in data and data['provider']:
            data['provider'] = CalendarProvider(data['provider'])
        return cls(**data)


@dataclass
class CalendarConfig:
    """Calendar provider configuration."""
    provider: CalendarProvider
    credentials: Dict[str, Any]
    calendar_id: Optional[str] = None
    timezone: str = "UTC"
    sync_enabled: bool = True
    sync_interval: int = 300  # seconds
    
    def get_timezone(self) -> timezone:
        """Get timezone object."""
        return pytz.timezone(self.timezone)


class CalendarIntegrationError(Exception):
    """Calendar integration specific errors."""
    pass


class GoogleCalendarProvider:
    """Google Calendar integration provider."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, config: CalendarConfig):
        self.config = config
        self.service = None
        self.credentials = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Google Calendar."""
        try:
            creds_data = self.config.credentials
            self.credentials = Credentials.from_authorized_user_info(
                creds_data, self.SCOPES
            )
            
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    raise CalendarIntegrationError("Invalid Google Calendar credentials")
            
            self.service = build('calendar', 'v3', credentials=self.credentials)
            return True
        except Exception as e:
            logger.error(f"Google Calendar authentication failed: {str(e)}")
            return False
    
    async def create_event(self, event: CalendarEvent) -> str:
        """Create event in Google Calendar."""
        try:
            calendar_id = self.config.calendar_id or 'primary'
            
            google_event = {
                'summary': event.title,
                'description': event.description,
                'start': {
                    'dateTime': event.start_time.isoformat(),
                    'timeZone': self.config.timezone,
                },
                'end': {
                    'dateTime': event.end_time.isoformat(),
                    'timeZone': self.config.timezone,
                },
            }
            
            if event.location:
                google_event['location'] = event.location
            
            if event.attendees:
                google_event['attendees'] = [{'email': email} for email in event.attendees]
            
            if event.reminders:
                google_event['reminders'] = {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': minutes}
                        for minutes in event.reminders
                    ]
                }
            
            result = self.service.events().insert(
                calendarId=calendar_id,
                body=google_event
            ).execute()
            
            return result.get('id')
        
        except Exception as e:
            logger.error(f"Failed to create Google Calendar event: {str(e)}")
            raise CalendarIntegrationError(f"Google Calendar event creation failed: {str(e)}")
    
    async def update_event(self, event_id: str, event: CalendarEvent) -> bool:
        """Update event in Google Calendar."""
        try:
            calendar_id = self.config.calendar_id or 'primary'
            
            google_event = {
                'summary': event.title,
                'description': event.description,
                'start': {
                    'dateTime': event.start_time.isoformat(),
                    'timeZone': self.config.timezone,
                },
                'end': {
                    'dateTime': event.end_time.isoformat(),
                    'timeZone': self.config.timezone,
                },
            }
            
            if event.location:
                google_event['location'] = event.location
            
            self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=google_event
            ).execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to update Google Calendar event: {str(e)}")
            return False
    
    async def delete_event(self, event_id: str) -> bool:
        """Delete event from Google Calendar."""
        try:
            calendar_id = self.config.calendar_id or 'primary'
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete Google Calendar event: {str(e)}")
            return False
    
    async def get_events(self, start_date: datetime, end_date: datetime) -> List[CalendarEvent]:
        """Get events from Google Calendar."""
        try:
            calendar_id = self.config.calendar_id or 'primary'
            
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=start_date.isoformat(),
                timeMax=end_date.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = []
            for item in events_result.get('items', []):
                start = item['start'].get('dateTime', item['start'].get('date'))
                end = item['end'].get('dateTime', item['end'].get('date'))
                
                event = CalendarEvent(
                    title=item.get('summary', ''),
                    description=item.get('description', ''),
                    start_time=datetime.fromisoformat(start.replace('Z', '+00:00')),
                    end_time=datetime.fromisoformat(end.replace('Z', '+00:00')),
                    event_type=EventType.MEETING,  # Default type
                    priority=EventPriority.MEDIUM,  # Default priority
                    location=item.get('location'),
                    external_event_id=item.get('id'),
                    provider=CalendarProvider.GOOGLE
                )
                events.append(event)
            
            return events
        
        except Exception as e:
            logger.error(f"Failed to get Google Calendar events: {str(e)}")
            return []


class OutlookCalendarProvider:
    """Microsoft Outlook/Office 365 integration provider."""
    
    def __init__(self, config: CalendarConfig):
        self.config = config
        self.client_app = None
        self.token = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Outlook Calendar."""
        try:
            client_id = self.config.credentials.get('client_id')
            client_secret = self.config.credentials.get('client_secret')
            tenant_id = self.config.credentials.get('tenant_id')
            
            self.client_app = msal.ConfidentialClientApplication(
                client_id,
                authority=f"https://login.microsoftonline.com/{tenant_id}",
                client_credential=client_secret
            )
            
            # Try to get token from cache or refresh
            accounts = self.client_app.get_accounts()
            if accounts:
                result = self.client_app.acquire_token_silent(
                    ['https://graph.microsoft.com/Calendars.ReadWrite'],
                    account=accounts[0]
                )
                if result and 'access_token' in result:
                    self.token = result['access_token']
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Outlook Calendar authentication failed: {str(e)}")
            return False
    
    async def create_event(self, event: CalendarEvent) -> str:
        """Create event in Outlook Calendar."""
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            outlook_event = {
                'subject': event.title,
                'body': {
                    'contentType': 'HTML',
                    'content': event.description
                },
                'start': {
                    'dateTime': event.start_time.isoformat(),
                    'timeZone': self.config.timezone
                },
                'end': {
                    'dateTime': event.end_time.isoformat(),
                    'timeZone': self.config.timezone
                }
            }
            
            if event.location:
                outlook_event['location'] = {'displayName': event.location}
            
            if event.attendees:
                outlook_event['attendees'] = [
                    {'emailAddress': {'address': email, 'name': email}}
                    for email in event.attendees
                ]
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://graph.microsoft.com/v1.0/me/events',
                    headers=headers,
                    json=outlook_event
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        return result.get('id')
                    else:
                        raise CalendarIntegrationError(f"Outlook API returned {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to create Outlook Calendar event: {str(e)}")
            raise CalendarIntegrationError(f"Outlook Calendar event creation failed: {str(e)}")
    
    async def update_event(self, event_id: str, event: CalendarEvent) -> bool:
        """Update event in Outlook Calendar."""
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            outlook_event = {
                'subject': event.title,
                'body': {
                    'contentType': 'HTML',
                    'content': event.description
                },
                'start': {
                    'dateTime': event.start_time.isoformat(),
                    'timeZone': self.config.timezone
                },
                'end': {
                    'dateTime': event.end_time.isoformat(),
                    'timeZone': self.config.timezone
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f'https://graph.microsoft.com/v1.0/me/events/{event_id}',
                    headers=headers,
                    json=outlook_event
                ) as response:
                    return response.status == 200
        
        except Exception as e:
            logger.error(f"Failed to update Outlook Calendar event: {str(e)}")
            return False
    
    async def delete_event(self, event_id: str) -> bool:
        """Delete event from Outlook Calendar."""
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f'https://graph.microsoft.com/v1.0/me/events/{event_id}',
                    headers=headers
                ) as response:
                    return response.status == 204
        
        except Exception as e:
            logger.error(f"Failed to delete Outlook Calendar event: {str(e)}")
            return False


class CalendarSyncManager:
    """Manages calendar synchronization across multiple providers."""
    
    def __init__(self):
        self.providers: Dict[str, Any] = {}
        self.sync_tasks: Dict[str, asyncio.Task] = {}
    
    def register_provider(self, name: str, config: CalendarConfig):
        """Register a calendar provider."""
        if config.provider == CalendarProvider.GOOGLE:
            provider = GoogleCalendarProvider(config)
        elif config.provider == CalendarProvider.OUTLOOK:
            provider = OutlookCalendarProvider(config)
        else:
            raise CalendarIntegrationError(f"Unsupported provider: {config.provider}")
        
        self.providers[name] = {
            'provider': provider,
            'config': config
        }
    
    async def authenticate_all(self) -> Dict[str, bool]:
        """Authenticate all registered providers."""
        results = {}
        for name, provider_info in self.providers.items():
            try:
                success = await provider_info['provider'].authenticate()
                results[name] = success
                logger.info(f"Provider {name} authentication: {'success' if success else 'failed'}")
            except Exception as e:
                logger.error(f"Authentication failed for {name}: {str(e)}")
                results[name] = False
        
        return results
    
    async def create_event(self, event: CalendarEvent, providers: Optional[List[str]] = None) -> Dict[str, str]:
        """Create event across specified providers."""
        if providers is None:
            providers = list(self.providers.keys())
        
        results = {}
        for provider_name in providers:
            if provider_name not in self.providers:
                logger.warning(f"Provider {provider_name} not registered")
                continue
            
            try:
                provider = self.providers[provider_name]['provider']
                event_id = await provider.create_event(event)
                results[provider_name] = event_id
                logger.info(f"Event created in {provider_name}: {event_id}")
            except Exception as e:
                logger.error(f"Failed to create event in {provider_name}: {str(e)}")
                results[provider_name] = None
        
        return results
    
    async def update_event(self, event_ids: Dict[str, str], event: CalendarEvent) -> Dict[str, bool]:
        """Update event across providers."""
        results = {}
        for provider_name, event_id in event_ids.items():
            if provider_name not in self.providers or not event_id:
                continue
            
            try:
                provider = self.providers[provider_name]['provider']
                success = await provider.update_event(event_id, event)
                results[provider_name] = success
            except Exception as e:
                logger.error(f"Failed to update event in {provider_name}: {str(e)}")
                results[provider_name] = False
        
        return results
    
    async def delete_event(self, event_ids: Dict[str, str]) -> Dict[str, bool]:
        """Delete event from providers."""
        results = {}
        for provider_name, event_id in event_ids.items():
            if provider_name not in self.providers or not event_id:
                continue
            
            try:
                provider = self.providers[provider_name]['provider']
                success = await provider.delete_event(event_id)
                results[provider_name] = success
            except Exception as e:
                logger.error(f"Failed to delete event from {provider_name}: {str(e)}")
                results[provider_name] = False
        
        return results
    
    def start_sync(self, provider_name: str):
        """Start background sync for a provider."""
        if provider_name not in self.providers:
            raise CalendarIntegrationError(f"Provider {provider_name} not registered")
        
        config = self.providers[provider_name]['config']
        if not config.sync_enabled:
            return
        
        if provider_name in self.sync_tasks:
            self.sync_tasks[provider_name].cancel()
        
        self.sync_tasks[provider_name] = asyncio.create_task(
            self._sync_loop(provider_name)
        )
    
    def stop_sync(self, provider_name: str):
        """Stop background sync for a provider."""
        if provider_name in self.sync_tasks:
            self.sync_tasks[provider_name].cancel()
            del self.sync_tasks[provider_name]
    
    async def _sync_loop(self, provider_name: str):
        """Background sync loop for a provider."""
        config = self.providers[provider_name]['config']
        provider = self.providers[provider_name]['provider']
        
        while True:
            try:
                await asyncio.sleep(config.sync_interval)
                
                # Get events from the last 30 days to 90 days ahead
                start_date = datetime.now() - timedelta(days=30)
                end_date = datetime.now() + timedelta(days=90)
                
                events = await provider.get_events(start_date, end_date)
                logger.info(f"Synced {len(events)} events from {provider_name}")
                
                # Here you would typically save events to database
                # and trigger any necessary notifications or updates
                
            except asyncio.CancelledError:
                logger.info(f"Sync cancelled for {provider_name}")
                break
            except Exception as e:
                logger.error(f"Sync error for {provider_name}: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying


class LegalCalendarManager:
    """Main manager for legal calendar integration."""
    
    def __init__(self):
        self.sync_manager = CalendarSyncManager()
        self.event_mappings: Dict[str, Dict[str, str]] = {}  # internal_id -> {provider: external_id}
    
    async def initialize(self, configs: List[Tuple[str, CalendarConfig]]):
        """Initialize with calendar configurations."""
        for name, config in configs:
            self.sync_manager.register_provider(name, config)
        
        auth_results = await self.sync_manager.authenticate_all()
        
        # Start sync for authenticated providers
        for provider_name, authenticated in auth_results.items():
            if authenticated:
                self.sync_manager.start_sync(provider_name)
        
        return auth_results
    
    async def create_deadline_event(self, 
                                  deadline_data: Dict[str, Any],
                                  providers: Optional[List[str]] = None) -> str:
        """Create calendar event for a legal deadline."""
        
        # Determine event priority based on deadline importance
        priority_map = {
            'critical': EventPriority.CRITICAL,
            'high': EventPriority.HIGH,
            'medium': EventPriority.MEDIUM,
            'low': EventPriority.LOW
        }
        
        priority = priority_map.get(
            deadline_data.get('priority', 'medium'),
            EventPriority.MEDIUM
        )
        
        # Create calendar event
        event = CalendarEvent(
            title=f"DEADLINE: {deadline_data.get('title', 'Legal Deadline')}",
            description=self._format_deadline_description(deadline_data),
            start_time=datetime.fromisoformat(deadline_data['due_date']),
            end_time=datetime.fromisoformat(deadline_data['due_date']) + timedelta(hours=1),
            event_type=EventType.DEADLINE,
            priority=priority,
            case_id=deadline_data.get('case_id'),
            client_id=deadline_data.get('client_id'),
            deadline_id=deadline_data.get('deadline_id'),
            reminders=self._get_deadline_reminders(priority),
            metadata=deadline_data
        )
        
        # Create in calendar providers
        event_ids = await self.sync_manager.create_event(event, providers)
        
        # Store mapping
        internal_id = deadline_data.get('deadline_id') or f"deadline_{datetime.now().timestamp()}"
        self.event_mappings[internal_id] = event_ids
        
        return internal_id
    
    async def create_court_event(self,
                               hearing_data: Dict[str, Any],
                               providers: Optional[List[str]] = None) -> str:
        """Create calendar event for court hearing."""
        
        event = CalendarEvent(
            title=f"COURT: {hearing_data.get('title', 'Court Hearing')}",
            description=self._format_hearing_description(hearing_data),
            start_time=datetime.fromisoformat(hearing_data['start_time']),
            end_time=datetime.fromisoformat(hearing_data['end_time']),
            event_type=EventType.COURT_DATE,
            priority=EventPriority.HIGH,
            case_id=hearing_data.get('case_id'),
            client_id=hearing_data.get('client_id'),
            location=hearing_data.get('location'),
            reminders=[1440, 480, 60, 15],  # 1 day, 8 hours, 1 hour, 15 minutes
            metadata=hearing_data
        )
        
        event_ids = await self.sync_manager.create_event(event, providers)
        
        internal_id = hearing_data.get('hearing_id') or f"hearing_{datetime.now().timestamp()}"
        self.event_mappings[internal_id] = event_ids
        
        return internal_id
    
    def _format_deadline_description(self, deadline_data: Dict[str, Any]) -> str:
        """Format deadline description for calendar event."""
        description_parts = [
            f"Legal Deadline: {deadline_data.get('title', 'Unknown')}",
            f"Case: {deadline_data.get('case_name', 'N/A')}",
            f"Client: {deadline_data.get('client_name', 'N/A')}",
            f"Type: {deadline_data.get('deadline_type', 'N/A')}",
            f"Priority: {deadline_data.get('priority', 'medium').upper()}"
        ]
        
        if deadline_data.get('description'):
            description_parts.append(f"Details: {deadline_data['description']}")
        
        if deadline_data.get('consequences'):
            description_parts.append(f"Consequences: {deadline_data['consequences']}")
        
        return "\n".join(description_parts)
    
    def _format_hearing_description(self, hearing_data: Dict[str, Any]) -> str:
        """Format hearing description for calendar event."""
        description_parts = [
            f"Court Hearing: {hearing_data.get('title', 'Unknown')}",
            f"Case: {hearing_data.get('case_name', 'N/A')}",
            f"Judge: {hearing_data.get('judge', 'N/A')}",
            f"Courtroom: {hearing_data.get('courtroom', 'N/A')}"
        ]
        
        if hearing_data.get('hearing_type'):
            description_parts.append(f"Type: {hearing_data['hearing_type']}")
        
        if hearing_data.get('notes'):
            description_parts.append(f"Notes: {hearing_data['notes']}")
        
        return "\n".join(description_parts)
    
    def _get_deadline_reminders(self, priority: EventPriority) -> List[int]:
        """Get reminder schedule based on deadline priority."""
        reminder_schedules = {
            EventPriority.CRITICAL: [10080, 2880, 1440, 480, 120, 60, 15],  # 1 week to 15 min
            EventPriority.HIGH: [2880, 1440, 480, 120, 60],  # 2 days to 1 hour
            EventPriority.MEDIUM: [1440, 480, 120],  # 1 day to 2 hours
            EventPriority.LOW: [1440, 240]  # 1 day to 4 hours
        }
        
        return reminder_schedules.get(priority, [1440, 120])  # Default reminders
    
    async def update_event(self, internal_id: str, updated_data: Dict[str, Any]) -> bool:
        """Update an existing calendar event."""
        if internal_id not in self.event_mappings:
            logger.warning(f"No event mapping found for {internal_id}")
            return False
        
        # Recreate event with updated data
        if 'deadline_id' in updated_data or 'due_date' in updated_data:
            # It's a deadline event
            event = CalendarEvent(
                title=f"DEADLINE: {updated_data.get('title', 'Legal Deadline')}",
                description=self._format_deadline_description(updated_data),
                start_time=datetime.fromisoformat(updated_data['due_date']),
                end_time=datetime.fromisoformat(updated_data['due_date']) + timedelta(hours=1),
                event_type=EventType.DEADLINE,
                priority=EventPriority(updated_data.get('priority', 'medium')),
                metadata=updated_data
            )
        else:
            # It's a hearing event
            event = CalendarEvent(
                title=f"COURT: {updated_data.get('title', 'Court Hearing')}",
                description=self._format_hearing_description(updated_data),
                start_time=datetime.fromisoformat(updated_data['start_time']),
                end_time=datetime.fromisoformat(updated_data['end_time']),
                event_type=EventType.COURT_DATE,
                priority=EventPriority.HIGH,
                metadata=updated_data
            )
        
        event_ids = self.event_mappings[internal_id]
        results = await self.sync_manager.update_event(event_ids, event)
        
        return all(results.values())
    
    async def delete_event(self, internal_id: str) -> bool:
        """Delete a calendar event."""
        if internal_id not in self.event_mappings:
            logger.warning(f"No event mapping found for {internal_id}")
            return False
        
        event_ids = self.event_mappings[internal_id]
        results = await self.sync_manager.delete_event(event_ids)
        
        # Remove from mappings if deletion was successful
        if any(results.values()):
            del self.event_mappings[internal_id]
        
        return all(results.values())
    
    async def shutdown(self):
        """Clean shutdown of calendar manager."""
        # Stop all sync tasks
        for provider_name in list(self.sync_manager.sync_tasks.keys()):
            self.sync_manager.stop_sync(provider_name)
        
        logger.info("Calendar manager shutdown complete")


# Example usage and configuration
async def example_usage():
    """Example usage of the calendar integration system."""
    
    # Configuration for different providers
    google_config = CalendarConfig(
        provider=CalendarProvider.GOOGLE,
        credentials={
            'client_id': 'your-google-client-id',
            'client_secret': 'your-google-client-secret',
            'refresh_token': 'your-refresh-token',
            'access_token': 'your-access-token'
        },
        calendar_id='primary',
        timezone='America/New_York'
    )
    
    outlook_config = CalendarConfig(
        provider=CalendarProvider.OUTLOOK,
        credentials={
            'client_id': 'your-outlook-client-id',
            'client_secret': 'your-outlook-client-secret',
            'tenant_id': 'your-tenant-id'
        },
        timezone='America/New_York'
    )
    
    # Initialize calendar manager
    calendar_manager = LegalCalendarManager()
    
    # Set up providers
    configs = [
        ('google', google_config),
        ('outlook', outlook_config)
    ]
    
    auth_results = await calendar_manager.initialize(configs)
    print(f"Authentication results: {auth_results}")
    
    # Create a deadline event
    deadline_data = {
        'deadline_id': 'deadline_123',
        'title': 'File Motion to Dismiss',
        'due_date': '2024-01-15T17:00:00',
        'case_name': 'Smith v. Jones',
        'client_name': 'John Smith',
        'deadline_type': 'Motion Filing',
        'priority': 'high',
        'description': 'File motion to dismiss with prejudice',
        'consequences': 'Case proceeds to discovery if not filed'
    }
    
    event_id = await calendar_manager.create_deadline_event(deadline_data)
    print(f"Created deadline event: {event_id}")
    
    # Create a court hearing event
    hearing_data = {
        'hearing_id': 'hearing_456',
        'title': 'Pre-trial Conference',
        'start_time': '2024-01-20T09:00:00',
        'end_time': '2024-01-20T10:00:00',
        'case_name': 'Smith v. Jones',
        'judge': 'Hon. Jane Doe',
        'courtroom': 'Room 302',
        'location': '123 Main St, Court Building',
        'hearing_type': 'Pre-trial Conference'
    }
    
    hearing_id = await calendar_manager.create_court_event(hearing_data)
    print(f"Created hearing event: {hearing_id}")
    
    # Cleanup
    await calendar_manager.shutdown()


if __name__ == "__main__":
    asyncio.run(example_usage())