"""
Comprehensive Help and Support System
Provides self-service knowledge base, ticket system, live chat,
contextual help, and community forum functionality.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import uuid
import re

logger = logging.getLogger(__name__)


class ContentCategory(Enum):
    GETTING_STARTED = "getting_started"
    DOCUMENT_ANALYSIS = "document_analysis"
    QA_SYSTEM = "qa_system"
    ACCOUNT_SETTINGS = "account_settings"
    BILLING = "billing"
    SECURITY = "security"
    TROUBLESHOOTING = "troubleshooting"
    INTEGRATIONS = "integrations"
    API_REFERENCE = "api_reference"
    COMPLIANCE = "compliance"


class ContentType(Enum):
    ARTICLE = "article"
    FAQ = "faq"
    TROUBLESHOOT = "troubleshoot"
    TUTORIAL = "tutorial"
    VIDEO = "video"
    GUIDE = "guide"


class TicketPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_CUSTOMER = "waiting_for_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class UserRole(Enum):
    ATTORNEY = "attorney"
    PARALEGAL = "paralegal"
    CLIENT = "client"
    ADMIN = "admin"


@dataclass
class HelpArticle:
    """Knowledge base article"""
    article_id: str
    title: str
    content: str
    category: ContentCategory
    content_type: ContentType
    tags: List[str] = field(default_factory=list)
    target_roles: List[UserRole] = field(default_factory=list)
    difficulty_level: str = "beginner"  # beginner, intermediate, advanced
    estimated_read_time: int = 5  # minutes
    related_articles: List[str] = field(default_factory=list)
    attachments: List[Dict[str, str]] = field(default_factory=list)
    video_url: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.now)
    views: int = 0
    helpful_votes: int = 0
    not_helpful_votes: int = 0
    featured: bool = False

    def is_available_for_role(self, role: UserRole) -> bool:
        """Check if article is available for the given role"""
        if not self.target_roles:
            return True
        return role in self.target_roles

    def get_helpfulness_ratio(self) -> float:
        """Get helpfulness ratio (0-1)"""
        total_votes = self.helpful_votes + self.not_helpful_votes
        if total_votes == 0:
            return 0.0
        return self.helpful_votes / total_votes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'article_id': self.article_id,
            'title': self.title,
            'content': self.content,
            'category': self.category.value,
            'content_type': self.content_type.value,
            'tags': self.tags,
            'target_roles': [role.value for role in self.target_roles],
            'difficulty_level': self.difficulty_level,
            'estimated_read_time': self.estimated_read_time,
            'related_articles': self.related_articles,
            'attachments': self.attachments,
            'video_url': self.video_url,
            'last_updated': self.last_updated.isoformat(),
            'views': self.views,
            'helpful_votes': self.helpful_votes,
            'not_helpful_votes': self.not_helpful_votes,
            'helpfulness_ratio': self.get_helpfulness_ratio(),
            'featured': self.featured
        }


@dataclass
class SupportTicket:
    """Support ticket for customer issues"""
    ticket_id: str
    user_id: str
    subject: str
    description: str
    category: ContentCategory
    priority: TicketPriority
    status: TicketStatus = TicketStatus.OPEN
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    attachments: List[Dict[str, str]] = field(default_factory=list)
    user_feedback: Optional[Dict[str, Any]] = None
    internal_notes: List[Dict[str, Any]] = field(default_factory=list)

    def add_internal_note(self, author: str, note: str):
        """Add internal staff note"""
        self.internal_notes.append({
            'author': author,
            'note': note,
            'timestamp': datetime.now().isoformat()
        })
        self.updated_at = datetime.now()

    def update_status(self, status: TicketStatus, assigned_to: Optional[str] = None):
        """Update ticket status"""
        self.status = status
        if assigned_to:
            self.assigned_to = assigned_to
        self.updated_at = datetime.now()

        if status == TicketStatus.RESOLVED:
            self.resolved_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'subject': self.subject,
            'description': self.description,
            'category': self.category.value,
            'priority': self.priority.value,
            'status': self.status.value,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'tags': self.tags,
            'attachments': self.attachments,
            'user_feedback': self.user_feedback,
            'internal_notes': len(self.internal_notes)  # Count only for privacy
        }


@dataclass
class ChatSession:
    """Live chat session"""
    session_id: str
    user_id: str
    agent_id: Optional[str] = None
    status: str = "waiting"  # waiting, active, ended
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    user_rating: Optional[int] = None
    user_feedback: Optional[str] = None

    def add_message(self, sender: str, message: str, sender_type: str = "user"):
        """Add message to chat"""
        self.messages.append({
            'sender': sender,
            'sender_type': sender_type,  # user, agent, system
            'message': message,
            'timestamp': datetime.now().isoformat()
        })

    def end_session(self, rating: Optional[int] = None, feedback: Optional[str] = None):
        """End chat session"""
        self.status = "ended"
        self.ended_at = datetime.now()
        if rating:
            self.user_rating = rating
        if feedback:
            self.user_feedback = feedback


@dataclass
class ContextualHelp:
    """Contextual help for UI elements"""
    element_id: str
    title: str
    content: str
    trigger_type: str = "hover"  # hover, click, focus
    position: str = "top"  # top, bottom, left, right
    category: ContentCategory = ContentCategory.GETTING_STARTED
    target_roles: List[UserRole] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)  # When to show
    priority: int = 1  # Higher priority shows first
    active: bool = True


class HelpSystem:
    """Comprehensive help and support system"""

    def __init__(self):
        self.articles: Dict[str, HelpArticle] = {}
        self.tickets: Dict[str, SupportTicket] = {}
        self.chat_sessions: Dict[str, ChatSession] = {}
        self.contextual_help: Dict[str, ContextualHelp] = {}
        self.search_index: Dict[str, List[str]] = defaultdict(list)

        # Initialize with default content
        self._initialize_help_content()
        self._build_search_index()

    def _initialize_help_content(self):
        """Initialize with default help articles"""

        # Getting Started Articles
        getting_started_article = HelpArticle(
            article_id="help-001",
            title="Getting Started with Legal AI System",
            content="""
            # Getting Started with Legal AI System

            Welcome to the Legal AI System! This guide will help you get up and running quickly.

            ## First Steps

            1. **Complete Your Profile**: Start by filling out your professional profile including your role, practice areas, and jurisdiction.

            2. **Upload Your First Document**: Try uploading a sample document to see how our AI analysis works.

            3. **Explore the Dashboard**: Familiarize yourself with the main interface and available features.

            4. **Set Up Notifications**: Configure how you want to receive updates about document analysis and system alerts.

            ## Key Features

            ### Document Analysis
            Upload legal documents in PDF, DOCX, or TXT format. Our AI will analyze the content and provide:
            - Key findings and summaries
            - Risk assessments
            - Important clause identification
            - Compliance checks

            ### Q&A System
            Ask natural language questions about your documents and get instant, contextual answers backed by the document content.

            ### Attorney Accountability
            All AI suggestions are clearly marked and require attorney review. The system maintains full audit trails for professional responsibility compliance.

            ## Need Help?
            - Check our comprehensive FAQ section
            - Watch video tutorials
            - Contact support via live chat or ticket system
            - Join our community forum
            """,
            category=ContentCategory.GETTING_STARTED,
            content_type=ContentType.GUIDE,
            tags=["basics", "setup", "introduction"],
            target_roles=[UserRole.ATTORNEY, UserRole.PARALEGAL, UserRole.CLIENT],
            difficulty_level="beginner",
            estimated_read_time=8,
            video_url="/videos/getting-started-overview.mp4",
            featured=True
        )

        # Document Upload FAQ
        document_upload_faq = HelpArticle(
            article_id="faq-001",
            title="Document Upload - Frequently Asked Questions",
            content="""
            # Document Upload FAQ

            ## What file formats are supported?
            We support PDF, Microsoft Word (DOCX), plain text (TXT), and Rich Text Format (RTF) files.

            ## What's the maximum file size?
            The maximum file size is 50MB per document. For larger files, consider splitting them into smaller sections.

            ## How long does analysis take?
            Most documents are analyzed within 1-3 minutes. Complex or lengthy documents may take up to 10 minutes.

            ## Is my data secure?
            Yes. All documents are encrypted in transit and at rest. We follow SOC 2 Type II and maintain attorney-client privilege protections.

            ## Can I upload multiple documents at once?
            Yes, you can select and upload multiple files simultaneously. Each will be analyzed separately.

            ## What happens if upload fails?
            If an upload fails, check your internet connection and try again. If problems persist, contact support.

            ## Can I delete documents?
            Yes, you can delete documents from your library. Note that this action is permanent and cannot be undone.

            ## How do I organize my documents?
            Use folders and tags to organize your documents. You can create custom folders and apply multiple tags to each document.
            """,
            category=ContentCategory.DOCUMENT_ANALYSIS,
            content_type=ContentType.FAQ,
            tags=["upload", "files", "formats", "security"],
            estimated_read_time=5
        )

        # Troubleshooting Guide
        troubleshooting_guide = HelpArticle(
            article_id="trouble-001",
            title="Common Issues and Solutions",
            content="""
            # Troubleshooting Guide

            ## Document Won't Upload

            **Symptoms**: Upload fails or gets stuck at 0%

            **Solutions**:
            1. Check file size (must be under 50MB)
            2. Verify file format is supported (PDF, DOCX, TXT, RTF)
            3. Clear browser cache and cookies
            4. Try a different browser
            5. Check internet connection stability

            ## Analysis Taking Too Long

            **Symptoms**: Document analysis stuck in "processing" state

            **Solutions**:
            1. Wait up to 10 minutes for complex documents
            2. Refresh the page to check status
            3. Try re-uploading if stuck for over 15 minutes
            4. Contact support if issue persists

            ## Q&A System Not Responding

            **Symptoms**: Questions not getting answers or getting irrelevant responses

            **Solutions**:
            1. Ensure document analysis is complete first
            2. Make questions specific and clear
            3. Reference specific sections when possible
            4. Try rephrasing the question
            5. Check that the question relates to the document content

            ## Login Issues

            **Symptoms**: Can't log in or session expires frequently

            **Solutions**:
            1. Reset password if login fails
            2. Clear browser data
            3. Check for browser extensions blocking cookies
            4. Try incognito/private browsing mode
            5. Contact support for account issues

            ## Slow Performance

            **Symptoms**: System feels slow or unresponsive

            **Solutions**:
            1. Close unnecessary browser tabs
            2. Clear browser cache
            3. Check internet connection speed
            4. Try a different browser
            5. Disable browser extensions temporarily
            """,
            category=ContentCategory.TROUBLESHOOTING,
            content_type=ContentType.TROUBLESHOOT,
            tags=["problems", "solutions", "bugs", "performance"],
            difficulty_level="beginner",
            estimated_read_time=7
        )

        # Security and Compliance
        security_article = HelpArticle(
            article_id="security-001",
            title="Security and Compliance Overview",
            content="""
            # Security and Compliance

            ## Data Security

            ### Encryption
            - All data encrypted in transit (TLS 1.3)
            - All data encrypted at rest (AES-256)
            - End-to-end encryption for sensitive communications

            ### Access Controls
            - Multi-factor authentication available
            - Role-based access permissions
            - Session timeout protections
            - IP address restrictions (enterprise)

            ### Compliance Standards
            - SOC 2 Type II certified
            - GDPR compliant
            - CCPA compliant
            - HIPAA compliant (healthcare clients)

            ## Attorney-Client Privilege

            ### Privilege Protection
            - Documents marked as privileged
            - Access audit trails maintained
            - Privilege warnings and confirmations
            - Secure sharing controls

            ### Professional Responsibility
            - All AI outputs clearly labeled
            - Attorney review requirements enforced
            - Competence and diligence safeguards
            - Client consent processes documented

            ## Data Retention

            ### Retention Periods
            - Documents: As long as account active + 7 years
            - Analysis results: Same as source documents
            - Audit logs: 7 years minimum
            - Chat/support: 2 years

            ### Data Deletion
            - Secure deletion processes
            - Certificate of destruction available
            - Right to be forgotten compliance
            - Backup deletion coordination

            ## Incident Response

            ### Security Incidents
            - 24/7 security monitoring
            - Immediate incident response team
            - Client notification within 24 hours
            - Regular security assessments

            ### Breach Procedures
            - Forensic investigation protocols
            - Legal notification requirements
            - Remediation and prevention measures
            - Post-incident reviews and improvements
            """,
            category=ContentCategory.SECURITY,
            content_type=ContentType.GUIDE,
            tags=["security", "compliance", "privacy", "professional-responsibility"],
            target_roles=[UserRole.ATTORNEY, UserRole.ADMIN],
            difficulty_level="intermediate",
            estimated_read_time=12
        )

        # Add articles to library
        articles = [getting_started_article, document_upload_faq, troubleshooting_guide, security_article]
        for article in articles:
            self.articles[article.article_id] = article

        # Initialize contextual help
        self._initialize_contextual_help()

    def _initialize_contextual_help(self):
        """Initialize contextual help tooltips"""

        contextual_helps = [
            ContextualHelp(
                element_id="upload-button",
                title="Upload Documents",
                content="Click here to upload legal documents for AI analysis. Supports PDF, DOCX, TXT, and RTF formats up to 50MB.",
                trigger_type="hover",
                position="bottom",
                category=ContentCategory.DOCUMENT_ANALYSIS,
                priority=1
            ),
            ContextualHelp(
                element_id="analysis-results",
                title="Analysis Results",
                content="This panel shows AI-generated analysis including key findings, risk assessment, and important clauses. All results require attorney review.",
                trigger_type="hover",
                position="left",
                category=ContentCategory.DOCUMENT_ANALYSIS,
                priority=1
            ),
            ContextualHelp(
                element_id="qa-input",
                title="Ask Questions",
                content="Type natural language questions about your document here. Be specific for better results.",
                trigger_type="focus",
                position="top",
                category=ContentCategory.QA_SYSTEM,
                priority=1
            ),
            ContextualHelp(
                element_id="notifications-bell",
                title="Notifications",
                content="View system notifications, document analysis updates, and important alerts here.",
                trigger_type="hover",
                position="bottom",
                category=ContentCategory.GETTING_STARTED,
                priority=1
            )
        ]

        for help_item in contextual_helps:
            self.contextual_help[help_item.element_id] = help_item

    def _build_search_index(self):
        """Build search index for articles"""
        self.search_index.clear()

        for article in self.articles.values():
            # Index title words
            title_words = re.findall(r'\w+', article.title.lower())
            for word in title_words:
                if len(word) > 2:  # Skip very short words
                    self.search_index[word].append(article.article_id)

            # Index content words (first 500 chars)
            content_words = re.findall(r'\w+', article.content.lower()[:500])
            for word in content_words:
                if len(word) > 3:  # Slightly longer for content
                    self.search_index[word].append(article.article_id)

            # Index tags
            for tag in article.tags:
                self.search_index[tag.lower()].append(article.article_id)

    async def search_articles(self, query: str, role: Optional[UserRole] = None, category: Optional[ContentCategory] = None) -> List[HelpArticle]:
        """Search help articles"""
        if not query:
            return []

        query_words = re.findall(r'\w+', query.lower())
        article_scores = defaultdict(int)

        # Score articles based on word matches
        for word in query_words:
            if word in self.search_index:
                for article_id in self.search_index[word]:
                    article_scores[article_id] += 1

        # Get articles and filter
        results = []
        for article_id, score in sorted(article_scores.items(), key=lambda x: x[1], reverse=True):
            article = self.articles.get(article_id)
            if not article:
                continue

            # Filter by role
            if role and not article.is_available_for_role(role):
                continue

            # Filter by category
            if category and article.category != category:
                continue

            results.append(article)

        return results[:20]  # Limit to top 20 results

    async def get_article(self, article_id: str, user_id: Optional[str] = None) -> Optional[HelpArticle]:
        """Get help article and track view"""
        article = self.articles.get(article_id)
        if not article:
            return None

        # Increment view count
        article.views += 1

        return article

    async def get_featured_articles(self, role: Optional[UserRole] = None) -> List[HelpArticle]:
        """Get featured articles"""
        featured = [article for article in self.articles.values() if article.featured]

        if role:
            featured = [article for article in featured if article.is_available_for_role(role)]

        return sorted(featured, key=lambda x: (x.views, x.helpful_votes), reverse=True)

    async def get_articles_by_category(self, category: ContentCategory, role: Optional[UserRole] = None) -> List[HelpArticle]:
        """Get articles by category"""
        articles = [article for article in self.articles.values() if article.category == category]

        if role:
            articles = [article for article in articles if article.is_available_for_role(role)]

        return sorted(articles, key=lambda x: x.helpful_votes, reverse=True)

    async def vote_article(self, article_id: str, helpful: bool) -> bool:
        """Vote on article helpfulness"""
        article = self.articles.get(article_id)
        if not article:
            return False

        if helpful:
            article.helpful_votes += 1
        else:
            article.not_helpful_votes += 1

        return True

    async def create_support_ticket(
        self,
        user_id: str,
        subject: str,
        description: str,
        category: ContentCategory,
        priority: TicketPriority = TicketPriority.MEDIUM,
        attachments: Optional[List[Dict[str, str]]] = None
    ) -> SupportTicket:
        """Create new support ticket"""
        ticket_id = f"TICKET-{datetime.now().strftime('%Y%m%d')}-{len(self.tickets) + 1:04d}"

        ticket = SupportTicket(
            ticket_id=ticket_id,
            user_id=user_id,
            subject=subject,
            description=description,
            category=category,
            priority=priority,
            attachments=attachments or []
        )

        self.tickets[ticket_id] = ticket
        logger.info(f"Created support ticket {ticket_id} for user {user_id}")

        return ticket

    async def get_user_tickets(self, user_id: str, status: Optional[TicketStatus] = None) -> List[SupportTicket]:
        """Get user's support tickets"""
        tickets = [ticket for ticket in self.tickets.values() if ticket.user_id == user_id]

        if status:
            tickets = [ticket for ticket in tickets if ticket.status == status]

        return sorted(tickets, key=lambda x: x.created_at, reverse=True)

    async def update_ticket_status(self, ticket_id: str, status: TicketStatus, assigned_to: Optional[str] = None) -> bool:
        """Update ticket status"""
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return False

        ticket.update_status(status, assigned_to)
        return True

    async def add_ticket_note(self, ticket_id: str, author: str, note: str) -> bool:
        """Add internal note to ticket"""
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return False

        ticket.add_internal_note(author, note)
        return True

    async def start_chat_session(self, user_id: str) -> ChatSession:
        """Start new chat session"""
        session_id = str(uuid.uuid4())

        session = ChatSession(
            session_id=session_id,
            user_id=user_id
        )

        self.chat_sessions[session_id] = session
        logger.info(f"Started chat session {session_id} for user {user_id}")

        return session

    async def add_chat_message(self, session_id: str, sender: str, message: str, sender_type: str = "user") -> bool:
        """Add message to chat session"""
        session = self.chat_sessions.get(session_id)
        if not session:
            return False

        session.add_message(sender, message, sender_type)
        return True

    async def end_chat_session(self, session_id: str, rating: Optional[int] = None, feedback: Optional[str] = None) -> bool:
        """End chat session"""
        session = self.chat_sessions.get(session_id)
        if not session:
            return False

        session.end_session(rating, feedback)
        return True

    async def get_contextual_help(self, element_id: str, role: Optional[UserRole] = None) -> Optional[ContextualHelp]:
        """Get contextual help for UI element"""
        help_item = self.contextual_help.get(element_id)
        if not help_item or not help_item.active:
            return None

        if role and help_item.target_roles and role not in help_item.target_roles:
            return None

        return help_item

    async def get_popular_articles(self, limit: int = 10, role: Optional[UserRole] = None) -> List[HelpArticle]:
        """Get most popular articles"""
        articles = list(self.articles.values())

        if role:
            articles = [article for article in articles if article.is_available_for_role(role)]

        return sorted(articles, key=lambda x: x.views, reverse=True)[:limit]

    async def get_help_suggestions(self, context: str, role: Optional[UserRole] = None) -> List[HelpArticle]:
        """Get contextual help suggestions"""
        # Simple keyword matching for suggestions
        suggestions = await self.search_articles(context, role)
        return suggestions[:5]

    async def get_support_statistics(self) -> Dict[str, Any]:
        """Get support system statistics"""
        total_tickets = len(self.tickets)
        open_tickets = len([t for t in self.tickets.values() if t.status == TicketStatus.OPEN])
        resolved_tickets = len([t for t in self.tickets.values() if t.status == TicketStatus.RESOLVED])

        # Average resolution time (for resolved tickets)
        resolution_times = []
        for ticket in self.tickets.values():
            if ticket.status == TicketStatus.RESOLVED and ticket.resolved_at:
                resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600  # hours
                resolution_times.append(resolution_time)

        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0

        return {
            'total_articles': len(self.articles),
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'resolved_tickets': resolved_tickets,
            'resolution_rate': (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0,
            'avg_resolution_time_hours': avg_resolution_time,
            'total_article_views': sum(article.views for article in self.articles.values()),
            'active_chat_sessions': len([s for s in self.chat_sessions.values() if s.status == "active"])
        }


# Global help system instance
help_system = HelpSystem()


# FastAPI endpoints
def get_help_endpoints():
    """Returns FastAPI endpoints for help system"""
    from fastapi import APIRouter, HTTPException, Query, UploadFile, File
    from pydantic import BaseModel
    from typing import Optional, List

    router = APIRouter(prefix="/api/help", tags=["help-support"])

    class CreateTicketRequest(BaseModel):
        user_id: str
        subject: str
        description: str
        category: str
        priority: str = "medium"

    class VoteRequest(BaseModel):
        helpful: bool

    class ChatMessageRequest(BaseModel):
        sender: str
        message: str
        sender_type: str = "user"

    class EndChatRequest(BaseModel):
        rating: Optional[int] = None
        feedback: Optional[str] = None

    # Knowledge Base Endpoints
    @router.get("/articles/search")
    async def search_articles(
        q: str = Query(..., description="Search query"),
        role: Optional[str] = None,
        category: Optional[str] = None
    ):
        """Search help articles"""
        try:
            role_enum = UserRole(role) if role else None
            category_enum = ContentCategory(category) if category else None

            results = await help_system.search_articles(q, role_enum, category_enum)
            return [article.to_dict() for article in results]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/articles/{article_id}")
    async def get_article(article_id: str, user_id: Optional[str] = None):
        """Get specific help article"""
        article = await help_system.get_article(article_id, user_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return article.to_dict()

    @router.get("/articles/featured")
    async def get_featured_articles(role: Optional[str] = None):
        """Get featured articles"""
        try:
            role_enum = UserRole(role) if role else None
            articles = await help_system.get_featured_articles(role_enum)
            return [article.to_dict() for article in articles]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/articles/category/{category}")
    async def get_articles_by_category(category: str, role: Optional[str] = None):
        """Get articles by category"""
        try:
            category_enum = ContentCategory(category)
            role_enum = UserRole(role) if role else None
            articles = await help_system.get_articles_by_category(category_enum, role_enum)
            return [article.to_dict() for article in articles]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/articles/popular")
    async def get_popular_articles(limit: int = 10, role: Optional[str] = None):
        """Get popular articles"""
        try:
            role_enum = UserRole(role) if role else None
            articles = await help_system.get_popular_articles(limit, role_enum)
            return [article.to_dict() for article in articles]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/articles/{article_id}/vote")
    async def vote_article(article_id: str, request: VoteRequest):
        """Vote on article helpfulness"""
        success = await help_system.vote_article(article_id, request.helpful)
        if not success:
            raise HTTPException(status_code=404, detail="Article not found")
        return {"success": True}

    # Support Tickets
    @router.post("/tickets")
    async def create_ticket(request: CreateTicketRequest):
        """Create support ticket"""
        try:
            category = ContentCategory(request.category)
            priority = TicketPriority(request.priority)

            ticket = await help_system.create_support_ticket(
                request.user_id,
                request.subject,
                request.description,
                category,
                priority
            )

            return ticket.to_dict()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/user/{user_id}/tickets")
    async def get_user_tickets(user_id: str, status: Optional[str] = None):
        """Get user tickets"""
        try:
            status_enum = TicketStatus(status) if status else None
            tickets = await help_system.get_user_tickets(user_id, status_enum)
            return [ticket.to_dict() for ticket in tickets]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Live Chat
    @router.post("/chat/start")
    async def start_chat(user_id: str):
        """Start chat session"""
        session = await help_system.start_chat_session(user_id)
        return {
            "session_id": session.session_id,
            "status": session.status,
            "started_at": session.started_at.isoformat()
        }

    @router.post("/chat/{session_id}/message")
    async def add_chat_message(session_id: str, request: ChatMessageRequest):
        """Add chat message"""
        success = await help_system.add_chat_message(
            session_id,
            request.sender,
            request.message,
            request.sender_type
        )
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return {"success": True}

    @router.post("/chat/{session_id}/end")
    async def end_chat(session_id: str, request: EndChatRequest):
        """End chat session"""
        success = await help_system.end_chat_session(
            session_id,
            request.rating,
            request.feedback
        )
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return {"success": True}

    # Contextual Help
    @router.get("/contextual/{element_id}")
    async def get_contextual_help(element_id: str, role: Optional[str] = None):
        """Get contextual help for UI element"""
        try:
            role_enum = UserRole(role) if role else None
            help_item = await help_system.get_contextual_help(element_id, role_enum)

            if not help_item:
                raise HTTPException(status_code=404, detail="Help item not found")

            return {
                "element_id": help_item.element_id,
                "title": help_item.title,
                "content": help_item.content,
                "trigger_type": help_item.trigger_type,
                "position": help_item.position,
                "priority": help_item.priority
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/suggestions")
    async def get_help_suggestions(context: str, role: Optional[str] = None):
        """Get contextual help suggestions"""
        try:
            role_enum = UserRole(role) if role else None
            suggestions = await help_system.get_help_suggestions(context, role_enum)
            return [article.to_dict() for article in suggestions]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/stats")
    async def get_support_statistics():
        """Get support system statistics"""
        return await help_system.get_support_statistics()

    return router


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def demo():
        system = HelpSystem()

        # Search articles
        results = await system.search_articles("upload document", UserRole.ATTORNEY)
        print(f"Found {len(results)} articles")

        # Create support ticket
        ticket = await system.create_support_ticket(
            user_id="user123",
            subject="Cannot upload PDF files",
            description="Getting error when trying to upload PDF files over 10MB",
            category=ContentCategory.DOCUMENT_ANALYSIS,
            priority=TicketPriority.HIGH
        )
        print(f"Created ticket: {ticket.ticket_id}")

        # Start chat session
        chat = await system.start_chat_session("user123")
        await system.add_chat_message(chat.session_id, "user123", "I need help with document upload")
        print(f"Started chat: {chat.session_id}")

        # Get statistics
        stats = await system.get_support_statistics()
        print(f"Support stats: {stats}")

        print("Help system demo completed!")

    asyncio.run(demo())