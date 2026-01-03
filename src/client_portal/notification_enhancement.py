"""
Notification Enhancement Module

Adds intelligent features to the existing notification system including
sentiment analysis, personalization, timing optimization, and multi-modal delivery.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from sqlalchemy.orm import Session

from .intelligent_notification_system import IntelligentNotificationSystem, ComplexityLevel, TranslationContext
from .notification_manager import NotificationManager
from .models import ClientUser, NotificationPriority


class SentimentType(Enum):
    POSITIVE = "positive"      # Good news, successful outcomes
    NEUTRAL = "neutral"        # Informational updates
    NEGATIVE = "negative"      # Bad news, setbacks
    URGENT = "urgent"         # Time-sensitive actions
    REASSURING = "reassuring" # Comfort during difficult times

class DeliveryChannel(Enum):
    PORTAL = "portal"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push_notification"
    PHONE_CALL = "phone_call"

class PersonalizationFactor(Enum):
    COMMUNICATION_STYLE = "communication_style"    # Formal vs. casual
    DETAIL_PREFERENCE = "detail_preference"        # Brief vs. comprehensive
    TIMING_PREFERENCE = "timing_preference"        # When to receive notifications
    ANXIETY_LEVEL = "anxiety_level"               # How much reassurance needed
    TECH_COMFORT = "tech_comfort"                 # Technology comfort level

@dataclass
class ClientPersonality:
    """Client's communication preferences and personality traits."""
    communication_style: str  # formal, friendly, casual
    detail_preference: str     # minimal, moderate, comprehensive
    anxiety_level: str         # low, moderate, high
    tech_comfort: str          # low, moderate, high
    preferred_channels: List[DeliveryChannel]
    quiet_hours: Dict[str, str]  # start_time, end_time
    timezone: str
    language: str = "en"

@dataclass
class EnhancedNotification:
    """Enhanced notification with sentiment and personalization."""
    base_notification: Dict[str, Any]
    sentiment: SentimentType
    personalized_content: Dict[str, str]  # Different versions for different channels
    optimal_delivery_time: datetime
    recommended_channels: List[DeliveryChannel]
    follow_up_needed: bool
    reassurance_level: int  # 1-5 scale
    call_to_action: Optional[str]


class NotificationEnhancementEngine:
    """Enhances notifications with personalization and intelligent delivery."""
    
    def __init__(
        self, 
        db_session: Session,
        intelligent_system: IntelligentNotificationSystem,
        notification_manager: NotificationManager
    ):
        self.db = db_session
        self.intelligent_system = intelligent_system
        self.notification_manager = notification_manager
        
        # Load personality detection patterns
        self.personality_indicators = self._load_personality_indicators()
        self.sentiment_patterns = self._load_sentiment_patterns()
        self.timing_rules = self._load_timing_optimization_rules()
        
    async def create_enhanced_notification(
        self,
        client_id: int,
        event_type: str,
        original_data: Dict[str, Any],
        context: TranslationContext,
        priority: NotificationPriority = NotificationPriority.MEDIUM
    ) -> Dict[str, Any]:
        """Create an enhanced notification with personalization."""
        try:
            # Get client personality profile
            client = self.db.query(ClientUser).filter(ClientUser.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}
            
            personality = await self._analyze_client_personality(client)
            
            # Create base intelligent notification
            base_result = await self.intelligent_system.create_intelligent_notification(
                client_id=client_id,
                event_type=event_type,
                original_data=original_data,
                context=context,
                priority=priority,
                complexity_override=self._get_complexity_for_personality(personality)
            )
            
            if not base_result['success']:
                return base_result
            
            # Enhance the notification
            enhanced = await self._enhance_notification(
                base_result['intelligent_notification'],
                personality,
                client,
                priority,
                context
            )
            
            # Optimize delivery timing and channels
            delivery_plan = await self._create_delivery_plan(enhanced, personality, priority)
            
            # Create personalized versions for different channels
            channel_content = await self._create_channel_specific_content(
                enhanced, personality, delivery_plan
            )
            
            return {
                'success': True,
                'notification_id': base_result['notification_id'],
                'enhanced_notification': enhanced,
                'delivery_plan': delivery_plan,
                'channel_content': channel_content,
                'personality_insights': personality
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Enhanced notification creation failed: {str(e)}'}
    
    async def _analyze_client_personality(self, client: ClientUser) -> ClientPersonality:
        """Analyze client's communication preferences and personality."""
        
        # Get explicit preferences
        prefs = client.notification_preferences or {}
        
        # Analyze communication history for implicit preferences
        communication_style = await self._detect_communication_style(client)
        detail_preference = await self._detect_detail_preference(client)
        anxiety_level = await self._detect_anxiety_level(client)
        tech_comfort = await self._detect_tech_comfort(client)
        
        # Determine preferred channels
        preferred_channels = self._determine_preferred_channels(prefs, tech_comfort)
        
        # Get timing preferences
        quiet_hours = prefs.get('quiet_hours', {'start_time': '22:00', 'end_time': '08:00'})
        
        return ClientPersonality(
            communication_style=communication_style,
            detail_preference=detail_preference,
            anxiety_level=anxiety_level,
            tech_comfort=tech_comfort,
            preferred_channels=preferred_channels,
            quiet_hours=quiet_hours,
            timezone=client.timezone or 'UTC',
            language=client.language or 'en'
        )
    
    async def _enhance_notification(
        self,
        base_notification: Any,
        personality: ClientPersonality,
        client: ClientUser,
        priority: NotificationPriority,
        context: TranslationContext
    ) -> EnhancedNotification:
        """Enhance notification based on client personality."""
        
        # Determine sentiment
        sentiment = self._analyze_sentiment(base_notification, context)
        
        # Create personalized content
        personalized_content = await self._personalize_content(
            base_notification, personality, sentiment, client
        )
        
        # Calculate optimal delivery time
        optimal_time = await self._calculate_optimal_delivery_time(
            personality, priority, sentiment
        )
        
        # Determine recommended channels
        recommended_channels = self._select_optimal_channels(
            personality, priority, sentiment, context
        )
        
        # Assess follow-up needs
        follow_up_needed = self._assess_follow_up_needs(
            base_notification, personality, context
        )
        
        # Calculate reassurance level needed
        reassurance_level = self._calculate_reassurance_level(
            sentiment, personality.anxiety_level, context
        )
        
        # Generate call to action
        call_to_action = self._generate_call_to_action(
            base_notification, personality, context
        )
        
        return EnhancedNotification(
            base_notification=base_notification.__dict__,
            sentiment=sentiment,
            personalized_content=personalized_content,
            optimal_delivery_time=optimal_time,
            recommended_channels=recommended_channels,
            follow_up_needed=follow_up_needed,
            reassurance_level=reassurance_level,
            call_to_action=call_to_action
        )
    
    async def _detect_communication_style(self, client: ClientUser) -> str:
        """Detect client's preferred communication style from history."""
        
        # Check explicit preference
        prefs = client.notification_preferences or {}
        if 'communication_style' in prefs:
            return prefs['communication_style']
        
        # Analyze from profile and interaction patterns
        # Simple heuristics for now - in production, could use ML
        
        if client.company_name:
            return "formal"  # Business clients often prefer formal tone
        
        # Default to friendly for individual clients
        return "friendly"
    
    async def _detect_detail_preference(self, client: ClientUser) -> str:
        """Detect how much detail the client prefers."""
        
        prefs = client.notification_preferences or {}
        if 'detail_level' in prefs:
            return prefs['detail_level']
        
        # Could analyze past interaction patterns here
        # For now, default to moderate
        return "moderate"
    
    async def _detect_anxiety_level(self, client: ClientUser) -> str:
        """Detect client's anxiety level regarding legal matters."""
        
        prefs = client.notification_preferences or {}
        if 'anxiety_level' in prefs:
            return prefs['anxiety_level']
        
        # Could analyze from frequency of contact, questions asked, etc.
        # For now, assume moderate anxiety (common for legal clients)
        return "moderate"
    
    async def _detect_tech_comfort(self, client: ClientUser) -> str:
        """Detect client's comfort level with technology."""
        
        prefs = client.notification_preferences or {}
        if 'tech_comfort' in prefs:
            return prefs['tech_comfort']
        
        # Heuristics based on age, industry, etc.
        # For now, default to moderate
        return "moderate"
    
    def _determine_preferred_channels(self, prefs: Dict, tech_comfort: str) -> List[DeliveryChannel]:
        """Determine preferred delivery channels."""
        
        if 'preferred_channels' in prefs:
            return [DeliveryChannel(ch) for ch in prefs['preferred_channels'] if ch in DeliveryChannel.__members__.values()]
        
        # Default channels based on tech comfort
        if tech_comfort == "high":
            return [DeliveryChannel.PORTAL, DeliveryChannel.PUSH, DeliveryChannel.EMAIL]
        elif tech_comfort == "low":
            return [DeliveryChannel.EMAIL, DeliveryChannel.PHONE_CALL]
        else:
            return [DeliveryChannel.PORTAL, DeliveryChannel.EMAIL]
    
    def _analyze_sentiment(self, notification: Any, context: TranslationContext) -> SentimentType:
        """Analyze the sentiment of the notification content."""
        
        title = notification.translated_title.lower()
        message = notification.translated_message.lower()
        combined_text = f"{title} {message}"
        
        # Check for positive indicators
        positive_patterns = [
            r'\b(settled|resolved|successful|approved|won|victory|good news|great news)\b',
            r'\b(completed|finished|accomplished|achieved)\b'
        ]
        
        # Check for negative indicators
        negative_patterns = [
            r'\b(denied|rejected|dismissed|failed|lost|bad news|unfortunately)\b',
            r'\b(problem|issue|concern|difficulty)\b'
        ]
        
        # Check for urgent indicators
        urgent_patterns = [
            r'\b(urgent|immediate|asap|deadline|due|expires|overdue)\b',
            r'\b(action required|respond by|must)\b'
        ]
        
        # Check for reassuring content
        reassuring_patterns = [
            r'\b(we\'re handling|we\'ll take care|don\'t worry|normal process)\b',
            r'\b(we\'re working|we\'ll keep you informed)\b'
        ]
        
        # Analyze sentiment
        if any(re.search(pattern, combined_text) for pattern in urgent_patterns):
            return SentimentType.URGENT
        elif any(re.search(pattern, combined_text) for pattern in positive_patterns):
            return SentimentType.POSITIVE
        elif any(re.search(pattern, combined_text) for pattern in negative_patterns):
            return SentimentType.NEGATIVE
        elif any(re.search(pattern, combined_text) for pattern in reassuring_patterns):
            return SentimentType.REASSURING
        else:
            return SentimentType.NEUTRAL
    
    async def _personalize_content(
        self,
        notification: Any,
        personality: ClientPersonality,
        sentiment: SentimentType,
        client: ClientUser
    ) -> Dict[str, str]:
        """Create personalized versions of the notification content."""
        
        base_title = notification.translated_title
        base_message = notification.translated_message
        
        personalized_versions = {}
        
        # Adjust for communication style
        if personality.communication_style == "formal":
            title = self._make_formal(base_title)
            message = self._make_formal(base_message)
        elif personality.communication_style == "casual":
            title = self._make_casual(base_title)
            message = self._make_casual(base_message)
        else:  # friendly
            title = base_title
            message = base_message
        
        # Add reassurance for high anxiety clients
        if personality.anxiety_level == "high" and sentiment in [SentimentType.NEGATIVE, SentimentType.URGENT]:
            message = self._add_reassurance(message, sentiment)
        
        # Adjust detail level
        if personality.detail_preference == "minimal":
            message = self._make_concise(message)
        elif personality.detail_preference == "comprehensive":
            message = self._add_details(message, notification)
        
        # Create versions for different channels
        personalized_versions = {
            'portal': {'title': title, 'message': message},
            'email': {'title': f"Legal Update: {title}", 'message': self._format_for_email(message)},
            'sms': {'title': title, 'message': self._format_for_sms(message)},
            'push': {'title': title, 'message': self._format_for_push(message)}
        }
        
        return personalized_versions
    
    async def _calculate_optimal_delivery_time(
        self,
        personality: ClientPersonality,
        priority: NotificationPriority,
        sentiment: SentimentType
    ) -> datetime:
        """Calculate the optimal time to deliver the notification."""
        
        now = datetime.utcnow()
        
        # For urgent notifications, send immediately
        if priority == NotificationPriority.URGENT or sentiment == SentimentType.URGENT:
            return now
        
        # Check quiet hours
        quiet_start = personality.quiet_hours.get('start_time', '22:00')
        quiet_end = personality.quiet_hours.get('end_time', '08:00')
        
        # Convert current time to client's timezone
        # For simplicity, using UTC here - in production, would convert properly
        current_hour = now.hour
        
        quiet_start_hour = int(quiet_start.split(':')[0])
        quiet_end_hour = int(quiet_end.split(':')[0])
        
        # If we're in quiet hours, schedule for end of quiet period
        if self._is_in_quiet_hours(current_hour, quiet_start_hour, quiet_end_hour):
            # Schedule for quiet end time
            next_delivery = now.replace(
                hour=quiet_end_hour, 
                minute=int(quiet_end.split(':')[1]), 
                second=0, 
                microsecond=0
            )
            
            # If that's in the past, schedule for tomorrow
            if next_delivery <= now:
                next_delivery += timedelta(days=1)
            
            return next_delivery
        
        # For negative news, consider if it's better to wait for business hours
        if sentiment == SentimentType.NEGATIVE and (current_hour < 9 or current_hour > 17):
            # Schedule for 9 AM
            next_business = now.replace(hour=9, minute=0, second=0, microsecond=0)
            if next_business <= now:
                next_business += timedelta(days=1)
            return next_business
        
        # Otherwise, send now
        return now
    
    def _is_in_quiet_hours(self, current_hour: int, quiet_start: int, quiet_end: int) -> bool:
        """Check if current time is in quiet hours."""
        if quiet_start < quiet_end:
            return quiet_start <= current_hour < quiet_end
        else:  # Quiet hours span midnight
            return current_hour >= quiet_start or current_hour < quiet_end
    
    def _select_optimal_channels(
        self,
        personality: ClientPersonality,
        priority: NotificationPriority,
        sentiment: SentimentType,
        context: TranslationContext
    ) -> List[DeliveryChannel]:
        """Select optimal delivery channels based on context."""
        
        channels = []
        
        # Always include portal
        channels.append(DeliveryChannel.PORTAL)
        
        # For urgent notifications, use multiple channels
        if priority == NotificationPriority.URGENT or sentiment == SentimentType.URGENT:
            channels.extend([DeliveryChannel.EMAIL, DeliveryChannel.SMS])
            if personality.tech_comfort == "high":
                channels.append(DeliveryChannel.PUSH)
        
        # For negative news, consider phone call for high-anxiety clients
        elif sentiment == SentimentType.NEGATIVE and personality.anxiety_level == "high":
            channels.extend([DeliveryChannel.EMAIL, DeliveryChannel.PHONE_CALL])
        
        # For positive news, use preferred channels
        elif sentiment == SentimentType.POSITIVE:
            channels.extend(personality.preferred_channels[:2])  # Limit to top 2
        
        # Default to email
        else:
            channels.append(DeliveryChannel.EMAIL)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(channels))
    
    def _assess_follow_up_needs(
        self,
        notification: Any,
        personality: ClientPersonality,
        context: TranslationContext
    ) -> bool:
        """Assess if follow-up communication is needed."""
        
        # High anxiety clients often need follow-up
        if personality.anxiety_level == "high":
            return True
        
        # Complex legal matters benefit from follow-up
        if context in [TranslationContext.SETTLEMENT_DISCUSSION, TranslationContext.COURT_FILING]:
            return True
        
        # Action-required notifications need follow-up
        if notification.action_required:
            return True
        
        return False
    
    def _calculate_reassurance_level(
        self,
        sentiment: SentimentType,
        anxiety_level: str,
        context: TranslationContext
    ) -> int:
        """Calculate how much reassurance to include (1-5 scale)."""
        
        base_level = 2  # Default moderate reassurance
        
        # Adjust based on sentiment
        if sentiment == SentimentType.NEGATIVE:
            base_level += 2
        elif sentiment == SentimentType.URGENT:
            base_level += 1
        elif sentiment == SentimentType.REASSURING:
            base_level += 1
        
        # Adjust based on anxiety level
        if anxiety_level == "high":
            base_level += 1
        elif anxiety_level == "low":
            base_level -= 1
        
        # Adjust based on context
        if context in [TranslationContext.COURT_FILING, TranslationContext.LEGAL_PROCEEDING]:
            base_level += 1
        
        return max(1, min(5, base_level))
    
    def _generate_call_to_action(
        self,
        notification: Any,
        personality: ClientPersonality,
        context: TranslationContext
    ) -> Optional[str]:
        """Generate appropriate call to action."""
        
        if not notification.action_required:
            return None
        
        # Base call to action
        if context == TranslationContext.SETTLEMENT_DISCUSSION:
            cta = "Review the settlement details and let us know your decision"
        elif context == TranslationContext.DOCUMENT_SHARING:
            cta = "Please review the new document in your portal"
        elif context == TranslationContext.DEADLINE_REMINDER:
            cta = "Contact us if you have questions about this deadline"
        elif context == TranslationContext.BILLING_INVOICE:
            cta = "View your invoice and make a payment through your portal"
        else:
            cta = "Contact us if you have any questions"
        
        # Personalize based on communication style
        if personality.communication_style == "formal":
            cta = f"Please {cta.lower()}"
        elif personality.communication_style == "casual":
            cta = cta.replace("Please", "").strip()
        
        return cta
    
    async def _create_delivery_plan(
        self,
        enhanced: EnhancedNotification,
        personality: ClientPersonality,
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Create a delivery plan with timing and channels."""
        
        plan = {
            'primary_delivery': {
                'channel': enhanced.recommended_channels[0].value,
                'scheduled_time': enhanced.optimal_delivery_time.isoformat(),
                'content_version': 'portal'
            },
            'follow_up_deliveries': []
        }
        
        # Add follow-up deliveries for multi-channel notifications
        for i, channel in enumerate(enhanced.recommended_channels[1:], 1):
            follow_up_time = enhanced.optimal_delivery_time + timedelta(minutes=15 * i)
            plan['follow_up_deliveries'].append({
                'channel': channel.value,
                'scheduled_time': follow_up_time.isoformat(),
                'content_version': channel.value,
                'condition': 'if_not_read'  # Only send if primary not read
            })
        
        # Add follow-up reminder if needed
        if enhanced.follow_up_needed:
            reminder_time = enhanced.optimal_delivery_time + timedelta(hours=24)
            plan['follow_up_deliveries'].append({
                'channel': 'email',
                'scheduled_time': reminder_time.isoformat(),
                'content_version': 'email',
                'condition': 'if_no_action',
                'message_type': 'reminder'
            })
        
        return plan
    
    async def _create_channel_specific_content(
        self,
        enhanced: EnhancedNotification,
        personality: ClientPersonality,
        delivery_plan: Dict[str, Any]
    ) -> Dict[str, Dict[str, str]]:
        """Create content optimized for each delivery channel."""
        
        return enhanced.personalized_content
    
    def _get_complexity_for_personality(self, personality: ClientPersonality) -> ComplexityLevel:
        """Get appropriate complexity level based on personality."""
        
        if personality.tech_comfort == "low" or personality.anxiety_level == "high":
            return ComplexityLevel.SIMPLE
        elif personality.detail_preference == "comprehensive":
            return ComplexityLevel.DETAILED
        else:
            return ComplexityLevel.MODERATE
    
    # Content modification helpers
    
    def _make_formal(self, text: str) -> str:
        """Make text more formal."""
        text = re.sub(r"\bhi\b", "Dear", text, flags=re.IGNORECASE)
        text = re.sub(r"\bwe're\b", "we are", text, flags=re.IGNORECASE)
        text = re.sub(r"\bdon't\b", "do not", text, flags=re.IGNORECASE)
        text = re.sub(r"\bcan't\b", "cannot", text, flags=re.IGNORECASE)
        return text
    
    def _make_casual(self, text: str) -> str:
        """Make text more casual."""
        text = re.sub(r"\bDear\b", "Hi", text, flags=re.IGNORECASE)
        text = re.sub(r"\bwe are\b", "we're", text, flags=re.IGNORECASE)
        text = re.sub(r"\bdo not\b", "don't", text, flags=re.IGNORECASE)
        text = re.sub(r"\bcannot\b", "can't", text, flags=re.IGNORECASE)
        return text
    
    def _add_reassurance(self, message: str, sentiment: SentimentType) -> str:
        """Add reassuring content to the message."""
        if sentiment == SentimentType.NEGATIVE:
            reassurance = " We understand this may be concerning, and we're here to guide you through every step."
        elif sentiment == SentimentType.URGENT:
            reassurance = " While this requires prompt attention, we're handling everything and will keep you informed."
        else:
            reassurance = " We're monitoring this closely and will update you with any developments."
        
        return message + reassurance
    
    def _make_concise(self, message: str) -> str:
        """Make message more concise."""
        # Remove unnecessary phrases
        concise = re.sub(r'\s+', ' ', message)  # Remove extra whitespace
        concise = re.sub(r'\b(please note that|it should be noted that|we would like to inform you that)\s*', '', concise, flags=re.IGNORECASE)
        
        # Keep only the most essential information
        sentences = concise.split('. ')
        if len(sentences) > 2:
            return '. '.join(sentences[:2]) + '.'
        
        return concise
    
    def _add_details(self, message: str, notification: Any) -> str:
        """Add more details to the message."""
        details = ""
        
        if hasattr(notification, 'next_steps') and notification.next_steps:
            details += f" Next steps: {'; '.join(notification.next_steps[:3])}."
        
        if hasattr(notification, 'explanation') and notification.explanation:
            details += f" Background: {notification.explanation}"
        
        return message + details
    
    def _format_for_email(self, message: str) -> str:
        """Format message for email delivery."""
        return f"""
        {message}
        
        You can view more details and take action by logging into your client portal.
        
        If you have any questions, please don't hesitate to contact us.
        
        Best regards,
        Your Legal Team
        """
    
    def _format_for_sms(self, message: str) -> str:
        """Format message for SMS delivery."""
        # Keep SMS under 160 characters
        if len(message) <= 140:  # Leave room for link
            return f"{message} View details: [portal link]"
        else:
            # Truncate and add link
            truncated = message[:120] + "..."
            return f"{truncated} Details: [portal link]"
    
    def _format_for_push(self, message: str) -> str:
        """Format message for push notification."""
        # Keep push notifications brief
        if len(message) <= 100:
            return message
        else:
            return message[:97] + "..."
    
    def _load_personality_indicators(self) -> Dict[str, List[str]]:
        """Load patterns that indicate personality traits."""
        return {
            'formal_indicators': ['corporate', 'business', 'professional', 'company'],
            'casual_indicators': ['personal', 'individual', 'family', 'informal'],
            'high_detail_indicators': ['comprehensive', 'detailed', 'thorough', 'complete'],
            'low_detail_indicators': ['brief', 'summary', 'quick', 'concise'],
            'high_anxiety_indicators': ['worried', 'concerned', 'anxious', 'nervous'],
            'tech_comfort_indicators': ['app', 'online', 'digital', 'portal']
        }
    
    def _load_sentiment_patterns(self) -> Dict[SentimentType, List[str]]:
        """Load patterns for sentiment detection."""
        return {
            SentimentType.POSITIVE: [
                r'\b(good news|great news|successful|approved|settled|resolved|won)\b',
                r'\b(completed|accomplished|achieved|progress)\b'
            ],
            SentimentType.NEGATIVE: [
                r'\b(denied|rejected|dismissed|failed|lost|problem|issue)\b',
                r'\b(unfortunately|regretfully|concern|difficulty)\b'
            ],
            SentimentType.URGENT: [
                r'\b(urgent|immediate|asap|deadline|expires|due|overdue)\b',
                r'\b(action required|must respond|time sensitive)\b'
            ],
            SentimentType.REASSURING: [
                r'\b(normal process|routine|standard procedure|don\'t worry)\b',
                r'\b(we\'re handling|taking care|monitoring|working on)\b'
            ]
        }
    
    def _load_timing_optimization_rules(self) -> Dict[str, Any]:
        """Load rules for optimizing notification timing."""
        return {
            'business_hours': {'start': 9, 'end': 17},
            'urgent_override': True,
            'weekend_delay': {
                'non_urgent': True,
                'delay_until': 'monday_9am'
            },
            'quiet_hours_default': {'start': '22:00', 'end': '08:00'},
            'negative_news_timing': {
                'avoid_fridays': True,
                'prefer_morning': True
            }
        }