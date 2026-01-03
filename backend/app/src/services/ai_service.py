"""
AI Service for Legal Document Analysis using OpenAI
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent.parent / '.env')

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered document analysis using OpenAI"""

    def __init__(self):
        self.openai_available = bool(os.getenv('OPENAI_API_KEY'))
        self.client = None

        if self.openai_available:
            self.client = OpenAI(
                api_key=os.getenv('OPENAI_API_KEY')
            )
        else:
            logger.warning("No OpenAI API key found. AI features will not work.")

    async def analyze_legal_document(self, text: str, filename: str = "") -> Dict[str, Any]:
        """
        Analyze legal document text using OpenAI GPT-4

        Args:
            text: The extracted text from the document
            filename: Original filename for context

        Returns:
            Dictionary with analysis results
        """
        try:
            if not os.getenv('OPENAI_API_KEY'):
                return self._fallback_analysis(text)

            prompt = self._create_analysis_prompt(text, filename)

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # More cost-effective than gpt-4
                messages=[
                    {
                        "role": "system",
                        "content": """You are a legal document analysis AI. Analyze legal documents and extract key information in JSON format. Be precise and professional."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=1500
            )

            # Parse the AI response
            ai_response = response.choices[0].message.content

            # Try to extract JSON from the response
            try:
                # Look for JSON in the response
                if "```json" in ai_response:
                    json_start = ai_response.find("```json") + 7
                    json_end = ai_response.find("```", json_start)
                    json_str = ai_response[json_start:json_end].strip()
                else:
                    # Assume the entire response is JSON
                    json_str = ai_response.strip()

                analysis_result = json.loads(json_str)

                # Validate required fields
                analysis_result = self._validate_analysis_result(analysis_result)

                logger.info(f"Successfully analyzed document: {filename}")
                return analysis_result

            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI response as JSON: {ai_response}")
                return self._fallback_analysis(text, ai_response)

        except Exception as e:
            logger.error(f"Error in AI document analysis: {str(e)}")
            return self._fallback_analysis(text, str(e))

    async def ask_document_question(self, prompt: str) -> str:
        """
        Ask a question about a document using OpenAI

        Args:
            prompt: The formatted prompt with document context and question

        Returns:
            AI response string
        """
        try:
            if not os.getenv('OPENAI_API_KEY'):
                return "AI Q&A service is not available. Please configure OpenAI API key."

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a legal document Q&A assistant. Provide accurate, helpful answers based on the document context provided. Always indicate your confidence level and any limitations in your analysis."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Lower temperature for more consistent Q&A
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in AI Q&A: {str(e)}")
            return f"I apologize, but I encountered an error while processing your question: {str(e)}. Please try rephrasing your question or try again later."

    async def analyze_defenses(self, prompt: str) -> str:
        """
        Analyze potential legal defenses using OpenAI

        Args:
            prompt: The formatted prompt with document context and defense analysis request

        Returns:
            AI response string with defense analysis
        """
        try:
            if not os.getenv('OPENAI_API_KEY'):
                return "Defense analysis service is not available. Please configure OpenAI API key."

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a legal defense strategy analyst. Analyze documents and identify potential legal defenses, considering both procedural and substantive defenses. Provide practical, actionable defense strategies while being clear about limitations and the need for professional legal counsel."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=1500
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in AI defense analysis: {str(e)}")
            return f"I encountered an error while analyzing potential defenses: {str(e)}. Please consult with a qualified attorney for defense strategy analysis."

    async def analyze_attorney_obligations(self, prompt: str) -> str:
        """
        Analyze attorney obligations and performance tracking using OpenAI

        Args:
            prompt: The formatted prompt with document context and tracking request

        Returns:
            AI response string with attorney obligation analysis
        """
        try:
            if not os.getenv('OPENAI_API_KEY'):
                return "Attorney tracking service is not available. Please configure OpenAI API key."

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an attorney performance and accountability analyst. Analyze legal documents and identify specific obligations, deadlines, and performance standards for attorneys. Focus on practical accountability measures while respecting attorney-client privilege and professional standards."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=1200
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error in AI attorney obligation analysis: {str(e)}")
            return f"I encountered an error while analyzing attorney obligations: {str(e)}. Please discuss performance expectations directly with your attorney."

    def _create_analysis_prompt(self, text: str, filename: str) -> str:
        """Create the analysis prompt for OpenAI"""
        return f"""
Analyze this legal document and extract the following information in JSON format:

Document filename: {filename}
Document text: {text[:4000]}...

Please provide a JSON response with exactly these fields:
{{
    "document_type": "string - type of legal document (Motion, Petition, Order, Contract, Brief, etc.)",
    "summary": "string - 2-3 sentence summary of what this document is about",
    "parties": ["array of strings - names of parties involved"],
    "key_dates": [
        {{
            "date": "YYYY-MM-DD format",
            "description": "what happens on this date"
        }}
    ],
    "deadlines": [
        {{
            "date": "YYYY-MM-DD format",
            "description": "deadline description"
        }}
    ],
    "confidence": "number between 0.0 and 1.0 - how confident you are in this analysis",
    "key_terms": ["array of important legal terms or concepts mentioned"],
    "case_number": "string - case number if mentioned, or null",
    "court": "string - court name if mentioned, or null",
    "requesting": "string - what is being requested or the main purpose"
}}

Extract actual information from the document. If something is not clearly stated, use null or empty array.
Be precise with dates - only include dates that are explicitly mentioned.
For confidence, consider factors like document clarity, completeness, and your certainty about the extracted information.
"""

    def _validate_analysis_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and ensure all required fields are present"""
        validated = {
            "document_type": result.get("document_type", "Unknown Document"),
            "summary": result.get("summary", "Document analysis completed"),
            "parties": result.get("parties", []),
            "key_dates": result.get("key_dates", []),
            "deadlines": result.get("deadlines", []),
            "confidence": float(result.get("confidence", 0.7)),
            "key_terms": result.get("key_terms", []),
            "case_number": result.get("case_number"),
            "court": result.get("court"),
            "requesting": result.get("requesting", "Analysis pending")
        }

        # Ensure confidence is between 0 and 1
        validated["confidence"] = max(0.0, min(1.0, validated["confidence"]))

        return validated

    def _fallback_analysis(self, text: str, error_msg: str = "") -> Dict[str, Any]:
        """Provide basic analysis when AI is not available"""
        logger.warning(f"Using fallback analysis. Error: {error_msg}")

        # Basic text analysis
        words = text.lower().split()

        # Detect document type based on keywords
        doc_type = "Legal Document"
        if "motion" in words:
            doc_type = "Motion"
        elif "petition" in words:
            doc_type = "Petition"
        elif "order" in words:
            doc_type = "Order"
        elif "contract" in words or "agreement" in words:
            doc_type = "Contract"
        elif "brief" in words:
            doc_type = "Brief"

        return {
            "document_type": doc_type,
            "summary": "Document uploaded and processed. AI analysis unavailable - using basic text processing.",
            "parties": [],
            "key_dates": [],
            "deadlines": [],
            "confidence": 0.3,  # Low confidence for fallback
            "key_terms": [],
            "case_number": None,
            "court": None,
            "requesting": "Basic document processing completed"
        }

# Global AI service instance
ai_service = AIService()