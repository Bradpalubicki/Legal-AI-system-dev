"""
Document Comparison System
Advanced document comparison with side-by-side viewing, change tracking, and collaborative review.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
import asyncio
import json
import hashlib
import difflib
from pathlib import Path
import re


class ChangeType(str, Enum):
    ADDITION = "addition"
    DELETION = "deletion"
    MODIFICATION = "modification"
    FORMATTING = "formatting"
    MOVE = "move"
    NO_CHANGE = "no_change"


class ComparisonMode(str, Enum):
    SIDE_BY_SIDE = "side_by_side"
    INLINE = "inline"
    REDLINE = "redline"
    TRACK_CHANGES = "track_changes"
    SUMMARY_ONLY = "summary_only"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    WITHDRAWN = "withdrawn"


class CommentType(str, Enum):
    GENERAL = "general"
    SUGGESTION = "suggestion"
    REQUIRED_CHANGE = "required_change"
    QUESTION = "question"
    APPROVAL = "approval"
    REJECTION = "rejection"


@dataclass
class DocumentChange:
    change_id: str
    change_type: ChangeType
    position: int
    length: int
    original_text: str
    new_text: str
    author: str
    timestamp: datetime
    line_number: int
    confidence_score: float
    context_before: str = ""
    context_after: str = ""
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Comment:
    comment_id: str
    document_id: str
    position: int
    length: int
    text: str
    comment_type: CommentType
    author: str
    created_at: datetime
    resolved: bool = False
    parent_id: Optional[str] = None
    replies: List[str] = field(default_factory=list)
    mentioned_users: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentVersion:
    version_id: str
    document_id: str
    version_number: int
    content: str
    author: str
    created_at: datetime
    description: str
    file_hash: str
    file_size: int
    changes_from_previous: List[DocumentChange] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    is_major_version: bool = False
    parent_version_id: Optional[str] = None


@dataclass
class ComparisonResult:
    comparison_id: str
    source_document_id: str
    target_document_id: str
    source_version_id: str
    target_version_id: str
    comparison_mode: ComparisonMode
    changes: List[DocumentChange]
    summary: Dict[str, Any]
    similarity_score: float
    total_changes: int
    processing_time_ms: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"


@dataclass
class ApprovalWorkflow:
    workflow_id: str
    document_id: str
    version_id: str
    approvers: List[str]
    required_approvals: int
    current_approvals: List[Dict[str, Any]] = field(default_factory=list)
    status: ApprovalStatus = ApprovalStatus.PENDING
    deadline: Optional[datetime] = None
    instructions: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class RedlineDocument:
    redline_id: str
    original_document_id: str
    modified_document_id: str
    redline_content: str
    markup_style: str
    show_deletions: bool
    show_additions: bool
    show_formatting: bool
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"


class DocumentComparison:
    def __init__(self):
        self.versions = {}
        self.comparisons = {}
        self.comments = {}
        self.workflows = {}
        self.redlines = {}

    async def create_version(self, document_id: str, content: str, author: str,
                           description: str = "", is_major: bool = False) -> DocumentVersion:
        """Create a new document version"""
        try:
            # Generate version info
            version_number = len([v for v in self.versions.values()
                                if v.document_id == document_id]) + 1
            version_id = f"{document_id}_v{version_number}"

            # Calculate file hash
            file_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            file_size = len(content.encode('utf-8'))

            # Get previous version for change tracking
            previous_version = None
            for version in sorted(self.versions.values(),
                                key=lambda x: x.version_number, reverse=True):
                if version.document_id == document_id:
                    previous_version = version
                    break

            # Calculate changes from previous version
            changes = []
            if previous_version:
                changes = await self._calculate_changes(
                    previous_version.content, content, author
                )

            version = DocumentVersion(
                version_id=version_id,
                document_id=document_id,
                version_number=version_number,
                content=content,
                author=author,
                created_at=datetime.utcnow(),
                description=description,
                file_hash=file_hash,
                file_size=file_size,
                changes_from_previous=changes,
                is_major_version=is_major,
                parent_version_id=previous_version.version_id if previous_version else None
            )

            self.versions[version_id] = version
            return version

        except Exception as e:
            print(f"Error creating version: {e}")
            raise

    async def _calculate_changes(self, old_content: str, new_content: str,
                               author: str) -> List[DocumentChange]:
        """Calculate changes between two document versions"""
        try:
            changes = []

            # Split into lines for comparison
            old_lines = old_content.splitlines()
            new_lines = new_content.splitlines()

            # Use difflib to get differences
            diff = difflib.unified_diff(old_lines, new_lines, lineterm='')

            change_id_counter = 0
            for line in diff:
                if line.startswith('@@'):
                    # Parse line number info
                    continue
                elif line.startswith('-'):
                    # Deletion
                    change_id_counter += 1
                    changes.append(DocumentChange(
                        change_id=f"change_{change_id_counter}",
                        change_type=ChangeType.DELETION,
                        position=0,  # Would calculate actual position
                        length=len(line[1:]),
                        original_text=line[1:],
                        new_text="",
                        author=author,
                        timestamp=datetime.utcnow(),
                        line_number=0,  # Would calculate actual line
                        confidence_score=0.95
                    ))
                elif line.startswith('+'):
                    # Addition
                    change_id_counter += 1
                    changes.append(DocumentChange(
                        change_id=f"change_{change_id_counter}",
                        change_type=ChangeType.ADDITION,
                        position=0,  # Would calculate actual position
                        length=len(line[1:]),
                        original_text="",
                        new_text=line[1:],
                        author=author,
                        timestamp=datetime.utcnow(),
                        line_number=0,  # Would calculate actual line
                        confidence_score=0.95
                    ))

            return changes

        except Exception as e:
            print(f"Error calculating changes: {e}")
            return []

    async def compare_documents(self, source_doc_id: str, target_doc_id: str,
                              source_version: Optional[str] = None,
                              target_version: Optional[str] = None,
                              mode: ComparisonMode = ComparisonMode.SIDE_BY_SIDE) -> ComparisonResult:
        """Compare two documents or versions"""
        try:
            start_time = datetime.utcnow()

            # Get document versions
            source_version_obj = await self._get_document_version(source_doc_id, source_version)
            target_version_obj = await self._get_document_version(target_doc_id, target_version)

            if not source_version_obj or not target_version_obj:
                raise ValueError("Could not find specified document versions")

            # Calculate changes
            changes = await self._calculate_changes(
                source_version_obj.content,
                target_version_obj.content,
                "system"
            )

            # Calculate similarity score
            similarity = await self._calculate_similarity(
                source_version_obj.content,
                target_version_obj.content
            )

            # Generate summary
            summary = await self._generate_comparison_summary(changes)

            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000

            # Create comparison result
            comparison_id = f"comp_{int(start_time.timestamp())}"
            result = ComparisonResult(
                comparison_id=comparison_id,
                source_document_id=source_doc_id,
                target_document_id=target_doc_id,
                source_version_id=source_version_obj.version_id,
                target_version_id=target_version_obj.version_id,
                comparison_mode=mode,
                changes=changes,
                summary=summary,
                similarity_score=similarity,
                total_changes=len(changes),
                processing_time_ms=processing_time
            )

            self.comparisons[comparison_id] = result
            return result

        except Exception as e:
            print(f"Error comparing documents: {e}")
            raise

    async def _get_document_version(self, doc_id: str,
                                  version_id: Optional[str] = None) -> Optional[DocumentVersion]:
        """Get a specific document version"""
        if version_id:
            return self.versions.get(version_id)

        # Get latest version
        latest_version = None
        max_version_num = 0

        for version in self.versions.values():
            if (version.document_id == doc_id and
                version.version_number > max_version_num):
                max_version_num = version.version_number
                latest_version = version

        return latest_version

    async def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity score between two documents"""
        try:
            # Simple similarity calculation using difflib
            similarity = difflib.SequenceMatcher(None, content1, content2).ratio()
            return similarity
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0

    async def _generate_comparison_summary(self, changes: List[DocumentChange]) -> Dict[str, Any]:
        """Generate summary of changes"""
        try:
            summary = {
                "total_changes": len(changes),
                "additions": len([c for c in changes if c.change_type == ChangeType.ADDITION]),
                "deletions": len([c for c in changes if c.change_type == ChangeType.DELETION]),
                "modifications": len([c for c in changes if c.change_type == ChangeType.MODIFICATION]),
                "formatting_changes": len([c for c in changes if c.change_type == ChangeType.FORMATTING]),
                "major_changes": len([c for c in changes if c.confidence_score < 0.8]),
                "minor_changes": len([c for c in changes if c.confidence_score >= 0.8]),
                "change_distribution": self._calculate_change_distribution(changes),
                "most_changed_sections": self._identify_most_changed_sections(changes)
            }

            return summary

        except Exception as e:
            print(f"Error generating summary: {e}")
            return {}

    def _calculate_change_distribution(self, changes: List[DocumentChange]) -> Dict[str, int]:
        """Calculate distribution of changes across document"""
        # Simplified distribution calculation
        return {
            "beginning": len([c for c in changes if c.position < 1000]),
            "middle": len([c for c in changes if 1000 <= c.position < 2000]),
            "end": len([c for c in changes if c.position >= 2000])
        }

    def _identify_most_changed_sections(self, changes: List[DocumentChange]) -> List[Dict[str, Any]]:
        """Identify sections with the most changes"""
        # Group changes by approximate section
        sections = {}
        for change in changes[:5]:  # Limit to top 5 for demo
            section_key = f"section_{change.position // 500}"
            if section_key not in sections:
                sections[section_key] = {
                    "section": section_key,
                    "change_count": 0,
                    "sample_change": change.new_text[:50] + "..." if len(change.new_text) > 50 else change.new_text
                }
            sections[section_key]["change_count"] += 1

        return list(sections.values())

    async def add_comment(self, document_id: str, position: int, length: int,
                         text: str, comment_type: CommentType, author: str,
                         parent_id: Optional[str] = None) -> Comment:
        """Add a comment to a document"""
        try:
            comment_id = f"comment_{len(self.comments) + 1}"

            comment = Comment(
                comment_id=comment_id,
                document_id=document_id,
                position=position,
                length=length,
                text=text,
                comment_type=comment_type,
                author=author,
                created_at=datetime.utcnow(),
                parent_id=parent_id
            )

            self.comments[comment_id] = comment

            # If this is a reply, add to parent's replies
            if parent_id and parent_id in self.comments:
                self.comments[parent_id].replies.append(comment_id)

            return comment

        except Exception as e:
            print(f"Error adding comment: {e}")
            raise

    async def create_approval_workflow(self, document_id: str, version_id: str,
                                     approvers: List[str], required_approvals: int,
                                     deadline: Optional[datetime] = None,
                                     instructions: str = "") -> ApprovalWorkflow:
        """Create an approval workflow for a document version"""
        try:
            workflow_id = f"workflow_{len(self.workflows) + 1}"

            workflow = ApprovalWorkflow(
                workflow_id=workflow_id,
                document_id=document_id,
                version_id=version_id,
                approvers=approvers,
                required_approvals=required_approvals,
                deadline=deadline,
                instructions=instructions
            )

            self.workflows[workflow_id] = workflow
            return workflow

        except Exception as e:
            print(f"Error creating approval workflow: {e}")
            raise

    async def submit_approval(self, workflow_id: str, approver: str,
                            approved: bool, comments: str = "") -> bool:
        """Submit an approval decision"""
        try:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                raise ValueError("Workflow not found")

            if approver not in workflow.approvers:
                raise ValueError("User not authorized to approve")

            # Check if already approved by this user
            existing_approval = next(
                (a for a in workflow.current_approvals if a["approver"] == approver),
                None
            )

            if existing_approval:
                raise ValueError("User has already provided approval")

            # Add approval
            approval = {
                "approver": approver,
                "approved": approved,
                "comments": comments,
                "timestamp": datetime.utcnow().isoformat()
            }

            workflow.current_approvals.append(approval)

            # Update workflow status
            approved_count = len([a for a in workflow.current_approvals if a["approved"]])
            rejected_count = len([a for a in workflow.current_approvals if not a["approved"]])

            if approved_count >= workflow.required_approvals:
                workflow.status = ApprovalStatus.APPROVED
                workflow.completed_at = datetime.utcnow()
            elif rejected_count > 0:
                workflow.status = ApprovalStatus.REJECTED
                workflow.completed_at = datetime.utcnow()

            return True

        except Exception as e:
            print(f"Error submitting approval: {e}")
            return False

    async def generate_redline(self, original_doc_id: str, modified_doc_id: str,
                             markup_style: str = "track_changes",
                             show_deletions: bool = True,
                             show_additions: bool = True,
                             show_formatting: bool = True) -> RedlineDocument:
        """Generate a redline document showing changes"""
        try:
            # Get document versions
            original_version = await self._get_document_version(original_doc_id)
            modified_version = await self._get_document_version(modified_doc_id)

            if not original_version or not modified_version:
                raise ValueError("Could not find specified documents")

            # Compare documents
            comparison = await self.compare_documents(
                original_doc_id, modified_doc_id,
                mode=ComparisonMode.REDLINE
            )

            # Generate redline content
            redline_content = await self._generate_redline_content(
                original_version.content,
                modified_version.content,
                comparison.changes,
                markup_style,
                show_deletions,
                show_additions,
                show_formatting
            )

            redline_id = f"redline_{len(self.redlines) + 1}"
            redline = RedlineDocument(
                redline_id=redline_id,
                original_document_id=original_doc_id,
                modified_document_id=modified_doc_id,
                redline_content=redline_content,
                markup_style=markup_style,
                show_deletions=show_deletions,
                show_additions=show_additions,
                show_formatting=show_formatting
            )

            self.redlines[redline_id] = redline
            return redline

        except Exception as e:
            print(f"Error generating redline: {e}")
            raise

    async def _generate_redline_content(self, original: str, modified: str,
                                      changes: List[DocumentChange],
                                      markup_style: str,
                                      show_deletions: bool,
                                      show_additions: bool,
                                      show_formatting: bool) -> str:
        """Generate redline markup content"""
        try:
            if markup_style == "track_changes":
                # Generate track changes style markup
                redline_content = modified

                for change in sorted(changes, key=lambda x: x.position, reverse=True):
                    if change.change_type == ChangeType.DELETION and show_deletions:
                        # Mark deletions
                        markup = f'<del style="color: red; text-decoration: line-through;">{change.original_text}</del>'
                        redline_content = redline_content[:change.position] + markup + redline_content[change.position:]

                    elif change.change_type == ChangeType.ADDITION and show_additions:
                        # Mark additions
                        markup = f'<ins style="color: blue; text-decoration: underline;">{change.new_text}</ins>'
                        redline_content = redline_content[:change.position] + markup + redline_content[change.position + change.length:]

            elif markup_style == "simple":
                # Generate simple markup
                redline_content = modified
                for change in changes:
                    if change.change_type == ChangeType.DELETION and show_deletions:
                        redline_content = redline_content.replace(
                            change.original_text,
                            f"[DELETED: {change.original_text}]"
                        )
                    elif change.change_type == ChangeType.ADDITION and show_additions:
                        redline_content = redline_content.replace(
                            change.new_text,
                            f"[ADDED: {change.new_text}]"
                        )
            else:
                # Default to modified content
                redline_content = modified

            return redline_content

        except Exception as e:
            print(f"Error generating redline content: {e}")
            return modified

    async def get_document_history(self, document_id: str) -> List[DocumentVersion]:
        """Get complete version history for a document"""
        try:
            versions = [v for v in self.versions.values() if v.document_id == document_id]
            return sorted(versions, key=lambda x: x.version_number)
        except Exception as e:
            print(f"Error getting document history: {e}")
            return []

    async def get_comments(self, document_id: str, include_resolved: bool = False) -> List[Comment]:
        """Get all comments for a document"""
        try:
            comments = [c for c in self.comments.values() if c.document_id == document_id]

            if not include_resolved:
                comments = [c for c in comments if not c.resolved]

            return sorted(comments, key=lambda x: x.created_at)
        except Exception as e:
            print(f"Error getting comments: {e}")
            return []

    async def resolve_comment(self, comment_id: str, resolver: str) -> bool:
        """Resolve a comment"""
        try:
            comment = self.comments.get(comment_id)
            if not comment:
                return False

            comment.resolved = True
            comment.metadata["resolved_by"] = resolver
            comment.metadata["resolved_at"] = datetime.utcnow().isoformat()

            return True
        except Exception as e:
            print(f"Error resolving comment: {e}")
            return False

    async def get_comparison_summary(self) -> Dict[str, Any]:
        """Get summary of all comparisons and activity"""
        try:
            return {
                "total_versions": len(self.versions),
                "total_comparisons": len(self.comparisons),
                "total_comments": len(self.comments),
                "active_workflows": len([w for w in self.workflows.values()
                                       if w.status == ApprovalStatus.PENDING]),
                "total_redlines": len(self.redlines),
                "recent_activity": await self._get_recent_activity()
            }
        except Exception as e:
            print(f"Error getting comparison summary: {e}")
            return {}

    async def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent activity across the system"""
        try:
            activities = []

            # Add recent versions
            for version in sorted(self.versions.values(),
                                key=lambda x: x.created_at, reverse=True)[:5]:
                activities.append({
                    "type": "version_created",
                    "timestamp": version.created_at.isoformat(),
                    "author": version.author,
                    "description": f"Version {version.version_number} created"
                })

            # Add recent comments
            for comment in sorted(self.comments.values(),
                                key=lambda x: x.created_at, reverse=True)[:5]:
                activities.append({
                    "type": "comment_added",
                    "timestamp": comment.created_at.isoformat(),
                    "author": comment.author,
                    "description": f"Comment added: {comment.text[:50]}..."
                })

            return sorted(activities, key=lambda x: x["timestamp"], reverse=True)[:10]

        except Exception as e:
            print(f"Error getting recent activity: {e}")
            return []


# Global instance
document_comparison = DocumentComparison()


# FastAPI endpoints configuration
async def get_comparison_endpoints():
    """Return FastAPI endpoint configurations for document comparison"""
    return [
        {
            "path": "/documents/versions",
            "method": "POST",
            "handler": "create_document_version",
            "description": "Create new document version"
        },
        {
            "path": "/documents/{doc_id}/versions",
            "method": "GET",
            "handler": "get_document_history",
            "description": "Get document version history"
        },
        {
            "path": "/documents/compare",
            "method": "POST",
            "handler": "compare_documents",
            "description": "Compare two documents"
        },
        {
            "path": "/documents/{doc_id}/comments",
            "method": "GET",
            "handler": "get_document_comments",
            "description": "Get document comments"
        },
        {
            "path": "/documents/comments",
            "method": "POST",
            "handler": "add_document_comment",
            "description": "Add comment to document"
        },
        {
            "path": "/documents/comments/{comment_id}/resolve",
            "method": "PUT",
            "handler": "resolve_document_comment",
            "description": "Resolve document comment"
        },
        {
            "path": "/documents/workflows",
            "method": "POST",
            "handler": "create_approval_workflow",
            "description": "Create approval workflow"
        },
        {
            "path": "/documents/workflows/{workflow_id}/approve",
            "method": "POST",
            "handler": "submit_workflow_approval",
            "description": "Submit approval decision"
        },
        {
            "path": "/documents/redline",
            "method": "POST",
            "handler": "generate_document_redline",
            "description": "Generate redline document"
        },
        {
            "path": "/documents/comparison/summary",
            "method": "GET",
            "handler": "get_comparison_system_summary",
            "description": "Get comparison system summary"
        }
    ]


async def initialize_document_comparison():
    """Initialize the document comparison system"""
    print("Document Comparison System initialized successfully")
    print(f"Available endpoints: {len(await get_comparison_endpoints())}")
    return True