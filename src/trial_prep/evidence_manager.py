"""
Evidence Management System

Comprehensive evidence management system for trial preparation including
evidence tracking, authenticity verification, chain of custody, and 
automated exhibit preparation.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class EvidenceType(Enum):
    """Types of evidence that can be managed."""
    DOCUMENT = "document"
    PHOTOGRAPH = "photograph" 
    VIDEO = "video"
    AUDIO = "audio"
    PHYSICAL = "physical"
    DIGITAL = "digital"
    TESTIMONY = "testimony"
    EXPERT_REPORT = "expert_report"
    CORRESPONDENCE = "correspondence"
    CONTRACT = "contract"
    FINANCIAL = "financial"
    MEDICAL = "medical"
    ELECTRONIC = "electronic"

class EvidenceStatus(Enum):
    """Status of evidence in preparation process."""
    COLLECTED = "collected"
    UNDER_REVIEW = "under_review"
    AUTHENTICATED = "authenticated"
    ADMITTED = "admitted"
    EXCLUDED = "excluded"
    PENDING_FOUNDATION = "pending_foundation"
    OBJECTED = "objected"
    RESERVED = "reserved"

class AuthenticityLevel(Enum):
    """Level of authenticity verification."""
    UNVERIFIED = "unverified"
    BASIC_VERIFIED = "basic_verified"
    EXPERT_VERIFIED = "expert_verified"
    COURT_CERTIFIED = "court_certified"
    FORENSIC_VERIFIED = "forensic_verified"

class RelevanceScore(Enum):
    """Relevance scoring for evidence items."""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    MINIMAL = 1

@dataclass
class CustodyEntry:
    """Single entry in chain of custody."""
    timestamp: datetime
    person: str
    organization: str
    action: str
    location: str
    purpose: str
    signature_hash: str
    witness: Optional[str] = None
    notes: Optional[str] = None

@dataclass
class FoundationElement:
    """Elements needed to establish foundation for evidence."""
    element_type: str
    description: str
    witness_required: Optional[str] = None
    documentation_needed: List[str] = field(default_factory=list)
    met: bool = False
    notes: Optional[str] = None

@dataclass
class EvidenceItem:
    """Individual evidence item with full metadata and tracking."""
    evidence_id: str
    evidence_type: EvidenceType
    title: str
    description: str
    source: str
    date_created: datetime
    date_collected: datetime
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    
    # Status and authentication
    status: EvidenceStatus = EvidenceStatus.COLLECTED
    authenticity_level: AuthenticityLevel = AuthenticityLevel.UNVERIFIED
    relevance_score: RelevanceScore = RelevanceScore.MEDIUM
    
    # Chain of custody
    custody_chain: List[CustodyEntry] = field(default_factory=list)
    current_custodian: Optional[str] = None
    
    # Legal foundation
    foundation_elements: List[FoundationElement] = field(default_factory=list)
    foundation_complete: bool = False
    foundation_witness: Optional[str] = None
    
    # Trial preparation
    exhibit_number: Optional[str] = None
    exhibit_prepared: bool = False
    demonstrative: bool = False
    
    # Metadata and tags
    tags: Set[str] = field(default_factory=set)
    case_relevance: str = ""
    opposing_arguments: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    related_witnesses: List[str] = field(default_factory=list)
    
    # Technical metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_by: str = ""
    last_modified: datetime = field(default_factory=datetime.now)
    notes: List[str] = field(default_factory=list)

@dataclass 
class EvidenceChain:
    """Chain of related evidence items forming a narrative."""
    chain_id: str
    title: str
    description: str
    evidence_items: List[str] = field(default_factory=list)  # Evidence IDs
    narrative_order: List[str] = field(default_factory=list)  # Ordered evidence IDs
    strength_assessment: float = 0.0
    gaps_identified: List[str] = field(default_factory=list)
    corroborating_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    created_by: str = ""

class EvidenceAnalyzer:
    """Analyzes evidence for patterns, gaps, and strategic value."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".EvidenceAnalyzer")
    
    def analyze_evidence_strength(self, evidence: EvidenceItem) -> Dict[str, Any]:
        """Analyze the strength and admissibility of evidence."""
        analysis = {
            'admissibility_score': 0.0,
            'reliability_score': 0.0,
            'persuasiveness_score': 0.0,
            'foundation_issues': [],
            'authenticity_concerns': [],
            'hearsay_issues': [],
            'privilege_concerns': [],
            'recommendations': []
        }
        
        # Calculate admissibility score
        admissibility_factors = []
        
        # Foundation completeness
        if evidence.foundation_complete:
            admissibility_factors.append(0.3)
        else:
            analysis['foundation_issues'].append("Foundation elements incomplete")
        
        # Authentication level
        auth_scores = {
            AuthenticityLevel.UNVERIFIED: 0.1,
            AuthenticityLevel.BASIC_VERIFIED: 0.4,
            AuthenticityLevel.EXPERT_VERIFIED: 0.7,
            AuthenticityLevel.COURT_CERTIFIED: 0.9,
            AuthenticityLevel.FORENSIC_VERIFIED: 1.0
        }
        admissibility_factors.append(auth_scores.get(evidence.authenticity_level, 0.1) * 0.3)
        
        # Chain of custody integrity
        if len(evidence.custody_chain) > 0:
            admissibility_factors.append(0.2)
        else:
            analysis['authenticity_concerns'].append("No chain of custody established")
        
        # Evidence type considerations
        type_reliability = {
            EvidenceType.DOCUMENT: 0.8,
            EvidenceType.PHOTOGRAPH: 0.7,
            EvidenceType.VIDEO: 0.9,
            EvidenceType.AUDIO: 0.6,
            EvidenceType.PHYSICAL: 0.9,
            EvidenceType.DIGITAL: 0.5,
            EvidenceType.TESTIMONY: 0.4,
            EvidenceType.EXPERT_REPORT: 0.8,
            EvidenceType.CORRESPONDENCE: 0.7,
            EvidenceType.CONTRACT: 0.9,
            EvidenceType.FINANCIAL: 0.8,
            EvidenceType.MEDICAL: 0.8,
            EvidenceType.ELECTRONIC: 0.4
        }
        admissibility_factors.append(type_reliability.get(evidence.evidence_type, 0.5) * 0.2)
        
        analysis['admissibility_score'] = sum(admissibility_factors)
        
        # Calculate reliability score based on source and verification
        reliability_factors = []
        
        # Source credibility (simplified scoring)
        if "official" in evidence.source.lower() or "government" in evidence.source.lower():
            reliability_factors.append(0.4)
        elif "expert" in evidence.source.lower() or "professional" in evidence.source.lower():
            reliability_factors.append(0.3)
        else:
            reliability_factors.append(0.2)
        
        # File integrity (if digital)
        if evidence.file_hash:
            reliability_factors.append(0.3)
        
        # Supporting evidence
        if evidence.supporting_evidence:
            reliability_factors.append(min(len(evidence.supporting_evidence) * 0.1, 0.3))
        
        analysis['reliability_score'] = sum(reliability_factors)
        
        # Calculate persuasiveness score
        persuasiveness_factors = []
        
        # Relevance score impact
        relevance_scores = {
            RelevanceScore.CRITICAL: 0.4,
            RelevanceScore.HIGH: 0.3,
            RelevanceScore.MEDIUM: 0.2,
            RelevanceScore.LOW: 0.1,
            RelevanceScore.MINIMAL: 0.05
        }
        persuasiveness_factors.append(relevance_scores.get(evidence.relevance_score, 0.2))
        
        # Corroboration
        if len(evidence.supporting_evidence) > 2:
            persuasiveness_factors.append(0.2)
        elif len(evidence.supporting_evidence) > 0:
            persuasiveness_factors.append(0.1)
        
        # Visual/demonstrative impact
        if evidence.demonstrative or evidence.evidence_type in [
            EvidenceType.PHOTOGRAPH, EvidenceType.VIDEO
        ]:
            persuasiveness_factors.append(0.2)
        
        # Opposition strength
        if evidence.opposing_arguments:
            persuasiveness_factors.append(-len(evidence.opposing_arguments) * 0.05)
        
        analysis['persuasiveness_score'] = max(0, sum(persuasiveness_factors))
        
        # Generate recommendations
        if analysis['admissibility_score'] < 0.6:
            analysis['recommendations'].append("Strengthen foundation elements before trial")
        
        if evidence.authenticity_level == AuthenticityLevel.UNVERIFIED:
            analysis['recommendations'].append("Obtain authentication for this evidence")
        
        if not evidence.custody_chain:
            analysis['recommendations'].append("Establish chain of custody documentation")
        
        if analysis['persuasiveness_score'] < 0.4:
            analysis['recommendations'].append("Consider demonstrative aids to enhance impact")
        
        return analysis
    
    def identify_evidence_gaps(self, evidence_chain: EvidenceChain, 
                             all_evidence: List[EvidenceItem]) -> List[str]:
        """Identify gaps in evidence chain."""
        gaps = []
        chain_evidence = [e for e in all_evidence if e.evidence_id in evidence_chain.evidence_items]
        
        # Temporal gaps
        dated_evidence = [e for e in chain_evidence if e.date_created]
        if len(dated_evidence) > 1:
            dated_evidence.sort(key=lambda x: x.date_created)
            for i in range(len(dated_evidence) - 1):
                time_gap = dated_evidence[i + 1].date_created - dated_evidence[i].date_created
                if time_gap.days > 30:
                    gaps.append(f"Significant time gap ({time_gap.days} days) between evidence items")
        
        # Source diversity
        sources = {e.source for e in chain_evidence}
        if len(sources) < 2:
            gaps.append("Evidence relies on single source - consider corroborating sources")
        
        # Evidence type diversity
        types = {e.evidence_type for e in chain_evidence}
        if len(types) < 2:
            gaps.append("Evidence chain lacks type diversity - consider multiple evidence forms")
        
        # Foundation completeness
        incomplete_foundation = [e for e in chain_evidence if not e.foundation_complete]
        if incomplete_foundation:
            gaps.append(f"{len(incomplete_foundation)} evidence items lack complete foundation")
        
        return gaps

class ExhibitManager:
    """Manages exhibit preparation and courtroom presentation."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".ExhibitManager")
    
    def prepare_exhibit(self, evidence: EvidenceItem, exhibit_number: str) -> Dict[str, Any]:
        """Prepare evidence as courtroom exhibit."""
        exhibit_info = {
            'exhibit_number': exhibit_number,
            'evidence_id': evidence.evidence_id,
            'title': evidence.title,
            'exhibit_prepared': False,
            'preparation_checklist': [],
            'foundation_requirements': [],
            'presentation_notes': [],
            'technical_requirements': []
        }
        
        # Generate preparation checklist
        checklist = []
        
        # Authentication requirements
        if evidence.authenticity_level == AuthenticityLevel.UNVERIFIED:
            checklist.append("Obtain authentication witness")
        
        # Foundation elements
        incomplete_elements = [e for e in evidence.foundation_elements if not e.met]
        for element in incomplete_elements:
            checklist.append(f"Establish foundation: {element.description}")
        
        # Physical preparation
        if evidence.file_path:
            checklist.append("Prepare physical copies for court")
            checklist.append("Test digital equipment for presentation")
        
        # Witness coordination
        if evidence.foundation_witness:
            checklist.append(f"Coordinate with foundation witness: {evidence.foundation_witness}")
        
        for witness in evidence.related_witnesses:
            checklist.append(f"Prepare witness: {witness}")
        
        exhibit_info['preparation_checklist'] = checklist
        
        # Generate foundation requirements
        foundation_reqs = []
        for element in evidence.foundation_elements:
            requirement = {
                'element': element.element_type,
                'description': element.description,
                'witness': element.witness_required,
                'documentation': element.documentation_needed,
                'status': 'complete' if element.met else 'pending'
            }
            foundation_reqs.append(requirement)
        
        exhibit_info['foundation_requirements'] = foundation_reqs
        
        # Technical requirements for presentation
        tech_reqs = []
        if evidence.evidence_type == EvidenceType.VIDEO:
            tech_reqs.extend([
                "Video playback equipment",
                "Audio system for courtroom",
                "Backup copies on multiple media"
            ])
        elif evidence.evidence_type == EvidenceType.AUDIO:
            tech_reqs.extend([
                "Audio playback system",
                "Transcription copies",
                "Volume adjustment capability"
            ])
        elif evidence.evidence_type == EvidenceType.DIGITAL:
            tech_reqs.extend([
                "Computer/laptop for presentation",
                "Projection system",
                "Backup storage devices"
            ])
        
        exhibit_info['technical_requirements'] = tech_reqs
        
        return exhibit_info
    
    def generate_exhibit_list(self, evidence_items: List[EvidenceItem]) -> List[Dict[str, Any]]:
        """Generate formal exhibit list for trial."""
        exhibit_list = []
        
        # Sort by exhibit number if assigned, then by relevance
        sorted_evidence = sorted(
            evidence_items,
            key=lambda x: (x.exhibit_number or "Z999", -x.relevance_score.value)
        )
        
        for evidence in sorted_evidence:
            if evidence.exhibit_number:
                exhibit_entry = {
                    'exhibit_number': evidence.exhibit_number,
                    'description': evidence.title,
                    'type': evidence.evidence_type.value,
                    'date': evidence.date_created.strftime("%Y-%m-%d") if evidence.date_created else "",
                    'source': evidence.source,
                    'foundation_witness': evidence.foundation_witness or "TBD",
                    'status': evidence.status.value,
                    'notes': "; ".join(evidence.notes) if evidence.notes else ""
                }
                exhibit_list.append(exhibit_entry)
        
        return exhibit_list

class EvidenceManager:
    """Main evidence management system coordinating all components."""
    
    def __init__(self):
        self.evidence_items: Dict[str, EvidenceItem] = {}
        self.evidence_chains: Dict[str, EvidenceChain] = {}
        self.analyzer = EvidenceAnalyzer()
        self.exhibit_manager = ExhibitManager()
        self.logger = logging.getLogger(__name__ + ".EvidenceManager")
    
    def add_evidence(self, evidence: EvidenceItem) -> str:
        """Add new evidence item to the system."""
        if not evidence.evidence_id:
            evidence.evidence_id = str(uuid.uuid4())
        
        # Generate file hash if file exists
        if evidence.file_path and Path(evidence.file_path).exists():
            evidence.file_hash = self._generate_file_hash(evidence.file_path)
            evidence.file_size = Path(evidence.file_path).stat().st_size
        
        # Initialize custody chain
        if not evidence.custody_chain and evidence.current_custodian:
            initial_custody = CustodyEntry(
                timestamp=datetime.now(),
                person=evidence.current_custodian,
                organization="Legal Team",
                action="Initial Collection",
                location="Law Office",
                purpose="Evidence Collection",
                signature_hash=self._generate_signature_hash(evidence.current_custodian, datetime.now())
            )
            evidence.custody_chain.append(initial_custody)
        
        self.evidence_items[evidence.evidence_id] = evidence
        self.logger.info(f"Added evidence item: {evidence.evidence_id}")
        return evidence.evidence_id
    
    def create_evidence_chain(self, title: str, description: str, 
                            evidence_ids: List[str]) -> str:
        """Create new evidence chain linking related items."""
        chain_id = str(uuid.uuid4())
        
        # Validate all evidence IDs exist
        valid_ids = [eid for eid in evidence_ids if eid in self.evidence_items]
        if len(valid_ids) != len(evidence_ids):
            self.logger.warning(f"Some evidence IDs not found when creating chain {chain_id}")
        
        chain = EvidenceChain(
            chain_id=chain_id,
            title=title,
            description=description,
            evidence_items=valid_ids,
            narrative_order=valid_ids.copy()  # Default to input order
        )
        
        # Analyze chain strength
        chain.strength_assessment = self._assess_chain_strength(chain)
        chain.gaps_identified = self.analyzer.identify_evidence_gaps(chain, 
                                                                   list(self.evidence_items.values()))
        
        self.evidence_chains[chain_id] = chain
        self.logger.info(f"Created evidence chain: {chain_id}")
        return chain_id
    
    def update_custody(self, evidence_id: str, new_custodian: str, 
                      action: str, location: str, purpose: str) -> bool:
        """Update chain of custody for evidence item."""
        if evidence_id not in self.evidence_items:
            return False
        
        evidence = self.evidence_items[evidence_id]
        
        custody_entry = CustodyEntry(
            timestamp=datetime.now(),
            person=new_custodian,
            organization="Legal Team",
            action=action,
            location=location,
            purpose=purpose,
            signature_hash=self._generate_signature_hash(new_custodian, datetime.now())
        )
        
        evidence.custody_chain.append(custody_entry)
        evidence.current_custodian = new_custodian
        evidence.last_modified = datetime.now()
        
        self.logger.info(f"Updated custody for evidence {evidence_id}")
        return True
    
    def authenticate_evidence(self, evidence_id: str, 
                            authenticity_level: AuthenticityLevel,
                            authenticator: str, method: str) -> bool:
        """Authenticate evidence item."""
        if evidence_id not in self.evidence_items:
            return False
        
        evidence = self.evidence_items[evidence_id]
        evidence.authenticity_level = authenticity_level
        evidence.last_modified = datetime.now()
        
        # Add authentication note
        auth_note = f"Authenticated by {authenticator} using {method} on {datetime.now().strftime('%Y-%m-%d')}"
        evidence.notes.append(auth_note)
        
        # Update custody for authentication
        self.update_custody(evidence_id, authenticator, "Authentication", 
                          "Authentication Lab", f"Authentication via {method}")
        
        self.logger.info(f"Authenticated evidence {evidence_id} at level {authenticity_level.value}")
        return True
    
    def prepare_for_trial(self, case_id: str) -> Dict[str, Any]:
        """Prepare all evidence for trial presentation."""
        case_evidence = [e for e in self.evidence_items.values() 
                        if case_id in e.tags or case_id in e.metadata.get('case_ids', [])]
        
        preparation_report = {
            'total_evidence_items': len(case_evidence),
            'exhibit_assignments': {},
            'foundation_issues': [],
            'authentication_needed': [],
            'custody_problems': [],
            'strength_analysis': {},
            'recommendations': []
        }
        
        # Assign exhibit numbers if not already assigned
        exhibit_counter = 1
        for evidence in sorted(case_evidence, key=lambda x: -x.relevance_score.value):
            if not evidence.exhibit_number:
                evidence.exhibit_number = f"Plaintiff-{exhibit_counter}"
                exhibit_counter += 1
            
            # Analyze evidence strength
            strength = self.analyzer.analyze_evidence_strength(evidence)
            preparation_report['strength_analysis'][evidence.evidence_id] = strength
            
            # Check for issues
            if not evidence.foundation_complete:
                preparation_report['foundation_issues'].append(evidence.evidence_id)
            
            if evidence.authenticity_level == AuthenticityLevel.UNVERIFIED:
                preparation_report['authentication_needed'].append(evidence.evidence_id)
            
            if not evidence.custody_chain:
                preparation_report['custody_problems'].append(evidence.evidence_id)
            
            preparation_report['exhibit_assignments'][evidence.exhibit_number] = evidence.evidence_id
        
        # Generate exhibit list
        exhibit_list = self.exhibit_manager.generate_exhibit_list(case_evidence)
        preparation_report['exhibit_list'] = exhibit_list
        
        # Overall recommendations
        if preparation_report['foundation_issues']:
            preparation_report['recommendations'].append(
                f"Complete foundation for {len(preparation_report['foundation_issues'])} evidence items"
            )
        
        if preparation_report['authentication_needed']:
            preparation_report['recommendations'].append(
                f"Authenticate {len(preparation_report['authentication_needed'])} evidence items"
            )
        
        return preparation_report
    
    def search_evidence(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[EvidenceItem]:
        """Search evidence items by various criteria."""
        results = []
        query_lower = query.lower()
        
        for evidence in self.evidence_items.values():
            # Text search in title, description, and notes
            searchable_text = (
                f"{evidence.title} {evidence.description} " +
                f"{evidence.source} {evidence.case_relevance} " +
                f"{' '.join(evidence.notes)} {' '.join(evidence.tags)}"
            ).lower()
            
            if query_lower in searchable_text:
                # Apply filters if provided
                if filters:
                    if 'evidence_type' in filters and evidence.evidence_type != filters['evidence_type']:
                        continue
                    if 'status' in filters and evidence.status != filters['status']:
                        continue
                    if 'relevance_min' in filters and evidence.relevance_score.value < filters['relevance_min']:
                        continue
                    if 'date_from' in filters and evidence.date_created < filters['date_from']:
                        continue
                    if 'date_to' in filters and evidence.date_created > filters['date_to']:
                        continue
                
                results.append(evidence)
        
        # Sort by relevance score (highest first)
        return sorted(results, key=lambda x: x.relevance_score.value, reverse=True)
    
    def generate_evidence_report(self, chain_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive evidence report."""
        if chain_id and chain_id in self.evidence_chains:
            chain = self.evidence_chains[chain_id]
            evidence_items = [self.evidence_items[eid] for eid in chain.evidence_items 
                            if eid in self.evidence_items]
            title = f"Evidence Chain Report: {chain.title}"
        else:
            evidence_items = list(self.evidence_items.values())
            title = "Complete Evidence Report"
        
        report = {
            'title': title,
            'generated_date': datetime.now(),
            'total_items': len(evidence_items),
            'summary': {},
            'strength_analysis': {},
            'preparation_status': {},
            'recommendations': []
        }
        
        # Summary statistics
        type_counts = {}
        status_counts = {}
        relevance_counts = {}
        
        for evidence in evidence_items:
            # Type distribution
            type_key = evidence.evidence_type.value
            type_counts[type_key] = type_counts.get(type_key, 0) + 1
            
            # Status distribution
            status_key = evidence.status.value
            status_counts[status_key] = status_counts.get(status_key, 0) + 1
            
            # Relevance distribution
            relevance_key = evidence.relevance_score.name
            relevance_counts[relevance_key] = relevance_counts.get(relevance_key, 0) + 1
        
        report['summary'] = {
            'by_type': type_counts,
            'by_status': status_counts,
            'by_relevance': relevance_counts,
            'authenticated_items': len([e for e in evidence_items 
                                      if e.authenticity_level != AuthenticityLevel.UNVERIFIED]),
            'foundation_complete': len([e for e in evidence_items if e.foundation_complete]),
            'exhibit_ready': len([e for e in evidence_items if e.exhibit_prepared])
        }
        
        # Detailed analysis for critical evidence
        critical_evidence = [e for e in evidence_items 
                           if e.relevance_score == RelevanceScore.CRITICAL]
        
        for evidence in critical_evidence:
            analysis = self.analyzer.analyze_evidence_strength(evidence)
            report['strength_analysis'][evidence.evidence_id] = analysis
        
        # Preparation status
        needs_auth = [e for e in evidence_items 
                     if e.authenticity_level == AuthenticityLevel.UNVERIFIED]
        needs_foundation = [e for e in evidence_items if not e.foundation_complete]
        
        report['preparation_status'] = {
            'authentication_needed': len(needs_auth),
            'foundation_needed': len(needs_foundation),
            'custody_issues': len([e for e in evidence_items if not e.custody_chain]),
            'ready_for_trial': len([e for e in evidence_items 
                                  if e.foundation_complete and 
                                     e.authenticity_level != AuthenticityLevel.UNVERIFIED])
        }
        
        # Generate recommendations
        if needs_auth:
            report['recommendations'].append(
                f"Prioritize authentication for {len(needs_auth)} evidence items"
            )
        
        if needs_foundation:
            report['recommendations'].append(
                f"Complete foundation elements for {len(needs_foundation)} items"
            )
        
        high_value_unprepped = [e for e in evidence_items 
                               if e.relevance_score.value >= 4 and not e.exhibit_prepared]
        if high_value_unprepped:
            report['recommendations'].append(
                f"Focus on preparing {len(high_value_unprepped)} high-value evidence items"
            )
        
        return report
    
    def _generate_file_hash(self, file_path: str) -> str:
        """Generate SHA-256 hash of file for integrity verification."""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"Error generating file hash: {e}")
            return ""
    
    def _generate_signature_hash(self, person: str, timestamp: datetime) -> str:
        """Generate signature hash for custody entries."""
        signature_string = f"{person}:{timestamp.isoformat()}"
        return hashlib.sha256(signature_string.encode()).hexdigest()[:16]
    
    def _assess_chain_strength(self, chain: EvidenceChain) -> float:
        """Assess the overall strength of an evidence chain."""
        if not chain.evidence_items:
            return 0.0
        
        total_strength = 0.0
        evidence_items = [self.evidence_items[eid] for eid in chain.evidence_items 
                         if eid in self.evidence_items]
        
        for evidence in evidence_items:
            item_strength = 0.0
            
            # Relevance weight
            item_strength += evidence.relevance_score.value * 0.3
            
            # Authentication weight
            auth_weights = {
                AuthenticityLevel.UNVERIFIED: 0.1,
                AuthenticityLevel.BASIC_VERIFIED: 0.4,
                AuthenticityLevel.EXPERT_VERIFIED: 0.7,
                AuthenticityLevel.COURT_CERTIFIED: 0.9,
                AuthenticityLevel.FORENSIC_VERIFIED: 1.0
            }
            item_strength += auth_weights.get(evidence.authenticity_level, 0.1) * 0.3
            
            # Foundation completeness weight
            if evidence.foundation_complete:
                item_strength += 0.2
            
            # Support/corroboration weight
            if evidence.supporting_evidence:
                item_strength += min(len(evidence.supporting_evidence) * 0.05, 0.2)
            
            total_strength += item_strength
        
        return total_strength / len(evidence_items) if evidence_items else 0.0