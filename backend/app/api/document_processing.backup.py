"""
Document Processing API for Legal AI System
Real AI-powered document analysis using OpenAI
"""
# Force reload to pick up DELETE endpoint

import logging
import uuid
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Body, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..src.services.dual_ai_service import dual_ai_service
from ..src.services.pdf_service import pdf_service
from ..src.core.database import get_db
from ..models.legal_documents import Document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["Document Processing"])


class AnalyzeTextRequest(BaseModel):
    text: str
    filename: str = "unknown.txt"
    session_id: str = None  # Frontend session ID
    document_id: str = None  # Optional: update existing document
    include_operational_details: bool = True  # Extract action items, obligations, etc.
    include_financial_details: bool = True  # Extract detailed financial information


def _validate_analysis_response(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize the analysis response to ensure consistent structure
    for frontend consumption.

    Args:
        analysis: Raw analysis result from dual AI service

    Returns:
        Normalized analysis with guaranteed array structures
    """
    # Ensure deadlines is always an array
    if not analysis.get("deadlines"):
        analysis["deadlines"] = []
    if not isinstance(analysis["deadlines"], list):
        # Convert single item or string to array
        deadlines = analysis["deadlines"]
        if isinstance(deadlines, str):
            analysis["deadlines"] = [{
                "date": "Unknown",
                "description": deadlines
            }]
        elif isinstance(deadlines, dict):
            analysis["deadlines"] = [deadlines]
        else:
            analysis["deadlines"] = []

    # Ensure key_dates is always an array
    if not analysis.get("key_dates"):
        analysis["key_dates"] = []
    if not isinstance(analysis["key_dates"], list):
        key_dates = analysis["key_dates"]
        if isinstance(key_dates, str):
            analysis["key_dates"] = [{
                "date": "Unknown",
                "description": key_dates
            }]
        elif isinstance(key_dates, dict):
            analysis["key_dates"] = [key_dates]
        else:
            analysis["key_dates"] = []

    # Ensure key_terms is always an array of strings
    if not analysis.get("key_terms"):
        analysis["key_terms"] = []
    if not isinstance(analysis["key_terms"], list):
        key_terms = analysis["key_terms"]
        if isinstance(key_terms, str):
            # Try to split on common delimiters
            for delimiter in [',', ';', '\n', '|']:
                if delimiter in key_terms:
                    analysis["key_terms"] = [term.strip() for term in key_terms.split(delimiter) if term.strip()]
                    break
            else:
                analysis["key_terms"] = [key_terms.strip()]
        else:
            analysis["key_terms"] = []

    # Ensure parties is always an array of strings
    if not analysis.get("parties"):
        analysis["parties"] = []
    if not isinstance(analysis["parties"], list):
        parties = analysis["parties"]
        if isinstance(parties, str):
            analysis["parties"] = [parties.strip()]
        else:
            analysis["parties"] = []

    # Ensure summary is always a string
    if not analysis.get("summary"):
        analysis["summary"] = "No summary available"
    if not isinstance(analysis["summary"], str):
        analysis["summary"] = str(analysis["summary"])

    # Ensure confidence is a number
    if not analysis.get("confidence"):
        analysis["confidence"] = 0.0
    if not isinstance(analysis["confidence"], (int, float)):
        try:
            analysis["confidence"] = float(analysis["confidence"])
        except (ValueError, TypeError):
            analysis["confidence"] = 0.0

    # Ensure document_type is a string
    if not analysis.get("document_type"):
        analysis["document_type"] = "Unknown Document Type"
    if not isinstance(analysis["document_type"], str):
        analysis["document_type"] = str(analysis["document_type"])

    logger.debug(f"Validated analysis response - deadlines: {len(analysis['deadlines'])}, key_dates: {len(analysis['key_dates'])}, key_terms: {len(analysis['key_terms'])}")

    return analysis

@router.post("/analyze")
async def analyze_document(
    file: UploadFile = File(..., description="PDF document to analyze")
) -> Dict[str, Any]:
    """
    Analyze a legal document using AI

    This endpoint:
    1. Validates the uploaded PDF file
    2. Extracts text from the PDF
    3. Sends the text to OpenAI for analysis
    4. Returns structured analysis results

    Returns:
        - document_type: Type of legal document
        - summary: Brief summary of the document
        - parties: Parties involved
        - key_dates: Important dates found
        - deadlines: Legal deadlines
        - confidence: AI confidence score
        - And more detailed analysis
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )

        # Read file contents
        file_contents = await file.read()

        # Validate PDF
        if not pdf_service.validate_pdf(file_contents):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file"
            )

        # Extract text from PDF
        extracted_text = pdf_service.extract_text_from_pdf(
            file_contents,
            file.filename
        )

        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract meaningful text from PDF"
            )

        # Analyze with Dual-AI (OpenAI + Claude) with operational details
        analysis_result = await dual_ai_service.analyze_document(
            extracted_text,
            file.filename,
            include_operational_details=True
        )

        # Validate and normalize response structure
        analysis_result = _validate_analysis_response(analysis_result)

        # Add metadata
        response = {
            "success": True,
            "filename": file.filename,
            "file_size": len(file_contents),
            "text_length": len(extracted_text),
            "analyzed_at": datetime.now().isoformat(),
            "analysis": analysis_result
        }

        logger.info(f"Successfully analyzed document: {file.filename}")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error analyzing document {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document analysis failed: {str(e)}"
        )

@router.post("/extract-text")
async def extract_text_only(
    file: UploadFile = File(..., description="PDF document to extract text from")
) -> Dict[str, Any]:
    """
    Extract text from a PDF document without AI analysis

    Useful for:
    - Testing text extraction
    - Getting raw text for manual review
    - Debugging PDF processing issues

    Returns:
        - extracted_text: The full text content
        - page_count: Number of pages processed
        - metadata: File information
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )

        # Read file contents
        file_contents = await file.read()

        # Validate PDF
        if not pdf_service.validate_pdf(file_contents):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file"
            )

        # Extract text
        extracted_text = pdf_service.extract_text_from_pdf(
            file_contents,
            file.filename
        )

        # Count pages (rough estimate from page markers)
        page_count = extracted_text.count("--- Page") if "--- Page" in extracted_text else 1

        response = {
            "success": True,
            "filename": file.filename,
            "file_size": len(file_contents),
            "extracted_text": extracted_text,
            "text_length": len(extracted_text),
            "estimated_pages": page_count,
            "extracted_at": datetime.now().isoformat()
        }

        logger.info(f"Successfully extracted text from: {file.filename}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting text from {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text extraction failed: {str(e)}"
        )

@router.post("/analyze-text")
async def analyze_text(
    request: AnalyzeTextRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Analyze extracted document text using AI and save to database

    This endpoint accepts already-extracted text instead of a file upload.
    Useful when text has already been extracted and you want to analyze it.

    Request body:
        - text: The document text to analyze
        - filename: Original filename (for context)
        - session_id: Frontend session ID (for persistence)
        - document_id: Optional document ID to update existing

    Returns:
        - document_id: ID for retrieving this document later
        - summary: Brief summary of the document
        - parties: Parties involved
        - key_dates: Important dates found
        - key_figures: Key monetary amounts or figures
        - key_terms: Important legal terms
        - And more detailed analysis
    """
    try:
        text = request.text
        filename = request.filename
        session_id = request.session_id or str(uuid.uuid4())
        document_id = request.document_id or str(uuid.uuid4())

        if not text or len(text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text content is required and must be at least 10 characters"
            )

        # Analyze with Dual-AI (OpenAI + Claude) with optional enhanced extractions
        analysis_result = await dual_ai_service.analyze_document(
            text,
            filename,
            include_operational_details=request.include_operational_details,
            include_financial_details=request.include_financial_details
        )

        # Validate and normalize response structure
        analysis_result = _validate_analysis_response(analysis_result)

        # Save to database
        try:
            # Check if document exists
            existing_doc = db.query(Document).filter(Document.id == document_id).first()

            if existing_doc:
                # Update existing document
                existing_doc.text_content = text
                existing_doc.summary = analysis_result.get('summary')
                existing_doc.document_type = analysis_result.get('document_type')
                existing_doc.parties = analysis_result.get('parties', [])
                existing_doc.important_dates = analysis_result.get('key_dates', [])
                existing_doc.key_figures = analysis_result.get('key_figures', [])
                existing_doc.keywords = analysis_result.get('key_terms', [])
                existing_doc.analysis_data = analysis_result
                existing_doc.operational_details = analysis_result.get('operational_details')
                existing_doc.financial_details = analysis_result.get('financial_details')
                existing_doc.updated_at = datetime.utcnow()
                logger.info(f"Updated existing document: {document_id}")
            else:
                # Create new document
                document = Document(
                    id=document_id,
                    session_id=session_id,
                    file_name=filename,
                    file_type="text/plain",
                    file_size=len(text),
                    text_content=text,
                    summary=analysis_result.get('summary'),
                    document_type=analysis_result.get('document_type'),
                    parties=analysis_result.get('parties', []),
                    important_dates=analysis_result.get('key_dates', []),
                    key_figures=analysis_result.get('key_figures', []),
                    keywords=analysis_result.get('key_terms', []),
                    analysis_data=analysis_result,
                    operational_details=analysis_result.get('operational_details'),
                    financial_details=analysis_result.get('financial_details')
                )
                db.add(document)
                logger.info(f"Created new document: {document_id}")

            db.commit()
            logger.info(f"Saved document to database: {filename}")
        except Exception as db_error:
            logger.error(f"Database save error: {str(db_error)}")
            db.rollback()
            # Continue even if DB save fails

        # Add metadata to response
        response = {
            "success": True,
            "document_id": document_id,  # Return ID for frontend
            "session_id": session_id,    # Return session ID
            "filename": filename,
            "text_length": len(text),
            "analyzed_at": datetime.now().isoformat(),
            **analysis_result  # Flatten the analysis into the response
        }

        logger.info(f"Successfully analyzed text from: {filename}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text analysis failed: {str(e)}"
        )

@router.get("/session/{session_id}")
async def get_session_documents(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retrieve all documents for a session

    Returns all documents associated with the given session_id,
    allowing frontend to restore state after page refresh.
    """
    try:
        documents = db.query(Document).filter(
            Document.session_id == session_id,
            Document.is_deleted == False
        ).order_by(Document.upload_date.desc()).all()

        return {
            "session_id": session_id,
            "document_count": len(documents),
            "documents": [
                {
                    "id": doc.id,
                    "fileName": doc.file_name,
                    "fileType": doc.file_type,
                    "uploadDate": doc.upload_date.isoformat(),
                    "text": doc.text_content,
                    "summary": doc.summary,
                    "parties": doc.parties,
                    "importantDates": doc.important_dates,
                    "keyFigures": doc.key_figures,
                    "keywords": doc.keywords,
                    "analysis": doc.analysis_data
                }
                for doc in documents
            ]
        }
    except Exception as e:
        logger.error(f"Error retrieving session documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session data: {str(e)}"
        )


@router.get("/document/{document_id}")
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retrieve a specific document by ID
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.is_deleted == False
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        return {
            "id": document.id,
            "session_id": document.session_id,
            "fileName": document.file_name,
            "fileType": document.file_type,
            "uploadDate": document.upload_date.isoformat(),
            "text": document.text_content,
            "summary": document.summary,
            "parties": document.parties,
            "importantDates": document.important_dates,
            "keyFigures": document.key_figures,
            "keywords": document.keywords,
            "analysis": document.analysis_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.delete("/document/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete a document (soft delete)

    Marks the document as deleted in the database.
    The document will no longer appear in session queries.
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.is_deleted == False
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Soft delete
        document.is_deleted = True
        document.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Deleted document: {document_id} ({document.file_name})")

        return {
            "success": True,
            "message": f"Document '{document.file_name}' has been deleted",
            "document_id": document_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/document/{document_id}/operational-details")
async def get_operational_details(
    document_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get operational details for a specific document

    Returns detailed extraction including:
    - Action items with deadlines (shall/must obligations)
    - Conditional obligations (if X then Y)
    - Permanent restrictions
    - Notice/contact information
    - Financial implications
    - Legal jurisdiction details
    - Critical review dates
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.is_deleted == False
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        operational_details = document.operational_details

        if not operational_details:
            # If not already extracted, extract now
            from ..src.services.enhanced_document_extractor import enhanced_extractor

            logger.info(f"Extracting operational details on-demand for document: {document_id}")

            basic_analysis = document.analysis_data if document.analysis_data else {}
            operational_details = await enhanced_extractor.extract_operational_details(
                document.text_content,
                document.file_name,
                basic_analysis
            )

            # Save to database
            document.operational_details = operational_details
            document.updated_at = datetime.utcnow()
            db.commit()

            logger.info(f"Extracted and saved operational details for document: {document_id}")

        return {
            "document_id": document_id,
            "filename": document.file_name,
            "extracted_at": document.updated_at.isoformat() if document.updated_at else None,
            **operational_details
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving operational details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve operational details: {str(e)}"
        )


@router.post("/document/{document_id}/extract-operational-details")
async def extract_operational_details(
    document_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Force re-extraction of operational details for an existing document

    Useful when:
    - Document was analyzed before operational extraction was available
    - You want to refresh the extraction with updated algorithms
    - Previous extraction failed or was incomplete
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.is_deleted == False
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        from ..src.services.enhanced_document_extractor import enhanced_extractor

        logger.info(f"Re-extracting operational details for document: {document_id}")

        basic_analysis = document.analysis_data if document.analysis_data else {}
        operational_details = await enhanced_extractor.extract_operational_details(
            document.text_content,
            document.file_name,
            basic_analysis
        )

        # Save to database
        document.operational_details = operational_details
        document.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Re-extracted and saved operational details for document: {document_id}")

        return {
            "success": True,
            "message": f"Operational details extracted for '{document.file_name}'",
            "document_id": document_id,
            "extracted_at": document.updated_at.isoformat(),
            **operational_details
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting operational details: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract operational details: {str(e)}"
        )


@router.post("/process-document")
async def process_document(
    file: UploadFile = File(..., description="Bankruptcy PDF document to process")
) -> Dict[str, Any]:
    """
    COMPREHENSIVE BANKRUPTCY DOCUMENT PROCESSOR
    THIS ENDPOINT MUST RETURN ALL EXTRACTED DATA

    This is the main endpoint for processing bankruptcy documents with:
    1. Complete text extraction (pdfplumber)
    2. Pattern-based extraction (BankruptcyDocumentProcessor)
    3. AI backup extraction (when patterns fail)
    4. Settlement metrics calculation
    5. Fraud detection
    6. Comprehensive validation

    Returns EVERYTHING extracted from the document.
    """
    import tempfile
    from pathlib import Path

    try:
        # Step 1: Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            file_path = tmp_file.name

        logger.info(f"Processing bankruptcy document: {file.filename}")

        # Step 2: Extract text using pdfplumber (better OCR than PyPDF2)
        try:
            import pdfplumber
            full_text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"

            logger.info(f"Extracted {len(full_text)} characters from {file.filename}")

        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}, trying PyPDF2")
            # Fallback to PyPDF2
            full_text = pdf_service.extract_text_from_pdf(content, file.filename)

        if not full_text or len(full_text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract meaningful text from PDF"
            )

        # Step 3: Run the COMPLETE extraction with bankruptcy processor
        from ..src.services.bankruptcy_document_processor import bankruptcy_processor

        financial_data = bankruptcy_processor.extract_all_financial_data(full_text)
        ownership_data = bankruptcy_processor.extract_ownership_structure(full_text)
        legal_issues = bankruptcy_processor.extract_legal_issues(full_text)

        logger.info(f"Pattern extraction found: {len(financial_data.get('monetary_amounts', []))} amounts, "
                   f"{len(financial_data.get('claims', []))} claims, "
                   f"{len(legal_issues.get('precedent_violations', []))} violations")

        # Step 4: Validate we got everything - if not, use AI backup
        from ..src.services.ai_backup_extractor import ai_backup_extractor

        # Check if financial extraction seems incomplete
        if len(financial_data.get('monetary_amounts', [])) < 3:
            logger.warning("Low monetary amount extraction, using AI backup")
            ai_financial = await ai_backup_extractor.extract_with_ai(
                full_text,
                "financial",
                financial_data
            )
            # Merge AI results with pattern results
            financial_data = merge_extraction_results(financial_data, ai_financial)

        # Check if ownership data is missing
        if not ownership_data.get('voting_control') and not ownership_data.get('economic_ownership'):
            logger.warning("No ownership data found, using AI backup")
            ai_ownership = await ai_backup_extractor.extract_with_ai(
                full_text,
                "ownership",
                ownership_data
            )
            ownership_data = merge_extraction_results(ownership_data, ai_ownership)

        # Check if legal issues seem incomplete
        if len(legal_issues.get('case_citations', [])) + len(legal_issues.get('precedent_violations', [])) == 0:
            logger.warning("No legal citations found, using AI backup")
            ai_legal = await ai_backup_extractor.extract_with_ai(
                full_text,
                "legal",
                legal_issues
            )
            legal_issues = merge_extraction_results(legal_issues, ai_legal)

        # Step 5: Calculate derived metrics and fraud detection
        from ..src.services.bankruptcy_metrics import (
            calculate_settlement_metrics,
            calculate_creditor_recovery_rates,
            identify_fraudulent_conveyances
        )

        metrics = calculate_settlement_metrics(financial_data)

        # Calculate creditor recovery rates
        creditor_recovery = calculate_creditor_recovery_rates(
            financial_data.get('claims', []),
            financial_data.get('settlements', [])
        )

        # Identify potentially fraudulent conveyances
        fraudulent_conveyances = identify_fraudulent_conveyances(
            financial_data.get('monetary_amounts', []),
            ownership_data
        )

        # Step 6: Return EVERYTHING
        response = {
            "success": True,
            "filename": file.filename,
            "file_size": len(content),
            "text_length": len(full_text),
            "processed_at": datetime.now().isoformat(),

            # Complete extraction results
            "financial": financial_data,
            "ownership": ownership_data,
            "legal": legal_issues,

            # Calculated metrics
            "metrics": metrics,
            "creditor_recovery": creditor_recovery,
            "fraudulent_conveyances": fraudulent_conveyances,

            # Statistics for validation
            "extraction_stats": {
                "amounts_found": len(financial_data.get('monetary_amounts', [])),
                "unique_amounts": len(set(a.get('amount', 0) for a in financial_data.get('monetary_amounts', []))),
                "percentages_found": len(financial_data.get('percentages', [])),
                "shares_found": len(financial_data.get('shares', [])),
                "claims_found": len(financial_data.get('claims', [])),
                "settlements_found": len(financial_data.get('settlements', [])),
                "case_citations": len(legal_issues.get('case_citations', [])),
                "precedent_violations": len(legal_issues.get('precedent_violations', [])),
                "statutory_references": len(legal_issues.get('statutory_references', [])),
                "legal_issues": len(legal_issues.get('precedent_violations', [])) + len(legal_issues.get('authority_limitations', [])),
                "fraud_indicators": metrics.get('overall_statistics', {}).get('fraud_indicators', 0),
                "extraction_complete": True,
                "ai_backup_used": len(financial_data.get('monetary_amounts', [])) >= 3  # Heuristic
            },

            # Red flags and alerts
            "alerts": generate_alerts(financial_data, ownership_data, legal_issues, metrics, fraudulent_conveyances),

            # UI-formatted data
            "ui_display": None  # Will be populated by /process-document/formatted endpoint
        }

        # Add UI-formatted version for easier frontend consumption
        from ..src.services.ui_formatter import format_results_for_display
        response["ui_display"] = format_results_for_display(response)

        # Clean up temp file
        try:
            Path(file_path).unlink()
        except:
            pass

        logger.info(f"Successfully processed bankruptcy document: {file.filename}")
        logger.info(f"Extraction stats: {response['extraction_stats']}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing bankruptcy document {file.filename}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )


def merge_extraction_results(pattern_results: Dict[str, Any], ai_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge pattern-based and AI extraction results

    Prefers pattern results but adds AI findings that were missed
    """
    merged = pattern_results.copy()

    for key, ai_value in ai_results.items():
        if isinstance(ai_value, list):
            # Merge lists, avoiding duplicates
            pattern_value = merged.get(key, [])

            # Simple deduplication by checking if similar items exist
            for ai_item in ai_value:
                # Check if this item is already in pattern results
                is_duplicate = False

                for pattern_item in pattern_value:
                    # Check for duplicate based on amount/value
                    if isinstance(ai_item, dict) and isinstance(pattern_item, dict):
                        if ai_item.get('amount') == pattern_item.get('amount'):
                            is_duplicate = True
                            break
                        if ai_item.get('value') == pattern_item.get('value'):
                            is_duplicate = True
                            break

                if not is_duplicate:
                    pattern_value.append(ai_item)

            merged[key] = pattern_value

        elif isinstance(ai_value, dict):
            # Merge dictionaries
            pattern_value = merged.get(key, {})
            for k, v in ai_value.items():
                if k not in pattern_value or not pattern_value[k]:
                    pattern_value[k] = v
            merged[key] = pattern_value

        else:
            # For other types, prefer pattern result if it exists
            if key not in merged or not merged[key]:
                merged[key] = ai_value

    return merged


def generate_alerts(
    financial_data: Dict[str, Any],
    ownership_data: Dict[str, Any],
    legal_issues: Dict[str, Any],
    metrics: Dict[str, Any],
    fraudulent_conveyances: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """
    Generate user-facing alerts about red flags in the document
    """
    alerts = []

    # Check for preferential treatments
    pref_treatments = metrics.get('preferential_treatments', [])
    if pref_treatments:
        for treatment in pref_treatments:
            if treatment.get('potential_fraud', False):
                alerts.append({
                    'level': 'CRITICAL',
                    'type': 'POTENTIAL_FRAUD',
                    'message': f"Settlement at {treatment['premium_multiple']}x premium to {treatment['beneficiary']} - HIGHLY SUSPICIOUS",
                    'details': f"Payment: ${treatment['payment_amount']:,.2f}, Original: ${treatment['original_claim']:,.2f}"
                })
            else:
                alerts.append({
                    'level': 'WARNING',
                    'type': 'PREFERENTIAL_TREATMENT',
                    'message': f"Preferential treatment detected: {treatment['beneficiary']} receiving {treatment['premium_multiple']}x",
                    'details': f"Excess payment: ${treatment['excess_payment']:,.2f}"
                })

    # Check for control disparities
    disparities = ownership_data.get('control_disparities', [])
    if disparities:
        for disparity in disparities:
            alerts.append({
                'level': 'WARNING',
                'type': 'CONTROL_DISPARITY',
                'message': f"{disparity['entity']} has {disparity['voting_control']}% voting control with only {disparity['economic_ownership']}% economic ownership",
                'details': f"Disparity: {disparity['disparity']}%"
            })

    # Check for precedent violations
    violations = legal_issues.get('precedent_violations', [])
    if violations:
        for violation in violations:
            alerts.append({
                'level': 'CRITICAL',
                'type': 'LEGAL_VIOLATION',
                'message': f"Violates {violation['case']}",
                'details': f"Violation type: {violation.get('violation_type', 'Unknown')}"
            })

    # Check for fraudulent conveyances
    if fraudulent_conveyances:
        for conveyance in fraudulent_conveyances:
            alerts.append({
                'level': 'CRITICAL',
                'type': 'FRAUDULENT_CONVEYANCE',
                'message': f"Suspicious transfer of ${conveyance['amount']:,.2f}",
                'details': f"Red flags: {', '.join([f for f in conveyance['red_flags'] if f])}"
            })

    # Check overall recovery rate
    recovery = metrics.get('recovery_analysis', {})
    if recovery.get('suspicious', False):
        alerts.append({
            'level': 'CRITICAL',
            'type': 'SUSPICIOUS_RECOVERY',
            'message': f"Total payments exceed total claims - recovery rate: {recovery.get('overall_recovery_rate', 0):.1%}",
            'details': "This is mathematically impossible in legitimate bankruptcy"
        })

    return alerts


@router.post("/analyze-bankruptcy")
async def analyze_bankruptcy_document(
    file: UploadFile = File(..., description="Bankruptcy PDF document to analyze")
) -> Dict[str, Any]:
    """
    Analyze a bankruptcy legal document with comprehensive financial and legal extraction

    This endpoint is specialized for bankruptcy cases and extracts:
    - ALL monetary amounts (claims, settlements, premiums)
    - Ownership structures (voting control vs economic ownership)
    - Share distributions and equity structures
    - Legal issues (case citations, precedent violations)
    - Authority limitations and jurisdictional problems

    This is NOT a generic text parser - it understands bankruptcy document structure.

    Returns comprehensive extraction including:
        - financial_data: All monetary amounts, percentages, shares, claims, settlements
        - ownership_structure: Voting control, economic ownership, control disparities
        - legal_issues: Case citations, statutory references, violations
        - summary_statistics: Aggregated counts and metrics
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported for bankruptcy analysis"
            )

        # Read file contents
        file_contents = await file.read()

        # Validate PDF
        if not pdf_service.validate_pdf(file_contents):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file"
            )

        # Extract text from PDF
        extracted_text = pdf_service.extract_text_from_pdf(
            file_contents,
            file.filename
        )

        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract meaningful text from PDF"
            )

        # Process with bankruptcy-specific processor
        from ..src.services.bankruptcy_document_processor import bankruptcy_processor

        logger.info(f"Processing bankruptcy document: {file.filename}")

        bankruptcy_analysis = bankruptcy_processor.process_bankruptcy_document(
            extracted_text,
            file.filename
        )

        # Add file metadata
        response = {
            "success": True,
            "filename": file.filename,
            "file_size": len(file_contents),
            "text_length": len(extracted_text),
            "analyzed_at": datetime.now().isoformat(),
            "analysis_type": "bankruptcy_specialized",
            **bankruptcy_analysis
        }

        logger.info(f"Successfully analyzed bankruptcy document: {file.filename}")
        logger.info(f"Extracted: {bankruptcy_analysis['summary_statistics']}")

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error analyzing bankruptcy document {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bankruptcy document analysis failed: {str(e)}"
        )


@router.post("/analyze-bankruptcy-text")
async def analyze_bankruptcy_text(
    request: AnalyzeTextRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Analyze bankruptcy document text (already extracted) with comprehensive extraction

    This endpoint accepts already-extracted text and performs specialized bankruptcy analysis.

    Request body:
        - text: The document text to analyze
        - filename: Original filename (for context)
        - session_id: Frontend session ID (for persistence)
        - document_id: Optional document ID to update existing

    Returns comprehensive extraction including all financial and legal data.
    """
    try:
        text = request.text
        filename = request.filename
        session_id = request.session_id or str(uuid.uuid4())
        document_id = request.document_id or str(uuid.uuid4())

        if not text or len(text.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text content is required and must be at least 10 characters"
            )

        # Process with bankruptcy-specific processor
        from ..src.services.bankruptcy_document_processor import bankruptcy_processor

        logger.info(f"Processing bankruptcy text: {filename}")

        bankruptcy_analysis = bankruptcy_processor.process_bankruptcy_document(
            text,
            filename
        )

        # Save to database with bankruptcy-specific data
        try:
            # Check if document exists
            existing_doc = db.query(Document).filter(Document.id == document_id).first()

            # Prepare bankruptcy-specific data for storage
            bankruptcy_data = {
                'financial_data': bankruptcy_analysis['financial_data'],
                'ownership_structure': bankruptcy_analysis['ownership_structure'],
                'legal_issues': bankruptcy_analysis['legal_issues'],
                'summary_statistics': bankruptcy_analysis['summary_statistics']
            }

            if existing_doc:
                # Update existing document
                existing_doc.text_content = text
                existing_doc.document_type = "Bankruptcy Legal Document"
                existing_doc.analysis_data = bankruptcy_data
                existing_doc.financial_details = bankruptcy_analysis['financial_data']
                existing_doc.updated_at = datetime.utcnow()
                logger.info(f"Updated existing bankruptcy document: {document_id}")
            else:
                # Create new document
                document = Document(
                    id=document_id,
                    session_id=session_id,
                    file_name=filename,
                    file_type="application/pdf",
                    file_size=len(text),
                    text_content=text,
                    summary=f"Bankruptcy document with {bankruptcy_analysis['summary_statistics']['total_monetary_amounts']} monetary amounts, "
                            f"{bankruptcy_analysis['summary_statistics']['total_claims']} claims, "
                            f"{bankruptcy_analysis['summary_statistics']['precedent_violations']} precedent violations",
                    document_type="Bankruptcy Legal Document",
                    analysis_data=bankruptcy_data,
                    financial_details=bankruptcy_analysis['financial_data']
                )
                db.add(document)
                logger.info(f"Created new bankruptcy document: {document_id}")

            db.commit()
            logger.info(f"Saved bankruptcy document to database: {filename}")
        except Exception as db_error:
            logger.error(f"Database save error: {str(db_error)}")
            db.rollback()
            # Continue even if DB save fails

        # Add metadata to response
        response = {
            "success": True,
            "document_id": document_id,
            "session_id": session_id,
            "filename": filename,
            "text_length": len(text),
            "analyzed_at": datetime.now().isoformat(),
            "analysis_type": "bankruptcy_specialized",
            **bankruptcy_analysis
        }

        logger.info(f"Successfully analyzed bankruptcy text from: {filename}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing bankruptcy text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bankruptcy text analysis failed: {str(e)}"
        )


@router.get("/status")
async def get_service_status() -> Dict[str, Any]:
    """
    Get the status of document processing services

    Returns:
        - AI service status
        - Available models
        - Service configuration
    """
    import os

    openai_configured = bool(os.getenv('OPENAI_API_KEY'))
    claude_configured = bool(os.getenv('CLAUDE_API_KEY'))
    dual_ai_available = openai_configured and claude_configured

    return {
        "document_processing": "available",
        "pdf_extraction": "available",
        "bankruptcy_specialized": "available",
        "ai_analysis": "dual_ai_enhanced" if dual_ai_available else "single_ai" if (openai_configured or claude_configured) else "fallback_mode",
        "openai_configured": openai_configured,
        "claude_configured": claude_configured,
        "dual_ai_pipeline": dual_ai_available,
        "harvard_professor_mode": claude_configured,
        "supported_formats": ["pdf"],
        "max_file_size": "10MB",
        "ai_models": "OpenAI GPT-4 + Claude-3 Opus (Dual-AI)" if dual_ai_available else "Single AI fallback",
        "analysis_features": [
            "OpenAI heavy-lifting extraction",
            "Claude legal enhancement",
            "Harvard lawyer explanations",
            "3rd-grade simplification",
            "Bankruptcy-specialized financial extraction",
            "Ownership structure analysis",
            "Legal violation detection"
        ] if dual_ai_available else ["Basic AI analysis", "Bankruptcy-specialized extraction"],
        "bankruptcy_features": [
            "Comprehensive financial data extraction",
            "Voting control vs economic ownership analysis",
            "Settlement premium calculations",
            "Case law violation detection",
            "Statutory reference extraction",
            "Authority limitation identification"
        ],
        "status": "operational"
    }
