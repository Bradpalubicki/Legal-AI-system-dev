"""
Comprehensive Trial Preparation System

AI-powered trial preparation tools for legal professionals including case analysis,
evidence management, witness preparation, document automation, and strategic planning.
"""

from .case_analyzer import CaseAnalyzer, CaseAnalysis, StrategicInsight
from .evidence_manager import EvidenceManager, EvidenceItem, EvidenceChain
from .witness_manager import WitnessManager, WitnessProfile, WitnessPreparation
from .document_generator import DocumentGenerator, TrialDocument, DocumentTemplate
from .timeline_builder import TimelineBuilder, TimelineEvent, CaseTimeline
from .jury_analyzer import JuryAnalyzer, JurorProfile, JurySelection
from .trial_manager import TrialManager, TrialPlan, TrialStrategy

__all__ = [
    # Core managers
    'TrialManager',
    'CaseAnalyzer', 
    'EvidenceManager',
    'WitnessManager',
    'DocumentGenerator',
    'TimelineBuilder',
    'JuryAnalyzer',
    
    # Data models
    'TrialPlan',
    'TrialStrategy',
    'CaseAnalysis',
    'StrategicInsight',
    'EvidenceItem',
    'EvidenceChain', 
    'WitnessProfile',
    'WitnessPreparation',
    'TrialDocument',
    'DocumentTemplate',
    'TimelineEvent',
    'CaseTimeline',
    'JurorProfile',
    'JurySelection'
]

__version__ = '1.0.0'
__author__ = 'Legal AI System'
__description__ = 'Comprehensive trial preparation and case management system'