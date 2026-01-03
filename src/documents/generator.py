"""
Document Generation System
Advanced document generation with merge capabilities, multi-document packets, and court-ready formatting.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, IO
from enum import Enum
import asyncio
import json
import re
import base64
from pathlib import Path
from io import BytesIO
import zipfile


class DocumentFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    RTF = "rtf"
    XML = "xml"


class WatermarkType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    DRAFT = "draft"
    CONFIDENTIAL = "confidential"
    PRIVILEGED = "privileged"
    CUSTOM = "custom"


class SignatureType(str, Enum):
    PLACEHOLDER = "placeholder"
    ELECTRONIC = "electronic"
    DIGITAL = "digital"
    HANDWRITTEN = "handwritten"


class CourtFormat(str, Enum):
    FEDERAL_DISTRICT = "federal_district"
    STATE_SUPERIOR = "state_superior"
    APPELLATE = "appellate"
    BANKRUPTCY = "bankruptcy"
    TAX_COURT = "tax_court"
    FAMILY_COURT = "family_court"
    CUSTOM = "custom"


class FilingType(str, Enum):
    ELECTRONIC = "electronic"
    PAPER = "paper"
    BOTH = "both"


@dataclass
class MergeField:
    field_name: str
    value: Any
    format_type: str = "text"
    formatting_rules: Dict[str, Any] = field(default_factory=dict)
    conditional_logic: Optional[Dict[str, Any]] = None
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SignaturePlacement:
    signature_id: str
    page_number: int
    x_position: float
    y_position: float
    width: float
    height: float
    signature_type: SignatureType
    required: bool = True
    signatory_name: str = ""
    signatory_title: str = ""
    date_required: bool = True
    witness_required: bool = False


@dataclass
class Watermark:
    watermark_id: str
    watermark_type: WatermarkType
    content: str
    position: str = "center"
    opacity: float = 0.3
    rotation: float = 45.0
    font_size: int = 48
    color: str = "#CCCCCC"
    pages: str = "all"  # "all", "first", "last", or page numbers


@dataclass
class DocumentPacket:
    packet_id: str
    name: str
    description: str
    documents: List[str]  # Document IDs
    cover_sheet: Optional[str] = None
    table_of_contents: bool = True
    page_numbering: str = "continuous"
    binding_instructions: str = ""
    filing_requirements: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CourtFormatting:
    format_id: str
    court_type: CourtFormat
    jurisdiction: str
    margins: Dict[str, float] = field(default_factory=lambda: {
        "top": 1.0, "bottom": 1.0, "left": 1.25, "right": 1.0
    })
    font_family: str = "Times New Roman"
    font_size: int = 12
    line_spacing: float = 2.0
    page_numbering: str = "bottom_center"
    header_requirements: Dict[str, Any] = field(default_factory=dict)
    footer_requirements: Dict[str, Any] = field(default_factory=dict)
    citation_format: str = "bluebook"
    filing_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedDocument:
    document_id: str
    name: str
    content: bytes
    format: DocumentFormat
    template_id: Optional[str]
    merge_data: Dict[str, Any]
    generation_parameters: Dict[str, Any]
    file_size: int
    page_count: int
    created_by: str
    created_at: datetime
    watermarks: List[Watermark] = field(default_factory=list)
    signatures: List[SignaturePlacement] = field(default_factory=list)
    court_formatting: Optional[CourtFormatting] = None
    filing_ready: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BulkGenerationJob:
    job_id: str
    template_id: str
    data_source: str  # "csv", "json", "database", etc.
    merge_data_list: List[Dict[str, Any]]
    output_format: DocumentFormat
    batch_size: int = 100
    status: str = "pending"
    progress: float = 0.0
    generated_documents: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)


class DocumentGenerator:
    def __init__(self):
        self.generated_documents = {}
        self.packets = {}
        self.court_formats = {}
        self.bulk_jobs = {}
        self.templates = {}  # Would integrate with template system

    async def initialize_court_formats(self) -> bool:
        """Initialize standard court formatting templates"""
        try:
            # Federal District Court Format
            federal_format = CourtFormatting(
                format_id="federal_district",
                court_type=CourtFormat.FEDERAL_DISTRICT,
                jurisdiction="Federal",
                margins={"top": 1.0, "bottom": 1.0, "left": 1.25, "right": 1.0},
                font_family="Times New Roman",
                font_size=12,
                line_spacing=2.0,
                page_numbering="bottom_center",
                header_requirements={
                    "case_number": True,
                    "court_name": True,
                    "judge_name": False
                },
                citation_format="bluebook",
                filing_requirements={
                    "electronic_filing": True,
                    "max_file_size_mb": 25,
                    "pdf_required": True,
                    "bookmarks_required": True
                }
            )

            # State Superior Court Format
            state_format = CourtFormatting(
                format_id="state_superior",
                court_type=CourtFormat.STATE_SUPERIOR,
                jurisdiction="State",
                margins={"top": 1.0, "bottom": 1.0, "left": 1.5, "right": 1.0},
                font_family="Times New Roman",
                font_size=12,
                line_spacing=2.0,
                page_numbering="top_right",
                filing_requirements={
                    "electronic_filing": True,
                    "paper_copies": 2,
                    "certificate_of_service": True
                }
            )

            self.court_formats["federal_district"] = federal_format
            self.court_formats["state_superior"] = state_format

            return True

        except Exception as e:
            print(f"Error initializing court formats: {e}")
            return False

    async def generate_document(self, template_id: str, merge_data: Dict[str, Any],
                              output_format: DocumentFormat = DocumentFormat.PDF,
                              court_formatting: Optional[str] = None,
                              watermarks: Optional[List[Watermark]] = None,
                              signatures: Optional[List[SignaturePlacement]] = None,
                              user_id: str = "system") -> Optional[GeneratedDocument]:
        """Generate document from template with merge data"""
        try:
            # Get template (would integrate with template system)
            template_content = await self._get_template_content(template_id)
            if not template_content:
                raise ValueError("Template not found")

            # Create merge fields
            merge_fields = []
            for field_name, value in merge_data.items():
                merge_fields.append(MergeField(
                    field_name=field_name,
                    value=value,
                    format_type=self._detect_format_type(value)
                ))

            # Perform merge
            merged_content = await self._merge_data_into_template(template_content, merge_fields)

            # Apply court formatting if specified
            if court_formatting and court_formatting in self.court_formats:
                court_format = self.court_formats[court_formatting]
                merged_content = await self._apply_court_formatting(merged_content, court_format)
            else:
                court_format = None

            # Apply watermarks
            if watermarks:
                merged_content = await self._apply_watermarks(merged_content, watermarks)

            # Add signature placeholders
            if signatures:
                merged_content = await self._add_signature_placeholders(merged_content, signatures)

            # Convert to requested format
            document_bytes = await self._convert_to_format(merged_content, output_format)

            # Calculate document stats
            file_size = len(document_bytes)
            page_count = await self._calculate_page_count(document_bytes, output_format)

            # Create generated document
            document_id = f"doc_{int(datetime.utcnow().timestamp())}"
            document = GeneratedDocument(
                document_id=document_id,
                name=f"Generated_{template_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                content=document_bytes,
                format=output_format,
                template_id=template_id,
                merge_data=merge_data,
                generation_parameters={
                    "court_formatting": court_formatting,
                    "output_format": output_format.value,
                    "watermarks_applied": len(watermarks) if watermarks else 0,
                    "signatures_added": len(signatures) if signatures else 0
                },
                file_size=file_size,
                page_count=page_count,
                created_by=user_id,
                created_at=datetime.utcnow(),
                watermarks=watermarks or [],
                signatures=signatures or [],
                court_formatting=court_format,
                filing_ready=court_formatting is not None
            )

            self.generated_documents[document_id] = document
            return document

        except Exception as e:
            print(f"Error generating document: {e}")
            return None

    async def _get_template_content(self, template_id: str) -> Optional[str]:
        """Get template content (would integrate with template system)"""
        # Sample template content for demo
        sample_templates = {
            "motion_001": """
IN THE UNITED STATES DISTRICT COURT
FOR THE {district}

{plaintiff_name},
                                          Plaintiff,
v.                                        Case No. {case_number}
{defendant_name},
                                          Defendant.

MOTION FOR {motion_type}

TO THE HONORABLE COURT:

Comes now {plaintiff_name}, through counsel, and respectfully moves this Court for {relief_sought} on the following grounds:

{grounds}

WHEREFORE, Plaintiff respectfully requests that this Court grant this Motion and award such other relief as the Court deems just and proper.

Respectfully submitted,

{attorney_signature}
{attorney_name}
{attorney_title}
{law_firm}
{address}
{phone}
{email}
Attorney for {plaintiff_name}
            """,
            "contract_001": """
SERVICE AGREEMENT

This Service Agreement ("Agreement") is entered into on {effective_date} between {client_name}, located at {client_address} ("Client"), and {service_provider}, located at {provider_address} ("Provider").

1. SERVICES
Provider agrees to provide the following services: {services_description}

2. TERM
This Agreement shall commence on {start_date} and continue for a period of {term_length}.

3. COMPENSATION
Client agrees to pay Provider {payment_amount} for the services described herein.

4. TERMINATION
Either party may terminate this Agreement with {termination_notice} days written notice.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.

CLIENT:                           PROVIDER:

{client_signature}               {provider_signature}
{client_name}                    {service_provider}
Date: ___________                Date: ___________
            """
        }

        return sample_templates.get(template_id)

    def _detect_format_type(self, value: Any) -> str:
        """Detect the format type of a merge field value"""
        if isinstance(value, (int, float)):
            return "number"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, datetime):
            return "date"
        elif isinstance(value, str):
            if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                return "date"
            elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                return "email"
            elif re.match(r'^\+?[\d\s\-\(\)]{10,}$', value):
                return "phone"
            else:
                return "text"
        else:
            return "text"

    async def _merge_data_into_template(self, template_content: str,
                                      merge_fields: List[MergeField]) -> str:
        """Merge data into template placeholders"""
        try:
            merged_content = template_content

            for field in merge_fields:
                placeholder = "{" + field.field_name + "}"
                formatted_value = await self._format_field_value(field)

                if placeholder in merged_content:
                    merged_content = merged_content.replace(placeholder, str(formatted_value))

            return merged_content

        except Exception as e:
            print(f"Error merging data: {e}")
            return template_content

    async def _format_field_value(self, field: MergeField) -> str:
        """Format field value according to its type and rules"""
        try:
            value = field.value

            if field.format_type == "date":
                if isinstance(value, str):
                    # Parse date string and format
                    return value  # Simplified for demo
                elif isinstance(value, datetime):
                    return value.strftime("%B %d, %Y")

            elif field.format_type == "number":
                formatting = field.formatting_rules.get("number", {})
                if formatting.get("currency"):
                    return f"${float(value):,.2f}"
                elif formatting.get("percentage"):
                    return f"{float(value):.1%}"
                else:
                    return str(value)

            elif field.format_type == "text":
                formatting = field.formatting_rules.get("text", {})
                if formatting.get("uppercase"):
                    return str(value).upper()
                elif formatting.get("lowercase"):
                    return str(value).lower()
                elif formatting.get("title_case"):
                    return str(value).title()

            return str(value)

        except Exception as e:
            print(f"Error formatting field value: {e}")
            return str(field.value)

    async def _apply_court_formatting(self, content: str, court_format: CourtFormatting) -> str:
        """Apply court-specific formatting rules"""
        try:
            # Add court-specific formatting directives
            formatted_content = f"[COURT_FORMAT: {court_format.format_id}]\n"
            formatted_content += f"[MARGINS: {court_format.margins}]\n"
            formatted_content += f"[FONT: {court_format.font_family}, {court_format.font_size}pt]\n"
            formatted_content += f"[LINE_SPACING: {court_format.line_spacing}]\n"
            formatted_content += f"[PAGE_NUMBERING: {court_format.page_numbering}]\n"
            formatted_content += "\n" + content

            return formatted_content

        except Exception as e:
            print(f"Error applying court formatting: {e}")
            return content

    async def _apply_watermarks(self, content: str, watermarks: List[Watermark]) -> str:
        """Apply watermarks to document"""
        try:
            watermarked_content = content

            for watermark in watermarks:
                watermark_directive = f"\n[WATERMARK: {watermark.content}, "
                watermark_directive += f"position={watermark.position}, "
                watermark_directive += f"opacity={watermark.opacity}, "
                watermark_directive += f"rotation={watermark.rotation}]\n"
                watermarked_content += watermark_directive

            return watermarked_content

        except Exception as e:
            print(f"Error applying watermarks: {e}")
            return content

    async def _add_signature_placeholders(self, content: str,
                                        signatures: List[SignaturePlacement]) -> str:
        """Add signature placeholders to document"""
        try:
            signature_content = content

            for sig in signatures:
                sig_placeholder = f"\n\n[SIGNATURE_PLACEHOLDER]\n"
                sig_placeholder += f"Signature: _________________________ Date: __________\n"
                sig_placeholder += f"{sig.signatory_name}\n"
                if sig.signatory_title:
                    sig_placeholder += f"{sig.signatory_title}\n"
                signature_content += sig_placeholder

            return signature_content

        except Exception as e:
            print(f"Error adding signature placeholders: {e}")
            return content

    async def _convert_to_format(self, content: str, format: DocumentFormat) -> bytes:
        """Convert content to requested document format"""
        try:
            if format == DocumentFormat.TXT:
                return content.encode('utf-8')
            elif format == DocumentFormat.HTML:
                html_content = f"<html><body><pre>{content}</pre></body></html>"
                return html_content.encode('utf-8')
            elif format == DocumentFormat.PDF:
                # Would use proper PDF generation library
                pdf_content = f"PDF_HEADER\n{content}\nPDF_FOOTER"
                return pdf_content.encode('utf-8')
            else:
                # Default to text
                return content.encode('utf-8')

        except Exception as e:
            print(f"Error converting to format: {e}")
            return content.encode('utf-8')

    async def _calculate_page_count(self, document_bytes: bytes, format: DocumentFormat) -> int:
        """Calculate approximate page count"""
        try:
            # Simplified page count calculation
            content_length = len(document_bytes)
            if format == DocumentFormat.PDF:
                return max(1, content_length // 3000)  # Rough estimate
            else:
                return max(1, content_length // 2500)  # Text-based estimate
        except:
            return 1

    async def create_document_packet(self, packet: DocumentPacket) -> bool:
        """Create a multi-document packet"""
        try:
            # Validate all documents exist
            missing_docs = []
            for doc_id in packet.documents:
                if doc_id not in self.generated_documents:
                    missing_docs.append(doc_id)

            if missing_docs:
                raise ValueError(f"Documents not found: {missing_docs}")

            self.packets[packet.packet_id] = packet
            return True

        except Exception as e:
            print(f"Error creating document packet: {e}")
            return False

    async def generate_packet_archive(self, packet_id: str) -> Optional[bytes]:
        """Generate ZIP archive of document packet"""
        try:
            packet = self.packets.get(packet_id)
            if not packet:
                return None

            # Create ZIP file in memory
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add cover sheet if specified
                if packet.cover_sheet:
                    cover_content = await self._generate_cover_sheet(packet)
                    zip_file.writestr("00_Cover_Sheet.txt", cover_content)

                # Add table of contents if requested
                if packet.table_of_contents:
                    toc_content = await self._generate_table_of_contents(packet)
                    zip_file.writestr("01_Table_of_Contents.txt", toc_content)

                # Add all documents
                for i, doc_id in enumerate(packet.documents):
                    doc = self.generated_documents.get(doc_id)
                    if doc:
                        filename = f"{i+2:02d}_{doc.name}.{doc.format.value}"
                        zip_file.writestr(filename, doc.content)

                # Add filing instructions if present
                if packet.filing_requirements:
                    instructions = await self._generate_filing_instructions(packet)
                    zip_file.writestr("Filing_Instructions.txt", instructions)

            return zip_buffer.getvalue()

        except Exception as e:
            print(f"Error generating packet archive: {e}")
            return None

    async def _generate_cover_sheet(self, packet: DocumentPacket) -> str:
        """Generate cover sheet for document packet"""
        cover_sheet = f"""
DOCUMENT PACKET COVER SHEET

Packet Name: {packet.name}
Description: {packet.description}
Generated: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p')}

CONTENTS:
"""
        for i, doc_id in enumerate(packet.documents, 1):
            doc = self.generated_documents.get(doc_id)
            if doc:
                cover_sheet += f"{i}. {doc.name} ({doc.format.value.upper()}, {doc.page_count} pages)\n"

        if packet.binding_instructions:
            cover_sheet += f"\nBinding Instructions: {packet.binding_instructions}\n"

        return cover_sheet

    async def _generate_table_of_contents(self, packet: DocumentPacket) -> str:
        """Generate table of contents for packet"""
        toc = "TABLE OF CONTENTS\n\n"

        page_num = 1
        if packet.cover_sheet:
            toc += "Cover Sheet ......................................................... 1\n"
            page_num += 1

        toc += "Table of Contents ................................................... 2\n"
        page_num += 1

        for doc_id in packet.documents:
            doc = self.generated_documents.get(doc_id)
            if doc:
                toc += f"{doc.name} ................................................. {page_num}\n"
                page_num += doc.page_count

        return toc

    async def _generate_filing_instructions(self, packet: DocumentPacket) -> str:
        """Generate filing instructions for packet"""
        instructions = "ELECTRONIC FILING INSTRUCTIONS\n\n"

        requirements = packet.filing_requirements
        if requirements.get("electronic_filing"):
            instructions += "This packet is prepared for electronic filing.\n\n"

        if requirements.get("pdf_required"):
            instructions += "- All documents must be in PDF format\n"

        if requirements.get("max_file_size_mb"):
            instructions += f"- Maximum file size: {requirements['max_file_size_mb']} MB\n"

        if requirements.get("bookmarks_required"):
            instructions += "- PDF bookmarks are required for multi-document filings\n"

        if requirements.get("certificate_of_service"):
            instructions += "- Certificate of Service must be included\n"

        return instructions

    async def start_bulk_generation(self, job: BulkGenerationJob) -> bool:
        """Start bulk document generation job"""
        try:
            job.status = "running"
            job.started_at = datetime.utcnow()
            self.bulk_jobs[job.job_id] = job

            # Start background processing
            asyncio.create_task(self._process_bulk_generation(job))

            return True

        except Exception as e:
            print(f"Error starting bulk generation: {e}")
            return False

    async def _process_bulk_generation(self, job: BulkGenerationJob):
        """Process bulk generation job in background"""
        try:
            total_items = len(job.merge_data_list)
            processed = 0

            for i, merge_data in enumerate(job.merge_data_list):
                try:
                    # Generate document
                    doc = await self.generate_document(
                        template_id=job.template_id,
                        merge_data=merge_data,
                        output_format=job.output_format,
                        user_id=job.created_by
                    )

                    if doc:
                        job.generated_documents.append(doc.document_id)

                    processed += 1
                    job.progress = (processed / total_items) * 100

                    # Batch processing pause
                    if (i + 1) % job.batch_size == 0:
                        await asyncio.sleep(0.1)

                except Exception as e:
                    job.errors.append(f"Item {i}: {str(e)}")

            job.status = "completed"
            job.completed_at = datetime.utcnow()

        except Exception as e:
            job.status = "failed"
            job.errors.append(f"Job failed: {str(e)}")
            job.completed_at = datetime.utcnow()

    async def get_bulk_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of bulk generation job"""
        try:
            job = self.bulk_jobs.get(job_id)
            if not job:
                return None

            return {
                "job_id": job.job_id,
                "status": job.status,
                "progress": job.progress,
                "total_items": len(job.merge_data_list),
                "completed_items": len(job.generated_documents),
                "errors": len(job.errors),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "estimated_completion": self._estimate_completion_time(job)
            }

        except Exception as e:
            print(f"Error getting bulk job status: {e}")
            return None

    def _estimate_completion_time(self, job: BulkGenerationJob) -> Optional[str]:
        """Estimate completion time for bulk job"""
        try:
            if job.status == "completed" or not job.started_at:
                return None

            elapsed = (datetime.utcnow() - job.started_at).total_seconds()
            if job.progress > 0:
                total_estimated = elapsed * (100 / job.progress)
                remaining = total_estimated - elapsed
                eta = datetime.utcnow() + timedelta(seconds=remaining)
                return eta.strftime('%Y-%m-%d %H:%M:%S')

            return None

        except:
            return None

    async def prepare_for_filing(self, document_id: str, filing_type: FilingType,
                               court_format: str) -> Optional[GeneratedDocument]:
        """Prepare document for court filing"""
        try:
            doc = self.generated_documents.get(document_id)
            if not doc:
                return None

            # Apply court formatting if not already applied
            if not doc.court_formatting and court_format in self.court_formats:
                court_fmt = self.court_formats[court_format]
                # Would reprocess document with court formatting
                doc.court_formatting = court_fmt

            # Add required filing metadata
            doc.metadata["filing_type"] = filing_type.value
            doc.metadata["filing_prepared_at"] = datetime.utcnow().isoformat()
            doc.filing_ready = True

            # Add filing-specific watermarks if required
            if filing_type == FilingType.ELECTRONIC:
                filing_watermark = Watermark(
                    watermark_id="filing_watermark",
                    watermark_type=WatermarkType.TEXT,
                    content="ELECTRONICALLY FILED",
                    position="top_right",
                    opacity=0.5
                )
                doc.watermarks.append(filing_watermark)

            return doc

        except Exception as e:
            print(f"Error preparing for filing: {e}")
            return None

    async def get_generation_summary(self) -> Dict[str, Any]:
        """Get summary of document generation system"""
        try:
            return {
                "total_documents": len(self.generated_documents),
                "total_packets": len(self.packets),
                "active_bulk_jobs": len([j for j in self.bulk_jobs.values() if j.status == "running"]),
                "court_formats": len(self.court_formats),
                "documents_by_format": self._count_by_format(),
                "recent_generations": self._get_recent_generations(),
                "filing_ready_documents": len([d for d in self.generated_documents.values() if d.filing_ready])
            }
        except Exception as e:
            print(f"Error getting generation summary: {e}")
            return {}

    def _count_by_format(self) -> Dict[str, int]:
        """Count documents by format"""
        formats = {}
        for doc in self.generated_documents.values():
            fmt = doc.format.value
            formats[fmt] = formats.get(fmt, 0) + 1
        return formats

    def _get_recent_generations(self) -> List[Dict[str, Any]]:
        """Get recent document generations"""
        sorted_docs = sorted(
            self.generated_documents.values(),
            key=lambda x: x.created_at,
            reverse=True
        )[:5]

        return [{
            "document_id": d.document_id,
            "name": d.name,
            "format": d.format.value,
            "created_at": d.created_at.isoformat(),
            "file_size": d.file_size
        } for d in sorted_docs]


# Global instance
document_generator = DocumentGenerator()


# FastAPI endpoints configuration
async def get_generation_endpoints():
    """Return FastAPI endpoint configurations for document generation"""
    return [
        {
            "path": "/documents/generate",
            "method": "POST",
            "handler": "generate_document_from_template",
            "description": "Generate document from template"
        },
        {
            "path": "/documents/packets",
            "method": "POST",
            "handler": "create_document_packet",
            "description": "Create document packet"
        },
        {
            "path": "/documents/packets/{packet_id}/download",
            "method": "GET",
            "handler": "download_document_packet",
            "description": "Download document packet archive"
        },
        {
            "path": "/documents/bulk-generate",
            "method": "POST",
            "handler": "start_bulk_document_generation",
            "description": "Start bulk document generation"
        },
        {
            "path": "/documents/bulk-jobs/{job_id}/status",
            "method": "GET",
            "handler": "get_bulk_generation_status",
            "description": "Get bulk generation job status"
        },
        {
            "path": "/documents/{document_id}/prepare-filing",
            "method": "POST",
            "handler": "prepare_document_for_filing",
            "description": "Prepare document for court filing"
        },
        {
            "path": "/documents/court-formats",
            "method": "GET",
            "handler": "get_court_formats",
            "description": "Get available court formats"
        },
        {
            "path": "/documents/generation/summary",
            "method": "GET",
            "handler": "get_document_generation_summary",
            "description": "Get document generation summary"
        }
    ]


async def initialize_document_generation():
    """Initialize the document generation system"""
    try:
        # Initialize court formats
        await document_generator.initialize_court_formats()

        print("Document Generation System initialized successfully")
        print(f"Available endpoints: {len(await get_generation_endpoints())}")
        print(f"Court formats loaded: {len(document_generator.court_formats)}")
        return True
    except Exception as e:
        print(f"Error initializing document generation: {e}")
        return False