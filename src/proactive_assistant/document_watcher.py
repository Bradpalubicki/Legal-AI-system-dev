"""
Document Watcher

Intelligent document monitoring system that tracks changes, analyzes content,
and provides proactive insights on document modifications and new filings.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import mimetypes
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, and_, or_, func, desc
from pydantic import BaseModel, Field

from ..core.database import get_db_session
from ..client_portal.models import Document, DocumentStatus, DocumentType
from ..trial_prep.models import Case


logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Types of document changes."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"
    RENAMED = "renamed"
    STATUS_CHANGED = "status_changed"
    PERMISSIONS_CHANGED = "permissions_changed"
    VERSION_ADDED = "version_added"
    METADATA_UPDATED = "metadata_updated"


class DocumentCategory(str, Enum):
    """Document categories for monitoring."""
    PLEADING = "pleading"
    MOTION = "motion"
    BRIEF = "brief"
    DISCOVERY = "discovery"
    EVIDENCE = "evidence"
    CONTRACT = "contract"
    CORRESPONDENCE = "correspondence"
    RESEARCH = "research"
    ADMINISTRATIVE = "administrative"
    CLIENT_COMMUNICATION = "client_communication"


class MonitoringScope(str, Enum):
    """Scope of document monitoring."""
    ALL_DOCUMENTS = "all_documents"
    CASE_SPECIFIC = "case_specific"
    DOCUMENT_TYPE = "document_type"
    PRIORITY_DOCUMENTS = "priority_documents"
    CLIENT_DOCUMENTS = "client_documents"


@dataclass
class DocumentChange:
    """Document change event."""
    id: str
    document_id: int
    case_id: Optional[int]
    change_type: ChangeType
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    changed_by: Optional[int] = None
    change_timestamp: datetime = field(default_factory=datetime.utcnow)
    change_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentAlert:
    """Document monitoring alert."""
    id: str
    document_id: int
    case_id: Optional[int]
    document_name: str
    alert_type: str
    priority: str
    message: str
    change_summary: str
    recommended_actions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_acknowledged: bool = False


class DocumentWatchRule(BaseModel):
    """Rule for document watching."""
    id: str
    name: str
    description: str
    scope: MonitoringScope
    document_types: List[DocumentType] = Field(default_factory=list)
    case_ids: List[int] = Field(default_factory=list)
    change_types: List[ChangeType] = Field(default_factory=list)
    conditions: Dict[str, Any] = Field(default_factory=dict)
    alert_threshold: int = 1  # Number of changes before alerting
    cooldown_minutes: int = 30  # Minimum time between similar alerts
    is_active: bool = True
    created_by: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentAnalysis(BaseModel):
    """Document content analysis results."""
    document_id: int
    content_hash: str
    word_count: int
    key_terms: List[str] = Field(default_factory=list)
    detected_entities: List[Dict[str, Any]] = Field(default_factory=list)
    sentiment_score: Optional[float] = None
    complexity_score: Optional[float] = None
    risk_indicators: List[str] = Field(default_factory=list)
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)


class DocumentWatcher:
    """
    Intelligent document monitoring with change detection and analysis.
    """
    
    def __init__(self):
        self.watch_rules: List[DocumentWatchRule] = []
        self.document_snapshots: Dict[int, Dict[str, Any]] = {}
        self.pending_changes: Dict[str, DocumentChange] = {}
        self.active_alerts: Dict[str, DocumentAlert] = {}
        self.content_analysis_cache: Dict[int, DocumentAnalysis] = {}
        self.is_watching = False
        self.scan_interval = 600  # 10 minutes
        
        # Load default watch rules
        self._load_default_rules()
        
    def _load_default_rules(self):
        """Load default document watching rules."""
        default_rules = [
            DocumentWatchRule(
                id="critical_document_changes",
                name="Critical Document Changes",
                description="Monitor changes to critical case documents",
                scope=MonitoringScope.DOCUMENT_TYPE,
                document_types=[
                    DocumentType.PLEADING,
                    DocumentType.MOTION,
                    DocumentType.BRIEF,
                    DocumentType.COURT_ORDER
                ],
                change_types=[ChangeType.MODIFIED, ChangeType.DELETED, ChangeType.STATUS_CHANGED],
                alert_threshold=1,
                cooldown_minutes=15,
                created_by=0
            ),
            DocumentWatchRule(
                id="new_court_documents",
                name="New Court Documents",
                description="Alert on new court filings and orders",
                scope=MonitoringScope.DOCUMENT_TYPE,
                document_types=[
                    DocumentType.COURT_ORDER,
                    DocumentType.COURT_FILING,
                    DocumentType.JUDGMENT
                ],
                change_types=[ChangeType.CREATED],
                alert_threshold=1,
                cooldown_minutes=0,
                created_by=0
            ),
            DocumentWatchRule(
                id="discovery_document_updates",
                name="Discovery Document Updates", 
                description="Monitor discovery-related document changes",
                scope=MonitoringScope.DOCUMENT_TYPE,
                document_types=[
                    DocumentType.DISCOVERY_REQUEST,
                    DocumentType.DISCOVERY_RESPONSE,
                    DocumentType.DEPOSITION
                ],
                change_types=[ChangeType.CREATED, ChangeType.MODIFIED, ChangeType.STATUS_CHANGED],
                alert_threshold=1,
                cooldown_minutes=30,
                created_by=0
            ),
            DocumentWatchRule(
                id="client_document_activity",
                name="Client Document Activity",
                description="Track client document uploads and modifications",
                scope=MonitoringScope.CLIENT_DOCUMENTS,
                change_types=[ChangeType.CREATED, ChangeType.MODIFIED],
                conditions={"client_uploaded": True},
                alert_threshold=1,
                cooldown_minutes=60,
                created_by=0
            )
        ]
        
        self.watch_rules.extend(default_rules)
        
    async def start_watching(self):
        """Start the document watching service."""
        if self.is_watching:
            return
            
        self.is_watching = True
        logger.info("Starting document watching service")
        
        # Initialize document snapshots
        await self._initialize_snapshots()
        
        while self.is_watching:
            try:
                await self._watching_cycle()
                await asyncio.sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"Error in document watching cycle: {str(e)}")
                await asyncio.sleep(60)
                
    async def stop_watching(self):
        """Stop the document watching service."""
        self.is_watching = False
        logger.info("Stopping document watching service")
        
    async def _initialize_snapshots(self):
        """Initialize document snapshots for change detection."""
        async with get_db_session() as db:
            # Get all active documents
            query = select(Document).where(
                Document.status != DocumentStatus.DELETED
            ).options(selectinload(Document.case))
            
            result = await db.execute(query)
            documents = result.scalars().all()
            
            for document in documents:
                snapshot = await self._create_document_snapshot(document, db)
                self.document_snapshots[document.id] = snapshot
                
        logger.info(f"Initialized snapshots for {len(self.document_snapshots)} documents")
        
    async def _watching_cycle(self):
        """Execute one document watching cycle."""
        async with get_db_session() as db:
            # Get current documents
            query = select(Document).where(
                Document.status != DocumentStatus.DELETED
            ).options(selectinload(Document.case))
            
            result = await db.execute(query)
            current_documents = result.scalars().all()
            
            current_doc_ids = {doc.id for doc in current_documents}
            previous_doc_ids = set(self.document_snapshots.keys())
            
            # Detect new documents
            new_doc_ids = current_doc_ids - previous_doc_ids
            for doc_id in new_doc_ids:
                document = next(doc for doc in current_documents if doc.id == doc_id)
                await self._handle_document_created(document, db)
                
            # Detect deleted documents
            deleted_doc_ids = previous_doc_ids - current_doc_ids
            for doc_id in deleted_doc_ids:
                await self._handle_document_deleted(doc_id, db)
                
            # Check for changes in existing documents
            for document in current_documents:
                if document.id in self.document_snapshots:
                    await self._check_document_changes(document, db)
                    
            # Update snapshots
            for document in current_documents:
                snapshot = await self._create_document_snapshot(document, db)
                self.document_snapshots[document.id] = snapshot
                
            # Process pending changes
            await self._process_pending_changes(db)
            
            # Clean up old alerts and changes
            await self._cleanup_old_items()
            
        logger.debug(f"Document watching cycle completed for {len(current_documents)} documents")
        
    async def _create_document_snapshot(self, document: Document, db: AsyncSession) -> Dict[str, Any]:
        """Create a snapshot of document state for change detection."""
        snapshot = {
            "id": document.id,
            "name": document.name,
            "status": document.status,
            "document_type": document.document_type,
            "file_size": document.file_size,
            "updated_at": document.updated_at,
            "case_id": document.case_id,
            "client_id": getattr(document, 'client_id', None),
            "tags": getattr(document, 'tags', []),
            "metadata": getattr(document, 'metadata', {})
        }
        
        # Calculate content hash if possible
        if document.file_path:
            content_hash = await self._calculate_file_hash(document.file_path)
            snapshot["content_hash"] = content_hash
            
        return snapshot
        
    async def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA-256 hash of file content."""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
                
            hash_sha256 = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash for {file_path}: {str(e)}")
            return None
            
    async def _handle_document_created(self, document: Document, db: AsyncSession):
        """Handle new document creation."""
        change_id = f"create_{document.id}_{int(datetime.utcnow().timestamp())}"
        
        change = DocumentChange(
            id=change_id,
            document_id=document.id,
            case_id=document.case_id,
            change_type=ChangeType.CREATED,
            new_value=document.name,
            changed_by=getattr(document, 'created_by', None),
            change_details={
                "document_type": document.document_type,
                "file_size": document.file_size,
                "status": document.status
            }
        )
        
        self.pending_changes[change_id] = change
        logger.info(f"Detected new document: {document.name}")
        
    async def _handle_document_deleted(self, doc_id: int, db: AsyncSession):
        """Handle document deletion."""
        if doc_id not in self.document_snapshots:
            return
            
        snapshot = self.document_snapshots[doc_id]
        change_id = f"delete_{doc_id}_{int(datetime.utcnow().timestamp())}"
        
        change = DocumentChange(
            id=change_id,
            document_id=doc_id,
            case_id=snapshot.get("case_id"),
            change_type=ChangeType.DELETED,
            old_value=snapshot.get("name"),
            change_details={"snapshot": snapshot}
        )
        
        self.pending_changes[change_id] = change
        
        # Remove from snapshots
        del self.document_snapshots[doc_id]
        logger.info(f"Detected deleted document: {snapshot.get('name')}")
        
    async def _check_document_changes(self, document: Document, db: AsyncSession):
        """Check for changes in a document."""
        doc_id = document.id
        old_snapshot = self.document_snapshots[doc_id]
        new_snapshot = await self._create_document_snapshot(document, db)
        
        changes = []
        
        # Check for specific field changes
        for field in ["name", "status", "document_type", "file_size", "case_id"]:
            old_value = old_snapshot.get(field)
            new_value = new_snapshot.get(field)
            
            if old_value != new_value:
                change_type = self._determine_change_type(field, old_value, new_value)
                
                change_id = f"{field}_{doc_id}_{int(datetime.utcnow().timestamp())}"
                change = DocumentChange(
                    id=change_id,
                    document_id=doc_id,
                    case_id=document.case_id,
                    change_type=change_type,
                    old_value=old_value,
                    new_value=new_value,
                    changed_by=getattr(document, 'updated_by', None),
                    change_details={"field": field}
                )
                
                changes.append(change)
                self.pending_changes[change_id] = change
                
        # Check for content changes
        old_hash = old_snapshot.get("content_hash")
        new_hash = new_snapshot.get("content_hash")
        
        if old_hash and new_hash and old_hash != new_hash:
            change_id = f"content_{doc_id}_{int(datetime.utcnow().timestamp())}"
            change = DocumentChange(
                id=change_id,
                document_id=doc_id,
                case_id=document.case_id,
                change_type=ChangeType.MODIFIED,
                old_value=old_hash[:8],  # First 8 chars of hash
                new_value=new_hash[:8],
                changed_by=getattr(document, 'updated_by', None),
                change_details={"content_modified": True}
            )
            
            changes.append(change)
            self.pending_changes[change_id] = change
            
        if changes:
            logger.info(f"Detected {len(changes)} changes in document: {document.name}")
            
    def _determine_change_type(self, field: str, old_value: Any, new_value: Any) -> ChangeType:
        """Determine the type of change based on field and values."""
        if field == "name":
            return ChangeType.RENAMED
        elif field == "status":
            return ChangeType.STATUS_CHANGED
        elif field == "case_id":
            return ChangeType.MOVED
        elif field in ["document_type", "file_size"]:
            return ChangeType.MODIFIED
        else:
            return ChangeType.METADATA_UPDATED
            
    async def _process_pending_changes(self, db: AsyncSession):
        """Process pending changes and generate alerts."""
        for change in self.pending_changes.values():
            try:
                await self._evaluate_change_for_alerts(change, db)
            except Exception as e:
                logger.error(f"Error processing change {change.id}: {str(e)}")
                
        # Clear processed changes
        self.pending_changes.clear()
        
    async def _evaluate_change_for_alerts(self, change: DocumentChange, db: AsyncSession):
        """Evaluate if a change should generate an alert."""
        for rule in self.watch_rules:
            if not rule.is_active:
                continue
                
            if await self._change_matches_rule(change, rule, db):
                await self._generate_document_alert(change, rule, db)
                
    async def _change_matches_rule(
        self,
        change: DocumentChange,
        rule: DocumentWatchRule,
        db: AsyncSession
    ) -> bool:
        """Check if a change matches a watch rule."""
        # Check change type
        if rule.change_types and change.change_type not in rule.change_types:
            return False
            
        # Get document for additional checks
        doc_query = select(Document).where(Document.id == change.document_id)
        result = await db.execute(doc_query)
        document = result.scalar_one_or_none()
        
        if not document:
            return False
            
        # Check document type
        if rule.document_types and document.document_type not in rule.document_types:
            return False
            
        # Check scope
        if rule.scope == MonitoringScope.CASE_SPECIFIC:
            if not rule.case_ids or document.case_id not in rule.case_ids:
                return False
        elif rule.scope == MonitoringScope.CLIENT_DOCUMENTS:
            # Check if it's a client document (would need client info)
            pass
        elif rule.scope == MonitoringScope.PRIORITY_DOCUMENTS:
            # Check if document is marked as priority
            priority_types = [DocumentType.COURT_ORDER, DocumentType.JUDGMENT, DocumentType.PLEADING]
            if document.document_type not in priority_types:
                return False
                
        # Check custom conditions
        for condition_key, condition_value in rule.conditions.items():
            if condition_key == "client_uploaded":
                # Would check if document was uploaded by client
                pass
            # Add more condition checks as needed
            
        # Check cooldown period
        if await self._is_in_cooldown(change, rule):
            return False
            
        return True
        
    async def _is_in_cooldown(self, change: DocumentChange, rule: DocumentWatchRule) -> bool:
        """Check if rule is in cooldown period for this document."""
        if rule.cooldown_minutes <= 0:
            return False
            
        cutoff_time = datetime.utcnow() - timedelta(minutes=rule.cooldown_minutes)
        
        # Check for recent similar alerts
        for alert in self.active_alerts.values():
            if (alert.document_id == change.document_id and
                alert.created_at > cutoff_time):
                return True
                
        return False
        
    async def _generate_document_alert(
        self,
        change: DocumentChange,
        rule: DocumentWatchRule,
        db: AsyncSession
    ):
        """Generate an alert for a document change."""
        # Get document details
        doc_query = select(Document).options(
            joinedload(Document.case)
        ).where(Document.id == change.document_id)
        
        result = await db.execute(doc_query)
        document = result.scalar_one_or_none()
        
        if not document:
            return
            
        alert_id = f"alert_{change.document_id}_{rule.id}_{int(datetime.utcnow().timestamp())}"
        
        # Generate alert content
        alert_type, priority, message, actions = await self._generate_alert_content(
            change, document, rule
        )
        
        # Create change summary
        change_summary = await self._create_change_summary(change, document)
        
        alert = DocumentAlert(
            id=alert_id,
            document_id=change.document_id,
            case_id=change.case_id,
            document_name=document.name,
            alert_type=alert_type,
            priority=priority,
            message=message,
            change_summary=change_summary,
            recommended_actions=actions
        )
        
        self.active_alerts[alert_id] = alert
        logger.info(f"Generated document alert: {document.name} - {change.change_type}")
        
    async def _generate_alert_content(
        self,
        change: DocumentChange,
        document: Document,
        rule: DocumentWatchRule
    ) -> Tuple[str, str, str, List[str]]:
        """Generate alert content based on change and rule."""
        doc_name = document.name
        change_type = change.change_type
        
        # Determine alert type and priority
        if change_type == ChangeType.DELETED:
            alert_type = "document_deleted"
            priority = "high"
            message = f"Document '{doc_name}' has been deleted."
            actions = [
                "Verify deletion was intentional",
                "Check if backup copy exists",
                "Notify relevant team members"
            ]
            
        elif change_type == ChangeType.CREATED and document.document_type in [
            DocumentType.COURT_ORDER, DocumentType.JUDGMENT
        ]:
            alert_type = "new_court_document"
            priority = "critical"
            message = f"New court document received: '{doc_name}'"
            actions = [
                "Review document immediately",
                "Check for deadlines or requirements",
                "Notify responsible attorney",
                "Update case calendar"
            ]
            
        elif change_type == ChangeType.STATUS_CHANGED:
            alert_type = "status_change"
            priority = "medium"
            old_status = change.old_value
            new_status = change.new_value
            message = f"Document '{doc_name}' status changed from {old_status} to {new_status}."
            actions = [
                "Review status change reason",
                "Update workflow if needed",
                "Notify stakeholders"
            ]
            
        elif change_type == ChangeType.MODIFIED:
            alert_type = "document_modified"
            priority = "medium"
            message = f"Document '{doc_name}' has been modified."
            actions = [
                "Review changes made",
                "Verify version control",
                "Check if approval needed"
            ]
            
        else:
            alert_type = "document_change"
            priority = "low"
            message = f"Document '{doc_name}' has been updated ({change_type})."
            actions = ["Review document changes"]
            
        return alert_type, priority, message, actions
        
    async def _create_change_summary(self, change: DocumentChange, document: Document) -> str:
        """Create a human-readable change summary."""
        change_type = change.change_type
        doc_name = document.name
        
        if change_type == ChangeType.CREATED:
            return f"New document '{doc_name}' was added to the system."
        elif change_type == ChangeType.DELETED:
            return f"Document '{doc_name}' was removed from the system."
        elif change_type == ChangeType.MODIFIED:
            if change.change_details.get("content_modified"):
                return f"Content of '{doc_name}' was modified."
            else:
                return f"Document '{doc_name}' was updated."
        elif change_type == ChangeType.RENAMED:
            old_name = change.old_value
            return f"Document renamed from '{old_name}' to '{doc_name}'."
        elif change_type == ChangeType.STATUS_CHANGED:
            old_status = change.old_value
            new_status = change.new_value
            return f"Status of '{doc_name}' changed from {old_status} to {new_status}."
        elif change_type == ChangeType.MOVED:
            return f"Document '{doc_name}' was moved to a different case."
        else:
            return f"Document '{doc_name}' was updated ({change_type})."
            
    async def _cleanup_old_items(self):
        """Clean up old alerts and changes."""
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Clean up old alerts
        old_alert_ids = []
        for alert_id, alert in self.active_alerts.items():
            if alert.created_at < cutoff_date or alert.is_acknowledged:
                old_alert_ids.append(alert_id)
                
        for alert_id in old_alert_ids:
            del self.active_alerts[alert_id]
            
        # Clean up very old snapshots for deleted documents
        old_snapshot_ids = []
        for doc_id, snapshot in self.document_snapshots.items():
            if snapshot.get("updated_at", datetime.min) < cutoff_date:
                # Verify document still exists
                async with get_db_session() as db:
                    doc_query = select(Document).where(Document.id == doc_id)
                    result = await db.execute(doc_query)
                    if not result.scalar_one_or_none():
                        old_snapshot_ids.append(doc_id)
                        
        for doc_id in old_snapshot_ids:
            del self.document_snapshots[doc_id]
            
        if old_alert_ids or old_snapshot_ids:
            logger.info(f"Cleaned up {len(old_alert_ids)} old alerts and {len(old_snapshot_ids)} old snapshots")
            
    # Public API methods
    
    async def get_document_alerts(
        self,
        document_id: Optional[int] = None,
        case_id: Optional[int] = None,
        priority: Optional[str] = None
    ) -> List[DocumentAlert]:
        """Get document alerts with optional filtering."""
        alerts = []
        
        for alert in self.active_alerts.values():
            if alert.is_acknowledged:
                continue
                
            if document_id is not None and alert.document_id != document_id:
                continue
            if case_id is not None and alert.case_id != case_id:
                continue
            if priority is not None and alert.priority != priority:
                continue
                
            alerts.append(alert)
            
        # Sort by priority and creation time
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        alerts.sort(key=lambda x: (priority_order.get(x.priority, 4), x.created_at))
        
        return alerts
        
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge a document alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].is_acknowledged = True
            logger.info(f"Acknowledged document alert: {alert_id}")
            return True
        return False
        
    async def add_watch_rule(self, rule: DocumentWatchRule) -> bool:
        """Add a new document watch rule."""
        # Check for existing rule with same ID
        for existing_rule in self.watch_rules:
            if existing_rule.id == rule.id:
                return False
                
        self.watch_rules.append(rule)
        logger.info(f"Added document watch rule: {rule.name}")
        return True
        
    async def remove_watch_rule(self, rule_id: str) -> bool:
        """Remove a document watch rule."""
        for i, rule in enumerate(self.watch_rules):
            if rule.id == rule_id:
                del self.watch_rules[i]
                logger.info(f"Removed document watch rule: {rule_id}")
                return True
        return False
        
    async def get_watch_rules(self) -> List[DocumentWatchRule]:
        """Get all document watch rules."""
        return self.watch_rules.copy()
        
    async def analyze_document_content(self, document_id: int, db: Optional[AsyncSession] = None) -> Optional[DocumentAnalysis]:
        """Analyze document content for insights."""
        if not db:
            async with get_db_session() as db:
                return await self._analyze_document_content_impl(document_id, db)
        return await self._analyze_document_content_impl(document_id, db)
        
    async def _analyze_document_content_impl(self, document_id: int, db: AsyncSession) -> Optional[DocumentAnalysis]:
        """Implementation of document content analysis."""
        # Check cache first
        if document_id in self.content_analysis_cache:
            return self.content_analysis_cache[document_id]
            
        # Get document
        doc_query = select(Document).where(Document.id == document_id)
        result = await db.execute(doc_query)
        document = result.scalar_one_or_none()
        
        if not document or not document.file_path:
            return None
            
        try:
            # Calculate content hash
            content_hash = await self._calculate_file_hash(document.file_path)
            if not content_hash:
                return None
                
            # Perform basic analysis (would use NLP libraries in production)
            analysis = DocumentAnalysis(
                document_id=document_id,
                content_hash=content_hash,
                word_count=await self._estimate_word_count(document.file_path),
                key_terms=await self._extract_key_terms(document.file_path),
                detected_entities=await self._detect_entities(document.file_path),
                sentiment_score=await self._analyze_sentiment(document.file_path),
                complexity_score=await self._calculate_complexity(document.file_path),
                risk_indicators=await self._identify_risk_indicators(document.file_path)
            )
            
            # Cache the analysis
            self.content_analysis_cache[document_id] = analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing document {document_id}: {str(e)}")
            return None
            
    # Placeholder analysis methods (would be implemented with proper NLP libraries)
    
    async def _estimate_word_count(self, file_path: str) -> int:
        """Estimate word count in document."""
        # Placeholder implementation
        return 1000
        
    async def _extract_key_terms(self, file_path: str) -> List[str]:
        """Extract key terms from document."""
        # Placeholder implementation
        return ["contract", "agreement", "liability", "damages"]
        
    async def _detect_entities(self, file_path: str) -> List[Dict[str, Any]]:
        """Detect named entities in document."""
        # Placeholder implementation
        return [
            {"text": "John Smith", "type": "PERSON", "confidence": 0.9},
            {"text": "ABC Corporation", "type": "ORGANIZATION", "confidence": 0.8}
        ]
        
    async def _analyze_sentiment(self, file_path: str) -> Optional[float]:
        """Analyze document sentiment."""
        # Placeholder implementation
        return 0.1  # Slightly positive
        
    async def _calculate_complexity(self, file_path: str) -> Optional[float]:
        """Calculate document complexity score."""
        # Placeholder implementation
        return 0.7  # Moderately complex
        
    async def _identify_risk_indicators(self, file_path: str) -> List[str]:
        """Identify potential risk indicators in document."""
        # Placeholder implementation
        return ["liability_clause", "indemnification_required"]
        
    async def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get document monitoring statistics."""
        active_alerts = len([a for a in self.active_alerts.values() if not a.is_acknowledged])
        
        # Count alerts by priority
        alert_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for alert in self.active_alerts.values():
            if not alert.is_acknowledged:
                alert_counts[alert.priority] = alert_counts.get(alert.priority, 0) + 1
                
        return {
            "watching_status": "active" if self.is_watching else "inactive",
            "monitored_documents": len(self.document_snapshots),
            "watch_rules": len([r for r in self.watch_rules if r.is_active]),
            "active_alerts": active_alerts,
            "alert_counts": alert_counts,
            "cached_analyses": len(self.content_analysis_cache),
            "last_scan": datetime.utcnow()  # Would track actual last scan time
        }