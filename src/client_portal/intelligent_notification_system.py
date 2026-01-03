"""
Intelligent Notification System with Plain English Translations

Converts complex legal terminology and system events into clear, 
understandable language for client communications. Uses AI-powered
translation and contextual understanding to make legal processes accessible.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from sqlalchemy.orm import Session

from .models import (
    NotificationType, NotificationPriority, ClientUser, ClientCase,
    ClientDocument, ClientMessage, ClientAppointment, ClientInvoice
)
from .notification_manager import NotificationManager


class ComplexityLevel(Enum):
    SIMPLE = "simple"          # 5th grade reading level
    MODERATE = "moderate"      # 8th grade reading level  
    DETAILED = "detailed"      # 12th grade reading level
    TECHNICAL = "technical"    # Professional/legal level

class TranslationContext(Enum):
    CASE_UPDATE = "case_update"
    DOCUMENT_SHARING = "document_sharing"
    COURT_FILING = "court_filing"
    DEADLINE_REMINDER = "deadline_reminder"
    BILLING_INVOICE = "billing_invoice"
    APPOINTMENT_SCHEDULING = "appointment_scheduling"
    LEGAL_PROCEEDING = "legal_proceeding"
    SETTLEMENT_DISCUSSION = "settlement_discussion"
    DISCOVERY_PROCESS = "discovery_process"
    MOTION_FILING = "motion_filing"

@dataclass
class TranslationRule:
    """Rule for translating legal/technical terms to plain English."""
    pattern: str
    replacement: str
    context: Optional[TranslationContext]
    complexity_level: ComplexityLevel
    explanation: Optional[str] = None

@dataclass
class NotificationTemplate:
    """Template for generating notifications in plain English."""
    event_type: str
    title_template: str
    message_template: str
    urgency_indicators: List[str]
    action_verbs: List[str]
    context_variables: List[str]

@dataclass
class IntelligentNotification:
    """Enhanced notification with plain English translation."""
    original_title: str
    original_message: str
    translated_title: str
    translated_message: str
    complexity_level: ComplexityLevel
    context: TranslationContext
    urgency_score: int  # 1-10 scale
    action_required: bool
    next_steps: List[str]
    explanation: Optional[str] = None
    related_links: List[Dict[str, str]] = None


class IntelligentNotificationSystem:
    """Intelligent system for creating user-friendly notifications."""
    
    def __init__(self, db_session: Session, notification_manager: NotificationManager):
        self.db = db_session
        self.notification_manager = notification_manager
        
        # Initialize translation rules and templates
        self.translation_rules = self._load_translation_rules()
        self.notification_templates = self._load_notification_templates()
        self.legal_glossary = self._load_legal_glossary()
        
        # User preference defaults
        self.default_complexity_level = ComplexityLevel.MODERATE
        
    async def create_intelligent_notification(
        self,
        client_id: int,
        event_type: str,
        original_data: Dict[str, Any],
        context: TranslationContext,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        complexity_override: Optional[ComplexityLevel] = None
    ) -> Dict[str, Any]:
        """Create an intelligent notification with plain English translation."""
        try:
            # Get client preferences
            client = self.db.query(ClientUser).filter(ClientUser.id == client_id).first()
            if not client:
                return {'success': False, 'error': 'Client not found'}
            
            # Determine complexity level
            complexity_level = complexity_override or self._get_client_complexity_preference(client)
            
            # Generate notification content
            notification = await self._generate_notification(
                event_type=event_type,
                data=original_data,
                context=context,
                complexity_level=complexity_level,
                client=client
            )
            
            # Calculate urgency and determine actions
            notification.urgency_score = self._calculate_urgency_score(
                event_type, original_data, priority
            )
            
            notification.action_required = self._requires_client_action(
                event_type, original_data
            )
            
            notification.next_steps = self._generate_next_steps(
                event_type, original_data, context, complexity_level
            )
            
            # Create the actual notification
            result = await self.notification_manager.create_notification(
                client_id=client_id,
                notification_type=self._map_event_to_notification_type(event_type),
                title=notification.translated_title,
                message=notification.translated_message,
                priority=priority,
                action_data={
                    'original_title': notification.original_title,
                    'original_message': notification.original_message,
                    'complexity_level': complexity_level.value,
                    'context': context.value,
                    'urgency_score': notification.urgency_score,
                    'action_required': notification.action_required,
                    'next_steps': notification.next_steps,
                    'explanation': notification.explanation,
                    'related_links': notification.related_links or []
                }
            )
            
            return {
                'success': True,
                'notification_id': result.get('notification_id'),
                'intelligent_notification': notification,
                'urgency_score': notification.urgency_score,
                'action_required': notification.action_required
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to create intelligent notification: {str(e)}'}
    
    async def translate_legal_document_event(
        self,
        client_id: int,
        document_title: str,
        document_type: str,
        action: str,
        case_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Translate document-related events into plain English."""
        
        # Determine document context and importance
        is_court_filing = 'filing' in document_type.lower() or 'motion' in document_type.lower()
        is_evidence = 'evidence' in document_type.lower() or 'exhibit' in document_type.lower()
        is_contract = 'contract' in document_type.lower() or 'agreement' in document_type.lower()
        
        # Generate context-aware translation
        if action == 'uploaded':
            if is_court_filing:
                translated_title = "New Court Document Added"
                translated_message = f"We've added a new court document to your case: {self._simplify_document_title(document_title)}. This document was filed with the court on your behalf."
                context = TranslationContext.COURT_FILING
                
            elif is_evidence:
                translated_title = "New Evidence Added to Your Case"
                translated_message = f"We've added new evidence to support your case: {self._simplify_document_title(document_title)}. This helps strengthen your position."
                context = TranslationContext.CASE_UPDATE
                
            elif is_contract:
                translated_title = "Contract Document Added"
                translated_message = f"We've added a contract document: {self._simplify_document_title(document_title)}. Please review this when convenient."
                context = TranslationContext.DOCUMENT_SHARING
                
            else:
                translated_title = "New Document Added to Your Case"
                translated_message = f"We've added a new document to your file: {self._simplify_document_title(document_title)}."
                context = TranslationContext.DOCUMENT_SHARING
        
        elif action == 'shared':
            translated_title = "Document Shared with You"
            translated_message = f"We've shared an important document with you: {self._simplify_document_title(document_title)}. You can view and download it from your portal."
            context = TranslationContext.DOCUMENT_SHARING
        
        else:
            translated_title = f"Document {action.title()}"
            translated_message = f"Action taken on document: {self._simplify_document_title(document_title)}"
            context = TranslationContext.DOCUMENT_SHARING
        
        return await self.create_intelligent_notification(
            client_id=client_id,
            event_type='document_event',
            original_data={
                'document_title': document_title,
                'document_type': document_type,
                'action': action,
                'case_context': case_context
            },
            context=context
        )
    
    async def translate_case_status_change(
        self,
        client_id: int,
        case_title: str,
        old_status: str,
        new_status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Translate case status changes into understandable updates."""
        
        status_translations = {
            'discovery': 'gathering information and evidence',
            'motion_filed': 'requesting the court to make a decision',
            'settlement_negotiation': 'working to reach an agreement without going to trial',
            'trial_preparation': 'getting ready for your court date',
            'pending_ruling': 'waiting for the judge\'s decision',
            'closed_settled': 'successfully resolved through agreement',
            'closed_dismissed': 'case has been dismissed',
            'appeal_filed': 'challenging the court\'s decision'
        }
        
        old_status_plain = status_translations.get(old_status.lower(), old_status.replace('_', ' '))
        new_status_plain = status_translations.get(new_status.lower(), new_status.replace('_', ' '))
        
        # Generate contextual message based on status change
        if 'settlement' in new_status.lower():
            title = "Great News About Your Case!"
            message = f"Your case '{self._simplify_case_title(case_title)}' has moved to settlement discussions. This means we're working to resolve your case through negotiation rather than going to trial, which could save you time and money."
            priority = NotificationPriority.HIGH
            
        elif 'trial' in new_status.lower():
            title = "Your Case is Moving to Trial"
            message = f"Your case '{self._simplify_case_title(case_title)}' is now in trial preparation. We're getting everything ready for your day in court. We'll keep you informed of all important dates and what you need to do."
            priority = NotificationPriority.HIGH
            
        elif 'closed' in new_status.lower():
            title = "Case Update: Resolution Reached"
            if 'settled' in new_status.lower():
                message = f"Good news! Your case '{self._simplify_case_title(case_title)}' has been successfully resolved through settlement. We'll send you the details shortly."
            else:
                message = f"Your case '{self._simplify_case_title(case_title)}' has been completed. We'll provide you with a summary of the outcome."
            priority = NotificationPriority.HIGH
            
        elif 'motion' in new_status.lower():
            title = "Court Action Taken on Your Case"
            message = f"We've filed a motion (formal request) with the court for your case '{self._simplify_case_title(case_title)}'. This is a normal part of the legal process, and we're working to get the best outcome for you."
            priority = NotificationPriority.MEDIUM
            
        else:
            title = f"Update on Your Case: {new_status_plain.title()}"
            message = f"Your case '{self._simplify_case_title(case_title)}' status has changed from '{old_status_plain}' to '{new_status_plain}'. We'll keep you updated on any actions needed from you."
            priority = NotificationPriority.MEDIUM
        
        return await self.create_intelligent_notification(
            client_id=client_id,
            event_type='case_status_change',
            original_data={
                'case_title': case_title,
                'old_status': old_status,
                'new_status': new_status,
                'details': details
            },
            context=TranslationContext.CASE_UPDATE
        )
    
    async def translate_court_deadline(
        self,
        client_id: int,
        deadline_type: str,
        deadline_date: datetime,
        case_title: str,
        requirements: List[str] = None
    ) -> Dict[str, Any]:
        """Translate court deadlines into actionable notifications."""
        
        days_until = (deadline_date - datetime.utcnow()).days
        
        # Determine urgency based on time remaining
        if days_until <= 1:
            urgency = "URGENT - Due tomorrow or today!"
            priority = NotificationPriority.URGENT
        elif days_until <= 3:
            urgency = "Important - Due very soon"
            priority = NotificationPriority.HIGH
        elif days_until <= 7:
            urgency = "Due next week"
            priority = NotificationPriority.MEDIUM
        else:
            urgency = f"Due in {days_until} days"
            priority = NotificationPriority.MEDIUM
        
        # Translate deadline types
        deadline_translations = {
            'discovery_deadline': 'deadline to submit evidence and information',
            'motion_deadline': 'deadline to file court requests',
            'response_deadline': 'deadline to respond to court documents',
            'filing_deadline': 'deadline to file required documents',
            'settlement_conference': 'settlement discussion meeting',
            'trial_date': 'your court trial date',
            'deposition': 'sworn testimony session',
            'mediation': 'mediation meeting to resolve the case'
        }
        
        deadline_plain = deadline_translations.get(deadline_type.lower(), deadline_type.replace('_', ' '))
        
        title = f"{urgency}: {deadline_plain.title()}"
        
        message = f"You have an important {deadline_plain} for your case '{self._simplify_case_title(case_title)}' on {deadline_date.strftime('%B %d, %Y')}."
        
        if requirements:
            req_plain = self._translate_requirements(requirements)
            message += f" Here's what needs to be done: {', '.join(req_plain)}."
        
        message += " We'll handle the legal requirements and let you know if you need to take any action."
        
        return await self.create_intelligent_notification(
            client_id=client_id,
            event_type='court_deadline',
            original_data={
                'deadline_type': deadline_type,
                'deadline_date': deadline_date.isoformat(),
                'case_title': case_title,
                'requirements': requirements or [],
                'days_until': days_until
            },
            context=TranslationContext.DEADLINE_REMINDER,
            priority=priority
        )
    
    async def translate_billing_event(
        self,
        client_id: int,
        event_type: str,
        amount: float,
        description: str,
        invoice_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Translate billing events into clear financial communications."""
        
        if event_type == 'invoice_generated':
            title = f"New Bill Available - ${amount:,.2f}"
            message = f"We've prepared your latest bill for ${amount:,.2f}. This covers the legal work we've done on your case recently. You can view the detailed breakdown and pay online through your portal."
            
        elif event_type == 'payment_received':
            title = "Payment Received - Thank You!"
            message = f"We've received your payment of ${amount:,.2f}. Thank you! Your account has been updated and you should see the payment reflected in your portal shortly."
            
        elif event_type == 'payment_overdue':
            title = f"Payment Reminder - ${amount:,.2f}"
            message = f"This is a friendly reminder that your payment of ${amount:,.2f} is now overdue. Please make your payment as soon as possible to avoid any service interruptions. You can pay securely through your portal."
            
        elif event_type == 'payment_plan_available':
            title = "Payment Plan Available"
            message = f"We understand that the ${amount:,.2f} balance might be challenging to pay all at once. We've set up payment plan options for you. Please contact us to discuss what works best for your situation."
            
        else:
            title = f"Billing Update - ${amount:,.2f}"
            message = f"There's been an update to your account balance: ${amount:,.2f}. {description}"
        
        return await self.create_intelligent_notification(
            client_id=client_id,
            event_type=event_type,
            original_data={
                'amount': amount,
                'description': description,
                'invoice_data': invoice_data
            },
            context=TranslationContext.BILLING_INVOICE
        )
    
    async def translate_settlement_offer(
        self,
        client_id: int,
        offer_amount: float,
        deadline: datetime,
        case_title: str,
        our_recommendation: str
    ) -> Dict[str, Any]:
        """Translate settlement offers into understandable terms."""
        
        days_to_respond = (deadline - datetime.utcnow()).days
        
        title = f"Settlement Offer Received - ${offer_amount:,.2f}"
        
        message = f"The other side has offered to settle your case '{self._simplify_case_title(case_title)}' for ${offer_amount:,.2f}. "
        
        if our_recommendation.lower() in ['accept', 'recommended']:
            message += "We recommend accepting this offer as it's fair and avoids the uncertainty of trial. "
        elif our_recommendation.lower() in ['reject', 'too_low']:
            message += "We believe this offer is too low and recommend negotiating for a better amount. "
        else:
            message += "We're reviewing this offer carefully and will provide our recommendation soon. "
        
        message += f"You have {days_to_respond} days to decide. We'll discuss all your options and help you make the best decision."
        
        return await self.create_intelligent_notification(
            client_id=client_id,
            event_type='settlement_offer',
            original_data={
                'offer_amount': offer_amount,
                'deadline': deadline.isoformat(),
                'case_title': case_title,
                'recommendation': our_recommendation,
                'days_to_respond': days_to_respond
            },
            context=TranslationContext.SETTLEMENT_DISCUSSION,
            priority=NotificationPriority.HIGH
        )
    
    def _get_client_complexity_preference(self, client: ClientUser) -> ComplexityLevel:
        """Get client's preferred complexity level for notifications."""
        prefs = client.notification_preferences or {}
        complexity = prefs.get('language_complexity', 'moderate')
        
        try:
            return ComplexityLevel(complexity)
        except ValueError:
            return self.default_complexity_level
    
    async def _generate_notification(
        self,
        event_type: str,
        data: Dict[str, Any],
        context: TranslationContext,
        complexity_level: ComplexityLevel,
        client: ClientUser
    ) -> IntelligentNotification:
        """Generate an intelligent notification with appropriate complexity."""
        
        # Get base template
        template = self.notification_templates.get(event_type)
        if not template:
            template = self._create_default_template(event_type)
        
        # Apply translation rules based on complexity level
        original_title = template.title_template.format(**data)
        original_message = template.message_template.format(**data)
        
        translated_title = self._apply_translations(
            original_title, context, complexity_level
        )
        translated_message = self._apply_translations(
            original_message, context, complexity_level
        )
        
        # Add personal touch
        if complexity_level in [ComplexityLevel.SIMPLE, ComplexityLevel.MODERATE]:
            translated_title = f"Hi {client.first_name}, {translated_title}"
        
        # Generate explanation if needed
        explanation = None
        if complexity_level == ComplexityLevel.SIMPLE:
            explanation = self._generate_simple_explanation(context, data)
        
        return IntelligentNotification(
            original_title=original_title,
            original_message=original_message,
            translated_title=translated_title,
            translated_message=translated_message,
            complexity_level=complexity_level,
            context=context,
            urgency_score=0,  # Will be calculated later
            action_required=False,  # Will be determined later
            next_steps=[],  # Will be generated later
            explanation=explanation
        )
    
    def _apply_translations(
        self,
        text: str,
        context: TranslationContext,
        complexity_level: ComplexityLevel
    ) -> str:
        """Apply translation rules to convert technical language to plain English."""
        
        translated_text = text
        
        # Apply context-specific and complexity-appropriate rules
        applicable_rules = [
            rule for rule in self.translation_rules
            if (rule.context is None or rule.context == context) and
               self._is_complexity_appropriate(rule.complexity_level, complexity_level)
        ]
        
        # Sort by specificity (more specific patterns first)
        applicable_rules.sort(key=lambda r: -len(r.pattern))
        
        for rule in applicable_rules:
            translated_text = re.sub(rule.pattern, rule.replacement, translated_text, flags=re.IGNORECASE)
        
        # Apply general simplifications based on complexity level
        if complexity_level == ComplexityLevel.SIMPLE:
            translated_text = self._simplify_for_grade_5(translated_text)
        elif complexity_level == ComplexityLevel.MODERATE:
            translated_text = self._simplify_for_grade_8(translated_text)
        
        return translated_text
    
    def _simplify_for_grade_5(self, text: str) -> str:
        """Simplify text for 5th grade reading level."""
        # Replace complex words with simpler alternatives
        simple_replacements = {
            r'\bassist\b': 'help',
            r'\bcommence\b': 'start',
            r'\bterminate\b': 'end',
            r'\bsubsequent\b': 'next',
            r'\bprevious\b': 'last',
            r'\butilize\b': 'use',
            r'\bobtain\b': 'get',
            r'\bpurchase\b': 'buy',
            r'\badditional\b': 'more',
            r'\brequire\b': 'need',
            r'\bprovide\b': 'give',
            r'\breceive\b': 'get'
        }
        
        result = text
        for pattern, replacement in simple_replacements.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        # Break long sentences
        sentences = result.split('. ')
        simplified_sentences = []
        
        for sentence in sentences:
            if len(sentence.split()) > 15:  # Long sentence
                # Try to break at conjunctions
                parts = re.split(r'\b(and|but|or|because|since|when|while|if)\b', sentence)
                if len(parts) > 1:
                    simplified_sentences.extend([part.strip() for part in parts if part.strip()])
                else:
                    simplified_sentences.append(sentence)
            else:
                simplified_sentences.append(sentence)
        
        return '. '.join(simplified_sentences)
    
    def _simplify_for_grade_8(self, text: str) -> str:
        """Simplify text for 8th grade reading level."""
        # Moderate simplification - keep some complexity but explain jargon
        moderate_replacements = {
            r'\blitigate\b': 'take to court',
            r'\bnegotiate\b': 'discuss and work out terms',
            r'\bmediation\b': 'meeting with a neutral person to help resolve the case',
            r'\barbitration\b': 'private court hearing with a neutral decision-maker',
            r'\bdeposition\b': 'sworn testimony given outside of court',
            r'\bdiscovery\b': 'process of gathering information and evidence',
            r'\bmotion\b': 'formal request to the court',
            r'\bpleading\b': 'legal document filed with the court'
        }
        
        result = text
        for pattern, replacement in moderate_replacements.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result
    
    def _is_complexity_appropriate(
        self,
        rule_complexity: ComplexityLevel,
        target_complexity: ComplexityLevel
    ) -> bool:
        """Check if a translation rule is appropriate for the target complexity level."""
        complexity_order = [
            ComplexityLevel.SIMPLE,
            ComplexityLevel.MODERATE, 
            ComplexityLevel.DETAILED,
            ComplexityLevel.TECHNICAL
        ]
        
        return complexity_order.index(rule_complexity) <= complexity_order.index(target_complexity)
    
    def _calculate_urgency_score(
        self,
        event_type: str,
        data: Dict[str, Any],
        priority: NotificationPriority
    ) -> int:
        """Calculate urgency score from 1-10."""
        base_score = {
            NotificationPriority.LOW: 2,
            NotificationPriority.MEDIUM: 5,
            NotificationPriority.HIGH: 7,
            NotificationPriority.URGENT: 9
        }.get(priority, 5)
        
        # Adjust based on event type
        urgency_modifiers = {
            'settlement_offer': 2,
            'court_deadline': 3,
            'trial_date': 3,
            'payment_overdue': 1,
            'case_status_change': 1,
            'document_event': 0
        }
        
        modifier = urgency_modifiers.get(event_type, 0)
        
        # Adjust based on time sensitivity
        if 'deadline' in data:
            try:
                deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
                days_until = (deadline - datetime.utcnow()).days
                if days_until <= 1:
                    modifier += 2
                elif days_until <= 3:
                    modifier += 1
            except (ValueError, KeyError):
                pass
        
        return min(10, max(1, base_score + modifier))
    
    def _requires_client_action(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Determine if the notification requires client action."""
        action_required_events = {
            'settlement_offer',
            'document_signature_required', 
            'deposition_scheduled',
            'payment_overdue',
            'information_request'
        }
        
        return event_type in action_required_events
    
    def _generate_next_steps(
        self,
        event_type: str,
        data: Dict[str, Any],
        context: TranslationContext,
        complexity_level: ComplexityLevel
    ) -> List[str]:
        """Generate actionable next steps for the client."""
        
        steps = []
        
        if event_type == 'settlement_offer':
            steps = [
                "Review the settlement offer details in your portal",
                "Consider the pros and cons we've outlined for you", 
                "Schedule a call with us to discuss your decision",
                "Let us know your decision before the deadline"
            ]
        
        elif event_type == 'court_deadline':
            steps = [
                "We'll handle all the legal requirements for you",
                "Watch for any follow-up communications from us",
                "Contact us if you have questions about this deadline"
            ]
        
        elif event_type == 'document_event':
            steps = [
                "Log into your portal to view the new document",
                "Read through the document carefully",
                "Contact us if you have any questions",
                "Keep this document in a safe place"
            ]
        
        elif event_type == 'payment_overdue':
            steps = [
                "Log into your portal to make a payment",
                "Contact us if you need to set up a payment plan",
                "Call us if there are any issues with the bill"
            ]
        
        # Simplify steps based on complexity level
        if complexity_level == ComplexityLevel.SIMPLE:
            steps = [step.replace('portal', 'your online account') for step in steps]
            steps = [re.sub(r'\bcontact us\b', 'call us', step) for step in steps]
        
        return steps
    
    def _simplify_document_title(self, title: str) -> str:
        """Simplify document titles for better understanding."""
        # Remove common legal prefixes and suffixes
        simplified = re.sub(r'^(MOTION|BRIEF|PLEADING|COMPLAINT|ANSWER|REPLY)\s+(FOR|TO|IN)\s+', '', title, flags=re.IGNORECASE)
        simplified = re.sub(r'\s+(BRIEF|PLEADING|MOTION|FILING)$', '', simplified, flags=re.IGNORECASE)
        
        # Replace legal terms
        replacements = {
            'SUMMARY JUDGMENT': 'request to win without trial',
            'DISCOVERY': 'information gathering',
            'INTERROGATORIES': 'written questions',
            'DEPOSITION': 'sworn testimony',
            'SUBPOENA': 'court order to provide information'
        }
        
        for legal_term, plain_term in replacements.items():
            simplified = re.sub(legal_term, plain_term, simplified, flags=re.IGNORECASE)
        
        return simplified.title()
    
    def _simplify_case_title(self, title: str) -> str:
        """Simplify case titles for better readability."""
        # Remove case numbers and legal formatting
        simplified = re.sub(r'\s+v\.\s+', ' vs. ', title)
        simplified = re.sub(r'\s+Case\s+No\..*$', '', simplified, flags=re.IGNORECASE)
        simplified = re.sub(r'^\d+[-\s]*', '', simplified)  # Remove leading numbers
        
        return simplified.strip()
    
    def _translate_requirements(self, requirements: List[str]) -> List[str]:
        """Translate legal requirements into plain English."""
        translated = []
        
        for req in requirements:
            # Apply basic translations
            plain_req = req.lower()
            plain_req = plain_req.replace('submit', 'provide')
            plain_req = plain_req.replace('execute', 'sign')
            plain_req = plain_req.replace('remit', 'send')
            plain_req = plain_req.replace('comply with', 'follow')
            
            translated.append(plain_req)
        
        return translated
    
    def _generate_simple_explanation(
        self,
        context: TranslationContext,
        data: Dict[str, Any]
    ) -> str:
        """Generate simple explanations for complex legal concepts."""
        
        explanations = {
            TranslationContext.COURT_FILING: "This means we've sent official papers to the court on your behalf. This is a normal part of the legal process.",
            
            TranslationContext.SETTLEMENT_DISCUSSION: "A settlement means both sides agree to end the case without going to trial. This can save time and money.",
            
            TranslationContext.DISCOVERY_PROCESS: "Discovery is when both sides share information and evidence. It helps everyone understand what happened.",
            
            TranslationContext.DEADLINE_REMINDER: "Court deadlines are dates when certain things must be done. Missing deadlines can hurt your case.",
            
            TranslationContext.LEGAL_PROCEEDING: "Legal proceedings are the formal steps in your case. Each step moves your case closer to resolution."
        }
        
        return explanations.get(context, "This is part of the normal legal process for your case.")
    
    def _map_event_to_notification_type(self, event_type: str) -> NotificationType:
        """Map event types to notification types."""
        mapping = {
            'case_status_change': NotificationType.CASE_UPDATE,
            'document_event': NotificationType.DOCUMENT_SHARED,
            'court_deadline': NotificationType.DEADLINE_REMINDER,
            'settlement_offer': NotificationType.CASE_UPDATE,
            'invoice_generated': NotificationType.INVOICE_GENERATED,
            'payment_overdue': NotificationType.INVOICE_GENERATED,
            'appointment_scheduled': NotificationType.APPOINTMENT_SCHEDULED
        }
        
        return mapping.get(event_type, NotificationType.SYSTEM_ALERT)
    
    def _load_translation_rules(self) -> List[TranslationRule]:
        """Load translation rules for converting legal language."""
        return [
            # Court and Legal Process Terms
            TranslationRule(
                pattern=r'\bmotion for summary judgment\b',
                replacement='request for the judge to decide without a trial',
                context=TranslationContext.COURT_FILING,
                complexity_level=ComplexityLevel.SIMPLE
            ),
            TranslationRule(
                pattern=r'\bdeposition\b',
                replacement='sworn testimony session',
                context=TranslationContext.DISCOVERY_PROCESS,
                complexity_level=ComplexityLevel.MODERATE
            ),
            TranslationRule(
                pattern=r'\binterrogatories\b',
                replacement='written questions that must be answered under oath',
                context=TranslationContext.DISCOVERY_PROCESS,
                complexity_level=ComplexityLevel.SIMPLE
            ),
            TranslationRule(
                pattern=r'\bsubpoena\b',
                replacement='court order requiring someone to provide information or appear in court',
                context=None,
                complexity_level=ComplexityLevel.MODERATE
            ),
            TranslationRule(
                pattern=r'\bmediation\b',
                replacement='meeting with a neutral person to help resolve the dispute',
                context=TranslationContext.SETTLEMENT_DISCUSSION,
                complexity_level=ComplexityLevel.SIMPLE
            ),
            TranslationRule(
                pattern=r'\barbitration\b',
                replacement='private hearing where a neutral person makes the final decision',
                context=TranslationContext.LEGAL_PROCEEDING,
                complexity_level=ComplexityLevel.MODERATE
            ),
            
            # Financial and Billing Terms  
            TranslationRule(
                pattern=r'\bretainer\b',
                replacement='upfront payment for legal services',
                context=TranslationContext.BILLING_INVOICE,
                complexity_level=ComplexityLevel.SIMPLE
            ),
            TranslationRule(
                pattern=r'\bbillable hours\b',
                replacement='time spent working on your case',
                context=TranslationContext.BILLING_INVOICE,
                complexity_level=ComplexityLevel.SIMPLE
            ),
            TranslationRule(
                pattern=r'\bcontingency fee\b',
                replacement='payment only if we win your case',
                context=TranslationContext.BILLING_INVOICE,
                complexity_level=ComplexityLevel.MODERATE
            ),
            
            # Case Status Terms
            TranslationRule(
                pattern=r'\bdiscovery phase\b',
                replacement='information and evidence gathering stage',
                context=TranslationContext.CASE_UPDATE,
                complexity_level=ComplexityLevel.SIMPLE
            ),
            TranslationRule(
                pattern=r'\bpre-trial\b',
                replacement='preparation before the court hearing',
                context=TranslationContext.CASE_UPDATE,
                complexity_level=ComplexityLevel.SIMPLE
            ),
            TranslationRule(
                pattern=r'\bstatute of limitations\b',
                replacement='time limit for filing your case',
                context=TranslationContext.DEADLINE_REMINDER,
                complexity_level=ComplexityLevel.MODERATE
            ),
            
            # Document Types
            TranslationRule(
                pattern=r'\bpleading\b',
                replacement='formal court document',
                context=TranslationContext.COURT_FILING,
                complexity_level=ComplexityLevel.SIMPLE
            ),
            TranslationRule(
                pattern=r'\bbrief\b',
                replacement='legal argument document',
                context=TranslationContext.COURT_FILING,
                complexity_level=ComplexityLevel.MODERATE
            ),
            TranslationRule(
                pattern=r'\baffidavit\b',
                replacement='sworn written statement',
                context=TranslationContext.DOCUMENT_SHARING,
                complexity_level=ComplexityLevel.MODERATE
            ),
            
            # General Legal Terms
            TranslationRule(
                pattern=r'\bplaintiff\b',
                replacement='the person who filed the lawsuit (you)',
                context=None,
                complexity_level=ComplexityLevel.SIMPLE
            ),
            TranslationRule(
                pattern=r'\bdefendant\b',
                replacement='the person or company being sued',
                context=None,
                complexity_level=ComplexityLevel.SIMPLE
            ),
            TranslationRule(
                pattern=r'\bliable\b',
                replacement='legally responsible',
                context=None,
                complexity_level=ComplexityLevel.SIMPLE
            ),
            TranslationRule(
                pattern=r'\bdamages\b',
                replacement='money to compensate for losses',
                context=None,
                complexity_level=ComplexityLevel.SIMPLE
            ),
            TranslationRule(
                pattern=r'\bsettlement\b',
                replacement='agreement to resolve the case without trial',
                context=TranslationContext.SETTLEMENT_DISCUSSION,
                complexity_level=ComplexityLevel.SIMPLE
            )
        ]
    
    def _load_notification_templates(self) -> Dict[str, NotificationTemplate]:
        """Load templates for different notification types."""
        return {
            'case_status_change': NotificationTemplate(
                event_type='case_status_change',
                title_template='Case Status Update: {case_title}',
                message_template='Your case status has changed from {old_status} to {new_status}.',
                urgency_indicators=['urgent', 'immediate', 'asap'],
                action_verbs=['review', 'respond', 'contact'],
                context_variables=['case_title', 'old_status', 'new_status', 'details']
            ),
            
            'document_event': NotificationTemplate(
                event_type='document_event',
                title_template='Document {action}: {document_title}',
                message_template='A document has been {action} for your case: {document_title}',
                urgency_indicators=['signature required', 'review needed'],
                action_verbs=['review', 'sign', 'download'],
                context_variables=['document_title', 'action', 'document_type']
            ),
            
            'settlement_offer': NotificationTemplate(
                event_type='settlement_offer',
                title_template='Settlement Offer Received: ${offer_amount}',
                message_template='We have received a settlement offer of ${offer_amount} for your case.',
                urgency_indicators=['response required', 'deadline'],
                action_verbs=['consider', 'discuss', 'decide'],
                context_variables=['offer_amount', 'deadline', 'recommendation']
            ),
            
            'court_deadline': NotificationTemplate(
                event_type='court_deadline',
                title_template='{deadline_type} Deadline: {deadline_date}',
                message_template='You have a {deadline_type} deadline on {deadline_date}.',
                urgency_indicators=['due soon', 'urgent', 'immediate'],
                action_verbs=['prepare', 'submit', 'comply'],
                context_variables=['deadline_type', 'deadline_date', 'requirements']
            )
        }
    
    def _load_legal_glossary(self) -> Dict[str, str]:
        """Load comprehensive legal glossary for translations."""
        return {
            'ad litem': 'for the purpose of the lawsuit',
            'affirmative defense': 'reason why the other side should not win',
            'allegation': 'claim or accusation',
            'amicus curiae': 'friend of the court (outside party providing information)',
            'appellant': 'party appealing a court decision',
            'appellee': 'party responding to an appeal',
            'burden of proof': 'requirement to prove your case',
            'cause of action': 'legal reason for the lawsuit',
            'class action': 'lawsuit on behalf of a group of people',
            'complaint': 'document that starts a lawsuit',
            'counterclaim': 'claim made by the defendant against the plaintiff',
            'cross-examination': 'questioning by the opposing lawyer',
            'default judgment': 'ruling when one party does not respond',
            'demurrer': 'challenge to the legal sufficiency of a claim',
            'due process': 'fair treatment under the law',
            'ex parte': 'communication with only one side present',
            'hearsay': 'statement made outside of court offered as evidence',
            'injunction': 'court order requiring or prohibiting an action',
            'jurisdiction': 'court\'s authority to hear a case',
            'lien': 'legal claim against property',
            'negligence': 'failure to exercise reasonable care',
            'prima facie': 'evidence sufficient to establish a fact',
            'pro se': 'representing yourself without a lawyer',
            'service of process': 'formal delivery of court documents',
            'standing': 'legal right to bring a lawsuit',
            'venue': 'proper location for the court case',
            'voir dire': 'jury selection process'
        }
    
    def _create_default_template(self, event_type: str) -> NotificationTemplate:
        """Create a default template for unknown event types."""
        return NotificationTemplate(
            event_type=event_type,
            title_template=f'{event_type.replace("_", " ").title()} Update',
            message_template='There has been an update regarding your case.',
            urgency_indicators=[],
            action_verbs=[],
            context_variables=[]
        )