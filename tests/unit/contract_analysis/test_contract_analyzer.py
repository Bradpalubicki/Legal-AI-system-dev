"""
Unit tests for contract analysis system.

Tests contract parsing, clause extraction, risk assessment,
compliance checking, and AI-powered contract analysis.
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any, Optional
import uuid

from src.contract_analysis.contract_analyzer import ContractAnalyzer
from src.contract_analysis.models import Contract, ContractClause, RiskAssessment, ComplianceCheck
from src.contract_analysis.enums import ContractType, ClauseType, RiskLevel, ComplianceStatus
from src.contract_analysis.exceptions import ContractParsingError, AnalysisError, InvalidContractError
from src.contract_analysis.clause_extractors import (
    PaymentTermsExtractor,
    TerminationClauseExtractor,
    LiabilityClauseExtractor,
    IntellectualPropertyExtractor
)
from src.ai_integration.openai_client import OpenAIClient


class TestContractAnalyzer:
    """Test suite for ContractAnalyzer class."""

    @pytest.fixture
    def contract_analyzer(self, mock_db_session):
        """Create ContractAnalyzer instance with mocked dependencies."""
        mock_openai_client = Mock(spec=OpenAIClient)
        return ContractAnalyzer(
            db_session=mock_db_session,
            ai_client=mock_openai_client
        )

    @pytest.fixture
    def sample_contract_data(self):
        """Sample contract data for testing."""
        return {
            "title": "Software Development Agreement",
            "contract_type": ContractType.SOFTWARE_DEVELOPMENT,
            "parties": [
                {"name": "TechCorp Inc.", "role": "client", "email": "legal@techcorp.com"},
                {"name": "DevStudio LLC", "role": "contractor", "email": "contracts@devstudio.com"}
            ],
            "effective_date": date.today(),
            "expiration_date": date.today() + timedelta(days=365),
            "value": Decimal("150000.00"),
            "currency": "USD",
            "jurisdiction": "State of California",
            "document_path": "/storage/contracts/software_dev_agreement.pdf"
        }

    @pytest.fixture
    def sample_contract_text(self):
        """Sample contract text for parsing."""
        return """
        SOFTWARE DEVELOPMENT AGREEMENT
        
        This Software Development Agreement ("Agreement") is entered into on January 1, 2024,
        between TechCorp Inc. ("Client") and DevStudio LLC ("Contractor").
        
        1. PAYMENT TERMS
        Client agrees to pay Contractor the sum of $150,000 USD for the services described herein.
        Payment shall be made in monthly installments of $12,500, due on the first day of each month.
        Late payments will incur a penalty of 1.5% per month.
        
        2. TERMINATION
        Either party may terminate this agreement with 30 days written notice.
        In case of material breach, the non-breaching party may terminate immediately.
        
        3. LIABILITY
        Contractor's total liability under this agreement shall not exceed the total contract value.
        Client acknowledges that software development involves inherent risks.
        
        4. INTELLECTUAL PROPERTY
        All work product created under this agreement shall be owned by the Client.
        Contractor retains rights to pre-existing intellectual property and general methodologies.
        
        5. CONFIDENTIALITY
        Both parties agree to maintain confidentiality of proprietary information.
        This obligation survives termination of the agreement.
        """

    @pytest.fixture
    def mock_contract(self, sample_contract_data):
        """Mock Contract object."""
        contract = Mock(spec=Contract)
        contract.id = str(uuid.uuid4())
        contract.title = sample_contract_data["title"]
        contract.contract_type = sample_contract_data["contract_type"]
        contract.parties = sample_contract_data["parties"]
        contract.effective_date = sample_contract_data["effective_date"]
        contract.expiration_date = sample_contract_data["expiration_date"]
        contract.value = sample_contract_data["value"]
        contract.status = "active"
        contract.created_at = datetime.now()
        return contract

    @pytest.fixture
    def mock_clause_extractors(self):
        """Mock clause extractor instances."""
        extractors = {
            ClauseType.PAYMENT_TERMS: Mock(spec=PaymentTermsExtractor),
            ClauseType.TERMINATION: Mock(spec=TerminationClauseExtractor),
            ClauseType.LIABILITY: Mock(spec=LiabilityClauseExtractor),
            ClauseType.INTELLECTUAL_PROPERTY: Mock(spec=IntellectualPropertyExtractor)
        }
        
        for extractor in extractors.values():
            extractor.extract = Mock()
            extractor.analyze_risk = Mock()
            
        return extractors

    @pytest.mark.asyncio
    async def test_analyze_contract_success(self, contract_analyzer, sample_contract_data, sample_contract_text, mock_db_session):
        """Test successful contract analysis."""
        # Arrange
        contract_analyzer.clause_extractors = self.mock_clause_extractors()
        
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        # Mock AI client response
        contract_analyzer.ai_client.chat_completion = AsyncMock(return_value={
            "choices": [{"message": {"content": "Contract analysis complete. Medium risk level identified."}}]
        })
        
        # Mock document reading
        with patch('src.document_processor.pdf_processor.PDFProcessor.extract_text', return_value=sample_contract_text):
            with patch('src.contract_analysis.models.Contract') as MockContract:
                mock_contract_instance = Mock()
                mock_contract_instance.id = str(uuid.uuid4())
                MockContract.return_value = mock_contract_instance
                
                # Act
                result = await contract_analyzer.analyze_contract(sample_contract_data)
                
                # Assert
                assert result is not None
                MockContract.assert_called_once()
                mock_db_session.add.assert_called()
                mock_db_session.commit.assert_called()
                contract_analyzer.ai_client.chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_payment_terms(self, contract_analyzer, sample_contract_text):
        """Test payment terms extraction."""
        # Arrange
        mock_extractor = Mock(spec=PaymentTermsExtractor)
        expected_terms = {
            "total_amount": Decimal("150000.00"),
            "currency": "USD",
            "payment_schedule": "monthly",
            "installment_amount": Decimal("12500.00"),
            "due_date": "1st of each month",
            "late_fee": "1.5% per month"
        }
        mock_extractor.extract.return_value = expected_terms
        
        contract_analyzer.clause_extractors = {ClauseType.PAYMENT_TERMS: mock_extractor}
        
        # Act
        result = contract_analyzer._extract_payment_terms(sample_contract_text)
        
        # Assert
        assert result == expected_terms
        mock_extractor.extract.assert_called_once_with(sample_contract_text)

    @pytest.mark.asyncio
    async def test_extract_termination_clauses(self, contract_analyzer, sample_contract_text):
        """Test termination clauses extraction."""
        # Arrange
        mock_extractor = Mock(spec=TerminationClauseExtractor)
        expected_clauses = {
            "notice_period": "30 days",
            "notice_method": "written notice",
            "immediate_termination_conditions": ["material breach"],
            "termination_for_convenience": True,
            "survival_clauses": ["confidentiality"]
        }
        mock_extractor.extract.return_value = expected_clauses
        
        contract_analyzer.clause_extractors = {ClauseType.TERMINATION: mock_extractor}
        
        # Act
        result = contract_analyzer._extract_termination_clauses(sample_contract_text)
        
        # Assert
        assert result == expected_clauses
        mock_extractor.extract.assert_called_once_with(sample_contract_text)

    @pytest.mark.asyncio
    async def test_assess_contract_risks(self, contract_analyzer, mock_contract, sample_contract_text):
        """Test contract risk assessment."""
        # Arrange
        contract_id = mock_contract.id
        
        # Mock extracted clauses
        extracted_clauses = [
            Mock(clause_type=ClauseType.PAYMENT_TERMS, content="Payment terms", risk_indicators=["late_fee"]),
            Mock(clause_type=ClauseType.LIABILITY, content="Liability terms", risk_indicators=["limited_liability"]),
            Mock(clause_type=ClauseType.TERMINATION, content="Termination terms", risk_indicators=["immediate_termination"])
        ]
        
        with patch.object(contract_analyzer, '_get_contract_clauses', return_value=extracted_clauses):
            with patch.object(contract_analyzer, '_calculate_risk_score', return_value=65):
                # Act
                risk_assessment = await contract_analyzer.assess_contract_risks(contract_id)
                
                # Assert
                assert risk_assessment is not None
                assert risk_assessment["overall_risk_score"] == 65
                assert risk_assessment["risk_level"] == RiskLevel.MEDIUM
                assert len(risk_assessment["risk_factors"]) > 0

    @pytest.mark.asyncio
    async def test_identify_missing_clauses(self, contract_analyzer, mock_contract):
        """Test identification of missing important clauses."""
        # Arrange
        contract_id = mock_contract.id
        existing_clauses = [ClauseType.PAYMENT_TERMS, ClauseType.TERMINATION]
        
        required_clauses = [
            ClauseType.PAYMENT_TERMS,
            ClauseType.TERMINATION,
            ClauseType.LIABILITY,
            ClauseType.CONFIDENTIALITY,
            ClauseType.INTELLECTUAL_PROPERTY
        ]
        
        with patch.object(contract_analyzer, '_get_existing_clause_types', return_value=existing_clauses):
            with patch.object(contract_analyzer, '_get_required_clauses', return_value=required_clauses):
                # Act
                missing_clauses = await contract_analyzer.identify_missing_clauses(contract_id)
                
                # Assert
                assert len(missing_clauses) == 3
                assert ClauseType.LIABILITY in missing_clauses
                assert ClauseType.CONFIDENTIALITY in missing_clauses
                assert ClauseType.INTELLECTUAL_PROPERTY in missing_clauses

    @pytest.mark.asyncio
    async def test_compare_contracts(self, contract_analyzer, mock_db_session):
        """Test contract comparison functionality."""
        # Arrange
        contract1_id = str(uuid.uuid4())
        contract2_id = str(uuid.uuid4())
        
        mock_contract1 = Mock(spec=Contract, id=contract1_id, title="Contract A")
        mock_contract2 = Mock(spec=Contract, id=contract2_id, title="Contract B")
        
        mock_db_session.get = AsyncMock(side_effect=[mock_contract1, mock_contract2])
        
        # Mock clause comparison
        with patch.object(contract_analyzer, '_compare_clauses') as mock_compare:
            mock_compare.return_value = {
                "differences": [
                    {"clause_type": "payment_terms", "difference": "Different payment schedules"},
                    {"clause_type": "liability", "difference": "Different liability caps"}
                ],
                "similarity_score": 0.75
            }
            
            # Act
            comparison = await contract_analyzer.compare_contracts(contract1_id, contract2_id)
            
            # Assert
            assert comparison is not None
            assert comparison["similarity_score"] == 0.75
            assert len(comparison["differences"]) == 2
            mock_compare.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_contract_summary(self, contract_analyzer, mock_contract, mock_db_session):
        """Test contract summary generation."""
        # Arrange
        contract_id = mock_contract.id
        mock_db_session.get = AsyncMock(return_value=mock_contract)
        
        # Mock AI summary generation
        contract_analyzer.ai_client.chat_completion = AsyncMock(return_value={
            "choices": [{"message": {"content": "This is a software development agreement with medium complexity and standard terms."}}]
        })
        
        # Mock clause data
        mock_clauses = [
            Mock(clause_type=ClauseType.PAYMENT_TERMS, content="Payment terms"),
            Mock(clause_type=ClauseType.TERMINATION, content="Termination terms")
        ]
        
        with patch.object(contract_analyzer, '_get_contract_clauses', return_value=mock_clauses):
            # Act
            summary = await contract_analyzer.generate_contract_summary(contract_id)
            
            # Assert
            assert summary is not None
            assert "overview" in summary
            assert "key_terms" in summary
            assert "risk_assessment" in summary
            contract_analyzer.ai_client.chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_contract_compliance(self, contract_analyzer, mock_contract):
        """Test contract compliance validation."""
        # Arrange
        contract_id = mock_contract.id
        compliance_rules = [
            {"rule_id": "gdpr_compliance", "description": "GDPR data protection compliance"},
            {"rule_id": "employment_law", "description": "Employment law compliance"}
        ]
        
        with patch.object(contract_analyzer, '_get_compliance_rules', return_value=compliance_rules):
            with patch.object(contract_analyzer, '_check_rule_compliance') as mock_check:
                mock_check.side_effect = [
                    {"compliant": True, "score": 95},
                    {"compliant": False, "score": 60, "violations": ["Missing privacy clause"]}
                ]
                
                # Act
                compliance_result = await contract_analyzer.validate_contract_compliance(contract_id)
                
                # Assert
                assert compliance_result is not None
                assert compliance_result["overall_compliance_score"] > 0
                assert len(compliance_result["rule_results"]) == 2
                assert compliance_result["rule_results"][0]["compliant"] is True
                assert compliance_result["rule_results"][1]["compliant"] is False

    @pytest.mark.asyncio
    async def test_extract_key_dates(self, contract_analyzer, sample_contract_text):
        """Test extraction of key dates from contract."""
        # Act
        key_dates = contract_analyzer._extract_key_dates(sample_contract_text)
        
        # Assert
        assert "effective_date" in key_dates
        assert "termination_notice_period" in key_dates
        assert key_dates["effective_date"] == date(2024, 1, 1)
        assert key_dates["termination_notice_period"] == "30 days"

    @pytest.mark.asyncio
    async def test_extract_financial_terms(self, contract_analyzer, sample_contract_text):
        """Test extraction of financial terms."""
        # Act
        financial_terms = contract_analyzer._extract_financial_terms(sample_contract_text)
        
        # Assert
        assert financial_terms["total_value"] == Decimal("150000.00")
        assert financial_terms["currency"] == "USD"
        assert financial_terms["payment_frequency"] == "monthly"
        assert financial_terms["installment_amount"] == Decimal("12500.00")
        assert financial_terms["late_penalty"] == "1.5% per month"

    @pytest.mark.asyncio
    async def test_detect_unusual_clauses(self, contract_analyzer, mock_contract):
        """Test detection of unusual or non-standard clauses."""
        # Arrange
        contract_id = mock_contract.id
        
        contract_text = """
        This contract includes an unusual clause requiring the contractor to work
        exclusively on weekends and a penalty of $50,000 for any delay exceeding 1 day.
        """
        
        # Mock AI analysis for unusual clause detection
        contract_analyzer.ai_client.chat_completion = AsyncMock(return_value={
            "choices": [{"message": {"content": "UNUSUAL_CLAUSES: Weekend work requirement, Excessive penalty for delays"}}]
        })
        
        with patch.object(contract_analyzer, '_get_contract_text', return_value=contract_text):
            # Act
            unusual_clauses = await contract_analyzer.detect_unusual_clauses(contract_id)
            
            # Assert
            assert len(unusual_clauses) > 0
            assert any("weekend" in clause.lower() for clause in unusual_clauses)
            assert any("penalty" in clause.lower() for clause in unusual_clauses)

    @pytest.mark.asyncio
    async def test_calculate_risk_score(self, contract_analyzer):
        """Test risk score calculation algorithm."""
        # Arrange
        risk_factors = [
            {"type": "payment_terms", "severity": "medium", "weight": 0.3},
            {"type": "liability", "severity": "high", "weight": 0.4},
            {"type": "termination", "severity": "low", "weight": 0.2},
            {"type": "intellectual_property", "severity": "medium", "weight": 0.1}
        ]
        
        # Act
        risk_score = contract_analyzer._calculate_risk_score(risk_factors)
        
        # Assert
        assert 0 <= risk_score <= 100
        assert isinstance(risk_score, (int, float))

    @pytest.mark.asyncio
    async def test_generate_redline_suggestions(self, contract_analyzer, mock_contract):
        """Test generation of redline suggestions."""
        # Arrange
        contract_id = mock_contract.id
        
        # Mock AI suggestions
        contract_analyzer.ai_client.chat_completion = AsyncMock(return_value={
            "choices": [{"message": {"content": """
            REDLINE_SUGGESTIONS:
            1. Section 1: Add more specific payment terms
            2. Section 3: Include liability cap
            3. Section 5: Strengthen confidentiality clause
            """}}]
        })
        
        with patch.object(contract_analyzer, '_get_contract_text', return_value="contract text"):
            # Act
            suggestions = await contract_analyzer.generate_redline_suggestions(contract_id)
            
            # Assert
            assert len(suggestions) > 0
            assert all("section" in suggestion.lower() for suggestion in suggestions)

    @pytest.mark.asyncio
    async def test_analyze_contract_language_complexity(self, contract_analyzer, sample_contract_text):
        """Test analysis of contract language complexity."""
        # Act
        complexity_analysis = contract_analyzer._analyze_language_complexity(sample_contract_text)
        
        # Assert
        assert "readability_score" in complexity_analysis
        assert "complexity_level" in complexity_analysis
        assert "average_sentence_length" in complexity_analysis
        assert "technical_terms_count" in complexity_analysis

    @pytest.mark.asyncio
    async def test_extract_party_obligations(self, contract_analyzer, sample_contract_text):
        """Test extraction of party obligations."""
        # Act
        obligations = contract_analyzer._extract_party_obligations(sample_contract_text)
        
        # Assert
        assert "Client" in obligations
        assert "Contractor" in obligations
        assert len(obligations["Client"]) > 0
        assert len(obligations["Contractor"]) > 0
        assert any("pay" in obligation.lower() for obligation in obligations["Client"])

    @pytest.mark.asyncio
    async def test_contract_renewal_analysis(self, contract_analyzer, mock_contract):
        """Test contract renewal analysis."""
        # Arrange
        contract_id = mock_contract.id
        mock_contract.expiration_date = date.today() + timedelta(days=30)  # Expiring soon
        
        with patch.object(contract_analyzer, '_analyze_performance_history') as mock_performance:
            mock_performance.return_value = {
                "payment_history": "excellent",
                "compliance_score": 95,
                "dispute_count": 0
            }
            
            # Act
            renewal_analysis = await contract_analyzer.analyze_contract_renewal(contract_id)
            
            # Assert
            assert renewal_analysis is not None
            assert "renewal_recommendation" in renewal_analysis
            assert "risk_factors" in renewal_analysis
            assert "performance_summary" in renewal_analysis

    @pytest.mark.parametrize("contract_type,expected_required_clauses", [
        (ContractType.SOFTWARE_DEVELOPMENT, [ClauseType.PAYMENT_TERMS, ClauseType.INTELLECTUAL_PROPERTY, ClauseType.LIABILITY]),
        (ContractType.EMPLOYMENT, [ClauseType.TERMINATION, ClauseType.CONFIDENTIALITY, ClauseType.COMPENSATION]),
        (ContractType.NDA, [ClauseType.CONFIDENTIALITY, ClauseType.LIABILITY, ClauseType.TERMINATION])
    ])
    def test_get_required_clauses_by_contract_type(self, contract_analyzer, contract_type, expected_required_clauses):
        """Test required clauses based on contract type."""
        # Act
        required_clauses = contract_analyzer._get_required_clauses(contract_type)
        
        # Assert
        for expected_clause in expected_required_clauses:
            assert expected_clause in required_clauses

    @pytest.mark.asyncio
    async def test_batch_contract_analysis(self, contract_analyzer, mock_db_session):
        """Test batch processing of multiple contracts."""
        # Arrange
        contract_ids = [str(uuid.uuid4()) for _ in range(3)]
        
        with patch.object(contract_analyzer, 'analyze_contract') as mock_analyze:
            mock_analyze.return_value = {"status": "completed", "risk_score": 65}
            
            # Act
            results = await contract_analyzer.batch_analyze_contracts(contract_ids)
            
            # Assert
            assert len(results) == 3
            assert all(result["status"] == "completed" for result in results)
            assert mock_analyze.call_count == 3

    @pytest.mark.asyncio
    async def test_contract_template_matching(self, contract_analyzer, mock_contract):
        """Test matching contracts against standard templates."""
        # Arrange
        contract_id = mock_contract.id
        
        template_matches = [
            {"template_name": "Standard Software Agreement", "similarity": 0.85},
            {"template_name": "IT Services Contract", "similarity": 0.72}
        ]
        
        with patch.object(contract_analyzer, '_match_against_templates', return_value=template_matches):
            # Act
            matches = await contract_analyzer.find_template_matches(contract_id)
            
            # Assert
            assert len(matches) == 2
            assert matches[0]["similarity"] > matches[1]["similarity"]
            assert matches[0]["template_name"] == "Standard Software Agreement"

    @pytest.mark.asyncio
    async def test_contract_clause_recommendation(self, contract_analyzer, mock_contract):
        """Test recommendation of additional clauses."""
        # Arrange
        contract_id = mock_contract.id
        missing_clauses = [ClauseType.FORCE_MAJEURE, ClauseType.DISPUTE_RESOLUTION]
        
        with patch.object(contract_analyzer, 'identify_missing_clauses', return_value=missing_clauses):
            # Mock clause recommendations
            contract_analyzer.ai_client.chat_completion = AsyncMock(return_value={
                "choices": [{"message": {"content": "Recommended force majeure clause: In the event of circumstances beyond..."}}]
            })
            
            # Act
            recommendations = await contract_analyzer.recommend_clauses(contract_id)
            
            # Assert
            assert len(recommendations) > 0
            assert all("clause_type" in rec for rec in recommendations)
            assert all("recommended_text" in rec for rec in recommendations)