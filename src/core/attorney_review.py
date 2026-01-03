#!/usr/bin/env python3
"""
Attorney Review System
Legal AI System - Comprehensive Attorney Review and UPL Prevention

This module ensures all AI outputs are properly reviewed and flagged
for attorney oversight to prevent Unauthorized Practice of Law (UPL).
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

# Setup logging
logger = logging.getLogger('attorney_review')

class ReviewStatus(str, Enum):
    """Attorney review status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVISION = "requires_revision"
    ESCALATED = "escalated"

class ReviewPriority(str, Enum):
    """Review priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class UPLRisk(str, Enum):
    """UPL (Unauthorized Practice of Law) risk levels"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ReviewFlag:
    """Attorney review flag"""
    flag_id: str
    content_id: str
    flag_type: str
    risk_level: UPLRisk
    priority: ReviewPriority
    description: str
    flagged_content: str
    reviewer_notes: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    status: ReviewStatus = ReviewStatus.PENDING

@dataclass
class AttorneyReviewResult:
    """Result of attorney review process"""
    content_approved: bool
    flags_raised: List[ReviewFlag]
    review_required: bool
    upl_risk_score: float
    recommendations: List[str]
    auto_approved: bool = False

class AttorneyReviewSystem:
    """
    Comprehensive attorney review and UPL prevention system
    Ensures all AI-generated legal content is properly reviewed
    """

    def __init__(self):
        self.logger = logger
        self.review_flags: List[ReviewFlag] = []

        # UPL risk patterns
        self.high_risk_patterns = [
            r'\blegal advice\b',
            r'\brecommend.*action\b',
            r'\byou should.*do\b',
            r'\bmust.*file\b',
            r'\badvise.*to\b',
            r'\bas your attorney\b',
            r'\bin my legal opinion\b',
            r'\blegal counsel\b'
        ]

        # Content requiring mandatory review
        self.mandatory_review_patterns = [
            r'\bcontract\b.*\bterm',
            r'\blitigation\b.*\bstrategy\b',
            r'\bcourt\b.*\bfiling\b',
            r'\bstatute.*limitation\b',
            r'\bjurisdiction\b',
            r'\bbar.*admission\b',
            r'\bprofessional.*responsibility\b'
        ]

        # Auto-approval safe patterns
        self.safe_patterns = [
            r'\bfor.*educational.*purposes\b',
            r'\bdoes.*not.*constitute.*legal.*advice\b',
            r'\bconsult.*qualified.*attorney\b',
            r'\bgeneral.*information.*only\b'
        ]

    def review_content(self, content: str, content_id: str = None,
                      jurisdiction: str = None) -> AttorneyReviewResult:
        """
        Comprehensive review of AI-generated content for UPL compliance
        """
        content_id = content_id or f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        flags_raised = []
        recommendations = []

        # Calculate UPL risk score
        upl_risk_score = self._calculate_upl_risk(content)

        # Check for high-risk patterns
        high_risk_flags = self._check_high_risk_patterns(content, content_id)
        flags_raised.extend(high_risk_flags)

        # Check for mandatory review requirements
        mandatory_flags = self._check_mandatory_review(content, content_id)
        flags_raised.extend(mandatory_flags)

        # Check jurisdiction-specific requirements
        if jurisdiction:
            jurisdiction_flags = self._check_jurisdiction_requirements(content, content_id, jurisdiction)
            flags_raised.extend(jurisdiction_flags)

        # Determine if auto-approval is possible
        auto_approved = self._can_auto_approve(content, flags_raised)

        # Generate recommendations
        recommendations = self._generate_recommendations(content, flags_raised, upl_risk_score)

        # Determine review requirements
        review_required = (
            upl_risk_score >= 0.5 or
            len(flags_raised) > 0 or
            not auto_approved
        )

        # Content approval decision
        content_approved = auto_approved and not review_required

        # Store flags for tracking
        self.review_flags.extend(flags_raised)

        # Log review decision
        self.logger.info(f"Content review completed: {content_id}, "
                        f"Risk: {upl_risk_score:.2f}, "
                        f"Flags: {len(flags_raised)}, "
                        f"Approved: {content_approved}")

        return AttorneyReviewResult(
            content_approved=content_approved,
            flags_raised=flags_raised,
            review_required=review_required,
            upl_risk_score=upl_risk_score,
            recommendations=recommendations,
            auto_approved=auto_approved
        )

    def _calculate_upl_risk(self, content: str) -> float:
        """Calculate UPL risk score (0.0 to 1.0)"""
        import re

        risk_score = 0.0
        content_lower = content.lower()

        # High-risk patterns (0.3 each)
        for pattern in self.high_risk_patterns:
            if re.search(pattern, content_lower):
                risk_score += 0.3

        # Lack of disclaimers increases risk
        disclaimer_patterns = [
            r'educational.*purposes',
            r'not.*legal.*advice',
            r'consult.*attorney'
        ]

        has_disclaimers = any(re.search(pattern, content_lower) for pattern in disclaimer_patterns)
        if not has_disclaimers:
            risk_score += 0.4

        # Length and complexity factor
        if len(content) > 1000:  # Long content needs more scrutiny
            risk_score += 0.1

        return min(risk_score, 1.0)

    def _check_high_risk_patterns(self, content: str, content_id: str) -> List[ReviewFlag]:
        """Check for high-risk UPL patterns"""
        import re
        flags = []

        for i, pattern in enumerate(self.high_risk_patterns):
            if re.search(pattern, content, re.IGNORECASE):
                flag = ReviewFlag(
                    flag_id=f"high_risk_{content_id}_{i}",
                    content_id=content_id,
                    flag_type="high_risk_upl",
                    risk_level=UPLRisk.HIGH,
                    priority=ReviewPriority.URGENT,
                    description=f"High-risk UPL pattern detected: {pattern}",
                    flagged_content=content[:200] + "..." if len(content) > 200 else content,
                    reviewer_notes="Requires immediate attorney review",
                    created_at=datetime.now()
                )
                flags.append(flag)

        return flags

    def _check_mandatory_review(self, content: str, content_id: str) -> List[ReviewFlag]:
        """Check for content requiring mandatory attorney review"""
        import re
        flags = []

        for i, pattern in enumerate(self.mandatory_review_patterns):
            if re.search(pattern, content, re.IGNORECASE):
                flag = ReviewFlag(
                    flag_id=f"mandatory_{content_id}_{i}",
                    content_id=content_id,
                    flag_type="mandatory_review",
                    risk_level=UPLRisk.MEDIUM,
                    priority=ReviewPriority.HIGH,
                    description=f"Mandatory review required: {pattern}",
                    flagged_content=content[:200] + "..." if len(content) > 200 else content,
                    reviewer_notes="Content type requires attorney review",
                    created_at=datetime.now()
                )
                flags.append(flag)

        return flags

    def _check_jurisdiction_requirements(self, content: str, content_id: str, jurisdiction: str) -> List[ReviewFlag]:
        """Check jurisdiction-specific requirements"""
        flags = []

        # Jurisdiction-specific patterns
        jurisdiction_patterns = {
            'california': [r'\bcalifornia.*law\b', r'\bstate.*bar.*california\b'],
            'new_york': [r'\bnew.*york.*law\b', r'\bnysba\b'],
            'federal': [r'\bfederal.*court\b', r'\bfederal.*law\b']
        }

        patterns = jurisdiction_patterns.get(jurisdiction.lower(), [])

        for i, pattern in enumerate(patterns):
            if re.search(pattern, content, re.IGNORECASE):
                flag = ReviewFlag(
                    flag_id=f"jurisdiction_{content_id}_{i}",
                    content_id=content_id,
                    flag_type="jurisdiction_specific",
                    risk_level=UPLRisk.MEDIUM,
                    priority=ReviewPriority.MEDIUM,
                    description=f"Jurisdiction-specific content detected: {jurisdiction}",
                    flagged_content=content[:200] + "..." if len(content) > 200 else content,
                    reviewer_notes=f"Requires review by {jurisdiction} licensed attorney",
                    created_at=datetime.now()
                )
                flags.append(flag)

        return flags

    def _can_auto_approve(self, content: str, flags: List[ReviewFlag]) -> bool:
        """Determine if content can be auto-approved"""
        import re

        # Cannot auto-approve if there are high-risk flags
        if any(flag.risk_level in [UPLRisk.HIGH, UPLRisk.CRITICAL] for flag in flags):
            return False

        # Must have safe patterns for auto-approval
        has_safe_patterns = any(re.search(pattern, content, re.IGNORECASE)
                               for pattern in self.safe_patterns)

        return has_safe_patterns and len(flags) == 0

    def _generate_recommendations(self, content: str, flags: List[ReviewFlag], risk_score: float) -> List[str]:
        """Generate recommendations for content improvement"""
        recommendations = []

        if risk_score > 0.7:
            recommendations.append("High UPL risk detected - mandatory attorney review required")

        if not any(re.search(r'educational.*purposes', content, re.IGNORECASE)):
            recommendations.append("Add educational purposes disclaimer")

        if not any(re.search(r'not.*legal.*advice', content, re.IGNORECASE)):
            recommendations.append("Add 'not legal advice' disclaimer")

        if not any(re.search(r'consult.*attorney', content, re.IGNORECASE)):
            recommendations.append("Add recommendation to consult qualified attorney")

        if len(flags) > 0:
            recommendations.append("Address flagged content before publication")

        if risk_score > 0.3:
            recommendations.append("Consider additional disclaimers and limitations")

        return recommendations

    def get_pending_reviews(self) -> List[ReviewFlag]:
        """Get all pending attorney reviews"""
        return [flag for flag in self.review_flags if flag.status == ReviewStatus.PENDING]

    def approve_content(self, flag_id: str, reviewer_notes: str = "") -> bool:
        """Approve flagged content"""
        for flag in self.review_flags:
            if flag.flag_id == flag_id:
                flag.status = ReviewStatus.APPROVED
                flag.reviewed_at = datetime.now()
                flag.reviewer_notes += f" | APPROVED: {reviewer_notes}"
                self.logger.info(f"Content approved: {flag_id}")
                return True
        return False

    def reject_content(self, flag_id: str, reviewer_notes: str = "") -> bool:
        """Reject flagged content"""
        for flag in self.review_flags:
            if flag.flag_id == flag_id:
                flag.status = ReviewStatus.REJECTED
                flag.reviewed_at = datetime.now()
                flag.reviewer_notes += f" | REJECTED: {reviewer_notes}"
                self.logger.info(f"Content rejected: {flag_id}")
                return True
        return False

    def get_review_statistics(self) -> Dict[str, Any]:
        """Get attorney review system statistics"""
        total_flags = len(self.review_flags)

        if total_flags == 0:
            return {
                "total_reviews": 0,
                "pending": 0,
                "approved": 0,
                "rejected": 0,
                "approval_rate": 0,
                "average_risk_score": 0
            }

        pending = len([f for f in self.review_flags if f.status == ReviewStatus.PENDING])
        approved = len([f for f in self.review_flags if f.status == ReviewStatus.APPROVED])
        rejected = len([f for f in self.review_flags if f.status == ReviewStatus.REJECTED])

        approval_rate = (approved / total_flags) * 100 if total_flags > 0 else 0

        return {
            "total_reviews": total_flags,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "approval_rate": approval_rate,
            "high_risk_flags": len([f for f in self.review_flags if f.risk_level == UPLRisk.HIGH])
        }

# Global attorney review system
attorney_review_system = AttorneyReviewSystem()

def review_ai_output(content: str, content_id: str = None, jurisdiction: str = None) -> AttorneyReviewResult:
    """Global function to review AI output for UPL compliance"""
    return attorney_review_system.review_content(content, content_id, jurisdiction)

def flag_for_attorney_review(content: str, reason: str = "Manual review requested") -> ReviewFlag:
    """Manually flag content for attorney review"""
    content_id = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    flag = ReviewFlag(
        flag_id=f"manual_{content_id}",
        content_id=content_id,
        flag_type="manual_flag",
        risk_level=UPLRisk.MEDIUM,
        priority=ReviewPriority.MEDIUM,
        description=reason,
        flagged_content=content[:200] + "..." if len(content) > 200 else content,
        reviewer_notes="Manual flag for attorney review",
        created_at=datetime.now()
    )

    attorney_review_system.review_flags.append(flag)
    return flag

# Example usage and testing
if __name__ == "__main__":
    # Test the attorney review system
    review_system = AttorneyReviewSystem()

    test_content = [
        "This information is for educational purposes only and does not constitute legal advice.",
        "You should definitely file a lawsuit against your employer.",
        "Contract terms typically include provisions for termination and dispute resolution.",
        "As your attorney, I recommend taking immediate legal action."
    ]

    print("Attorney Review System Test Results:")
    print("=" * 60)

    for i, content in enumerate(test_content):
        result = review_system.review_content(content, f"test_{i}")
        print(f"\nContent {i+1}: {content[:50]}...")
        print(f"Approved: {result.content_approved}")
        print(f"Review Required: {result.review_required}")
        print(f"UPL Risk Score: {result.upl_risk_score:.2f}")
        print(f"Flags: {len(result.flags_raised)}")
        print(f"Auto-approved: {result.auto_approved}")
        if result.recommendations:
            print(f"Recommendations: {', '.join(result.recommendations[:2])}")

    print(f"\nSystem Statistics:")
    stats = review_system.get_review_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")