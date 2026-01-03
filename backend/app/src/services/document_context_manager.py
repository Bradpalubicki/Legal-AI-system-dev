"""
Multi-Document Context Manager

Prevents AI "amnesia" and "hallucinations" when handling multiple documents:
- Maintains full document context (no truncation)
- Enables cross-document querying
- Prevents document confusion
- Tracks what the AI has "seen"
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.legal_documents import Document

logger = logging.getLogger(__name__)


class DocumentContextManager:
    """
    Manages multi-document context to prevent AI confusion and hallucinations.

    Key Features:
    - Full document text retrieval (no truncation)
    - Cross-document search and correlation
    - Context window management for AI calls
    - Document similarity detection
    - Prevents mixing information between documents
    """

    def __init__(self, db: Session):
        self.db = db
        self.max_context_chars = 100000  # 100K chars for Claude (vs current 3K limit!)


    def get_full_document_context(
        self,
        document_id: str,
        include_related: bool = False
    ) -> Dict[str, Any]:
        """
        Get FULL document context without truncation.

        Args:
            document_id: Document to retrieve
            include_related: Include related documents in same session

        Returns:
            Complete document with full text and analysis
        """
        document = self.db.query(Document).filter(
            Document.id == document_id,
            Document.is_deleted == False
        ).first()

        if not document:
            raise ValueError(f"Document {document_id} not found")

        context = {
            "document_id": document.id,
            "file_name": document.file_name,
            "document_type": document.document_type,
            "summary": document.summary,
            "full_text": document.text_content,  # FULL TEXT, NO TRUNCATION
            "text_length": len(document.text_content),
            "parties": document.parties or [],
            "important_dates": document.important_dates or [],
            "key_figures": document.key_figures or [],
            "keywords": document.keywords or [],
            "analysis": document.analysis_data or {}
        }

        # Include related documents from same session
        if include_related:
            related = self.get_session_documents(document.session_id, exclude_id=document_id)
            context["related_documents"] = [
                {
                    "id": doc.id,
                    "file_name": doc.file_name,
                    "document_type": doc.document_type,
                    "summary": doc.summary
                }
                for doc in related[:5]  # Limit to 5 related
            ]

        return context


    def get_session_documents(
        self,
        session_id: str,
        exclude_id: Optional[str] = None
    ) -> List[Document]:
        """
        Get all documents in a session.

        Args:
            session_id: Session identifier
            exclude_id: Optionally exclude a specific document

        Returns:
            List of documents in session
        """
        query = self.db.query(Document).filter(
            Document.session_id == session_id,
            Document.is_deleted == False
        )

        if exclude_id:
            query = query.filter(Document.id != exclude_id)

        return query.order_by(Document.upload_date).all()


    def search_across_documents(
        self,
        session_id: str,
        search_query: str,
        search_fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search across all documents in a session.

        Prevents hallucinations by searching actual document content,
        not relying on AI memory.

        Args:
            session_id: Session to search within
            search_query: Text to search for
            search_fields: Fields to search (text_content, summary, parties, etc.)

        Returns:
            List of matching documents with highlighted excerpts
        """
        if search_fields is None:
            search_fields = ["text_content", "summary"]

        documents = self.get_session_documents(session_id)
        results = []

        query_lower = search_query.lower()

        for doc in documents:
            matches = []

            # Search in specified fields
            if "text_content" in search_fields and doc.text_content:
                if query_lower in doc.text_content.lower():
                    # Find excerpt around match
                    idx = doc.text_content.lower().find(query_lower)
                    start = max(0, idx - 200)
                    end = min(len(doc.text_content), idx + 200)
                    excerpt = doc.text_content[start:end]
                    matches.append({
                        "field": "document_text",
                        "excerpt": f"...{excerpt}...",
                        "position": idx
                    })

            if "summary" in search_fields and doc.summary:
                if query_lower in doc.summary.lower():
                    matches.append({
                        "field": "summary",
                        "excerpt": doc.summary,
                        "position": 0
                    })

            if "parties" in search_fields and doc.parties:
                party_match = [p for p in doc.parties if query_lower in p.lower()]
                if party_match:
                    matches.append({
                        "field": "parties",
                        "excerpt": ", ".join(party_match),
                        "position": 0
                    })

            if matches:
                results.append({
                    "document_id": doc.id,
                    "file_name": doc.file_name,
                    "document_type": doc.document_type,
                    "matches": matches,
                    "match_count": len(matches)
                })

        # Sort by relevance (number of matches)
        results.sort(key=lambda x: x["match_count"], reverse=True)

        logger.info(f"Cross-document search for '{search_query}': {len(results)} documents matched")
        return results


    def build_smart_context(
        self,
        primary_document_id: str,
        question: str,
        max_chars: Optional[int] = None
    ) -> str:
        """
        Build optimized context for AI that includes relevant portions
        of the document without truncation artifacts.

        Uses semantic chunking instead of blind truncation.

        Args:
            primary_document_id: Main document being asked about
            question: User's question
            max_chars: Maximum context characters (default: 100K)

        Returns:
            Optimized context string for AI
        """
        if max_chars is None:
            max_chars = self.max_context_chars

        doc_context = self.get_full_document_context(primary_document_id, include_related=True)
        full_text = doc_context["full_text"]

        # If document fits in context, send it all
        if len(full_text) <= max_chars:
            return self._format_full_context(doc_context, question)

        # For long documents, use intelligent extraction
        relevant_sections = self._extract_relevant_sections(
            full_text,
            question,
            doc_context,
            max_chars
        )

        # Handle parties that may be dicts or strings
        parties = doc_context.get('parties', [])[:5]
        if parties and isinstance(parties[0], dict):
            parties_str = ', '.join(p.get('name', str(p)) for p in parties)
        else:
            parties_str = ', '.join(str(p) for p in parties)

        context = f"""DOCUMENT: {doc_context['file_name']}
TYPE: {doc_context['document_type']}
PARTIES: {parties_str}

SUMMARY:
{doc_context['summary']}

RELEVANT SECTIONS (from {doc_context['text_length']:,} character document):
{relevant_sections}

QUESTION: {question}

IMPORTANT: This is a {doc_context['text_length']:,} character document. The sections above are the most relevant to the question. If the answer isn't in these sections, state that you need to see other parts of the document.
"""

        return context


    def _format_full_context(
        self,
        doc_context: Dict[str, Any],
        question: str
    ) -> str:
        """Format complete document context for AI"""
        related_info = ""
        if doc_context.get("related_documents"):
            related_list = ", ".join([
                f"{d['file_name']} ({d['document_type']})"
                for d in doc_context["related_documents"]
            ])
            related_info = f"\n\nRELATED DOCUMENTS IN SESSION: {related_list}"

        # Handle parties that may be dicts or strings
        full_parties = doc_context.get('parties', [])[:10]
        if full_parties and isinstance(full_parties[0], dict):
            full_parties_str = ', '.join(p.get('name', str(p)) for p in full_parties)
        else:
            full_parties_str = ', '.join(str(p) for p in full_parties)

        return f"""DOCUMENT: {doc_context['file_name']}
TYPE: {doc_context['document_type']}
LENGTH: {doc_context['text_length']:,} characters
PARTIES: {full_parties_str}
{related_info}

SUMMARY:
{doc_context['summary']}

FULL DOCUMENT TEXT:
{doc_context['full_text']}

QUESTION: {question}

INSTRUCTIONS: Answer based ONLY on the document text above. Cite specific sections, page references, or quotes. If the information is not in this document, say so explicitly. Do not make assumptions or fill in gaps.
"""


    def _extract_relevant_sections(
        self,
        full_text: str,
        question: str,
        doc_context: Dict[str, Any],
        max_chars: int
    ) -> str:
        """
        Extract most relevant sections of a long document.

        Uses keyword matching and context windows rather than
        blind truncation.
        """
        # Extract key terms from question
        question_keywords = self._extract_keywords(question)

        # Split document into sections
        sections = self._split_into_sections(full_text)

        # Score sections by relevance
        scored_sections = []
        for section in sections:
            score = self._score_section_relevance(
                section,
                question_keywords,
                doc_context
            )
            if score > 0:
                scored_sections.append((score, section))

        # Sort by relevance
        scored_sections.sort(key=lambda x: x[0], reverse=True)

        # Build context from most relevant sections
        context_parts = []
        current_length = 0

        for score, section in scored_sections:
            section_length = len(section)
            if current_length + section_length > max_chars:
                break
            context_parts.append(section)
            current_length += section_length

        if not context_parts:
            # Fallback: use beginning and end
            mid_point = len(full_text) // 2
            first_half = full_text[:max_chars // 2]
            second_half = full_text[-max_chars // 2:]
            return f"{first_half}\n\n[... middle sections omitted ...]\n\n{second_half}"

        return "\n\n".join(context_parts)


    def _extract_keywords(self, question: str) -> List[str]:
        """Extract important keywords from question"""
        import re

        # Remove common words
        common_words = {
            'what', 'when', 'where', 'who', 'how', 'why', 'is', 'are', 'the',
            'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'does', 'do', 'can', 'should', 'would', 'could', 'my', 'this', 'that'
        }

        words = re.findall(r'\b\w+\b', question.lower())
        keywords = [w for w in words if w not in common_words and len(w) > 3]

        return keywords


    def _split_into_sections(self, text: str, section_size: int = 2000) -> List[str]:
        """Split document into semantic sections"""
        # Split on paragraph boundaries
        paragraphs = text.split('\n\n')

        sections = []
        current_section = []
        current_length = 0

        for para in paragraphs:
            para_length = len(para)

            if current_length + para_length > section_size and current_section:
                # Save current section
                sections.append('\n\n'.join(current_section))
                current_section = [para]
                current_length = para_length
            else:
                current_section.append(para)
                current_length += para_length

        # Add final section
        if current_section:
            sections.append('\n\n'.join(current_section))

        return sections


    def _score_section_relevance(
        self,
        section: str,
        keywords: List[str],
        doc_context: Dict[str, Any]
    ) -> float:
        """Score section relevance to question"""
        score = 0.0
        section_lower = section.lower()

        # Keyword matches
        for keyword in keywords:
            if keyword in section_lower:
                score += 1.0
                # Bonus for multiple occurrences
                score += section_lower.count(keyword) * 0.5

        # Important document elements
        for party in doc_context.get("parties", []):
            if party.lower() in section_lower:
                score += 2.0

        for keyword in doc_context.get("keywords", []):
            if keyword.lower() in section_lower:
                score += 1.5

        # Legal terms boost
        legal_terms = ['plaintiff', 'defendant', 'contract', 'agreement', 'breach',
                       'damages', 'liability', 'obligation', 'rights', 'clause']
        for term in legal_terms:
            if term in section_lower:
                score += 0.5

        return score


    def compare_documents(
        self,
        document_ids: List[str],
        comparison_fields: List[str] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple documents side-by-side.

        Prevents confusion by explicitly showing differences.

        Args:
            document_ids: Documents to compare
            comparison_fields: Fields to compare (parties, dates, amounts, etc.)

        Returns:
            Structured comparison data
        """
        if comparison_fields is None:
            comparison_fields = ["parties", "important_dates", "key_figures", "document_type"]

        documents = self.db.query(Document).filter(
            Document.id.in_(document_ids),
            Document.is_deleted == False
        ).all()

        comparison = {
            "document_count": len(documents),
            "documents": [],
            "common_parties": set(),
            "unique_parties_by_doc": {},
            "date_conflicts": [],
            "amount_differences": []
        }

        all_parties = []

        for doc in documents:
            doc_data = {
                "id": doc.id,
                "file_name": doc.file_name,
                "document_type": doc.document_type
            }

            for field in comparison_fields:
                value = getattr(doc, field, None)
                doc_data[field] = value

                # Track parties across documents
                if field == "parties" and value:
                    all_parties.extend(value)
                    comparison["unique_parties_by_doc"][doc.file_name] = value

            comparison["documents"].append(doc_data)

        # Find common parties
        if all_parties:
            from collections import Counter
            party_counts = Counter(all_parties)
            comparison["common_parties"] = [
                party for party, count in party_counts.items()
                if count > 1
            ]

        logger.info(f"Document comparison: {len(documents)} documents analyzed")
        return comparison


    def validate_cross_references(
        self,
        session_id: str,
        ai_response: str
    ) -> Dict[str, Any]:
        """
        Validate that AI's cross-references are accurate.

        Prevents hallucinations by checking if mentioned documents
        actually exist and contain referenced information.

        Args:
            session_id: Session to validate within
            ai_response: AI's response to validate

        Returns:
            Validation results with warnings for potential hallucinations
        """
        validation = {
            "is_valid": True,
            "warnings": [],
            "referenced_documents": [],
            "hallucination_risk": "low"
        }

        documents = self.get_session_documents(session_id)
        doc_names = {doc.file_name.lower(): doc for doc in documents}

        # Check for document name mentions
        response_lower = ai_response.lower()
        for doc_name, doc in doc_names.items():
            if doc_name in response_lower:
                validation["referenced_documents"].append({
                    "document_name": doc.file_name,
                    "document_id": doc.id,
                    "mentioned_in_response": True
                })

        # Check for party mentions not in any document
        # Extract potential party names (capitalized words)
        import re
        capitalized_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', ai_response)

        all_known_parties = set()
        for doc in documents:
            if doc.parties:
                all_known_parties.update(p.lower() for p in doc.parties)

        for word in capitalized_words:
            if word.lower() not in all_known_parties and len(word) > 3:
                # Potential hallucinated party name
                validation["warnings"].append({
                    "type": "unknown_party",
                    "text": word,
                    "message": f"Mentioned party '{word}' not found in uploaded documents"
                })
                validation["hallucination_risk"] = "medium"

        # Check for specific numbers/dates not in documents
        numbers = re.findall(r'\$[\d,]+(?:\.\d{2})?', ai_response)
        for number in numbers:
            found = False
            for doc in documents:
                if number in doc.text_content:
                    found = True
                    break

            if not found:
                validation["warnings"].append({
                    "type": "unverified_amount",
                    "text": number,
                    "message": f"Amount {number} not found in document text"
                })
                validation["hallucination_risk"] = "high"

        validation["is_valid"] = len(validation["warnings"]) == 0

        return validation


# Singleton instance getter
_context_manager_instance = None

def get_context_manager(db: Session) -> DocumentContextManager:
    """Get or create DocumentContextManager instance"""
    return DocumentContextManager(db)
