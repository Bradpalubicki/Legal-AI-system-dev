"""
Case Notification History Model
Stores all notifications sent for monitored cases
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text
from datetime import datetime
from app.models.legal_documents import Base


class CaseNotification(Base):
    """Store notification history for monitored cases"""
    __tablename__ = "case_notifications"

    id = Column(Integer, primary_key=True, index=True)

    # Case information
    docket_id = Column(Integer, nullable=False, index=True)
    case_name = Column(String(500))
    court = Column(String(255))  # Increased to handle full court URLs

    # Notification details
    notification_type = Column(String(50), default="new_documents")  # new_documents, error, etc.
    document_count = Column(Integer, default=0)
    documents = Column(JSON)  # Store document details as JSON

    # Delivery tracking
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
    websocket_sent = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    email_to = Column(String(255))
    email_error = Column(Text)

    # Additional data
    extra_data = Column(JSON)  # Any extra notification data

    def __repr__(self):
        return f"<CaseNotification(docket_id={self.docket_id}, documents={self.document_count}, sent_at={self.sent_at})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "docket_id": self.docket_id,
            "case_name": self.case_name,
            "court": self.court,
            "notification_type": self.notification_type,
            "document_count": self.document_count,
            "documents": self.documents,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "websocket_sent": self.websocket_sent,
            "email_sent": self.email_sent,
            "email_to": self.email_to,
            "email_error": self.email_error,
            "extra_data": self.extra_data
        }
