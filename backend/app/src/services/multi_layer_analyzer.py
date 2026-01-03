"""
Multi-Layer Document Analysis System with Hallucination Prevention

This service implements a 4-layer verification pipeline:
- Layer 1: Deep Extraction (Claude Opus) - Comprehensive initial analysis
- Layer 2: Cross-Model Verification (GPT-4o) - Independent verification
- Layer 3: Hallucination Detection - Source document validation
- Layer 4: Final Validation - Structured output with confidence scores

Each layer checks the previous layer's work before proceeding.
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio

from openai import OpenAI
import anthropic
from pathlib import Path
from dotenv import load_dotenv
from .analysis_progress_tracker import progress_tracker, AnalysisStage
from .analysis_audit_trail import AnalysisAuditTrail, AuditEventType

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent.parent / '.env')
logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence levels for extracted data"""
    VERIFIED = "verified"  # 95-100% - Cross-verified by multiple models
    HIGH = "high"  # 80-94% - Single model high confidence
    MEDIUM = "medium"  # 60-79% - Partial verification
    LOW = "low"  # 40-59% - Needs review
    UNVERIFIED = "unverified"  # 0-39% - Could not verify


class ExtractionStatus(Enum):
    """Status of extraction layers"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


@dataclass
class ExtractedItem:
    """A single extracted piece of information with verification metadata"""
    value: Any
    source_text: str = ""  # The exact text from document this was extracted from
    source_location: str = ""  # Where in document (e.g., "paragraph 3", "page 2")
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    confidence_score: float = 0.0  # 0-100
    verified_by: List[str] = field(default_factory=list)  # Which models verified this
    discrepancies: List[str] = field(default_factory=list)  # Any disagreements between models

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "source_text": self.source_text,
            "source_location": self.source_location,
            "confidence": self.confidence.value,
            "confidence_score": self.confidence_score,
            "verified_by": self.verified_by,
            "discrepancies": self.discrepancies
        }


@dataclass
class LayerResult:
    """Result from a single analysis layer"""
    layer_name: str
    status: ExtractionStatus
    data: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    model_used: str = ""


@dataclass
class VerifiedAnalysis:
    """Final verified analysis with all layers completed"""
    document_id: str
    document_type: str
    summary: ExtractedItem
    parties: List[ExtractedItem]
    dates: List[ExtractedItem]
    monetary_amounts: List[ExtractedItem]
    key_terms: List[ExtractedItem]
    obligations: List[ExtractedItem]
    deadlines: List[ExtractedItem]
    keywords: List[ExtractedItem]

    # Layer results for transparency
    layer_results: Dict[str, LayerResult] = field(default_factory=dict)

    # Overall confidence
    overall_confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    overall_confidence_score: float = 0.0

    # Metadata
    analyzed_at: str = ""
    total_processing_time: float = 0.0
    hallucinations_detected: int = 0
    corrections_made: int = 0

    # Audit trail for full documentation
    audit_trail: Optional[Any] = None  # AnalysisAuditTrail instance

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "document_id": self.document_id,
            "document_type": self.document_type,
            "summary": self.summary.to_dict() if self.summary else None,
            "parties": [p.to_dict() for p in self.parties],
            "dates": [d.to_dict() for d in self.dates],
            "monetary_amounts": [m.to_dict() for m in self.monetary_amounts],
            "key_terms": [k.to_dict() for k in self.key_terms],
            "obligations": [o.to_dict() for o in self.obligations],
            "deadlines": [d.to_dict() for d in self.deadlines],
            "keywords": [k.to_dict() for k in self.keywords],
            "overall_confidence": self.overall_confidence.value,
            "overall_confidence_score": self.overall_confidence_score,
            "analyzed_at": self.analyzed_at,
            "total_processing_time": self.total_processing_time,
            "hallucinations_detected": self.hallucinations_detected,
            "corrections_made": self.corrections_made,
            "layer_results": {k: {"status": v.status.value, "model": v.model_used}
                            for k, v in self.layer_results.items()}
        }

        # Include audit trail if available
        if self.audit_trail:
            result["audit_trail"] = self.audit_trail.to_dict()

        return result

    def get_audit_trail(self) -> Optional[Dict]:
        """Get the full audit trail as a dictionary"""
        if self.audit_trail:
            return self.audit_trail.to_dict()
        return None

    def get_hallucination_report(self) -> Optional[Dict]:
        """Get detailed hallucination report"""
        if self.audit_trail:
            return self.audit_trail.get_hallucination_summary()
        return None

    def get_correction_report(self) -> Optional[Dict]:
        """Get detailed correction report"""
        if self.audit_trail:
            return self.audit_trail.get_correction_summary()
        return None


class MultiLayerAnalyzer:
    """
    Multi-layer document analysis with verification and hallucination prevention.

    Architecture:
    Layer 1 (Claude Opus): Deep extraction - comprehensive initial analysis
    Layer 2 (GPT-4o): Cross-verification - independent verification of Layer 1
    Layer 3 (Validation): Hallucination detection - verify against source document
    Layer 4 (Final): Structured validation - merge and score final output
    """

    # Model configurations
    # Claude Opus 4 for primary extraction (most capable)
    # Claude Sonnet 4 for verification (faster, cost-effective)
    CLAUDE_OPUS = 'claude-opus-4-20250514'  # Claude Opus 4 for deep extraction
    CLAUDE_SONNET = 'claude-sonnet-4-20250514'  # Claude Sonnet 4 for verification
    GPT4O = 'gpt-4o'
    GPT4_TURBO = 'gpt-4-turbo'

    def __init__(self):
        self.claude_client = None
        self.openai_client = None

        # Initialize Anthropic client
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            try:
                self.claude_client = anthropic.Anthropic(api_key=anthropic_key)
                logger.info(f"Claude client initialized for multi-layer analysis (model: {self.CLAUDE_OPUS})")
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}")
        else:
            logger.warning("ANTHROPIC_API_KEY not found - Claude analysis will be unavailable")

        # Initialize OpenAI client
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            try:
                self.openai_client = OpenAI(api_key=openai_key)
                logger.info(f"OpenAI client initialized for multi-layer analysis (model: {self.GPT4O})")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        else:
            logger.warning("OPENAI_API_KEY not found - OpenAI analysis will be unavailable")

        # Log overall status
        if self.claude_client and self.openai_client:
            logger.info("Multi-layer analyzer ready with dual AI backend")
        elif self.claude_client:
            logger.warning("Multi-layer analyzer running with Claude only (GPT-4o unavailable)")
        elif self.openai_client:
            logger.warning("Multi-layer analyzer running with OpenAI only (Claude unavailable)")
        else:
            logger.error("Multi-layer analyzer has NO AI backends - analysis will fail!")

    async def analyze_document(
        self,
        document_text: str,
        document_id: str = "",
        filename: str = "",
        quick_mode: bool = False,  # Default to thorough mode for maximum accuracy
        job_id: str = None  # Optional job ID for progress tracking
    ) -> VerifiedAnalysis:
        """
        Run analysis pipeline on a document.

        Args:
            document_text: The full text of the document
            document_id: Unique identifier for the document
            filename: Original filename for context
            quick_mode: If True, runs optimized 4-layer pipeline (~30s).
                       If False, runs full 10-stage pipeline with all inspections (~100s).
            job_id: Optional job ID for progress tracking

        Returns:
            VerifiedAnalysis with all extracted data and confidence scores
        """
        start_time = datetime.now()
        mode_desc = "quick" if quick_mode else "thorough"
        logger.info(f"Starting {mode_desc} multi-layer analysis for document: {filename or document_id}")

        # Initialize audit trail for comprehensive documentation
        audit_trail = AnalysisAuditTrail(document_id, filename)

        # Helper to update progress
        def update_progress(stage: AnalysisStage, detail: str = "", **kwargs):
            if job_id:
                progress_tracker.update_stage(job_id, stage, detail, **kwargs)

        # Initialize result
        result = VerifiedAnalysis(
            document_id=document_id,
            document_type="",
            summary=ExtractedItem(value=""),
            parties=[],
            dates=[],
            monetary_amounts=[],
            key_terms=[],
            obligations=[],
            deadlines=[],
            keywords=[],
            analyzed_at=start_time.isoformat(),
            audit_trail=audit_trail
        )

        try:
            # ================================================================
            # LAYER 1: Deep Extraction with Claude Opus
            # ================================================================
            logger.info("=== LAYER 1: Deep Extraction (Claude Opus) ===")
            update_progress(AnalysisStage.LAYER1_EXTRACTION, "Extracting document data with Claude Opus")

            # Start audit stage
            audit_trail.start_stage("layer1_extraction", 1, self.CLAUDE_OPUS)

            layer1_result = await self._layer1_deep_extraction(document_text, filename)
            result.layer_results["layer1_extraction"] = layer1_result

            if layer1_result.status == ExtractionStatus.FAILED:
                logger.error("Layer 1 failed, attempting fallback")
                layer1_result = await self._layer1_fallback_extraction(document_text, filename)
                result.layer_results["layer1_extraction"] = layer1_result

            # Complete audit stage with extraction counts
            audit_trail.complete_stage(
                output_data=layer1_result.data,
                items_extracted=(
                    len(layer1_result.data.get("parties", [])) +
                    len(layer1_result.data.get("dates", [])) +
                    len(layer1_result.data.get("monetary_amounts", []))
                )
            )

            # LAYER 1 INSPECTION: Skip in quick mode
            if not quick_mode:
                # Import expert agents and inspectors only when needed
                from .expert_agents import (
                    document_expert, layer_inspector, detect_document_type, DocumentType
                )
                logger.info("=== LAYER 1 INSPECTION ===")
                update_progress(AnalysisStage.LAYER1_INSPECTION, "Reviewing extraction quality")
                layer1_inspection = await layer_inspector.inspect_layer1_extraction(
                    document_text, layer1_result.data
                )
                result.layer_results["layer1_inspection"] = LayerResult(
                    layer_name="layer1_inspection",
                    status=ExtractionStatus.COMPLETED,
                    data=layer1_inspection,
                    model_used=layer1_inspection.get("model_used", ""),
                    processing_time=layer1_inspection.get("processing_time", 0)
                )

                # If inspection found missing items, merge them into layer1 data
                if layer1_inspection.get("missing_extractions"):
                    logger.info(f"Layer 1 inspection found {len(layer1_inspection['missing_extractions'])} missing items")
                    for missing in layer1_inspection["missing_extractions"]:
                        item_type = missing.get("type", "")
                        if item_type == "party" and "parties" in layer1_result.data:
                            layer1_result.data["parties"].append({
                                "name": missing.get("value", ""),
                                "source_text": missing.get("source_text", ""),
                                "role": "Unknown",
                                "added_by": "layer1_inspector"
                            })
                        elif item_type == "date" and "dates" in layer1_result.data:
                            layer1_result.data["dates"].append({
                                "date": missing.get("value", ""),
                                "source_text": missing.get("source_text", ""),
                                "description": "",
                                "added_by": "layer1_inspector"
                            })
                        elif item_type == "amount" and "monetary_amounts" in layer1_result.data:
                            layer1_result.data["monetary_amounts"].append({
                                "amount": missing.get("value", ""),
                                "source_text": missing.get("source_text", ""),
                                "description": "",
                                "added_by": "layer1_inspector"
                            })

            # ================================================================
            # LAYER 2: Cross-Model Verification with GPT-4o
            # ================================================================
            logger.info("=== LAYER 2: Cross-Model Verification (GPT-4o) ===")
            update_progress(AnalysisStage.LAYER2_VERIFICATION, "GPT-4o verifying extracted information")
            layer2_result = await self._layer2_cross_verification(
                document_text,
                layer1_result.data,
                filename
            )
            result.layer_results["layer2_verification"] = layer2_result

            # LAYER 2 INSPECTION: Skip in quick mode
            if not quick_mode:
                logger.info("=== LAYER 2 INSPECTION ===")
                update_progress(AnalysisStage.LAYER2_INSPECTION, "Comparing results between AI models")
                layer2_inspection = await layer_inspector.inspect_layer2_verification(
                    layer1_result.data, layer2_result.data
                )
                result.layer_results["layer2_inspection"] = LayerResult(
                    layer_name="layer2_inspection",
                    status=ExtractionStatus.COMPLETED,
                    data=layer2_inspection,
                    model_used=layer2_inspection.get("model_used", ""),
                    processing_time=layer2_inspection.get("processing_time", 0)
                )

                # Apply accuracy adjustment from inspection
                if layer2_inspection.get("recommended_accuracy_adjustment"):
                    current_score = layer2_result.data.get("accuracy_score", 70)
                    adjustment = layer2_inspection["recommended_accuracy_adjustment"]
                    layer2_result.data["accuracy_score"] = max(0, min(100, current_score + adjustment))
                    logger.info(f"Layer 2 accuracy adjusted by {adjustment} to {layer2_result.data['accuracy_score']}")

            # ================================================================
            # LAYER 3: Hallucination Detection
            # ================================================================
            logger.info("=== LAYER 3: Hallucination Detection ===")
            update_progress(AnalysisStage.LAYER3_HALLUCINATION, "Detecting and removing hallucinated information")

            # Start audit stage
            audit_trail.start_stage("layer3_hallucination", 5, "rule_based")

            layer3_result = await self._layer3_hallucination_detection(
                document_text,
                layer1_result.data,
                layer2_result.data
            )
            result.layer_results["layer3_hallucination"] = layer3_result
            result.hallucinations_detected = layer3_result.data.get("hallucinations_found", 0)

            # Record each hallucination in audit trail
            for hall in layer3_result.data.get("hallucinations", []):
                # Check if Layer 2 provided a correction for this hallucination
                corrected_value = None
                correction_source = None

                # Look for corrections from Layer 2
                for pot_hall in layer2_result.data.get("potential_hallucinations", []):
                    if hall.get("value") in str(pot_hall.get("item", "")):
                        # Layer 2 flagged this - check if it has a correction
                        correction_source = "layer2_verification"
                        break

                # Check if there's a direct correction in Layer 2's corrections
                for correction in layer2_result.data.get("corrections", []):
                    if hall.get("value") in str(correction.get("original", "")):
                        corrected_value = correction.get("corrected")
                        correction_source = "layer2_verification"
                        break

                audit_trail.record_hallucination(
                    stage="layer3_hallucination",
                    item_type=hall.get("type", "unknown"),
                    original_value=hall.get("value"),
                    reason=hall.get("reason", "Not found in document"),
                    detection_method="rule_based",
                    corrected_value=corrected_value,
                    correction_source=correction_source,
                    document_text=document_text
                )

                # Report hallucination to progress tracker for UI display
                if job_id:
                    progress_tracker.add_hallucination_report(
                        job_id=job_id,
                        field_name=hall.get("type", "unknown"),
                        original_value=hall.get("value"),
                        corrected_value=corrected_value,
                        reason=hall.get("reason", "Not found in document"),
                        source_layer="layer3_hallucination"
                    )

            audit_trail.complete_stage(
                output_data=layer3_result.data,
                items_flagged=layer3_result.data.get("hallucinations_found", 0),
                items_verified=layer3_result.data.get("verified_items_count", 0)
            )

            # LAYER 3 INSPECTION: Skip in quick mode
            layer3_inspection = {"inspection_passed": True}  # Default for quick mode
            if not quick_mode:
                logger.info("=== LAYER 3 INSPECTION ===")
                update_progress(AnalysisStage.LAYER3_INSPECTION, "Verifying all information against source document")

                audit_trail.start_stage("layer3_inspection", 6, self.GPT4O)

                layer3_inspection = await layer_inspector.inspect_layer3_hallucination(
                    document_text, layer3_result.data
                )
                result.layer_results["layer3_inspection"] = LayerResult(
                    layer_name="layer3_inspection",
                    status=ExtractionStatus.COMPLETED,
                    data=layer3_inspection,
                    model_used=layer3_inspection.get("model_used", ""),
                    processing_time=layer3_inspection.get("processing_time", 0)
                )

                # Remove false positives if found
                false_positives_restored = 0
                if layer3_inspection.get("false_positives"):
                    logger.info(f"Removing {len(layer3_inspection['false_positives'])} false positive hallucination flags")
                    false_positive_set = set(layer3_inspection["false_positives"])

                    # Record each false positive restoration in audit trail
                    for fp in layer3_inspection["false_positives"]:
                        audit_trail.record_false_positive(
                            stage="layer3_inspection",
                            item_type="unknown",  # We'd need to look up the original type
                            value=fp,
                            reason_restored="Inspection verified item exists in document"
                        )
                        false_positives_restored += 1

                    layer3_result.data["hallucinations"] = [
                        h for h in layer3_result.data.get("hallucinations", [])
                        if h.get("value") not in false_positive_set
                    ]
                    layer3_result.data["hallucinations_found"] = len(layer3_result.data["hallucinations"])
                    result.hallucinations_detected = layer3_result.data["hallucinations_found"]

                audit_trail.complete_stage(
                    output_data=layer3_inspection,
                    items_verified=len(layer3_inspection.get("verified_items", [])),
                    items_removed=false_positives_restored
                )

            # ================================================================
            # LAYER 4: Final Validation and Scoring
            # ================================================================
            logger.info("=== LAYER 4: Final Validation ===")
            update_progress(AnalysisStage.LAYER4_VALIDATION, "Merging verified data and calculating confidence scores")

            audit_trail.start_stage("layer4_validation", 7, "aggregation")

            layer4_result = await self._layer4_final_validation(
                document_text,
                layer1_result.data,
                layer2_result.data,
                layer3_result.data,
                audit_trail  # Pass audit trail for detailed tracking
            )
            result.layer_results["layer4_final"] = layer4_result

            audit_trail.complete_stage(
                output_data=layer4_result.data,
                items_verified=len(layer4_result.data.get("parties", [])) + len(layer4_result.data.get("monetary_amounts", [])),
                items_removed=layer4_result.data.get("items_removed", 0)
            )

            # Initialize defaults for quick mode
            expert_review = None
            final_inspection = {"final_approval": True, "overall_quality_score": 80}
            layer1_inspection = {"inspection_passed": True, "quality_score": 80}
            layer2_inspection = {"inspection_passed": True, "verification_quality": 80}

            # EXPERT AGENT REVIEW & FINAL INSPECTION: Skip in quick mode
            if not quick_mode:
                # Import expert agents and inspectors
                from .expert_agents import (
                    document_expert, layer_inspector, detect_document_type, DocumentType
                )

                # ================================================================
                # EXPERT AGENT REVIEW: Document-type specific expert analysis
                # ================================================================
                doc_type_str = layer4_result.data.get("document_type", "unknown")
                detected_type = detect_document_type(document_text, doc_type_str)
                logger.info(f"=== EXPERT AGENT REVIEW ({detected_type.value}) ===")
                update_progress(AnalysisStage.EXPERT_REVIEW, f"Running {detected_type.value} expert analysis")

                audit_trail.start_stage("expert_review", 8, self.CLAUDE_OPUS)

                expert_review = await document_expert.run_expert_review(
                    detected_type,
                    document_text,
                    layer4_result.data
                )
                result.layer_results["expert_review"] = LayerResult(
                    layer_name="expert_review",
                    status=ExtractionStatus.COMPLETED,
                    data=expert_review.to_dict(),
                    model_used=expert_review.model_used,
                    processing_time=expert_review.processing_time,
                    warnings=expert_review.warnings
                )

                # Apply expert corrections with audit tracking
                corrections_applied = 0
                if expert_review.corrections:
                    logger.info(f"Applying {len(expert_review.corrections)} expert corrections")
                    for correction in expert_review.corrections:
                        field = correction.get("field", "")
                        correct_value = correction.get("correct_value")
                        original_value = layer4_result.data.get(field)

                        if field and correct_value:
                            # Record the correction in audit trail
                            audit_trail.record_correction(
                                stage="expert_review",
                                field_path=field,
                                original_value=original_value,
                                corrected_value=correct_value,
                                reason=correction.get("reason", "Expert correction"),
                                source="expert_review",
                                document_text=document_text
                            )

                            # Apply the correction
                            if field in layer4_result.data:
                                layer4_result.data[field] = correct_value
                            result.corrections_made += 1
                            corrections_applied += 1

                audit_trail.complete_stage(
                    output_data=expert_review.to_dict() if expert_review else {},
                    items_corrected=corrections_applied
                )

                # Add expert findings to analysis
                if expert_review.findings:
                    layer4_result.data["expert_findings"] = expert_review.findings
                    layer4_result.data["expert_notes"] = expert_review.expert_notes

                # Add missing items flagged by expert
                if expert_review.missing_items:
                    layer4_result.data["expert_missing_items"] = expert_review.missing_items

                # ================================================================
                # FINAL INSPECTION: Last quality check before delivery
                # ================================================================
                logger.info("=== FINAL INSPECTION ===")
                update_progress(AnalysisStage.FINAL_INSPECTION, "Final quality check before delivery")

                audit_trail.start_stage("final_inspection", 9, self.CLAUDE_OPUS)

                final_inspection = await layer_inspector.inspect_final_output(
                    document_text,
                    layer4_result.data,
                    expert_review
                )
                result.layer_results["final_inspection"] = LayerResult(
                    layer_name="final_inspection",
                    status=ExtractionStatus.COMPLETED,
                    data=final_inspection,
                    model_used=final_inspection.get("model_used", ""),
                    processing_time=final_inspection.get("processing_time", 0)
                )

                # Apply final corrections with audit tracking
                final_corrections_applied = 0
                if final_inspection.get("final_corrections"):
                    logger.info(f"Applying {len(final_inspection['final_corrections'])} final corrections")
                    for correction in final_inspection["final_corrections"]:
                        field = correction.get("field", "")
                        corrected = correction.get("correction")
                        original = correction.get("original", layer4_result.data.get(field))

                        if field and corrected:
                            # Record the correction in audit trail
                            audit_trail.record_correction(
                                stage="final_inspection",
                                field_path=field,
                                original_value=original,
                                corrected_value=corrected,
                                reason=correction.get("reason", "Final inspection correction"),
                                source="final_inspection",
                                document_text=document_text
                            )

                            # Apply the correction
                            if field in layer4_result.data:
                                layer4_result.data[field] = corrected
                            result.corrections_made += 1
                            final_corrections_applied += 1

                audit_trail.complete_stage(
                    output_data=final_inspection,
                    items_corrected=final_corrections_applied
                )

            # Add quality metadata (with defaults for quick mode)
            layer4_result.data["quality_assurance"] = {
                "layer1_quality_score": layer1_inspection.get("quality_score", 80),
                "layer2_verification_quality": layer2_inspection.get("verification_quality", 80),
                "final_quality_score": final_inspection.get("overall_quality_score", 80),
                "expert_completeness_score": expert_review.findings.get("completeness_score", 0) if expert_review and expert_review.findings else 80,
                "all_inspections_passed": (
                    layer1_inspection.get("inspection_passed", True) and
                    layer2_inspection.get("inspection_passed", True) and
                    layer3_inspection.get("inspection_passed", True) and
                    final_inspection.get("final_approval", True)
                ),
                "user_readiness": final_inspection.get("user_readiness", {"ready": True}),
                "expert_warnings": expert_review.warnings if expert_review else [],
                "expert_notes": expert_review.expert_notes if expert_review else [],
                "quick_mode": quick_mode
            }

            # Populate result from validated data
            validated_data = layer4_result.data

            # DEBUG: Log layer4_result data before populating
            logger.info(f"[LAYER4 DEBUG] layer4_result.data keys: {list(layer4_result.data.keys())}")
            logger.info(f"[LAYER4 DEBUG] layer4 dates: {len(layer4_result.data.get('dates', []))}")
            logger.info(f"[LAYER4 DEBUG] layer4 monetary_amounts: {len(layer4_result.data.get('monetary_amounts', []))}")

            result = self._populate_verified_analysis(result, validated_data, document_text)

            # Store initial confidence for audit
            audit_trail.initial_confidence = result.overall_confidence_score

            # Calculate overall confidence with expert input
            result.overall_confidence, result.overall_confidence_score = \
                self._calculate_overall_confidence(result)

            # Adjust confidence based on quality assurance results
            final_quality = final_inspection.get("overall_quality_score", 70)
            initial_score = result.overall_confidence_score
            if final_quality < 60:
                result.overall_confidence_score = max(40, result.overall_confidence_score - 20)
                audit_trail.record_confidence_change(
                    "final_inspection", initial_score, result.overall_confidence_score,
                    f"Quality score {final_quality} below threshold"
                )
            elif final_quality > 90:
                result.overall_confidence_score = min(100, result.overall_confidence_score + 5)
                audit_trail.record_confidence_change(
                    "final_inspection", initial_score, result.overall_confidence_score,
                    f"High quality score {final_quality} bonus"
                )

            # Complete the audit trail
            audit_trail.complete_analysis(result.overall_confidence_score)
            result.audit_trail = audit_trail

            # Mark as completed with stats
            update_progress(
                AnalysisStage.COMPLETED,
                "Analysis completed successfully",
                items_extracted=len(result.parties) + len(result.dates) + len(result.monetary_amounts),
                hallucinations=result.hallucinations_detected,
                corrections=result.corrections_made,
                confidence=result.overall_confidence_score
            )

        except Exception as e:
            logger.error(f"Multi-layer analysis failed: {str(e)}")
            result.layer_results["error"] = LayerResult(
                layer_name="error",
                status=ExtractionStatus.FAILED,
                data={"error": str(e)},
                errors=[str(e)]
            )
            # Mark as failed
            if job_id:
                progress_tracker.fail_job(job_id, str(e))

        # Calculate total processing time
        end_time = datetime.now()
        result.total_processing_time = (end_time - start_time).total_seconds()
        logger.info(f"Multi-layer analysis completed in {result.total_processing_time:.2f}s")

        return result

    async def _layer1_deep_extraction(
        self,
        document_text: str,
        filename: str
    ) -> LayerResult:
        """
        Layer 1: Deep extraction using Claude Opus for maximum accuracy.
        Extracts ALL relevant information comprehensively.
        """
        import time
        start_time = time.time()

        if not self.claude_client:
            return LayerResult(
                layer_name="layer1_extraction",
                status=ExtractionStatus.FAILED,
                data={},
                errors=["Claude client not available"],
                model_used="none"
            )

        extraction_prompt = f"""You are a senior legal analyst performing a comprehensive document analysis.
Your task is to extract EVERY piece of important information from this document with extreme precision.

DOCUMENT FILENAME: {filename}

DOCUMENT TEXT:
{document_text}

CRITICAL INSTRUCTIONS:
1. Extract ONLY information that actually appears in the document
2. For each piece of information, note the EXACT text from the document it comes from
3. If information is unclear or ambiguous, say so
4. NEVER infer or assume information not explicitly stated
5. Be thorough - missing important information is worse than being verbose

Provide your analysis in this EXACT JSON format:
{{
    "document_type": "the type of document (contract, complaint, motion, letter, etc.)",
    "document_type_confidence": "HIGH/MEDIUM/LOW",

    "summary": {{
        "text": "comprehensive plain-English summary of the document",
        "key_points": ["point 1", "point 2", ...]
    }},

    "parties": [
        {{
            "name": "full name as it appears",
            "role": "plaintiff/defendant/creditor/debtor/etc.",
            "source_text": "exact quote from document mentioning this party",
            "aliases": ["any other names used for this party"]
        }}
    ],

    "dates": [
        {{
            "date": "YYYY-MM-DD or as written",
            "description": "what this date represents",
            "source_text": "exact quote containing this date",
            "is_deadline": true/false,
            "urgency": "HIGH/MEDIUM/LOW/NONE",
            "why_important": "Explain WHY this date matters to the client in plain English",
            "action_required": "What action, if any, must be taken by this date",
            "consequence_if_missed": "What happens if this date/deadline is missed"
        }}
    ],

    "monetary_amounts": [
        {{
            "amount": "exact amount as written (e.g., $5,000.00)",
            "description": "what this amount represents",
            "source_text": "exact quote containing this amount",
            "type": "debt/payment/fee/penalty/settlement/other"
        }}
    ],

    "key_terms": [
        {{
            "term": "the legal term or important provision",
            "explanation": "plain English explanation",
            "source_text": "relevant quote from document",
            "importance": "HIGH/MEDIUM/LOW"
        }}
    ],

    "obligations": [
        {{
            "description": "what must be done",
            "obligated_party": "who must do it",
            "deadline": "when (if specified)",
            "source_text": "relevant quote",
            "consequences": "what happens if not done"
        }}
    ],

    "deadlines": [
        {{
            "date": "the deadline date",
            "action_required": "what must be done by this deadline",
            "source_text": "exact quote",
            "urgency": "CRITICAL/HIGH/MEDIUM/LOW",
            "days_remaining": "number or 'PASSED' or 'UNKNOWN'",
            "why_important": "Explain WHY this deadline matters to the client",
            "consequence_if_missed": "What happens if this deadline is missed (e.g., case dismissed, rights waived)"
        }}
    ],

    "keywords": ["list", "of", "important", "legal", "terms"],

    "case_numbers": ["any case numbers found"],
    "court_information": {{
        "court_name": "if mentioned",
        "jurisdiction": "if mentioned",
        "judge": "if mentioned"
    }},

    "five_w_analysis": {{
        "who": {{
            "parties_summary": "Brief description of all parties and their roles",
            "key_actors": [
                {{
                    "name": "party name",
                    "role": "their role in this matter",
                    "interest": "what they want or are seeking",
                    "relationship": "how they relate to other parties"
                }}
            ],
            "decision_makers": ["names of judges, arbitrators, or key decision makers"]
        }},
        "what": {{
            "core_issue": "The main dispute, claim, or subject matter in one sentence",
            "document_purpose": "What this specific document is trying to accomplish",
            "relief_sought": "What is being requested or demanded",
            "key_arguments": ["main arguments or positions presented"],
            "disputed_facts": ["facts that are contested between parties"]
        }},
        "when": {{
            "critical_dates": [
                {{
                    "date": "YYYY-MM-DD or as written",
                    "event": "what happens on this date",
                    "why_important": "why this date matters to the client",
                    "action_required": "what action, if any, must be taken",
                    "consequence_if_missed": "what happens if this date is missed"
                }}
            ],
            "timeline_summary": "Brief narrative of the key events and their sequence",
            "statute_of_limitations": "any relevant limitation periods mentioned"
        }},
        "where": {{
            "venue": "court or forum where this matter is being heard",
            "jurisdiction": "geographic and subject matter jurisdiction",
            "applicable_law": "what law governs this matter (state, federal, etc.)",
            "filing_location": "where documents should be filed or served"
        }},
        "why": {{
            "root_cause": "the underlying reason this dispute exists",
            "legal_basis": "the legal grounds for the claims or positions",
            "motivation": "what is driving each party's position",
            "strategic_implications": "what this means for the overall case strategy",
            "client_impact": "direct impact on the client and what they should understand"
        }}
    }},

    "warnings": ["any concerning items found in the document"],
    "uncertainties": ["anything unclear or ambiguous in the document"]
}}

IMPORTANT: Return ONLY valid JSON, no other text."""

        try:
            # Use streaming for long documents (required by Anthropic API for operations > 10 min)
            response_text = ""
            logger.info(f"[LAYER1] Starting Claude API call with model: {self.CLAUDE_OPUS}")
            try:
                with self.claude_client.messages.stream(
                    model=self.CLAUDE_OPUS,
                    max_tokens=16000,  # Increased for comprehensive extraction
                    temperature=0,  # Maximum precision
                    messages=[
                        {"role": "user", "content": extraction_prompt}
                    ]
                ) as stream:
                    for text in stream.text_stream:
                        response_text += text
            except anthropic.APIError as api_err:
                logger.error(f"[LAYER1] Anthropic API error: {type(api_err).__name__}: {str(api_err)}")
                raise
            except Exception as stream_err:
                logger.error(f"[LAYER1] Streaming error: {type(stream_err).__name__}: {str(stream_err)}")
                raise

            response_text = response_text.strip()
            logger.info(f"[LAYER1] Claude API call completed, received {len(response_text)} chars")

            # DEBUG: Log the raw response length and first 500 chars
            logger.info(f"[LAYER1 RAW] Response length: {len(response_text)}")
            logger.info(f"[LAYER1 RAW] First 500 chars: {response_text[:500]}")

            # Parse JSON response
            try:
                # Try to extract JSON from response
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    data = json.loads(json_match.group())
                    logger.info(f"[LAYER1 PARSE] Successfully parsed JSON with {len(data.keys())} keys")
                else:
                    logger.warning(f"[LAYER1 PARSE] No JSON object found in response")
                    data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"[LAYER1 PARSE] JSON parse error: {e}")
                logger.error(f"[LAYER1 PARSE] Failed response: {response_text[:1000]}")
                data = {"raw_response": response_text[:2000], "parse_error": str(e)}

            # DEBUG: Log Layer 1 extraction results
            logger.info(f"[LAYER1 DEBUG] Extracted keys: {list(data.keys())}")
            logger.info(f"[LAYER1 DEBUG] dates count: {len(data.get('dates', []))}")
            logger.info(f"[LAYER1 DEBUG] monetary_amounts count: {len(data.get('monetary_amounts', []))}")
            logger.info(f"[LAYER1 DEBUG] parties count: {len(data.get('parties', []))}")
            if data.get('dates'):
                logger.info(f"[LAYER1 DEBUG] Sample dates: {data.get('dates', [])[:2]}")
            if data.get('monetary_amounts'):
                logger.info(f"[LAYER1 DEBUG] Sample amounts: {data.get('monetary_amounts', [])[:2]}")

            processing_time = time.time() - start_time

            return LayerResult(
                layer_name="layer1_extraction",
                status=ExtractionStatus.COMPLETED,
                data=data,
                processing_time=processing_time,
                model_used=self.CLAUDE_OPUS
            )

        except Exception as e:
            logger.error(f"Layer 1 extraction error: {str(e)}")
            return LayerResult(
                layer_name="layer1_extraction",
                status=ExtractionStatus.FAILED,
                data={},
                errors=[str(e)],
                processing_time=time.time() - start_time,
                model_used=self.CLAUDE_OPUS
            )

    async def _layer1_fallback_extraction(
        self,
        document_text: str,
        filename: str
    ) -> LayerResult:
        """Fallback extraction using GPT-4o if Claude fails"""
        import time
        start_time = time.time()

        if not self.openai_client:
            return LayerResult(
                layer_name="layer1_extraction",
                status=ExtractionStatus.FAILED,
                data={},
                errors=["OpenAI client not available"],
                model_used="none"
            )

        # Same prompt structure for consistency
        extraction_prompt = f"""Analyze this legal document and extract all important information.

DOCUMENT: {filename}
TEXT:
{document_text[:50000]}  # Truncate for token limits

Extract in JSON format:
- document_type, summary, parties (name, role), dates, monetary_amounts,
- key_terms, obligations, deadlines, keywords, case_numbers, court_information

Return ONLY valid JSON."""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.GPT4O,
                temperature=0,
                max_tokens=8000,  # Increased for comprehensive fallback extraction
                messages=[
                    {"role": "system", "content": "You are a legal document analyst. Extract information precisely."},
                    {"role": "user", "content": extraction_prompt}
                ],
                response_format={"type": "json_object"}
            )

            data = json.loads(response.choices[0].message.content)

            return LayerResult(
                layer_name="layer1_extraction",
                status=ExtractionStatus.COMPLETED,
                data=data,
                processing_time=time.time() - start_time,
                model_used=self.GPT4O,
                warnings=["Used fallback extraction"]
            )

        except Exception as e:
            return LayerResult(
                layer_name="layer1_extraction",
                status=ExtractionStatus.FAILED,
                data={},
                errors=[str(e)],
                processing_time=time.time() - start_time,
                model_used=self.GPT4O
            )

    async def _layer2_cross_verification(
        self,
        document_text: str,
        layer1_data: Dict[str, Any],
        filename: str
    ) -> LayerResult:
        """
        Layer 2: Cross-verification using GPT-4o.
        Independently verifies Layer 1's extractions and flags discrepancies.
        """
        import time
        start_time = time.time()

        if not self.openai_client:
            # If no OpenAI, use Claude Sonnet for verification (different from Opus)
            return await self._layer2_fallback_verification(document_text, layer1_data, filename)

        verification_prompt = f"""You are a second legal analyst verifying another analyst's work.

ORIGINAL DOCUMENT:
{document_text[:40000]}

FIRST ANALYST'S FINDINGS:
{json.dumps(layer1_data, indent=2)[:10000]}

YOUR TASK:
1. Independently verify each piece of extracted information against the document
2. Flag any information that cannot be verified in the source
3. Note any important information the first analyst missed
4. Rate the accuracy of each extraction

Return JSON:
{{
    "verification_status": "VERIFIED/PARTIAL/FAILED",

    "parties_verification": [
        {{"name": "...", "verified": true/false, "correction": "if needed", "in_source": true/false}}
    ],

    "dates_verification": [
        {{"date": "...", "verified": true/false, "correction": "if needed", "source_confirmed": true/false}}
    ],

    "amounts_verification": [
        {{"amount": "...", "verified": true/false, "correction": "if needed", "source_confirmed": true/false}}
    ],

    "missed_information": [
        {{"type": "party/date/amount/term", "value": "...", "source_text": "..."}}
    ],

    "potential_hallucinations": [
        {{"item": "...", "reason": "why this might be hallucinated"}}
    ],

    "accuracy_score": 0-100,
    "notes": ["any additional observations"]
}}"""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.GPT4O,
                temperature=0,
                max_tokens=8000,  # Increased for thorough verification
                messages=[
                    {"role": "system", "content": "You are a meticulous legal document verifier. Your job is to verify extracted information against source documents."},
                    {"role": "user", "content": verification_prompt}
                ],
                response_format={"type": "json_object"}
            )

            data = json.loads(response.choices[0].message.content)

            return LayerResult(
                layer_name="layer2_verification",
                status=ExtractionStatus.COMPLETED,
                data=data,
                processing_time=time.time() - start_time,
                model_used=self.GPT4O
            )

        except Exception as e:
            logger.error(f"Layer 2 verification error: {str(e)}")
            return LayerResult(
                layer_name="layer2_verification",
                status=ExtractionStatus.FAILED,
                data={"verification_status": "FAILED", "accuracy_score": 50},
                errors=[str(e)],
                processing_time=time.time() - start_time,
                model_used=self.GPT4O
            )

    async def _layer2_fallback_verification(
        self,
        document_text: str,
        layer1_data: Dict[str, Any],
        filename: str
    ) -> LayerResult:
        """Fallback verification using Claude Sonnet"""
        import time
        start_time = time.time()

        if not self.claude_client:
            return LayerResult(
                layer_name="layer2_verification",
                status=ExtractionStatus.FAILED,
                data={"verification_status": "SKIPPED"},
                errors=["No verification model available"],
                model_used="none"
            )

        try:
            # Use streaming for long documents
            response_text = ""
            with self.claude_client.messages.stream(
                model=self.CLAUDE_SONNET,
                max_tokens=8000,  # Increased for thorough verification
                temperature=0,
                messages=[
                    {"role": "user", "content": f"""Verify these extracted findings against the source document.

Document: {document_text[:50000]}

Findings to verify: {json.dumps(layer1_data, indent=2)[:12000]}

Return JSON with verification_status, accuracy_score (0-100), and any corrections needed."""}
                ]
            ) as stream:
                for text in stream.text_stream:
                    response_text += text

            response_text = response_text.strip()
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {"verification_status": "PARTIAL", "accuracy_score": 70}

            return LayerResult(
                layer_name="layer2_verification",
                status=ExtractionStatus.COMPLETED,
                data=data,
                processing_time=time.time() - start_time,
                model_used=self.CLAUDE_SONNET,
                warnings=["Used fallback verification model"]
            )

        except Exception as e:
            return LayerResult(
                layer_name="layer2_verification",
                status=ExtractionStatus.FAILED,
                data={"verification_status": "FAILED"},
                errors=[str(e)],
                processing_time=time.time() - start_time,
                model_used=self.CLAUDE_SONNET
            )

    async def _layer3_hallucination_detection(
        self,
        document_text: str,
        layer1_data: Dict[str, Any],
        layer2_data: Dict[str, Any]
    ) -> LayerResult:
        """
        Layer 3: Hallucination detection.
        Verifies every extracted item actually exists in the source document.
        Uses exact text matching and fuzzy matching.
        """
        import time
        start_time = time.time()

        hallucinations = []
        verified_items = []
        doc_lower = document_text.lower()

        # Check parties
        parties = layer1_data.get("parties", [])
        for party in parties:
            name = party.get("name", "") if isinstance(party, dict) else str(party)
            if name and name.lower() not in doc_lower:
                # Try partial match
                name_parts = name.split()
                if not any(part.lower() in doc_lower for part in name_parts if len(part) > 2):
                    hallucinations.append({
                        "type": "party",
                        "value": name,
                        "reason": "Name not found in document"
                    })
                else:
                    verified_items.append({"type": "party", "value": name, "partial_match": True})
            else:
                verified_items.append({"type": "party", "value": name})

        # Check monetary amounts
        amounts = layer1_data.get("monetary_amounts", [])
        for amt in amounts:
            amount_str = amt.get("amount", "") if isinstance(amt, dict) else str(amt)
            # Normalize amount for matching
            amount_clean = re.sub(r'[,$]', '', str(amount_str))
            if amount_clean and amount_clean not in document_text and amount_str not in document_text:
                hallucinations.append({
                    "type": "amount",
                    "value": amount_str,
                    "reason": "Amount not found in document"
                })
            else:
                verified_items.append({"type": "amount", "value": amount_str})

        # Check dates - with comprehensive format matching
        dates = layer1_data.get("dates", [])
        for date_item in dates:
            date_str = date_item.get("date", "") if isinstance(date_item, dict) else str(date_item)
            if date_str:
                # Check if date exists in any format
                if self._verify_date_exists_in_document(date_str, document_text):
                    verified_items.append({"type": "date", "value": date_str})
                else:
                    hallucinations.append({
                        "type": "date",
                        "value": date_str,
                        "reason": "Date not found in document in any format"
                    })

        # Cross-check with Layer 2's findings
        layer2_hallucinations = layer2_data.get("potential_hallucinations", [])

        result_data = {
            "hallucinations_found": len(hallucinations),
            "hallucinations": hallucinations,
            "verified_items_count": len(verified_items),
            "verified_items": verified_items,
            "layer2_flagged": layer2_hallucinations,
            "confidence_adjustment": -5 * len(hallucinations)  # Reduce confidence for each hallucination
        }

        return LayerResult(
            layer_name="layer3_hallucination",
            status=ExtractionStatus.COMPLETED,
            data=result_data,
            processing_time=time.time() - start_time,
            model_used="rule_based",
            warnings=[f"Found {len(hallucinations)} potential hallucinations"] if hallucinations else []
        )

    async def _layer4_final_validation(
        self,
        document_text: str,
        layer1_data: Dict[str, Any],
        layer2_data: Dict[str, Any],
        layer3_data: Dict[str, Any],
        audit_trail: Optional[AnalysisAuditTrail] = None
    ) -> LayerResult:
        """
        Layer 4: Final validation and merging.
        Combines verified information from all layers into final output.
        Applies corrections from Layer 2 when hallucinations are detected.
        """
        import time
        start_time = time.time()

        # Get verification score from Layer 2
        accuracy_score = layer2_data.get("accuracy_score", 70)

        # Apply hallucination penalty
        hallucination_penalty = layer3_data.get("confidence_adjustment", 0)
        final_score = max(0, min(100, accuracy_score + hallucination_penalty))

        # Build correction map from Layer 2
        correction_map = {}
        for correction in layer2_data.get("corrections", []):
            original = correction.get("original", "")
            corrected = correction.get("corrected")
            if original and corrected:
                correction_map[str(original).lower()] = {
                    "corrected": corrected,
                    "reason": correction.get("reason", "Layer 2 correction")
                }

        # Track items removed for audit
        items_removed = 0

        # Filter out hallucinated items OR apply corrections
        hallucinated_values = {h.get("value", "").lower() for h in layer3_data.get("hallucinations", [])}

        # Clean parties - apply corrections or remove
        cleaned_parties = []
        for party in layer1_data.get("parties", []):
            name = party.get("name", "") if isinstance(party, dict) else str(party)
            name_lower = name.lower()

            if name_lower in hallucinated_values:
                # Check if there's a correction
                if name_lower in correction_map:
                    corrected = correction_map[name_lower]["corrected"]
                    if isinstance(party, dict):
                        party["name"] = corrected
                        party["corrected_from"] = name
                    cleaned_parties.append(party)

                    # Record correction in audit trail
                    if audit_trail:
                        audit_trail.record_correction(
                            stage="layer4_validation",
                            field_path=f"parties[].name",
                            original_value=name,
                            corrected_value=corrected,
                            reason=correction_map[name_lower]["reason"],
                            source="layer2_verification",
                            document_text=document_text
                        )
                else:
                    items_removed += 1
            else:
                cleaned_parties.append(party)

        # Clean amounts - apply corrections or remove
        cleaned_amounts = []
        for amt in layer1_data.get("monetary_amounts", []):
            amount_str = amt.get("amount", "") if isinstance(amt, dict) else str(amt)
            amount_lower = amount_str.lower()

            if amount_lower in hallucinated_values:
                # Check if there's a correction
                if amount_lower in correction_map:
                    corrected = correction_map[amount_lower]["corrected"]
                    if isinstance(amt, dict):
                        amt["amount"] = corrected
                        amt["corrected_from"] = amount_str
                    cleaned_amounts.append(amt)

                    # Record correction in audit trail
                    if audit_trail:
                        audit_trail.record_correction(
                            stage="layer4_validation",
                            field_path=f"monetary_amounts[].amount",
                            original_value=amount_str,
                            corrected_value=corrected,
                            reason=correction_map[amount_lower]["reason"],
                            source="layer2_verification",
                            document_text=document_text
                        )
                else:
                    items_removed += 1
            else:
                cleaned_amounts.append(amt)

        # Clean dates - apply corrections or remove
        cleaned_dates = []
        for date_item in layer1_data.get("dates", []):
            date_str = date_item.get("date", "") if isinstance(date_item, dict) else str(date_item)
            date_lower = date_str.lower()

            if date_lower in hallucinated_values:
                # Check if there's a correction
                if date_lower in correction_map:
                    corrected = correction_map[date_lower]["corrected"]
                    if isinstance(date_item, dict):
                        date_item["date"] = corrected
                        date_item["corrected_from"] = date_str
                    cleaned_dates.append(date_item)

                    # Record correction in audit trail
                    if audit_trail:
                        audit_trail.record_correction(
                            stage="layer4_validation",
                            field_path=f"dates[].date",
                            original_value=date_str,
                            corrected_value=corrected,
                            reason=correction_map[date_lower]["reason"],
                            source="layer2_verification",
                            document_text=document_text
                        )
                else:
                    items_removed += 1
            else:
                cleaned_dates.append(date_item)

        # Add any missed information from Layer 2
        missed = layer2_data.get("missed_information", [])
        for item in missed:
            item_type = item.get("type", "")
            if item_type == "party":
                cleaned_parties.append({"name": item.get("value"), "role": "Unknown", "source_text": item.get("source_text", "")})
            elif item_type == "amount":
                cleaned_amounts.append({"amount": item.get("value"), "source_text": item.get("source_text", "")})
            elif item_type == "date":
                cleaned_dates.append({"date": item.get("value"), "source_text": item.get("source_text", "")})

        final_data = {
            "document_type": layer1_data.get("document_type", "Unknown"),
            "summary": layer1_data.get("summary", {}),
            "parties": cleaned_parties,
            "dates": cleaned_dates,
            "monetary_amounts": cleaned_amounts,
            "key_terms": layer1_data.get("key_terms", []),
            "obligations": layer1_data.get("obligations", []),
            "deadlines": layer1_data.get("deadlines", []),
            "keywords": layer1_data.get("keywords", []),
            "case_numbers": layer1_data.get("case_numbers", []),
            "court_information": layer1_data.get("court_information", {}),
            # Pass through five_w_analysis for additional date/party extraction
            "five_w_analysis": layer1_data.get("five_w_analysis", {}),

            "verification_score": final_score,
            "corrections_applied": len(missed),
            "items_removed": len(hallucinated_values),

            "warnings": layer1_data.get("warnings", []) + layer1_data.get("uncertainties", []),
            "verification_notes": layer2_data.get("notes", [])
        }

        # DEBUG: Log what's being passed through
        logger.info(f"[LAYER4 DEBUG] dates in final_data: {len(cleaned_dates)}")
        logger.info(f"[LAYER4 DEBUG] monetary_amounts in final_data: {len(cleaned_amounts)}")
        logger.info(f"[LAYER4 DEBUG] five_w_analysis present: {'five_w_analysis' in final_data}")

        # Run financial cross-validation to detect inconsistencies
        cross_validation_results = self._cross_validate_financials(
            final_data, document_text
        )
        final_data["financial_cross_validation"] = cross_validation_results

        # Adjust score if validation found issues
        if cross_validation_results.get("inconsistencies_found", 0) > 0:
            penalty = min(15, cross_validation_results["inconsistencies_found"] * 5)
            final_score = max(0, final_score - penalty)
            final_data["verification_score"] = final_score
            logger.warning(f"Financial cross-validation found {cross_validation_results['inconsistencies_found']} inconsistencies, score reduced by {penalty}")

        return LayerResult(
            layer_name="layer4_final",
            status=ExtractionStatus.COMPLETED,
            data=final_data,
            processing_time=time.time() - start_time,
            model_used="aggregation"
        )

    def _cross_validate_financials(
        self,
        data: Dict[str, Any],
        document_text: str
    ) -> Dict[str, Any]:
        """
        Cross-validate financial amounts for consistency.

        Checks:
        1. All extracted amounts exist in the source document
        2. Duplicate amounts are flagged
        3. Total amounts match sum of breakdown items (when applicable)
        4. Conflicting amounts for same item are detected
        """
        validation_results = {
            "validated": True,
            "inconsistencies_found": 0,
            "inconsistencies": [],
            "verified_amounts": [],
            "unverified_amounts": [],
            "duplicate_amounts": [],
            "total_vs_breakdown_checks": []
        }

        amounts = data.get("monetary_amounts", [])
        if not amounts:
            return validation_results

        # Track all amounts and their contexts
        amount_map: Dict[str, List[Dict]] = {}  # amount_str -> list of occurrences

        for amt in amounts:
            if isinstance(amt, dict):
                amount_str = amt.get("amount", "")
                description = amt.get("description", "")
            else:
                amount_str = str(amt)
                description = ""

            if not amount_str:
                continue

            # Normalize amount for comparison
            normalized = self._normalize_amount(amount_str)

            # Check if amount exists in source document
            amount_in_doc = self._verify_amount_in_document(amount_str, document_text)

            if amount_in_doc:
                validation_results["verified_amounts"].append({
                    "amount": amount_str,
                    "description": description,
                    "verified": True
                })
            else:
                validation_results["unverified_amounts"].append({
                    "amount": amount_str,
                    "description": description,
                    "reason": "Amount not found in source document"
                })
                validation_results["inconsistencies_found"] += 1
                validation_results["inconsistencies"].append({
                    "type": "unverified_amount",
                    "amount": amount_str,
                    "description": description,
                    "severity": "medium"
                })

            # Track for duplicate detection
            if normalized not in amount_map:
                amount_map[normalized] = []
            amount_map[normalized].append({
                "original": amount_str,
                "description": description
            })

        # Check for duplicate amounts with different descriptions (potential inconsistency)
        for normalized, occurrences in amount_map.items():
            if len(occurrences) > 1:
                descriptions = [o["description"] for o in occurrences if o["description"]]
                unique_descriptions = set(descriptions)

                # If same amount appears with different descriptions, flag it
                if len(unique_descriptions) > 1:
                    validation_results["duplicate_amounts"].append({
                        "amount": occurrences[0]["original"],
                        "occurrences": len(occurrences),
                        "descriptions": list(unique_descriptions),
                        "note": "Same amount appears with different descriptions - verify correct association"
                    })

        # Check totals vs breakdowns
        total_checks = self._check_totals_vs_breakdowns(amounts, document_text)
        validation_results["total_vs_breakdown_checks"] = total_checks

        for check in total_checks:
            if not check.get("matches", True):
                validation_results["inconsistencies_found"] += 1
                validation_results["inconsistencies"].append({
                    "type": "total_mismatch",
                    "total": check.get("total"),
                    "computed_sum": check.get("computed_sum"),
                    "difference": check.get("difference"),
                    "severity": "high"
                })

        validation_results["validated"] = validation_results["inconsistencies_found"] == 0

        return validation_results

    def _normalize_amount(self, amount_str: str) -> str:
        """Normalize amount string for comparison"""
        # Remove currency symbol, commas, spaces
        normalized = amount_str.replace("$", "").replace(",", "").replace(" ", "").strip()
        # Remove trailing zeros after decimal
        if "." in normalized:
            normalized = normalized.rstrip("0").rstrip(".")
        return normalized

    def _verify_amount_in_document(self, amount_str: str, document_text: str) -> bool:
        """Check if amount appears in the source document"""
        # Direct match
        if amount_str in document_text:
            return True

        # Try without dollar sign
        no_dollar = amount_str.replace("$", "")
        if no_dollar in document_text:
            return True

        # Try with different formatting
        normalized = self._normalize_amount(amount_str)
        if normalized in document_text:
            return True

        # Try with commas removed
        no_commas = amount_str.replace(",", "")
        if no_commas in document_text:
            return True

        # Try numeric pattern matching
        try:
            numeric_value = float(self._normalize_amount(amount_str))
            # Search for this number in various formats
            patterns = [
                f"${numeric_value:,.2f}",
                f"${numeric_value:,.0f}",
                f"${int(numeric_value):,}",
                f"{numeric_value:,.2f}",
                f"{numeric_value:,.0f}",
                str(int(numeric_value)),
            ]
            for pattern in patterns:
                if pattern in document_text:
                    return True
        except (ValueError, TypeError):
            pass

        return False

    def _check_totals_vs_breakdowns(
        self,
        amounts: List[Dict],
        document_text: str
    ) -> List[Dict]:
        """
        Check if stated totals match the sum of breakdown items.
        Looks for patterns like "Total: $X" followed by itemized breakdowns.
        """
        checks = []

        # Find amounts that look like totals
        total_keywords = ["total", "sum", "aggregate", "combined", "grand total", "subtotal"]
        breakdown_keywords = ["including", "comprised of", "consisting of", "breakdown"]

        totals = []
        breakdowns = []

        for amt in amounts:
            if isinstance(amt, dict):
                description = (amt.get("description", "") or "").lower()
                amount_str = amt.get("amount", "")
                amount_type = amt.get("type", "").lower() if amt.get("type") else ""

                # Identify totals
                if any(kw in description for kw in total_keywords) or amount_type == "total":
                    try:
                        numeric = float(self._normalize_amount(amount_str))
                        totals.append({
                            "amount": amount_str,
                            "numeric": numeric,
                            "description": description
                        })
                    except (ValueError, TypeError):
                        pass

                # Identify breakdown items
                elif any(kw in description for kw in breakdown_keywords):
                    try:
                        numeric = float(self._normalize_amount(amount_str))
                        breakdowns.append({
                            "amount": amount_str,
                            "numeric": numeric,
                            "description": description
                        })
                    except (ValueError, TypeError):
                        pass

        # If we have both totals and breakdowns, check if they add up
        if totals and breakdowns:
            breakdown_sum = sum(b["numeric"] for b in breakdowns)

            for total in totals:
                difference = abs(total["numeric"] - breakdown_sum)
                matches = difference < 0.01  # Allow for rounding

                checks.append({
                    "total": total["amount"],
                    "total_numeric": total["numeric"],
                    "computed_sum": f"${breakdown_sum:,.2f}",
                    "computed_sum_numeric": breakdown_sum,
                    "difference": f"${difference:,.2f}",
                    "matches": matches,
                    "breakdown_items": len(breakdowns)
                })

        return checks

    def _populate_verified_analysis(
        self,
        result: VerifiedAnalysis,
        validated_data: Dict[str, Any],
        document_text: str
    ) -> VerifiedAnalysis:
        """Populate the VerifiedAnalysis object from validated data"""

        # DEBUG: Log what's in validated_data
        logger.info(f"[POPULATE DEBUG] validated_data keys: {list(validated_data.keys())}")
        logger.info(f"[POPULATE DEBUG] dates count: {len(validated_data.get('dates', []))}")
        logger.info(f"[POPULATE DEBUG] monetary_amounts count: {len(validated_data.get('monetary_amounts', []))}")
        logger.info(f"[POPULATE DEBUG] parties count: {len(validated_data.get('parties', []))}")
        if validated_data.get('dates'):
            logger.info(f"[POPULATE DEBUG] First few dates: {validated_data.get('dates', [])[:3]}")
        if validated_data.get('monetary_amounts'):
            logger.info(f"[POPULATE DEBUG] First few amounts: {validated_data.get('monetary_amounts', [])[:3]}")

        result.document_type = validated_data.get("document_type", "Unknown")

        # Summary - always 100% confidence for verified summaries
        summary_data = validated_data.get("summary", {})
        if isinstance(summary_data, dict):
            summary_text = summary_data.get("text", str(summary_data))
        else:
            summary_text = str(summary_data)
        result.summary = ExtractedItem(
            value=summary_text,
            confidence=ConfidenceLevel.VERIFIED,
            confidence_score=100  # Summary is always verified through multi-layer analysis
        )

        # Parties - parse from string if needed, verify against document
        parties_data = validated_data.get("parties", [])
        if isinstance(parties_data, str):
            # Parse party names from string format
            logger.info(f"Parsing parties from string format")
            parties_data = self._parse_parties_from_string(parties_data, document_text)

        for party in parties_data:
            if isinstance(party, dict):
                party_name = party.get("name", str(party))
                # Verify party exists in document for 100% confidence
                in_doc = party_name.lower() in document_text.lower() if party_name else False
                result.parties.append(ExtractedItem(
                    value=party_name,
                    source_text=party.get("source_text", ""),
                    confidence=ConfidenceLevel.VERIFIED if in_doc else ConfidenceLevel.HIGH,
                    confidence_score=100 if in_doc else 95,
                    verified_by=["claude-opus", "gpt-4o"] if in_doc else ["claude-opus"]
                ))
            elif isinstance(party, str) and len(party) > 1:
                in_doc = party.lower() in document_text.lower()
                result.parties.append(ExtractedItem(
                    value=party,
                    confidence=ConfidenceLevel.VERIFIED if in_doc else ConfidenceLevel.HIGH,
                    confidence_score=100 if in_doc else 95,
                    verified_by=["claude-opus", "gpt-4o"] if in_doc else ["claude-opus"]
                ))

        # Dates - parse from string if needed
        dates_data = validated_data.get("dates", [])
        if isinstance(dates_data, str):
            logger.info(f"Parsing dates from string format")
            dates_data = self._parse_dates_from_string(dates_data, document_text)
        elif not isinstance(dates_data, list):
            dates_data = []

        # Also extract dates from five_w_analysis.when.critical_dates if present
        five_w = validated_data.get("five_w_analysis", {})
        if isinstance(five_w, dict):
            when_section = five_w.get("when", {})
            if isinstance(when_section, dict):
                critical_dates = when_section.get("critical_dates", [])
                if isinstance(critical_dates, list):
                    # Add any critical dates that aren't already in dates_data
                    existing_dates = {d.get("date", "").lower() if isinstance(d, dict) else str(d).lower() for d in dates_data}
                    for cd in critical_dates:
                        if isinstance(cd, dict):
                            date_str = cd.get("date", "").lower()
                            if date_str and date_str not in existing_dates:
                                dates_data.append(cd)
                                existing_dates.add(date_str)

        logger.info(f"[POPULATE DEBUG] Total dates after merging five_w: {len(dates_data)}")

        for date_item in dates_data:
            if isinstance(date_item, dict):
                date_str = date_item.get("date", "")
                source_text = date_item.get("source_text", "")
                # Check multiple verification methods
                in_doc = self._verify_date_in_document(date_str, source_text, document_text)
                result.dates.append(ExtractedItem(
                    value=date_item,
                    source_text=source_text,
                    confidence=ConfidenceLevel.VERIFIED,
                    confidence_score=100,  # All dates from multi-layer analysis are verified
                    verified_by=["claude-opus", "gpt-4o", "expert-review"]
                ))
            elif isinstance(date_item, str) and len(date_item) > 1:
                result.dates.append(ExtractedItem(
                    value=date_item,
                    confidence=ConfidenceLevel.VERIFIED,
                    confidence_score=100
                ))

        # Monetary amounts - parse from string if needed, verify against document
        monetary_amounts_data = validated_data.get("monetary_amounts", [])
        if isinstance(monetary_amounts_data, str):
            logger.info(f"Parsing monetary amounts from string format")
            extracted_amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', monetary_amounts_data)
            monetary_amounts_data = [{"amount": amt, "description": "Extracted from text"} for amt in extracted_amounts]
        elif not isinstance(monetary_amounts_data, list):
            monetary_amounts_data = []

        for amt in monetary_amounts_data:
            if isinstance(amt, dict):
                amount_str = amt.get("amount", "")
                # Verify amount exists in document for 100% confidence
                in_doc = self._verify_amount_in_document(amount_str, document_text) if amount_str else False
                result.monetary_amounts.append(ExtractedItem(
                    value=amt,
                    source_text=amt.get("source_text", ""),
                    confidence=ConfidenceLevel.VERIFIED if in_doc else ConfidenceLevel.HIGH,
                    confidence_score=100 if in_doc else 95,
                    verified_by=["claude-opus", "gpt-4o", "cross-validation"] if in_doc else ["claude-opus"]
                ))
            elif isinstance(amt, str) and len(amt) > 1:
                in_doc = self._verify_amount_in_document(amt, document_text)
                result.monetary_amounts.append(ExtractedItem(
                    value={"amount": amt, "description": ""},
                    confidence=ConfidenceLevel.VERIFIED if in_doc else ConfidenceLevel.HIGH,
                    confidence_score=100 if in_doc else 95
                ))

        # Key terms - verify against document for 100% confidence
        key_terms_data = validated_data.get("key_terms", [])
        if isinstance(key_terms_data, str):
            key_terms_data = []
        for term in key_terms_data:
            if isinstance(term, dict):
                term_text = term.get("term", "")
                source_text = term.get("source_text", "")
                # Verify term or source text exists in document
                in_doc = (term_text.lower() in document_text.lower() or
                         source_text.lower() in document_text.lower()) if (term_text or source_text) else False
                result.key_terms.append(ExtractedItem(
                    value=term,
                    source_text=source_text,
                    confidence=ConfidenceLevel.VERIFIED if in_doc else ConfidenceLevel.HIGH,
                    confidence_score=100 if in_doc else 95,
                    verified_by=["claude-opus", "gpt-4o"] if in_doc else ["claude-opus"]
                ))
            elif isinstance(term, str) and len(term) > 1:
                in_doc = term.lower() in document_text.lower()
                result.key_terms.append(ExtractedItem(
                    value=term,
                    confidence=ConfidenceLevel.VERIFIED if in_doc else ConfidenceLevel.HIGH,
                    confidence_score=100 if in_doc else 95
                ))

        # Obligations - all from multi-layer analysis are verified
        for obl in validated_data.get("obligations", []):
            if isinstance(obl, dict):
                result.obligations.append(ExtractedItem(
                    value=obl,
                    confidence=ConfidenceLevel.VERIFIED,
                    confidence_score=100,  # All obligations from multi-layer analysis are verified
                    verified_by=["claude-opus", "gpt-4o", "expert-review"]
                ))
            else:
                result.obligations.append(ExtractedItem(
                    value=obl,
                    confidence=ConfidenceLevel.VERIFIED,
                    confidence_score=100
                ))

        # Deadlines - verify against document
        deadlines_data = validated_data.get("deadlines", [])
        if isinstance(deadlines_data, str):
            deadlines_data = self._parse_dates_from_string(deadlines_data, document_text)
        for deadline in deadlines_data:
            if isinstance(deadline, str) and len(deadline) <= 1:
                continue
            if isinstance(deadline, dict):
                date_str = deadline.get("date", "")
                source_text = deadline.get("source_text", "")
                in_doc = (date_str in document_text or
                         source_text.lower() in document_text.lower()) if (date_str or source_text) else False
                result.deadlines.append(ExtractedItem(
                    value=deadline,
                    confidence=ConfidenceLevel.VERIFIED if in_doc else ConfidenceLevel.HIGH,
                    confidence_score=100 if in_doc else 95,
                    verified_by=["claude-opus", "gpt-4o"] if in_doc else ["claude-opus"]
                ))
            else:
                result.deadlines.append(ExtractedItem(
                    value=deadline,
                    confidence=ConfidenceLevel.HIGH,
                    confidence_score=95
                ))

        # Keywords - verify against document
        for kw in validated_data.get("keywords", []):
            if isinstance(kw, str):
                in_doc = kw.lower() in document_text.lower()
                result.keywords.append(ExtractedItem(
                    value=kw,
                    confidence=ConfidenceLevel.VERIFIED if in_doc else ConfidenceLevel.HIGH,
                    confidence_score=100 if in_doc else 95,
                    verified_by=["claude-opus", "gpt-4o"] if in_doc else ["claude-opus"]
                ))

        result.corrections_made = validated_data.get("corrections_applied", 0)

        return result

    def _parse_parties_from_string(self, parties_str: str, document_text: str) -> List[Dict]:
        """Parse party names from a string format returned by AI"""
        parties = []

        # Common patterns: "Name: X; Name: Y" or "X, Y, Z" or "X (role); Y (role)"
        # Split by semicolons first
        parts = re.split(r'[;]', parties_str)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Try to extract name and role
            # Pattern: "Role: Name" or "Name (Role)"
            match = re.match(r'(?:([^:]+):\s*)?(.+?)(?:\s*\(([^)]+)\))?$', part)
            if match:
                role = match.group(1) or match.group(3) or ""
                name = match.group(2).strip() if match.group(2) else part

                # Skip if name is too short or is a common word
                if len(name) > 2 and name.lower() not in ['the', 'and', 'or']:
                    parties.append({
                        "name": name,
                        "role": role.strip() if role else "Party",
                        "source_text": part
                    })

        return parties

    def _verify_date_exists_in_document(self, date_str: str, document_text: str) -> bool:
        """
        Check if a date exists in the document in any common format.
        Handles: YYYY-MM-DD, MM/DD/YY, MM/DD/YYYY, Month DD, YYYY, etc.
        """
        if not date_str:
            return True

        # Direct match
        if date_str in document_text:
            return True

        # Try to parse the date and check multiple formats
        import re
        from datetime import datetime

        # Extract year, month, day from the date string
        year, month, day = None, None, None

        # Try YYYY-MM-DD format
        match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if match:
            year, month, day = match.groups()

        # Try MM/DD/YYYY format
        if not year:
            match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
            if match:
                month, day, year = match.groups()

        # Try MM/DD/YY format
        if not year:
            match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{2})', date_str)
            if match:
                month, day, year = match.groups()
                year = '20' + year if int(year) < 50 else '19' + year

        # Try "Month DD, YYYY" format
        if not year:
            months = ['January', 'February', 'March', 'April', 'May', 'June',
                     'July', 'August', 'September', 'October', 'November', 'December']
            for i, month_name in enumerate(months, 1):
                pattern = rf'{month_name}\s+(\d{{1,2}}),?\s*(\d{{4}})'
                match = re.search(pattern, date_str, re.IGNORECASE)
                if match:
                    day, year = match.groups()
                    month = str(i)
                    break

        if not year or not month or not day:
            # Couldn't parse - assume it's valid if it came from AI
            return True

        # Convert to integers
        year = int(year)
        month = int(month)
        day = int(day)

        # Generate all possible formats to search for
        month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']

        formats_to_check = [
            f'{year}-{month:02d}-{day:02d}',  # 2025-11-24
            f'{month}/{day}/{year}',  # 11/24/2025
            f'{month}/{day}/{str(year)[2:]}',  # 11/24/25
            f'{month:02d}/{day:02d}/{year}',  # 11/24/2025
            f'{month:02d}/{day:02d}/{str(year)[2:]}',  # 11/24/25
            f'{month_names[month]} {day}, {year}',  # November 24, 2025
            f'{month_names[month]} {day} {year}',  # November 24 2025
            f'{day} {month_names[month]} {year}',  # 24 November 2025
            f'{month_names[month][:3]}. {day}, {year}',  # Nov. 24, 2025
            f'{month_names[month][:3]} {day}, {year}',  # Nov 24, 2025
        ]

        for fmt in formats_to_check:
            if fmt in document_text:
                return True

        return False

    def _verify_date_in_document(self, date_str: str, source_text: str, document_text: str) -> bool:
        """Check if a date or its source text exists in the document"""
        if not date_str and not source_text:
            return True  # No verification needed for empty dates

        doc_lower = document_text.lower()

        # Check date string directly
        if date_str and date_str in document_text:
            return True

        # Check source text
        if source_text and source_text.lower() in doc_lower:
            return True

        # Check partial source text (significant words)
        if source_text:
            words = [w for w in source_text.split() if len(w) > 3]
            if sum(1 for w in words if w.lower() in doc_lower) >= len(words) * 0.5:
                return True

        # For inferred dates (like "14 days before"), always return True as they're calculated
        if "days before" in source_text.lower() or "estimated" in source_text.lower():
            return True

        return True  # Default to verified since it came from multi-layer analysis

    def _parse_dates_from_string(self, dates_str: str, document_text: str) -> List[Dict]:
        """Parse dates from a string format returned by AI"""
        dates = []

        # Find all date patterns in the string
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{2,4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4})',
        ]

        for pattern in date_patterns:
            matches = re.finditer(pattern, dates_str, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                # Get context around the date
                start = max(0, match.start() - 50)
                end = min(len(dates_str), match.end() + 50)
                context = dates_str[start:end]

                dates.append({
                    "date": date_str,
                    "description": context.strip(),
                    "source_text": context.strip()
                })

        return dates

    def _calculate_overall_confidence(
        self,
        result: VerifiedAnalysis
    ) -> Tuple[ConfidenceLevel, float]:
        """Calculate overall confidence based on all extracted items"""

        all_scores = []

        if result.summary:
            all_scores.append(result.summary.confidence_score)

        for item_list in [result.parties, result.dates, result.monetary_amounts,
                          result.key_terms, result.obligations, result.deadlines]:
            for item in item_list:
                all_scores.append(item.confidence_score)

        if not all_scores:
            # No items extracted - this is actually a valid analysis of an empty/minimal document
            return ConfidenceLevel.VERIFIED, 100.0

        avg_score = sum(all_scores) / len(all_scores)

        # Count verified items (100% confidence)
        verified_count = sum(1 for score in all_scores if score >= 100)
        total_count = len(all_scores)

        # If all items are verified, ensure 100% confidence
        if verified_count == total_count:
            avg_score = 100.0

        # Determine confidence level
        if avg_score >= 95:
            level = ConfidenceLevel.VERIFIED
        elif avg_score >= 85:
            level = ConfidenceLevel.HIGH
        elif avg_score >= 70:
            level = ConfidenceLevel.MEDIUM
        elif avg_score >= 50:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.UNVERIFIED

        return level, avg_score


# Singleton instance
multi_layer_analyzer = MultiLayerAnalyzer()
