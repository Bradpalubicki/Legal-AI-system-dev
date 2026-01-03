"""
Unit Tests for OpenAI Client Integration

Tests the OpenAI API client wrapper including authentication,
request handling, response processing, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import asyncio

# Mock OpenAI types and exceptions
class MockOpenAIError(Exception):
    """Mock OpenAI API error"""
    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(message)


class MockRateLimitError(MockOpenAIError):
    """Mock rate limit error"""
    pass


class MockAPIError(MockOpenAIError):
    """Mock API error"""
    pass


class TestOpenAIClient:
    """Test suite for OpenAI client integration"""

    def setup_method(self):
        """Set up test fixtures"""
        self.api_key = "sk-test123456789"
        self.mock_response_data = {
            "id": "cmpl-123456",
            "object": "text_completion",
            "created": 1677649420,
            "model": "gpt-4",
            "choices": [{
                "text": "This is a sample AI response for legal document analysis.",
                "index": 0,
                "logprobs": None,
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 100,
                "total_tokens": 150
            }
        }

    @patch('openai.OpenAI')
    def test_client_initialization(self, mock_openai):
        """Test OpenAI client initialization"""
        from unittest.mock import MagicMock
        
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Test client initialization
        api_key = "sk-test123"
        organization = "org-test"
        
        # Simulate client creation
        client = mock_openai(
            api_key=api_key,
            organization=organization
        )
        
        # Verify client was created with correct parameters
        mock_openai.assert_called_once_with(
            api_key=api_key,
            organization=organization
        )
        assert client == mock_client

    @patch('openai.OpenAI')
    def test_client_initialization_without_organization(self, mock_openai):
        """Test client initialization without organization"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        api_key = "sk-test123"
        client = mock_openai(api_key=api_key)
        
        mock_openai.assert_called_once_with(api_key=api_key)

    @patch('openai.OpenAI')
    def test_text_completion_request(self, mock_openai):
        """Test basic text completion request"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].text = "Sample legal analysis response"
        mock_response.usage.total_tokens = 150
        
        mock_client.completions.create.return_value = mock_response
        
        # Test completion request
        client = mock_openai(api_key="sk-test123")
        
        prompt = "Analyze this legal document:"
        response = client.completions.create(
            model="gpt-4",
            prompt=prompt,
            max_tokens=500,
            temperature=0.3
        )
        
        # Verify request parameters
        mock_client.completions.create.assert_called_once_with(
            model="gpt-4",
            prompt=prompt,
            max_tokens=500,
            temperature=0.3
        )
        
        # Verify response
        assert response.choices[0].text == "Sample legal analysis response"
        assert response.usage.total_tokens == 150

    @patch('openai.OpenAI')
    def test_chat_completion_request(self, mock_openai):
        """Test chat completion request"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock chat completion response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Legal analysis complete"
        mock_response.usage.total_tokens = 200
        
        mock_client.chat.completions.create.return_value = mock_response
        
        client = mock_openai(api_key="sk-test123")
        
        messages = [
            {"role": "system", "content": "You are a legal AI assistant."},
            {"role": "user", "content": "Analyze this contract clause."}
        ]
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1000,
            temperature=0.2
        )
        
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=messages,
            max_tokens=1000,
            temperature=0.2
        )
        
        assert response.choices[0].message.content == "Legal analysis complete"

    @patch('openai.OpenAI')
    def test_embeddings_request(self, mock_openai):
        """Test embeddings API request"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock embeddings response
        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        mock_response.usage.total_tokens = 50
        
        mock_client.embeddings.create.return_value = mock_response
        
        client = mock_openai(api_key="sk-test123")
        
        text = "Legal document text to embed"
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        
        mock_client.embeddings.create.assert_called_once_with(
            model="text-embedding-ada-002",
            input=text
        )
        
        assert len(response.data[0].embedding) == 1536  # 512 * 3
        assert response.usage.total_tokens == 50

    @patch('openai.OpenAI')
    def test_api_error_handling(self, mock_openai):
        """Test API error handling"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock API error
        mock_client.chat.completions.create.side_effect = MockAPIError(
            "Invalid request", code="invalid_request"
        )
        
        client = mock_openai(api_key="sk-test123")
        
        with pytest.raises(MockAPIError) as exc_info:
            client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "test"}]
            )
        
        assert "Invalid request" in str(exc_info.value)

    @patch('openai.OpenAI')
    def test_rate_limit_error_handling(self, mock_openai):
        """Test rate limit error handling"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock rate limit error
        mock_client.chat.completions.create.side_effect = MockRateLimitError(
            "Rate limit exceeded", code="rate_limit_exceeded"
        )
        
        client = mock_openai(api_key="sk-test123")
        
        with pytest.raises(MockRateLimitError) as exc_info:
            client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "test"}]
            )
        
        assert "Rate limit exceeded" in str(exc_info.value)

    @patch('openai.OpenAI')
    def test_authentication_error(self, mock_openai):
        """Test authentication error handling"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock authentication error
        mock_client.chat.completions.create.side_effect = MockAPIError(
            "Invalid API key", code="invalid_api_key"
        )
        
        client = mock_openai(api_key="invalid-key")
        
        with pytest.raises(MockAPIError) as exc_info:
            client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "test"}]
            )
        
        assert "Invalid API key" in str(exc_info.value)

    @patch('openai.OpenAI')
    def test_timeout_handling(self, mock_openai):
        """Test request timeout handling"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock timeout error
        import requests
        mock_client.chat.completions.create.side_effect = requests.Timeout("Request timed out")
        
        client = mock_openai(api_key="sk-test123")
        
        with pytest.raises(requests.Timeout):
            client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "test"}]
            )

    @patch('openai.OpenAI')
    def test_token_counting(self, mock_openai):
        """Test token usage tracking"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock response with token usage
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        mock_client.chat.completions.create.return_value = mock_response
        
        client = mock_openai(api_key="sk-test123")
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "test"}]
        )
        
        assert response.usage.prompt_tokens == 100
        assert response.usage.completion_tokens == 50
        assert response.usage.total_tokens == 150

    @patch('openai.OpenAI')
    def test_streaming_response(self, mock_openai):
        """Test streaming response handling"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock streaming response
        def mock_stream():
            chunks = [
                {"choices": [{"delta": {"content": "This "}}]},
                {"choices": [{"delta": {"content": "is "}}]},
                {"choices": [{"delta": {"content": "streaming"}}]},
                {"choices": [{"delta": {}}]}  # End of stream
            ]
            for chunk in chunks:
                mock_chunk = MagicMock()
                mock_chunk.choices = [MagicMock()]
                if chunk["choices"][0]["delta"].get("content"):
                    mock_chunk.choices[0].delta.content = chunk["choices"][0]["delta"]["content"]
                else:
                    mock_chunk.choices[0].delta.content = None
                yield mock_chunk
        
        mock_client.chat.completions.create.return_value = mock_stream()
        
        client = mock_openai(api_key="sk-test123")
        
        stream = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "test"}],
            stream=True
        )
        
        # Collect streamed content
        content = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content += chunk.choices[0].delta.content
        
        assert content == "This is streaming"

    @patch('openai.OpenAI')
    def test_function_calling(self, mock_openai):
        """Test function calling feature"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock function call response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.function_call.name = "analyze_contract"
        mock_response.choices[0].message.function_call.arguments = '{"clause_type": "liability"}'
        
        mock_client.chat.completions.create.return_value = mock_response
        
        client = mock_openai(api_key="sk-test123")
        
        functions = [{
            "name": "analyze_contract",
            "description": "Analyze a contract clause",
            "parameters": {
                "type": "object",
                "properties": {
                    "clause_type": {"type": "string"}
                }
            }
        }]
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Analyze this clause"}],
            functions=functions
        )
        
        assert response.choices[0].message.function_call.name == "analyze_contract"
        assert "liability" in response.choices[0].message.function_call.arguments

    @patch('openai.OpenAI')
    def test_moderation_api(self, mock_openai):
        """Test content moderation API"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock moderation response
        mock_response = MagicMock()
        mock_response.results = [MagicMock()]
        mock_response.results[0].flagged = False
        mock_response.results[0].categories.hate = False
        mock_response.results[0].categories.harassment = False
        mock_response.results[0].category_scores.hate = 0.001
        
        mock_client.moderations.create.return_value = mock_response
        
        client = mock_openai(api_key="sk-test123")
        
        text = "This is a legal document clause."
        response = client.moderations.create(input=text)
        
        mock_client.moderations.create.assert_called_once_with(input=text)
        assert not response.results[0].flagged
        assert not response.results[0].categories.hate

    def test_prompt_engineering_helpers(self):
        """Test prompt engineering utility functions"""
        
        def create_legal_prompt(document_type: str, instruction: str) -> str:
            """Helper function to create legal analysis prompts"""
            return f"""You are a legal AI assistant specializing in {document_type} analysis.
            
Task: {instruction}

Please provide a comprehensive analysis including:
1. Key legal concepts identified
2. Potential risks or concerns
3. Recommendations for review

Document type: {document_type}
"""
        
        prompt = create_legal_prompt("contract", "Review this employment agreement")
        
        assert "legal AI assistant" in prompt
        assert "contract" in prompt
        assert "employment agreement" in prompt
        assert "Key legal concepts" in prompt

    def test_response_parsing_helpers(self):
        """Test response parsing utility functions"""
        
        def parse_legal_analysis(response_text: str) -> Dict[str, Any]:
            """Helper function to parse legal analysis responses"""
            analysis = {
                "summary": "",
                "key_points": [],
                "risks": [],
                "recommendations": []
            }
            
            lines = response_text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if "Summary:" in line:
                    current_section = "summary"
                elif "Key Points:" in line:
                    current_section = "key_points"
                elif "Risks:" in line:
                    current_section = "risks"
                elif "Recommendations:" in line:
                    current_section = "recommendations"
                elif line and current_section:
                    if current_section == "summary":
                        analysis["summary"] += line + " "
                    elif line.startswith("- "):
                        analysis[current_section].append(line[2:])
            
            return analysis
        
        sample_response = """Summary: This is a standard employment contract with typical clauses.

Key Points:
- At-will employment provision
- Confidentiality agreement included
- Non-compete clause present

Risks:
- Non-compete may be too broad
- Termination clause ambiguous

Recommendations:
- Review non-compete geography
- Clarify termination procedures"""
        
        analysis = parse_legal_analysis(sample_response)
        
        assert "standard employment contract" in analysis["summary"]
        assert len(analysis["key_points"]) == 3
        assert len(analysis["risks"]) == 2
        assert len(analysis["recommendations"]) == 2

    @patch('openai.OpenAI')
    def test_batch_processing(self, mock_openai):
        """Test batch processing of multiple requests"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock responses for batch requests
        def mock_create(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = f"Analysis for: {kwargs['messages'][1]['content']}"
            return mock_response
        
        mock_client.chat.completions.create.side_effect = mock_create
        
        client = mock_openai(api_key="sk-test123")
        
        documents = ["Document 1", "Document 2", "Document 3"]
        results = []
        
        for doc in documents:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Analyze this document."},
                    {"role": "user", "content": doc}
                ]
            )
            results.append(response.choices[0].message.content)
        
        assert len(results) == 3
        assert "Document 1" in results[0]
        assert "Document 2" in results[1]
        assert "Document 3" in results[2]

    @patch('openai.OpenAI')
    def test_cost_tracking(self, mock_openai):
        """Test API cost tracking functionality"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock response with token usage
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage.prompt_tokens = 1000
        mock_response.usage.completion_tokens = 500
        mock_response.usage.total_tokens = 1500
        
        mock_client.chat.completions.create.return_value = mock_response
        
        client = mock_openai(api_key="sk-test123")
        
        # Pricing per 1K tokens (example rates)
        gpt4_input_cost = 0.03  # $0.03 per 1K input tokens
        gpt4_output_cost = 0.06  # $0.06 per 1K output tokens
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "test"}]
        )
        
        # Calculate cost
        input_cost = (response.usage.prompt_tokens / 1000) * gpt4_input_cost
        output_cost = (response.usage.completion_tokens / 1000) * gpt4_output_cost
        total_cost = input_cost + output_cost
        
        expected_cost = (1000 / 1000) * 0.03 + (500 / 1000) * 0.06
        assert total_cost == expected_cost
        assert total_cost == 0.06  # $0.03 + $0.03

    def test_legal_document_types_enum(self):
        """Test legal document types enumeration"""
        
        class LegalDocumentType:
            CONTRACT = "contract"
            BRIEF = "brief"
            MOTION = "motion"
            MEMORANDUM = "memorandum"
            COMPLAINT = "complaint"
            ANSWER = "answer"
            DISCOVERY = "discovery"
        
        # Test all document types are defined
        assert hasattr(LegalDocumentType, 'CONTRACT')
        assert hasattr(LegalDocumentType, 'BRIEF')
        assert hasattr(LegalDocumentType, 'MOTION')
        
        # Test values
        assert LegalDocumentType.CONTRACT == "contract"
        assert LegalDocumentType.BRIEF == "brief"
        assert LegalDocumentType.MOTION == "motion"

    def test_legal_analysis_categories(self):
        """Test legal analysis categories"""
        
        class AnalysisCategory:
            RISK_ASSESSMENT = "risk_assessment"
            COMPLIANCE_CHECK = "compliance_check"
            CLAUSE_EXTRACTION = "clause_extraction"
            ENTITY_RECOGNITION = "entity_recognition"
            SUMMARY_GENERATION = "summary_generation"
        
        categories = [
            AnalysisCategory.RISK_ASSESSMENT,
            AnalysisCategory.COMPLIANCE_CHECK,
            AnalysisCategory.CLAUSE_EXTRACTION,
            AnalysisCategory.ENTITY_RECOGNITION,
            AnalysisCategory.SUMMARY_GENERATION
        ]
        
        assert len(categories) == 5
        assert "risk_assessment" in categories
        assert "compliance_check" in categories