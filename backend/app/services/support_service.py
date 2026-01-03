"""
Legal AI System - Comprehensive Support Service
Help desk, knowledge base, and customer support management
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, and_, or_
from fastapi import HTTPException, BackgroundTasks
import logging
import openai

from ..models.support import (
    SupportTicket, KnowledgeBaseArticle, SupportCategory,
    ChatSession, SupportAgent, FAQ, TicketComment
)
from ..models.user import User
from ..core.database import get_async_session
from ..core.config import settings
from ..utils.email import send_email
from ..utils.notifications import send_notification, send_slack_alert

logger = logging.getLogger(__name__)

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting_for_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"

class SupportService:
    """Comprehensive support and help desk service"""

    def __init__(self):
        self.openai_available = bool(settings.OPENAI_API_KEY)
        self.openai_client = None
        if self.openai_available:
            self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            logger.warning("OpenAI API key not found. AI support features will be disabled.")

    async def create_ticket(
        self,
        user_id: int,
        subject: str,
        description: str,
        category_id: Optional[int] = None,
        priority: str = "medium",
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Create a new support ticket"""
        try:
            async with get_async_session() as session:
                # Auto-categorize and prioritize if not provided
                if not category_id:
                    category_id = await self._auto_categorize_ticket(subject, description)

                priority = await self._auto_prioritize_ticket(subject, description, priority)

                # Create ticket
                ticket = SupportTicket(
                    user_id=user_id,
                    subject=subject,
                    description=description,
                    category_id=category_id,
                    priority=priority,
                    status=TicketStatus.OPEN,
                    ticket_number=await self._generate_ticket_number()
                )

                session.add(ticket)
                await session.commit()
                await session.refresh(ticket)

                # Auto-assign to agent based on category and workload
                await self._auto_assign_ticket(ticket.id)

                # Send notifications
                await self._send_ticket_created_notifications(ticket.id)

                # Check for immediate response from knowledge base
                suggested_articles = await self._suggest_articles(subject, description)

                logger.info(f"Created support ticket {ticket.ticket_number} for user {user_id}")

                return {
                    "ticket_id": ticket.id,
                    "ticket_number": ticket.ticket_number,
                    "status": ticket.status,
                    "priority": ticket.priority,
                    "suggested_articles": suggested_articles
                }

        except Exception as e:
            logger.error(f"Failed to create support ticket: {e}")
            raise HTTPException(status_code=500, detail="Failed to create ticket")

    async def update_ticket(
        self,
        ticket_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[int] = None,
        internal_notes: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """Update a support ticket"""
        try:
            async with get_async_session() as session:
                ticket = await session.get(
                    SupportTicket,
                    ticket_id,
                    options=[selectinload(SupportTicket.user)]
                )

                if not ticket:
                    raise HTTPException(status_code=404, detail="Ticket not found")

                # Check permissions
                if user_id and ticket.user_id != user_id:
                    # Check if user is admin or agent
                    user = await session.get(User, user_id)
                    if not (user.is_admin or user.is_support_agent):
                        raise HTTPException(status_code=403, detail="Permission denied")

                old_status = ticket.status
                old_priority = ticket.priority

                # Update fields
                if status:
                    ticket.status = status
                if priority:
                    ticket.priority = priority
                if assigned_to:
                    ticket.assigned_to = assigned_to
                if internal_notes:
                    # Add to comments
                    comment = TicketComment(
                        ticket_id=ticket_id,
                        user_id=user_id,
                        content=internal_notes,
                        is_internal=True
                    )
                    session.add(comment)

                ticket.updated_at = datetime.utcnow()

                # Track resolution time
                if status == TicketStatus.RESOLVED and old_status != TicketStatus.RESOLVED:
                    ticket.resolved_at = datetime.utcnow()
                    ticket.resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds()

                await session.commit()

                # Send notifications for status changes
                if status and status != old_status:
                    await self._send_status_change_notifications(ticket_id, old_status, status)

                logger.info(f"Updated ticket {ticket.ticket_number}")
                return True

        except Exception as e:
            logger.error(f"Failed to update ticket: {e}")
            raise HTTPException(status_code=500, detail="Failed to update ticket")

    async def add_ticket_comment(
        self,
        ticket_id: int,
        user_id: int,
        content: str,
        is_internal: bool = False,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Add a comment to a ticket"""
        try:
            async with get_async_session() as session:
                # Verify ticket exists and user has permission
                ticket = await session.get(SupportTicket, ticket_id)
                if not ticket:
                    raise HTTPException(status_code=404, detail="Ticket not found")

                user = await session.get(User, user_id)
                if ticket.user_id != user_id and not (user.is_admin or user.is_support_agent):
                    raise HTTPException(status_code=403, detail="Permission denied")

                # Create comment
                comment = TicketComment(
                    ticket_id=ticket_id,
                    user_id=user_id,
                    content=content,
                    is_internal=is_internal,
                    attachments=attachments or []
                )

                session.add(comment)

                # Update ticket last activity
                ticket.updated_at = datetime.utcnow()
                if not is_internal and ticket.user_id != user_id:
                    # Agent responded, set status to waiting for customer
                    ticket.status = TicketStatus.WAITING

                await session.commit()

                # Send notifications
                await self._send_comment_notifications(ticket_id, user_id, is_internal)

                logger.info(f"Added comment to ticket {ticket.ticket_number}")

                return {
                    "comment_id": comment.id,
                    "created_at": comment.created_at
                }

        except Exception as e:
            logger.error(f"Failed to add comment: {e}")
            raise HTTPException(status_code=500, detail="Failed to add comment")

    async def search_knowledge_base(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search knowledge base articles"""
        try:
            async with get_async_session() as session:
                # Build search query
                search_query = select(KnowledgeBaseArticle).where(
                    KnowledgeBaseArticle.is_published == True
                )

                if category:
                    search_query = search_query.join(SupportCategory).where(
                        SupportCategory.name == category
                    )

                # Full-text search (simplified - would use proper search in production)
                search_query = search_query.where(
                    or_(
                        KnowledgeBaseArticle.title.ilike(f"%{query}%"),
                        KnowledgeBaseArticle.content.ilike(f"%{query}%"),
                        KnowledgeBaseArticle.tags.ilike(f"%{query}%")
                    )
                ).limit(limit)

                articles = await session.execute(search_query)
                articles = articles.scalars().all()

                # Score articles by relevance (simplified)
                results = []
                for article in articles:
                    relevance_score = self._calculate_relevance(query, article)
                    results.append({
                        "id": article.id,
                        "title": article.title,
                        "excerpt": article.content[:200] + "...",
                        "url": f"/kb/{article.slug}",
                        "relevance_score": relevance_score,
                        "helpful_count": article.helpful_count,
                        "view_count": article.view_count
                    })

                # Sort by relevance
                results.sort(key=lambda x: x["relevance_score"], reverse=True)

                logger.info(f"Knowledge base search for '{query}' returned {len(results)} results")
                return results

        except Exception as e:
            logger.error(f"Knowledge base search failed: {e}")
            raise HTTPException(status_code=500, detail="Search failed")

    async def create_chat_session(
        self,
        user_id: int,
        initial_message: str
    ) -> Dict[str, Any]:
        """Create a new chat session"""
        try:
            async with get_async_session() as session:
                # Check if user has active chat session
                existing_session = await session.execute(
                    select(ChatSession).where(
                        and_(
                            ChatSession.user_id == user_id,
                            ChatSession.status == "active"
                        )
                    )
                )
                existing_session = existing_session.scalar_one_or_none()

                if existing_session:
                    return {
                        "session_id": existing_session.id,
                        "status": "existing_session",
                        "message": "You have an active chat session"
                    }

                # Create new session
                chat_session = ChatSession(
                    user_id=user_id,
                    status="active",
                    initial_message=initial_message
                )

                session.add(chat_session)
                await session.commit()
                await session.refresh(chat_session)

                # Try to auto-respond with AI first
                ai_response = await self._generate_ai_response(initial_message)

                # If AI can't handle it, route to human agent
                if not ai_response or "transfer_to_human" in ai_response.get("action", ""):
                    await self._assign_chat_agent(chat_session.id)
                    response_message = "Connecting you with a support agent..."
                else:
                    response_message = ai_response.get("message", "How can I help you?")

                logger.info(f"Created chat session {chat_session.id} for user {user_id}")

                return {
                    "session_id": chat_session.id,
                    "status": "created",
                    "initial_response": response_message
                }

        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            raise HTTPException(status_code=500, detail="Failed to create chat session")

    async def get_faq(
        self,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get frequently asked questions"""
        try:
            async with get_async_session() as session:
                query = select(FAQ).where(FAQ.is_active == True)

                if category:
                    query = query.join(SupportCategory).where(
                        SupportCategory.name == category
                    )

                query = query.order_by(FAQ.sort_order, FAQ.view_count.desc()).limit(limit)

                faqs = await session.execute(query)
                faqs = faqs.scalars().all()

                return [
                    {
                        "id": faq.id,
                        "question": faq.question,
                        "answer": faq.answer,
                        "helpful_count": faq.helpful_count,
                        "view_count": faq.view_count
                    }
                    for faq in faqs
                ]

        except Exception as e:
            logger.error(f"Failed to get FAQ: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve FAQ")

    async def escalate_ticket(
        self,
        ticket_id: int,
        reason: str,
        escalated_by: int
    ) -> bool:
        """Escalate a ticket to higher priority/management"""
        try:
            async with get_async_session() as session:
                ticket = await session.get(SupportTicket, ticket_id)
                if not ticket:
                    raise HTTPException(status_code=404, detail="Ticket not found")

                # Update priority
                old_priority = ticket.priority
                if ticket.priority == "low":
                    ticket.priority = "medium"
                elif ticket.priority == "medium":
                    ticket.priority = "high"
                elif ticket.priority == "high":
                    ticket.priority = "urgent"

                ticket.updated_at = datetime.utcnow()

                # Add escalation comment
                comment = TicketComment(
                    ticket_id=ticket_id,
                    user_id=escalated_by,
                    content=f"Ticket escalated from {old_priority} to {ticket.priority}. Reason: {reason}",
                    is_internal=True
                )
                session.add(comment)

                await session.commit()

                # Send escalation notifications
                await self._send_escalation_notifications(ticket_id, reason)

                logger.info(f"Escalated ticket {ticket.ticket_number} to {ticket.priority}")
                return True

        except Exception as e:
            logger.error(f"Failed to escalate ticket: {e}")
            raise HTTPException(status_code=500, detail="Failed to escalate ticket")

    # Private helper methods
    async def _auto_categorize_ticket(self, subject: str, description: str) -> int:
        """Auto-categorize ticket using AI"""
        try:
            # Use AI to categorize
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Categorize this support ticket into one of: billing, technical, account, feature_request, bug_report"
                    },
                    {
                        "role": "user",
                        "content": f"Subject: {subject}\nDescription: {description}"
                    }
                ],
                max_tokens=50
            )

            category_name = response.choices[0].message.content.strip().lower()

            # Get category ID
            async with get_async_session() as session:
                category = await session.execute(
                    select(SupportCategory).where(SupportCategory.name == category_name)
                )
                category = category.scalar_one_or_none()

                return category.id if category else 1  # Default to general

        except Exception as e:
            logger.error(f"Auto-categorization failed: {e}")
            return 1  # Default category

    async def _auto_prioritize_ticket(self, subject: str, description: str, default: str) -> str:
        """Auto-prioritize ticket based on content"""
        urgent_keywords = ["urgent", "critical", "down", "error", "broken", "can't access"]
        high_keywords = ["billing", "payment", "refund", "security"]

        content = f"{subject} {description}".lower()

        if any(keyword in content for keyword in urgent_keywords):
            return "urgent"
        elif any(keyword in content for keyword in high_keywords):
            return "high"
        else:
            return default

    async def _generate_ticket_number(self) -> str:
        """Generate unique ticket number"""
        import uuid
        return f"TKT-{str(uuid.uuid4())[:8].upper()}"

    async def _auto_assign_ticket(self, ticket_id: int) -> None:
        """Auto-assign ticket to available agent"""
        try:
            async with get_async_session() as session:
                # Find agent with lowest active ticket count
                # This is simplified - would use more sophisticated load balancing
                pass

        except Exception as e:
            logger.error(f"Auto-assignment failed: {e}")

    async def _suggest_articles(self, subject: str, description: str) -> List[Dict]:
        """Suggest relevant knowledge base articles"""
        return await self.search_knowledge_base(f"{subject} {description}", limit=3)

    async def _generate_ai_response(self, message: str) -> Optional[Dict]:
        """Generate AI response for chat"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful Legal AI support assistant.
                        Help users with billing, technical issues, and general questions.
                        If the issue is complex or requires human intervention, respond with 'transfer_to_human'."""
                    },
                    {"role": "user", "content": message}
                ],
                max_tokens=200
            )

            return {
                "message": response.choices[0].message.content,
                "action": "ai_response"
            }

        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return None

    def _calculate_relevance(self, query: str, article: KnowledgeBaseArticle) -> float:
        """Calculate relevance score for search results"""
        # Simplified relevance scoring
        query_words = query.lower().split()
        title_words = article.title.lower().split()
        content_words = article.content.lower().split()

        title_matches = sum(1 for word in query_words if word in title_words)
        content_matches = sum(1 for word in query_words if word in content_words)

        return (title_matches * 2 + content_matches) / len(query_words)

    async def _send_ticket_created_notifications(self, ticket_id: int) -> None:
        """Send notifications for new ticket"""
        # Send email to customer, alert agents
        pass

    async def _send_status_change_notifications(self, ticket_id: int, old_status: str, new_status: str) -> None:
        """Send notifications for status changes"""
        # Send email updates
        pass

    async def _send_comment_notifications(self, ticket_id: int, user_id: int, is_internal: bool) -> None:
        """Send notifications for new comments"""
        # Send email/push notifications
        pass

    async def _send_escalation_notifications(self, ticket_id: int, reason: str) -> None:
        """Send escalation notifications"""
        # Alert management team
        pass

    async def _assign_chat_agent(self, session_id: int) -> None:
        """Assign human agent to chat session"""
        # Implement agent assignment logic
        pass

# Initialize support service
support_service = SupportService()