"""
Voice Command Processing Module

Handles speech-to-text conversion, natural language understanding,
and command routing for mobile voice interactions.
"""

import asyncio
import base64
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import openai
from fastapi import HTTPException

from .models import (
    VoiceCommand,
    VoiceCommandType,
    VoiceCommandStatus,
    VoiceCommandRequest,
    VoiceCommandResponse
)

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """
    Main voice processing engine that handles:
    - Speech-to-text conversion
    - Intent recognition
    - Command classification
    - Response generation
    """
    
    def __init__(self, openai_client: openai.AsyncOpenAI):
        self.openai_client = openai_client
        self.command_patterns = self._initialize_command_patterns()
        
    def _initialize_command_patterns(self) -> Dict[VoiceCommandType, List[str]]:
        """Initialize command pattern matching for intent recognition"""
        return {
            VoiceCommandType.SEARCH_DOCUMENTS: [
                "search", "find", "look for", "locate", "show me"
            ],
            VoiceCommandType.CREATE_CASE: [
                "create case", "new case", "start case", "open case"
            ],
            VoiceCommandType.DICTATE_NOTES: [
                "take note", "add note", "dictate", "record", "note that"
            ],
            VoiceCommandType.SCHEDULE_MEETING: [
                "schedule", "book meeting", "set up meeting", "plan meeting"
            ],
            VoiceCommandType.GET_CALENDAR: [
                "calendar", "schedule", "appointments", "meetings today"
            ],
            VoiceCommandType.SUMMARIZE_DOCUMENT: [
                "summarize", "summary", "brief", "overview", "key points"
            ],
            VoiceCommandType.LEGAL_RESEARCH: [
                "research", "case law", "statutes", "precedent", "legal"
            ],
            VoiceCommandType.CHECK_DEADLINES: [
                "deadlines", "due dates", "upcoming", "timeline", "due"
            ],
            VoiceCommandType.CLIENT_UPDATE: [
                "client", "update client", "notify client", "client status"
            ],
            VoiceCommandType.GENERAL_QUERY: [
                "what", "how", "when", "why", "tell me", "explain"
            ]
        }

    async def process_voice_command(
        self,
        request: VoiceCommandRequest,
        user_id: UUID,
        session_id: UUID
    ) -> VoiceCommandResponse:
        """
        Main entry point for processing voice commands
        """
        start_time = datetime.utcnow()
        
        try:
            # Convert speech to text if audio provided
            if request.audio_data:
                text, confidence = await self._speech_to_text(
                    request.audio_data,
                    request.audio_format,
                    request.language
                )
            else:
                text = request.text_input
                confidence = 1.0
            
            # Create voice command record
            command = VoiceCommand(
                user_id=user_id,
                session_id=session_id,
                command_type=VoiceCommandType.GENERAL_QUERY,  # Will be updated
                original_text=text,
                processed_text=text,
                confidence_score=confidence,
                status=VoiceCommandStatus.PROCESSING
            )
            
            # Classify the command
            command.command_type = await self._classify_command(text)
            
            # Process the command based on type
            response_data = await self._execute_command(command)
            
            # Update command status
            command.status = VoiceCommandStatus.COMPLETED
            command.response_data = response_data
            command.completed_at = datetime.utcnow()
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            command.processing_time_ms = processing_time
            
            return VoiceCommandResponse(
                command_id=command.id,
                status=command.status,
                message=self._generate_response_message(command),
                data=response_data,
                suggested_actions=self._get_suggested_actions(command),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing voice command: {str(e)}")
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return VoiceCommandResponse(
                command_id=command.id if 'command' in locals() else UUID('00000000-0000-0000-0000-000000000000'),
                status=VoiceCommandStatus.FAILED,
                message=f"Failed to process command: {str(e)}",
                processing_time_ms=processing_time
            )

    async def _speech_to_text(
        self,
        audio_data: str,
        audio_format: str,
        language: str
    ) -> Tuple[str, float]:
        """
        Convert speech audio to text using OpenAI Whisper
        """
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Create temporary file-like object for OpenAI API
            from io import BytesIO
            audio_file = BytesIO(audio_bytes)
            audio_file.name = f"audio.{audio_format}"
            
            # Use OpenAI Whisper for transcription
            response = await self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language.split('-')[0],  # Convert en-US to en
                response_format="verbose_json"
            )
            
            confidence = getattr(response, 'confidence', 0.8)  # Default confidence
            return response.text, confidence
            
        except Exception as e:
            logger.error(f"Speech-to-text conversion failed: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to process audio: {str(e)}"
            )

    async def _classify_command(self, text: str) -> VoiceCommandType:
        """
        Classify the command type based on the text content
        """
        text_lower = text.lower()
        
        # Pattern matching approach
        for command_type, patterns in self.command_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return command_type
        
        # Fallback: Use OpenAI for intent classification
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a legal AI assistant that classifies voice commands.
                        Classify the following command into one of these categories:
                        - search_documents: Finding or searching for documents
                        - create_case: Creating new legal cases
                        - dictate_notes: Adding notes or dictating content
                        - schedule_meeting: Scheduling appointments or meetings
                        - get_calendar: Checking calendar or schedule
                        - summarize_document: Summarizing documents
                        - legal_research: Legal research queries
                        - check_deadlines: Checking deadlines or due dates
                        - client_update: Updating client information
                        - general_query: General questions or queries
                        
                        Respond with only the category name."""
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            classification = response.choices[0].message.content.strip().lower()
            
            # Map response to enum
            for command_type in VoiceCommandType:
                if command_type.value == classification:
                    return command_type
                    
        except Exception as e:
            logger.warning(f"AI classification failed: {str(e)}")
        
        return VoiceCommandType.GENERAL_QUERY

    async def _execute_command(self, command: VoiceCommand) -> Dict[str, Any]:
        """
        Execute the classified command and return response data
        """
        command_handlers = {
            VoiceCommandType.SEARCH_DOCUMENTS: self._handle_search_documents,
            VoiceCommandType.CREATE_CASE: self._handle_create_case,
            VoiceCommandType.DICTATE_NOTES: self._handle_dictate_notes,
            VoiceCommandType.SCHEDULE_MEETING: self._handle_schedule_meeting,
            VoiceCommandType.GET_CALENDAR: self._handle_get_calendar,
            VoiceCommandType.SUMMARIZE_DOCUMENT: self._handle_summarize_document,
            VoiceCommandType.LEGAL_RESEARCH: self._handle_legal_research,
            VoiceCommandType.CHECK_DEADLINES: self._handle_check_deadlines,
            VoiceCommandType.CLIENT_UPDATE: self._handle_client_update,
            VoiceCommandType.GENERAL_QUERY: self._handle_general_query
        }
        
        handler = command_handlers.get(command.command_type, self._handle_general_query)
        return await handler(command)

    async def _handle_search_documents(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle document search commands"""
        return {
            "action": "document_search",
            "query": command.processed_text,
            "results": [],  # Would be populated by actual search
            "message": f"Searching for documents matching: {command.processed_text}"
        }

    async def _handle_create_case(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle case creation commands"""
        return {
            "action": "create_case",
            "case_details": {"name": "New Case", "description": command.processed_text},
            "message": "Case creation initiated. Please provide additional details."
        }

    async def _handle_dictate_notes(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle note dictation commands"""
        return {
            "action": "add_note",
            "note_content": command.processed_text,
            "message": "Note has been recorded successfully."
        }

    async def _handle_schedule_meeting(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle meeting scheduling commands"""
        return {
            "action": "schedule_meeting",
            "meeting_request": command.processed_text,
            "message": "Meeting scheduling request received. Please confirm details."
        }

    async def _handle_get_calendar(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle calendar queries"""
        return {
            "action": "get_calendar",
            "events": [],  # Would be populated by actual calendar data
            "message": "Retrieving your calendar information..."
        }

    async def _handle_summarize_document(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle document summarization commands"""
        return {
            "action": "summarize_document",
            "request": command.processed_text,
            "message": "Document summarization request received."
        }

    async def _handle_legal_research(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle legal research commands"""
        return {
            "action": "legal_research",
            "query": command.processed_text,
            "results": [],  # Would be populated by actual research
            "message": f"Conducting legal research for: {command.processed_text}"
        }

    async def _handle_check_deadlines(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle deadline checking commands"""
        return {
            "action": "check_deadlines",
            "upcoming_deadlines": [],  # Would be populated by actual data
            "message": "Checking your upcoming deadlines..."
        }

    async def _handle_client_update(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle client update commands"""
        return {
            "action": "client_update",
            "update_request": command.processed_text,
            "message": "Client update request processed."
        }

    async def _handle_general_query(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle general queries using AI"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful legal AI assistant. Provide concise,
                        accurate responses to legal questions. If you need more context,
                        ask clarifying questions."""
                    },
                    {
                        "role": "user",
                        "content": command.processed_text
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return {
                "action": "general_response",
                "response": response.choices[0].message.content,
                "message": "Query processed successfully."
            }
            
        except Exception as e:
            logger.error(f"General query processing failed: {str(e)}")
            return {
                "action": "general_response",
                "response": "I'm sorry, I couldn't process your query at the moment.",
                "message": "Query processing failed."
            }

    def _generate_response_message(self, command: VoiceCommand) -> str:
        """Generate appropriate response message based on command type"""
        messages = {
            VoiceCommandType.SEARCH_DOCUMENTS: "Document search completed",
            VoiceCommandType.CREATE_CASE: "Case creation initiated",
            VoiceCommandType.DICTATE_NOTES: "Note recorded successfully",
            VoiceCommandType.SCHEDULE_MEETING: "Meeting scheduling in progress",
            VoiceCommandType.GET_CALENDAR: "Calendar information retrieved",
            VoiceCommandType.SUMMARIZE_DOCUMENT: "Document summary generated",
            VoiceCommandType.LEGAL_RESEARCH: "Legal research completed",
            VoiceCommandType.CHECK_DEADLINES: "Deadline check completed",
            VoiceCommandType.CLIENT_UPDATE: "Client update processed",
            VoiceCommandType.GENERAL_QUERY: "Query processed successfully"
        }
        
        return messages.get(command.command_type, "Command processed")

    def _get_suggested_actions(self, command: VoiceCommand) -> List[str]:
        """Get suggested follow-up actions based on command type"""
        suggestions = {
            VoiceCommandType.SEARCH_DOCUMENTS: [
                "Open document", "Refine search", "Save search"
            ],
            VoiceCommandType.CREATE_CASE: [
                "Add client", "Set deadlines", "Upload documents"
            ],
            VoiceCommandType.DICTATE_NOTES: [
                "Edit note", "Share note", "Add to case"
            ],
            VoiceCommandType.SCHEDULE_MEETING: [
                "Confirm time", "Add attendees", "Set reminder"
            ],
            VoiceCommandType.GET_CALENDAR: [
                "Schedule meeting", "View details", "Set reminder"
            ],
            VoiceCommandType.SUMMARIZE_DOCUMENT: [
                "Read full document", "Share summary", "Export summary"
            ],
            VoiceCommandType.LEGAL_RESEARCH: [
                "Save research", "Export results", "Create brief"
            ],
            VoiceCommandType.CHECK_DEADLINES: [
                "Set reminder", "View details", "Update status"
            ],
            VoiceCommandType.CLIENT_UPDATE: [
                "Send notification", "Schedule call", "Update records"
            ],
            VoiceCommandType.GENERAL_QUERY: [
                "Ask follow-up", "Search documents", "Create task"
            ]
        }
        
        return suggestions.get(command.command_type, [])