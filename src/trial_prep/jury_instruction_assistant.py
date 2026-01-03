"""
Jury Instruction Drafting Assistant

Comprehensive jury instruction drafting system including standard instruction
libraries, customization tools, legal compliance checking, and automated
generation based on case facts and legal theories.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Union
from datetime import datetime, date
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json
import logging
import re
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)

class InstructionType(Enum):
    """Types of jury instructions."""
    PRELIMINARY = "preliminary"
    SUBSTANTIVE = "substantive"
    BURDEN_OF_PROOF = "burden_of_proof"
    DAMAGES = "damages"
    LIABILITY = "liability"
    CREDIBILITY = "credibility"
    EVIDENCE = "evidence"
    EXPERT_WITNESS = "expert_witness"
    DELIBERATION = "deliberation"
    VERDICT = "verdict"
    CLOSING = "closing"
    SPECIAL_VERDICT = "special_verdict"
    INTERROGATORIES = "interrogatories"
    LIMITING = "limiting"
    CURATIVE = "curative"

class InstructionCategory(Enum):
    """Categories of legal instructions."""
    GENERAL_CIVIL = "general_civil"
    PERSONAL_INJURY = "personal_injury"
    CONTRACT = "contract"
    TORT = "tort"
    EMPLOYMENT = "employment"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    MEDICAL_MALPRACTICE = "medical_malpractice"
    PRODUCT_LIABILITY = "product_liability"
    BUSINESS_LITIGATION = "business_litigation"
    REAL_ESTATE = "real_estate"
    FAMILY_LAW = "family_law"
    CRIMINAL = "criminal"
    CONSTITUTIONAL = "constitutional"

class InstructionStatus(Enum):
    """Status of instruction development."""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    FILED = "filed"
    OBJECTED = "objected"
    MODIFIED = "modified"
    GIVEN = "given"
    REFUSED = "refused"

class JurisdictionLevel(Enum):
    """Jurisdiction levels for instructions."""
    FEDERAL = "federal"
    STATE = "state"
    LOCAL = "local"
    CIRCUIT = "circuit"

class InstructionSource(Enum):
    """Sources of jury instruction text."""
    PATTERN_JURY_INSTRUCTIONS = "pattern_jury_instructions"
    CASE_LAW = "case_law"
    STATUTE = "statute"
    MODEL_INSTRUCTIONS = "model_instructions"
    CUSTOM_DRAFTED = "custom_drafted"
    JUDICIAL_COUNCIL = "judicial_council"
    BAR_ASSOCIATION = "bar_association"

@dataclass
class LegalElement:
    """Individual legal element that must be proven."""
    element_id: str
    element_text: str
    burden_standard: str = "preponderance"  # preponderance, clear_convincing, beyond_reasonable_doubt
    required: bool = True
    alternative_elements: List[str] = field(default_factory=list)  # Element IDs
    supporting_evidence: List[str] = field(default_factory=list)
    case_citations: List[str] = field(default_factory=list)
    jury_instruction_language: str = ""

@dataclass
class InstructionTemplate:
    """Template for generating jury instructions."""
    template_id: str
    template_name: str
    instruction_type: InstructionType
    category: InstructionCategory
    jurisdiction: str
    
    # Template content
    template_text: str
    variable_fields: List[str] = field(default_factory=list)  # {{variable_name}}
    required_elements: List[str] = field(default_factory=list)  # Element IDs
    
    # Legal framework
    applicable_law: List[str] = field(default_factory=list)  # Statute/case citations
    burden_of_proof: str = "preponderance"
    legal_standard: str = ""
    
    # Usage guidelines
    usage_notes: str = ""
    modification_guidelines: str = ""
    common_objections: List[str] = field(default_factory=list)
    
    # Version control
    version: str = "1.0"
    created_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    author: str = ""
    approved_by: Optional[str] = None

@dataclass
class JuryInstruction:
    """Individual jury instruction with full details."""
    instruction_id: str
    instruction_number: Optional[str] = None
    title: str = ""
    instruction_type: InstructionType = InstructionType.SUBSTANTIVE
    category: InstructionCategory = InstructionCategory.GENERAL_CIVIL
    
    # Content
    instruction_text: str = ""
    template_used: Optional[str] = None  # Template ID
    source: InstructionSource = InstructionSource.CUSTOM_DRAFTED
    
    # Legal basis
    legal_elements: List[str] = field(default_factory=list)  # Element IDs
    supporting_citations: List[str] = field(default_factory=list)
    applicable_statutes: List[str] = field(default_factory=list)
    case_law_basis: List[str] = field(default_factory=list)
    
    # Customization
    case_specific_facts: Dict[str, str] = field(default_factory=dict)
    variable_substitutions: Dict[str, str] = field(default_factory=dict)
    modifications_made: List[str] = field(default_factory=list)
    
    # Status and tracking
    status: InstructionStatus = InstructionStatus.DRAFT
    priority: int = 3  # 1-5 scale
    required_instruction: bool = False
    
    # Court interaction
    filed_with_court: bool = False
    filing_date: Optional[datetime] = None
    objections_received: List[str] = field(default_factory=list)
    court_modifications: List[str] = field(default_factory=list)
    given_to_jury: bool = False
    
    # Related instructions
    prerequisite_instructions: List[str] = field(default_factory=list)  # Instruction IDs
    conflicting_instructions: List[str] = field(default_factory=list)
    alternative_instructions: List[str] = field(default_factory=list)
    
    # Quality control
    legal_review_complete: bool = False
    reviewed_by: List[str] = field(default_factory=list)
    review_notes: str = ""
    
    # Metadata
    created_date: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    last_modified: datetime = field(default_factory=datetime.now)
    modification_history: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class InstructionSet:
    """Complete set of jury instructions for a case."""
    set_id: str
    case_id: str
    case_type: str
    jurisdiction: str
    
    # Instruction organization
    instructions: List[str] = field(default_factory=list)  # Instruction IDs
    instruction_order: List[str] = field(default_factory=list)  # Ordered instruction IDs
    
    # Set metadata
    total_instructions: int = 0
    preliminary_instructions: List[str] = field(default_factory=list)
    substantive_instructions: List[str] = field(default_factory=list)
    closing_instructions: List[str] = field(default_factory=list)
    
    # Court submission
    filed: bool = False
    filing_deadline: Optional[datetime] = None
    filing_date: Optional[datetime] = None
    
    # Conference and objections
    instruction_conference_date: Optional[datetime] = None
    objections_due_date: Optional[datetime] = None
    objections_filed: List[str] = field(default_factory=list)
    court_rulings: Dict[str, str] = field(default_factory=dict)  # Instruction ID -> ruling
    
    # Final status
    final_instructions_approved: bool = False
    given_to_jury_date: Optional[datetime] = None
    
    # Quality metrics
    completeness_score: float = 0.0
    legal_sufficiency_score: float = 0.0
    
    created_date: datetime = field(default_factory=datetime.now)
    created_by: str = ""

class InstructionAnalyzer:
    """Analyzes jury instructions for completeness and legal adequacy."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".InstructionAnalyzer")
        
        # Common instruction requirements by case type
        self.required_instructions = {
            InstructionCategory.PERSONAL_INJURY: [
                InstructionType.BURDEN_OF_PROOF,
                InstructionType.LIABILITY,
                InstructionType.DAMAGES,
                InstructionType.CREDIBILITY,
                InstructionType.EVIDENCE
            ],
            InstructionCategory.CONTRACT: [
                InstructionType.BURDEN_OF_PROOF,
                InstructionType.LIABILITY,
                InstructionType.DAMAGES,
                InstructionType.EVIDENCE
            ],
            InstructionCategory.EMPLOYMENT: [
                InstructionType.BURDEN_OF_PROOF,
                InstructionType.LIABILITY,
                InstructionType.DAMAGES,
                InstructionType.CREDIBILITY
            ]
        }
    
    def analyze_instruction_completeness(self, instruction_set: InstructionSet,
                                       instructions: List[JuryInstruction],
                                       case_category: InstructionCategory) -> Dict[str, Any]:
        """Analyze completeness of instruction set."""
        analysis = {
            'completeness_score': 0.0,
            'required_instructions': [],
            'missing_instructions': [],
            'coverage_gaps': [],
            'redundant_instructions': [],
            'recommendations': []
        }
        
        # Get required instruction types for case category
        required_types = self.required_instructions.get(case_category, [])
        present_types = [inst.instruction_type for inst in instructions]
        
        # Check coverage of required instruction types
        missing_types = []
        for req_type in required_types:
            if req_type not in present_types:
                missing_types.append(req_type.value)
        
        analysis['missing_instructions'] = missing_types
        
        # Calculate completeness score
        if required_types:
            covered_count = len(required_types) - len(missing_types)
            analysis['completeness_score'] = covered_count / len(required_types)
        else:
            analysis['completeness_score'] = 1.0
        
        # Identify potential redundancies
        type_counts = defaultdict(int)
        for inst in instructions:
            type_counts[inst.instruction_type] += 1
        
        redundant_types = [inst_type.value for inst_type, count in type_counts.items() if count > 1]
        analysis['redundant_instructions'] = redundant_types
        
        # Generate recommendations
        recommendations = []
        
        if analysis['completeness_score'] < 0.8:
            recommendations.append("Address missing required instruction types")
        
        if missing_types:
            recommendations.append(f"Add missing instructions: {', '.join(missing_types)}")
        
        if redundant_types:
            recommendations.append(f"Review potential redundancies: {', '.join(redundant_types)}")
        
        analysis['recommendations'] = recommendations
        
        return analysis
    
    def analyze_instruction_quality(self, instruction: JuryInstruction) -> Dict[str, Any]:
        """Analyze quality and potential issues with individual instruction."""
        analysis = {
            'quality_score': 0.0,
            'clarity_score': 0.0,
            'legal_sufficiency': 0.0,
            'potential_issues': [],
            'improvement_suggestions': [],
            'objection_risks': []
        }
        
        text = instruction.instruction_text
        
        # Clarity analysis
        clarity_factors = []
        
        # Sentence length analysis
        sentences = re.split(r'[.!?]+', text)
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            # Optimal sentence length for jury instructions: 15-20 words
            if 15 <= avg_sentence_length <= 20:
                clarity_factors.append(0.3)
            elif 10 <= avg_sentence_length <= 25:
                clarity_factors.append(0.2)
            else:
                clarity_factors.append(0.1)
                analysis['improvement_suggestions'].append("Adjust sentence length for better clarity")
        
        # Use of plain language
        complex_words = re.findall(r'\b\w{12,}\b', text.lower())
        if len(complex_words) / len(text.split()) < 0.1:  # Less than 10% complex words
            clarity_factors.append(0.2)
        else:
            analysis['improvement_suggestions'].append("Consider using simpler language")
        
        # Active voice preference
        passive_indicators = ['is', 'was', 'were', 'been', 'being']
        passive_count = sum(1 for word in passive_indicators if word in text.lower())
        if passive_count / len(text.split()) < 0.05:  # Less than 5% passive indicators
            clarity_factors.append(0.2)
        
        # Logical structure
        if any(connector in text.lower() for connector in ['first', 'second', 'therefore', 'if', 'then']):
            clarity_factors.append(0.2)
        
        # Avoid legal jargon
        jargon_terms = ['heretofore', 'whereas', 'aforementioned', 'said party', 'hereinafter']
        jargon_count = sum(1 for term in jargon_terms if term.lower() in text.lower())
        if jargon_count == 0:
            clarity_factors.append(0.1)
        else:
            analysis['improvement_suggestions'].append("Reduce legal jargon for jury comprehension")
        
        analysis['clarity_score'] = sum(clarity_factors)
        
        # Legal sufficiency analysis
        sufficiency_factors = []
        
        # Citation support
        if instruction.supporting_citations:
            sufficiency_factors.append(0.3)
        else:
            analysis['potential_issues'].append("No supporting citations provided")
        
        # Legal elements coverage
        if instruction.legal_elements:
            sufficiency_factors.append(0.3)
        else:
            analysis['potential_issues'].append("Legal elements not specified")
        
        # Burden of proof clarity
        burden_keywords = ['preponderance', 'more likely than not', 'clear and convincing', 'beyond reasonable doubt']
        if any(keyword in text.lower() for keyword in burden_keywords):
            sufficiency_factors.append(0.2)
        
        # Complete legal standard
        if len(text.split()) > 50:  # Minimum substance threshold
            sufficiency_factors.append(0.2)
        else:
            analysis['potential_issues'].append("Instruction may be too brief to cover legal standard")
        
        analysis['legal_sufficiency'] = sum(sufficiency_factors)
        
        # Objection risk analysis
        objection_risks = []
        
        if not instruction.supporting_citations:
            objection_risks.append("Lack of legal authority - relevance objection risk")
        
        if 'preponderance' not in text.lower() and instruction.instruction_type == InstructionType.BURDEN_OF_PROOF:
            objection_risks.append("Burden of proof standard unclear")
        
        if len(complex_words) > 10:
            objection_risks.append("Complex language may confuse jury")
        
        analysis['objection_risks'] = objection_risks
        
        # Overall quality score
        analysis['quality_score'] = (analysis['clarity_score'] + analysis['legal_sufficiency']) / 2
        
        return analysis
    
    def identify_instruction_conflicts(self, instructions: List[JuryInstruction]) -> List[Dict[str, Any]]:
        """Identify potential conflicts between instructions."""
        conflicts = []
        
        # Check for contradictory burden of proof standards
        burden_instructions = [inst for inst in instructions 
                              if inst.instruction_type == InstructionType.BURDEN_OF_PROOF]
        
        if len(burden_instructions) > 1:
            standards = []
            for inst in burden_instructions:
                text_lower = inst.instruction_text.lower()
                if 'preponderance' in text_lower:
                    standards.append('preponderance')
                elif 'clear and convincing' in text_lower:
                    standards.append('clear_and_convincing')
                elif 'beyond reasonable doubt' in text_lower:
                    standards.append('beyond_reasonable_doubt')
            
            if len(set(standards)) > 1:
                conflicts.append({
                    'type': 'burden_of_proof_conflict',
                    'description': 'Multiple burden of proof standards specified',
                    'instructions_involved': [inst.instruction_id for inst in burden_instructions],
                    'severity': 'high'
                })
        
        # Check for inconsistent damage calculations
        damage_instructions = [inst for inst in instructions 
                              if inst.instruction_type == InstructionType.DAMAGES]
        
        damage_types = []
        for inst in damage_instructions:
            text_lower = inst.instruction_text.lower()
            if 'economic damages' in text_lower:
                damage_types.append('economic')
            if 'punitive damages' in text_lower:
                damage_types.append('punitive')
            if 'pain and suffering' in text_lower:
                damage_types.append('non_economic')
        
        # Check for duplicate instruction content
        text_similarity_threshold = 0.8
        for i, inst1 in enumerate(instructions):
            for j, inst2 in enumerate(instructions[i+1:], i+1):
                similarity = self._calculate_text_similarity(inst1.instruction_text, inst2.instruction_text)
                if similarity > text_similarity_threshold:
                    conflicts.append({
                        'type': 'duplicate_content',
                        'description': f'Instructions have {similarity:.0%} similar content',
                        'instructions_involved': [inst1.instruction_id, inst2.instruction_id],
                        'severity': 'medium'
                    })
        
        return conflicts
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two instruction texts."""
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        overlap = len(words1.intersection(words2))
        total_unique = len(words1.union(words2))
        
        return overlap / total_unique if total_unique > 0 else 0.0

class InstructionDrafter:
    """Assists in drafting jury instructions using templates and legal analysis."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".InstructionDrafter")
        
        # Standard instruction templates (would be loaded from database)
        self.standard_templates = self._initialize_standard_templates()
    
    def draft_from_template(self, template_id: str, case_facts: Dict[str, str],
                          legal_elements: List[LegalElement]) -> JuryInstruction:
        """Draft instruction from template with case-specific customization."""
        if template_id not in self.standard_templates:
            raise ValueError(f"Template {template_id} not found")
        
        template = self.standard_templates[template_id]
        
        # Create new instruction
        instruction = JuryInstruction(
            instruction_id=str(uuid.uuid4()),
            title=template.template_name,
            instruction_type=template.instruction_type,
            category=template.category,
            template_used=template_id,
            source=InstructionSource.PATTERN_JURY_INSTRUCTIONS,
            legal_elements=[elem.element_id for elem in legal_elements],
            case_specific_facts=case_facts
        )
        
        # Substitute variables in template
        instruction_text = template.template_text
        
        for variable in template.variable_fields:
            placeholder = f"{{{{{variable}}}}}"
            if variable in case_facts:
                instruction_text = instruction_text.replace(placeholder, case_facts[variable])
            elif variable in instruction.variable_substitutions:
                instruction_text = instruction_text.replace(placeholder, instruction.variable_substitutions[variable])
        
        instruction.instruction_text = instruction_text
        
        # Add legal citations from template
        instruction.supporting_citations = template.applicable_law.copy()
        
        self.logger.info(f"Drafted instruction from template {template_id}")
        return instruction
    
    def draft_custom_instruction(self, instruction_type: InstructionType,
                               category: InstructionCategory, legal_elements: List[LegalElement],
                               case_facts: Dict[str, str], legal_standard: str) -> JuryInstruction:
        """Draft custom instruction based on legal elements and case facts."""
        instruction = JuryInstruction(
            instruction_id=str(uuid.uuid4()),
            instruction_type=instruction_type,
            category=category,
            source=InstructionSource.CUSTOM_DRAFTED,
            legal_elements=[elem.element_id for elem in legal_elements],
            case_specific_facts=case_facts
        )
        
        # Generate instruction text based on legal elements
        instruction_text_parts = []
        
        # Introduction
        if instruction_type == InstructionType.LIABILITY:
            instruction_text_parts.append("To find in favor of the plaintiff, you must find that each of the following elements has been proven by a preponderance of the evidence:")
        elif instruction_type == InstructionType.DAMAGES:
            instruction_text_parts.append("If you find that the defendant is liable, you must determine the amount of damages to award the plaintiff.")
        
        # Add elements
        for i, element in enumerate(legal_elements, 1):
            if element.jury_instruction_language:
                element_text = element.jury_instruction_language
            else:
                element_text = element.element_text
            
            instruction_text_parts.append(f"{i}. {element_text}")
        
        # Add burden of proof explanation
        if any(elem.burden_standard != "preponderance" for elem in legal_elements):
            instruction_text_parts.append("\nDifferent elements may require different standards of proof as specified above.")
        else:
            instruction_text_parts.append("\n'Preponderance of the evidence' means that the evidence on one side outweighs the evidence on the other side.")
        
        instruction.instruction_text = "\n\n".join(instruction_text_parts)
        
        self.logger.info(f"Drafted custom {instruction_type.value} instruction")
        return instruction
    
    def suggest_instructions_for_case(self, case_type: InstructionCategory,
                                    legal_theories: List[str],
                                    case_facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest appropriate instructions for a case type and legal theories."""
        suggestions = []
        
        # Required instructions for case type
        required_types = [
            InstructionType.PRELIMINARY,
            InstructionType.BURDEN_OF_PROOF,
            InstructionType.CREDIBILITY,
            InstructionType.EVIDENCE,
            InstructionType.DELIBERATION
        ]
        
        # Add case-specific required instructions
        if case_type == InstructionCategory.PERSONAL_INJURY:
            required_types.extend([
                InstructionType.LIABILITY,
                InstructionType.DAMAGES
            ])
        elif case_type == InstructionCategory.CONTRACT:
            required_types.extend([
                InstructionType.LIABILITY,
                InstructionType.DAMAGES
            ])
        elif case_type == InstructionCategory.EMPLOYMENT:
            required_types.extend([
                InstructionType.LIABILITY,
                InstructionType.DAMAGES
            ])
        
        # Generate suggestions
        for inst_type in required_types:
            # Find matching templates
            matching_templates = [
                template for template in self.standard_templates.values()
                if template.instruction_type == inst_type and template.category == case_type
            ]
            
            suggestion = {
                'instruction_type': inst_type.value,
                'required': inst_type in required_types[:6],  # First 6 are always required
                'available_templates': [
                    {
                        'template_id': template.template_id,
                        'template_name': template.template_name,
                        'jurisdiction': template.jurisdiction
                    }
                    for template in matching_templates
                ],
                'custom_drafting_recommended': len(matching_templates) == 0
            }
            
            suggestions.append(suggestion)
        
        # Theory-specific instructions
        if 'negligence' in [theory.lower() for theory in legal_theories]:
            suggestions.append({
                'instruction_type': 'negligence_standard',
                'required': True,
                'available_templates': [],
                'custom_drafting_recommended': True
            })
        
        if 'punitive_damages' in [theory.lower() for theory in legal_theories]:
            suggestions.append({
                'instruction_type': 'punitive_damages',
                'required': False,
                'available_templates': [],
                'custom_drafting_recommended': True
            })
        
        return suggestions
    
    def _initialize_standard_templates(self) -> Dict[str, InstructionTemplate]:
        """Initialize standard instruction templates."""
        templates = {}
        
        # Burden of Proof Template
        burden_template = InstructionTemplate(
            template_id="burden_preponderance_civil",
            template_name="Burden of Proof - Preponderance of Evidence",
            instruction_type=InstructionType.BURDEN_OF_PROOF,
            category=InstructionCategory.GENERAL_CIVIL,
            jurisdiction="Pattern",
            template_text="""The burden of proof is on the {{plaintiff_party}} to prove each element of {{plaintiff_party}}'s claim by a preponderance of the evidence.

'Preponderance of the evidence' means evidence that has more convincing force than the evidence opposed to it. If the evidence is equally balanced, then you must find against the party who had the burden to prove that fact.

In determining whether any fact has been proved by a preponderance of the evidence, you may consider the believability of the witnesses, the weight of the evidence, and all other factors that bear on whether the fact is more likely true than not true.""",
            variable_fields=["plaintiff_party"],
            burden_of_proof="preponderance",
            usage_notes="Standard burden of proof instruction for civil cases"
        )
        templates[burden_template.template_id] = burden_template
        
        # Credibility Template
        credibility_template = InstructionTemplate(
            template_id="witness_credibility_standard",
            template_name="Witness Credibility",
            instruction_type=InstructionType.CREDIBILITY,
            category=InstructionCategory.GENERAL_CIVIL,
            jurisdiction="Pattern",
            template_text="""In deciding the facts in this case, you may have to decide which testimony to believe and which testimony not to believe. You may believe everything a witness says, or part of it, or none of it.

In considering the testimony of any witness, you may take into account:
• the witness's opportunity and ability to see or hear or know the things testified to;
• the witness's memory;
• the witness's manner while testifying;
• the witness's interest in the outcome of the case and any bias or prejudice;
• whether other evidence contradicted the witness's testimony;
• the reasonableness of the witness's testimony in light of all the evidence; and
• any other factors that bear on believability.

The weight of the evidence as to a fact does not necessarily depend on the number of witnesses who testify about it.""",
            variable_fields=[],
            usage_notes="Standard credibility instruction applicable to all witness testimony"
        )
        templates[credibility_template.template_id] = credibility_template
        
        # Negligence Template
        negligence_template = InstructionTemplate(
            template_id="negligence_standard",
            template_name="Standard of Care - Negligence",
            instruction_type=InstructionType.LIABILITY,
            category=InstructionCategory.PERSONAL_INJURY,
            jurisdiction="Pattern",
            template_text="""To prove negligence, {{plaintiff_party}} must show that {{defendant_party}} failed to use the care that a reasonably careful person would use in the same situation.

A person is negligent when he or she fails to act as a reasonably careful person would act in the same or similar circumstances. You must decide how a reasonably careful person would have acted in {{defendant_party}}'s situation.

{{defendant_party}} is not required to be perfect. A person can be reasonably careful even if he or she makes an error in judgment, so long as the person acts as a reasonably careful person would act when facing the same circumstances and needing to make the same decision.

In deciding whether {{defendant_party}} was negligent, you should consider only what {{defendant_party}} knew or reasonably should have known at the time.""",
            variable_fields=["plaintiff_party", "defendant_party"],
            legal_standard="reasonable person standard",
            usage_notes="Standard negligence instruction for personal injury cases"
        )
        templates[negligence_template.template_id] = negligence_template
        
        # Economic Damages Template
        economic_damages_template = InstructionTemplate(
            template_id="economic_damages_personal_injury",
            template_name="Economic Damages",
            instruction_type=InstructionType.DAMAGES,
            category=InstructionCategory.PERSONAL_INJURY,
            jurisdiction="Pattern",
            template_text="""If you find that {{defendant_party}} is liable, you must determine {{plaintiff_party}}'s damages.

Economic damages are those with a specific dollar amount that can be calculated. Economic damages include:

• Medical expenses: The reasonable cost of medical care that {{plaintiff_party}} has received and is reasonably certain to need in the future because of the injury.

• Lost earnings: Income that {{plaintiff_party}} has lost and is reasonably certain to lose in the future because of the injury.

• Other economic losses: Any other expenses or economic losses that resulted from the injury.

You should consider only damages that were caused by the injury that is the subject of this case. Damages must be proved by a preponderance of the evidence.

Do not include in your award any amount for interest, attorney fees, or costs of suit.""",
            variable_fields=["plaintiff_party", "defendant_party"],
            usage_notes="Economic damages instruction for personal injury cases"
        )
        templates[economic_damages_template.template_id] = economic_damages_template
        
        return templates

class JuryInstructionAssistant:
    """Main jury instruction drafting and management system."""
    
    def __init__(self):
        self.instruction_sets: Dict[str, InstructionSet] = {}
        self.instructions: Dict[str, JuryInstruction] = {}
        self.templates: Dict[str, InstructionTemplate] = {}
        self.legal_elements: Dict[str, LegalElement] = {}
        
        self.analyzer = InstructionAnalyzer()
        self.drafter = InstructionDrafter()
        
        self.logger = logging.getLogger(__name__ + ".JuryInstructionAssistant")
    
    def create_instruction_set(self, case_id: str, case_type: str,
                             jurisdiction: str) -> str:
        """Create new jury instruction set for a case."""
        set_id = str(uuid.uuid4())
        
        instruction_set = InstructionSet(
            set_id=set_id,
            case_id=case_id,
            case_type=case_type,
            jurisdiction=jurisdiction
        )
        
        self.instruction_sets[set_id] = instruction_set
        self.logger.info(f"Created instruction set: {set_id}")
        return set_id
    
    def add_instruction_to_set(self, set_id: str, instruction_id: str,
                             order_position: Optional[int] = None) -> bool:
        """Add instruction to instruction set."""
        if set_id not in self.instruction_sets or instruction_id not in self.instructions:
            return False
        
        instruction_set = self.instruction_sets[set_id]
        instruction = self.instructions[instruction_id]
        
        if instruction_id not in instruction_set.instructions:
            instruction_set.instructions.append(instruction_id)
            instruction_set.total_instructions += 1
            
            # Categorize instruction
            if instruction.instruction_type in [InstructionType.PRELIMINARY]:
                instruction_set.preliminary_instructions.append(instruction_id)
            elif instruction.instruction_type in [InstructionType.CLOSING, InstructionType.DELIBERATION]:
                instruction_set.closing_instructions.append(instruction_id)
            else:
                instruction_set.substantive_instructions.append(instruction_id)
            
            # Add to ordered list
            if order_position is not None:
                instruction_set.instruction_order.insert(order_position, instruction_id)
            else:
                instruction_set.instruction_order.append(instruction_id)
            
            self.logger.info(f"Added instruction {instruction_id} to set {set_id}")
            
        return True
    
    def draft_instruction_from_template(self, template_id: str, case_facts: Dict[str, str],
                                      title: str = "") -> str:
        """Draft new instruction from template."""
        # Create legal elements (simplified for template use)
        legal_elements = []
        
        # Use drafter to create instruction
        instruction = self.drafter.draft_from_template(template_id, case_facts, legal_elements)
        
        if title:
            instruction.title = title
        
        # Add to system
        instruction_id = instruction.instruction_id
        self.instructions[instruction_id] = instruction
        
        self.logger.info(f"Drafted instruction {instruction_id} from template {template_id}")
        return instruction_id
    
    def draft_custom_instruction(self, instruction_type: InstructionType,
                               category: InstructionCategory, title: str,
                               legal_elements: List[str], case_facts: Dict[str, str]) -> str:
        """Draft custom instruction."""
        # Get legal elements
        elements = [self.legal_elements[elem_id] for elem_id in legal_elements 
                   if elem_id in self.legal_elements]
        
        # Use drafter to create instruction
        instruction = self.drafter.draft_custom_instruction(
            instruction_type, category, elements, case_facts, ""
        )
        instruction.title = title
        
        # Add to system
        instruction_id = instruction.instruction_id
        self.instructions[instruction_id] = instruction
        
        self.logger.info(f"Drafted custom instruction {instruction_id}")
        return instruction_id
    
    def analyze_instruction_set(self, set_id: str) -> Dict[str, Any]:
        """Analyze instruction set for completeness and quality."""
        if set_id not in self.instruction_sets:
            return {'error': 'Instruction set not found'}
        
        instruction_set = self.instruction_sets[set_id]
        instructions = [self.instructions[inst_id] for inst_id in instruction_set.instructions 
                       if inst_id in self.instructions]
        
        if not instructions:
            return {'error': 'No instructions in set'}
        
        # Determine case category from case type
        case_category = self._map_case_type_to_category(instruction_set.case_type)
        
        # Run completeness analysis
        completeness_analysis = self.analyzer.analyze_instruction_completeness(
            instruction_set, instructions, case_category
        )
        
        # Analyze individual instruction quality
        instruction_quality = {}
        overall_quality_scores = []
        
        for instruction in instructions:
            quality_analysis = self.analyzer.analyze_instruction_quality(instruction)
            instruction_quality[instruction.instruction_id] = quality_analysis
            overall_quality_scores.append(quality_analysis['quality_score'])
        
        # Check for conflicts
        conflicts = self.analyzer.identify_instruction_conflicts(instructions)
        
        # Generate comprehensive analysis
        analysis = {
            'set_id': set_id,
            'completeness_analysis': completeness_analysis,
            'average_quality_score': sum(overall_quality_scores) / len(overall_quality_scores) if overall_quality_scores else 0,
            'instruction_quality': instruction_quality,
            'conflicts_identified': conflicts,
            'overall_assessment': {},
            'recommendations': []
        }
        
        # Overall assessment
        overall_ready = (
            completeness_analysis['completeness_score'] >= 0.9 and
            analysis['average_quality_score'] >= 0.7 and
            len(conflicts) == 0
        )
        
        analysis['overall_assessment'] = {
            'ready_for_filing': overall_ready,
            'completion_percentage': completeness_analysis['completeness_score'] * 100,
            'quality_rating': self._quality_score_to_rating(analysis['average_quality_score']),
            'critical_issues_count': len([c for c in conflicts if c.get('severity') == 'high'])
        }
        
        # Generate recommendations
        recommendations = []
        recommendations.extend(completeness_analysis.get('recommendations', []))
        
        if analysis['average_quality_score'] < 0.6:
            recommendations.append("Review and improve instruction quality - average below 60%")
        
        if conflicts:
            recommendations.append(f"Resolve {len(conflicts)} instruction conflicts")
        
        analysis['recommendations'] = recommendations
        
        # Update instruction set metrics
        instruction_set.completeness_score = completeness_analysis['completeness_score']
        instruction_set.legal_sufficiency_score = analysis['average_quality_score']
        
        return analysis
    
    def generate_filing_package(self, set_id: str) -> Dict[str, Any]:
        """Generate court filing package for instruction set."""
        if set_id not in self.instruction_sets:
            return {'error': 'Instruction set not found'}
        
        instruction_set = self.instruction_sets[set_id]
        instructions = [self.instructions[inst_id] for inst_id in instruction_set.instruction_order 
                       if inst_id in self.instructions]
        
        # Generate filing package
        filing_package = {
            'case_information': {
                'case_id': instruction_set.case_id,
                'case_type': instruction_set.case_type,
                'jurisdiction': instruction_set.jurisdiction,
                'total_instructions': len(instructions)
            },
            'instructions': [],
            'cover_sheet': self._generate_cover_sheet(instruction_set),
            'citation_index': self._generate_citation_index(instructions),
            'filing_metadata': {
                'generated_date': datetime.now(),
                'generated_by': 'Jury Instruction Assistant',
                'format_version': '1.0'
            }
        }
        
        # Format instructions for filing
        for i, instruction in enumerate(instructions, 1):
            formatted_instruction = {
                'instruction_number': instruction.instruction_number or str(i),
                'title': instruction.title,
                'instruction_text': instruction.instruction_text,
                'legal_authority': instruction.supporting_citations,
                'source': instruction.source.value,
                'type': instruction.instruction_type.value
            }
            filing_package['instructions'].append(formatted_instruction)
        
        return filing_package
    
    def track_court_interaction(self, set_id: str, interaction_type: str,
                              details: Dict[str, Any]) -> bool:
        """Track court interactions with instruction set."""
        if set_id not in self.instruction_sets:
            return False
        
        instruction_set = self.instruction_sets[set_id]
        
        if interaction_type == "filed":
            instruction_set.filed = True
            instruction_set.filing_date = datetime.now()
        elif interaction_type == "objection":
            instruction_id = details.get('instruction_id')
            objection_text = details.get('objection_text', '')
            if instruction_id:
                instruction_set.objections_filed.append(f"{instruction_id}: {objection_text}")
        elif interaction_type == "ruling":
            instruction_id = details.get('instruction_id')
            ruling = details.get('ruling', '')
            if instruction_id:
                instruction_set.court_rulings[instruction_id] = ruling
        elif interaction_type == "given":
            instruction_set.given_to_jury_date = datetime.now()
            instruction_set.final_instructions_approved = True
        
        return True
    
    def suggest_instructions_for_case(self, case_type: str, legal_theories: List[str],
                                    case_facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get instruction suggestions for case."""
        case_category = self._map_case_type_to_category(case_type)
        return self.drafter.suggest_instructions_for_case(case_category, legal_theories, case_facts)
    
    def search_instructions(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[JuryInstruction]:
        """Search instructions by content and metadata."""
        results = []
        query_lower = query.lower()
        
        for instruction in self.instructions.values():
            # Text search in instruction content and title
            searchable_text = f"{instruction.title} {instruction.instruction_text}".lower()
            
            if query_lower in searchable_text:
                # Apply filters if provided
                if filters:
                    if 'instruction_type' in filters and instruction.instruction_type != filters['instruction_type']:
                        continue
                    if 'category' in filters and instruction.category != filters['category']:
                        continue
                    if 'status' in filters and instruction.status != filters['status']:
                        continue
                
                results.append(instruction)
        
        # Sort by priority and creation date
        return sorted(results, key=lambda x: (-x.priority, x.created_date), reverse=True)
    
    def _map_case_type_to_category(self, case_type: str) -> InstructionCategory:
        """Map case type string to instruction category enum."""
        case_type_mapping = {
            'personal_injury': InstructionCategory.PERSONAL_INJURY,
            'contract': InstructionCategory.CONTRACT,
            'employment': InstructionCategory.EMPLOYMENT,
            'tort': InstructionCategory.TORT,
            'business': InstructionCategory.BUSINESS_LITIGATION,
            'medical_malpractice': InstructionCategory.MEDICAL_MALPRACTICE,
            'product_liability': InstructionCategory.PRODUCT_LIABILITY
        }
        
        return case_type_mapping.get(case_type.lower(), InstructionCategory.GENERAL_CIVIL)
    
    def _quality_score_to_rating(self, score: float) -> str:
        """Convert quality score to text rating."""
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.8:
            return "Good" 
        elif score >= 0.7:
            return "Satisfactory"
        elif score >= 0.6:
            return "Needs Improvement"
        else:
            return "Poor"
    
    def _generate_cover_sheet(self, instruction_set: InstructionSet) -> Dict[str, Any]:
        """Generate cover sheet for instruction filing."""
        return {
            'title': f"Proposed Jury Instructions - Case {instruction_set.case_id}",
            'total_instructions': instruction_set.total_instructions,
            'preliminary_count': len(instruction_set.preliminary_instructions),
            'substantive_count': len(instruction_set.substantive_instructions),
            'closing_count': len(instruction_set.closing_instructions),
            'filing_date': datetime.now().strftime("%B %d, %Y"),
            'jurisdiction': instruction_set.jurisdiction
        }
    
    def _generate_citation_index(self, instructions: List[JuryInstruction]) -> List[Dict[str, Any]]:
        """Generate index of legal citations used in instructions."""
        citations = {}
        
        for instruction in instructions:
            for citation in instruction.supporting_citations:
                if citation not in citations:
                    citations[citation] = []
                citations[citation].append(instruction.instruction_number or instruction.instruction_id)
        
        citation_index = []
        for citation, instruction_nums in citations.items():
            citation_index.append({
                'citation': citation,
                'instructions_cited_in': instruction_nums,
                'usage_count': len(instruction_nums)
            })
        
        return sorted(citation_index, key=lambda x: x['citation'])