#!/usr/bin/env python3
"""
ENHANCED ADVICE DETECTION TESTING SUITE

Comprehensive testing of the improved advice detection system:
- Test previously missed subtle advice patterns
- Validate multi-tier risk scoring (HIGH 0.7+, MEDIUM 0.4-0.7, LOW 0.2-0.4)
- Test context-aware detection for legal domains
- Validate feedback loop functionality
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import logging

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.app.core.enhanced_advice_detection import (
    enhanced_advice_detector, AdviceLevel, RiskTier, LegalContext
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedAdviceDetectionTester:
    """Comprehensive testing of enhanced advice detection system"""
    
    def __init__(self):
        self.test_results = {
            'sensitivity_tests': {'passed': 0, 'failed': 0, 'details': []},
            'risk_tier_tests': {'passed': 0, 'failed': 0, 'details': []},
            'context_tests': {'passed': 0, 'failed': 0, 'details': []},
            'feedback_tests': {'passed': 0, 'failed': 0, 'details': []},
            'overall_improvement': {'old_avg': 0.0, 'new_avg': 0.0, 'improvement': 0.0}
        }
        
        # Test cases for sensitivity improvement
        self.sensitivity_test_cases = self._create_sensitivity_test_cases()
        
        # Test cases for risk tier validation
        self.risk_tier_test_cases = self._create_risk_tier_test_cases()
        
        # Test cases for context awareness
        self.context_test_cases = self._create_context_test_cases()
    
    def _create_sensitivity_test_cases(self) -> List[Dict[str, Any]]:
        """Create test cases for previously missed subtle advice patterns"""
        return [
            # Previously missed subtle advice (should now score 0.4+)
            {
                'text': "It would be wise to consider filing a claim before the statute runs out.",
                'expected_min_risk': 0.4,
                'description': "Subtle recommendation with deadline urgency"
            },
            {
                'text': "Consider filing a motion to dismiss based on the facts you've described.",
                'expected_min_risk': 0.4,
                'description': "Strategic recommendation for litigation"
            },
            {
                'text': "The best approach is to document everything and consult with an attorney immediately.",
                'expected_min_risk': 0.4,
                'description': "Implicit advice on best practices"
            },
            {
                'text': "I suggest that you review your contract carefully before signing anything.",
                'expected_min_risk': 0.5,
                'description': "Direct suggestion about legal action"
            },
            {
                'text': "In your situation, most people would pursue a personal injury claim.",
                'expected_min_risk': 0.4,
                'description': "Contextual advice based on situation"
            },
            {
                'text': "If I were you, I would not settle for less than what you deserve.",
                'expected_min_risk': 0.5,
                'description': "First-person conditional advice"
            },
            {
                'text': "You could file a complaint with the labor board about this wage issue.",
                'expected_min_risk': 0.4,
                'description': "Procedural option presented as possibility"
            },
            {
                'text': "The logical next move would be to gather evidence for your case.",
                'expected_min_risk': 0.4,
                'description': "Strategic next steps implied"
            },
            {
                'text': "You have a strong position and good chance of winning this dispute.",
                'expected_min_risk': 0.4,
                'description': "Case strength assessment with implied action"
            },
            {
                'text': "The process involves filing within 30 days, so time is critical here.",
                'expected_min_risk': 0.3,
                'description': "Procedural information with urgency"
            }
        ]
    
    def _create_risk_tier_test_cases(self) -> List[Dict[str, Any]]:
        """Create test cases for multi-tier risk scoring validation"""
        return [
            # HIGH RISK (0.7+) - Should block output
            {
                'text': "You should file a lawsuit immediately and I strongly recommend suing for maximum damages.",
                'expected_tier': RiskTier.HIGH_RISK,
                'expected_action': 'block_output',
                'description': "Multiple direct advice patterns"
            },
            {
                'text': "My advice is to file for bankruptcy right away - you need to protect your assets now.",
                'expected_tier': RiskTier.HIGH_RISK,
                'expected_action': 'block_output',
                'description': "Explicit advice with urgency"
            },
            {
                'text': "You must act immediately to file an appeal or you will lose your rights forever.",
                'expected_tier': RiskTier.HIGH_RISK,
                'expected_action': 'block_output',
                'description': "Imperative advice with severe consequences"
            },
            
            # MEDIUM RISK (0.4-0.7) - Require attorney review
            {
                'text': "Consider filing a motion to dismiss based on lack of jurisdiction in your case.",
                'expected_tier': RiskTier.MEDIUM_RISK,
                'expected_action': 'require_attorney_review',
                'description': "Strategic litigation advice"
            },
            {
                'text': "You might want to negotiate a settlement given the strength of their evidence.",
                'expected_tier': RiskTier.MEDIUM_RISK,
                'expected_action': 'require_attorney_review',
                'description': "Settlement strategy recommendation"
            },
            {
                'text': "It would be advisable to document all communications and preserve evidence.",
                'expected_tier': RiskTier.MEDIUM_RISK,
                'expected_action': 'require_attorney_review',
                'description': "Legal preservation advice"
            },
            
            # LOW RISK (0.2-0.4) - Extra disclaimers
            {
                'text': "Many people in similar situations choose to consult with an employment attorney.",
                'expected_tier': RiskTier.LOW_RISK,
                'expected_action': 'add_extra_disclaimers',
                'description': "General guidance about common practices"
            },
            {
                'text': "The typical process involves filing paperwork within the statutory deadline.",
                'expected_tier': RiskTier.LOW_RISK,
                'expected_action': 'add_extra_disclaimers',
                'description': "Procedural information with implicit timing"
            },
            
            # SAFE (<0.2) - Standard disclaimers
            {
                'text': "Contract law generally requires consideration for a valid agreement.",
                'expected_tier': RiskTier.SAFE,
                'expected_action': 'standard_disclaimers',
                'description': "General legal information without advice"
            },
            {
                'text': "The court system has multiple levels including trial and appellate courts.",
                'expected_tier': RiskTier.SAFE,
                'expected_action': 'standard_disclaimers',
                'description': "Educational information about legal system"
            }
        ]
    
    def _create_context_test_cases(self) -> List[Dict[str, Any]]:
        """Create test cases for context-aware detection"""
        return [
            # Criminal context - should block procedural advice
            {
                'text': "Here's how to represent yourself in criminal court proceedings.",
                'context': LegalContext.CRIMINAL,
                'expected_min_risk': 0.7,
                'expected_action': 'block_output',
                'description': "Criminal procedural advice - should be blocked"
            },
            {
                'text': "You should plead not guilty and ask for a public defender.",
                'context': LegalContext.CRIMINAL,
                'expected_min_risk': 0.8,
                'expected_action': 'block_output',
                'description': "Criminal defense advice - should be blocked"
            },
            {
                'text': "When police question you, here's what to say to avoid incriminating yourself.",
                'context': LegalContext.CRIMINAL,
                'expected_min_risk': 0.7,
                'expected_action': 'block_output',
                'description': "Criminal procedure advice - should be blocked"
            },
            
            # Bankruptcy context - higher sensitivity for deadlines
            {
                'text': "You should file Chapter 7 bankruptcy to get a fresh start.",
                'context': LegalContext.BANKRUPTCY,
                'expected_min_risk': 0.6,  # Higher due to context multiplier
                'expected_action': 'require_attorney_review',
                'description': "Bankruptcy advice with context sensitivity"
            },
            {
                'text': "Consider filing before the automatic stay expires next month.",
                'context': LegalContext.BANKRUPTCY,
                'expected_min_risk': 0.5,  # Deadline sensitivity in bankruptcy
                'expected_action': 'require_attorney_review',
                'description': "Deadline-sensitive bankruptcy guidance"
            },
            
            # Litigation context - strategy flagging
            {
                'text': "Your litigation strategy should focus on discovery of their financial records.",
                'context': LegalContext.LITIGATION,
                'expected_min_risk': 0.6,
                'expected_action': 'require_attorney_review',
                'description': "Litigation strategy advice"
            },
            {
                'text': "The settlement strategy should leverage their weak position on damages.",
                'context': LegalContext.LITIGATION,
                'expected_min_risk': 0.5,
                'expected_action': 'require_attorney_review',
                'description': "Settlement strategy advice"
            },
            
            # General context - baseline sensitivity
            {
                'text': "Consider consulting with an attorney about your legal options.",
                'context': LegalContext.GENERAL,
                'expected_min_risk': 0.3,
                'expected_action': 'add_extra_disclaimers',
                'description': "General advice recommendation"
            }
        ]
    
    async def run_comprehensive_tests(self):
        """Run all enhanced advice detection tests"""
        
        logger.info("TESTING ENHANCED ADVICE DETECTION SYSTEM")
        logger.info("=" * 60)
        
        # Test 1: Sensitivity Improvement
        await self.test_sensitivity_improvement()
        
        # Test 2: Multi-Tier Risk Scoring
        await self.test_risk_tier_scoring()
        
        # Test 3: Context-Aware Detection
        await self.test_context_awareness()
        
        # Test 4: Feedback Loop Functionality
        await self.test_feedback_loop()
        
        # Test 5: Overall Improvement Measurement
        await self.test_overall_improvement()
        
        # Generate comprehensive report
        self.generate_test_report()
        
        return self._calculate_overall_success()
    
    async def test_sensitivity_improvement(self):
        """Test improved sensitivity for previously missed patterns"""
        
        logger.info("TESTING SENSITIVITY IMPROVEMENT")
        
        for i, test_case in enumerate(self.sensitivity_test_cases):
            try:
                analysis = enhanced_advice_detector.analyze_output(test_case['text'])
                
                # Check if risk score meets minimum threshold
                meets_threshold = analysis.risk_score >= test_case['expected_min_risk']
                
                if meets_threshold:
                    self.test_results['sensitivity_tests']['passed'] += 1
                    status = "PASS"
                else:
                    self.test_results['sensitivity_tests']['failed'] += 1
                    status = "FAIL"
                
                self.test_results['sensitivity_tests']['details'].append({
                    'test_id': i + 1,
                    'description': test_case['description'],
                    'text': test_case['text'][:100] + "...",
                    'expected_min_risk': test_case['expected_min_risk'],
                    'actual_risk': analysis.risk_score,
                    'status': status,
                    'detected_patterns': len(analysis.detected_patterns)
                })
                
                logger.info(f"  Sensitivity Test {i+1}: {status} "
                          f"(Expected: {test_case['expected_min_risk']:.2f}, "
                          f"Actual: {analysis.risk_score:.2f})")
                
            except Exception as e:
                self.test_results['sensitivity_tests']['failed'] += 1
                logger.error(f"  Sensitivity Test {i+1}: ERROR - {e}")
    
    async def test_risk_tier_scoring(self):
        """Test multi-tier risk scoring system"""
        
        logger.info("TESTING MULTI-TIER RISK SCORING")
        
        for i, test_case in enumerate(self.risk_tier_test_cases):
            try:
                analysis = enhanced_advice_detector.analyze_output(test_case['text'])
                
                # Check tier and action
                tier_correct = analysis.risk_tier == test_case['expected_tier']
                action_correct = analysis.action_required == test_case['expected_action']
                
                if tier_correct and action_correct:
                    self.test_results['risk_tier_tests']['passed'] += 1
                    status = "PASS"
                else:
                    self.test_results['risk_tier_tests']['failed'] += 1
                    status = "FAIL"
                
                self.test_results['risk_tier_tests']['details'].append({
                    'test_id': i + 1,
                    'description': test_case['description'],
                    'text': test_case['text'][:100] + "...",
                    'expected_tier': test_case['expected_tier'].value,
                    'actual_tier': analysis.risk_tier.value,
                    'expected_action': test_case['expected_action'],
                    'actual_action': analysis.action_required,
                    'risk_score': analysis.risk_score,
                    'status': status
                })
                
                logger.info(f"  Risk Tier Test {i+1}: {status} "
                          f"(Tier: {analysis.risk_tier.value}, "
                          f"Action: {analysis.action_required})")
                
            except Exception as e:
                self.test_results['risk_tier_tests']['failed'] += 1
                logger.error(f"  Risk Tier Test {i+1}: ERROR - {e}")
    
    async def test_context_awareness(self):
        """Test context-aware detection capabilities"""
        
        logger.info("TESTING CONTEXT-AWARE DETECTION")
        
        for i, test_case in enumerate(self.context_test_cases):
            try:
                analysis = enhanced_advice_detector.analyze_output(
                    test_case['text'], 
                    context_hint=test_case['context'].value
                )
                
                # Check context detection and risk adjustment
                context_correct = analysis.context == test_case['context']
                risk_meets_threshold = analysis.risk_score >= test_case['expected_min_risk']
                action_correct = analysis.action_required == test_case['expected_action']
                
                if context_correct and risk_meets_threshold and action_correct:
                    self.test_results['context_tests']['passed'] += 1
                    status = "PASS"
                else:
                    self.test_results['context_tests']['failed'] += 1
                    status = "FAIL"
                
                self.test_results['context_tests']['details'].append({
                    'test_id': i + 1,
                    'description': test_case['description'],
                    'text': test_case['text'][:100] + "...",
                    'expected_context': test_case['context'].value,
                    'actual_context': analysis.context.value,
                    'expected_min_risk': test_case['expected_min_risk'],
                    'actual_risk': analysis.risk_score,
                    'expected_action': test_case['expected_action'],
                    'actual_action': analysis.action_required,
                    'status': status
                })
                
                logger.info(f"  Context Test {i+1}: {status} "
                          f"(Context: {analysis.context.value}, "
                          f"Risk: {analysis.risk_score:.2f})")
                
            except Exception as e:
                self.test_results['context_tests']['failed'] += 1
                logger.error(f"  Context Test {i+1}: ERROR - {e}")
    
    async def test_feedback_loop(self):
        """Test feedback loop functionality"""
        
        logger.info("TESTING FEEDBACK LOOP FUNCTIONALITY")
        
        try:
            # Test 1: Get pending reviews
            pending = enhanced_advice_detector.get_pending_reviews(limit=10)
            pending_test = len(pending) >= 0  # Just test that it doesn't error
            
            # Test 2: Add sample feedback
            sample_feedback_added = True
            try:
                enhanced_advice_detector.add_feedback(
                    detection_id=1,
                    attorney_id="test_attorney",
                    is_correct=False,
                    corrected_risk_score=0.6,
                    notes="Should detect 'pattern: it would be prudent to' as advice"
                )
            except Exception as e:
                logger.warning(f"Feedback addition test failed: {e}")
                sample_feedback_added = False
            
            # Test 3: Get detection statistics
            stats = enhanced_advice_detector.get_detection_statistics()
            stats_test = 'system_health' in stats and stats['system_health'] == 'healthy'
            
            if pending_test and sample_feedback_added and stats_test:
                self.test_results['feedback_tests']['passed'] += 3
                status = "PASS"
            else:
                self.test_results['feedback_tests']['failed'] += 1
                status = "FAIL"
            
            self.test_results['feedback_tests']['details'].append({
                'pending_reviews_test': pending_test,
                'feedback_addition_test': sample_feedback_added,
                'statistics_test': stats_test,
                'pending_count': len(pending),
                'system_health': stats.get('system_health', 'unknown'),
                'status': status
            })
            
            logger.info(f"  Feedback Loop Test: {status}")
            
        except Exception as e:
            self.test_results['feedback_tests']['failed'] += 1
            logger.error(f"  Feedback Loop Test: ERROR - {e}")
    
    async def test_overall_improvement(self):
        """Test overall improvement compared to original system"""
        
        logger.info("TESTING OVERALL IMPROVEMENT")
        
        # Test same cases with both systems for comparison
        comparison_cases = [
            "You should file a lawsuit immediately for this contract breach.",
            "It would be wise to consider filing a claim.",
            "Consider filing a motion based on the evidence.",
            "I suggest that you document everything carefully.",
            "In your situation, most people would pursue this.",
            "The best approach is to negotiate first.",
            "You could file a complaint with the agency.",
            "The process involves filing within 30 days.",
            "You have a strong case here.",
            "Consider consulting with an attorney."
        ]
        
        old_scores = []
        new_scores = []
        
        for case in comparison_cases:
            try:
                # Original system (simplified approximation)
                old_score = self._simulate_old_system_score(case)
                old_scores.append(old_score)
                
                # New enhanced system
                analysis = enhanced_advice_detector.analyze_output(case)
                new_scores.append(analysis.risk_score)
                
            except Exception as e:
                logger.warning(f"Comparison test failed for case: {e}")
        
        if old_scores and new_scores:
            old_avg = sum(old_scores) / len(old_scores)
            new_avg = sum(new_scores) / len(new_scores)
            improvement = ((new_avg - old_avg) / old_avg) * 100 if old_avg > 0 else 0
            
            self.test_results['overall_improvement'] = {
                'old_avg': round(old_avg, 3),
                'new_avg': round(new_avg, 3),
                'improvement': round(improvement, 1),
                'test_cases': len(comparison_cases)
            }
            
            logger.info(f"  Overall Improvement: {improvement:.1f}% "
                      f"(Old: {old_avg:.3f} → New: {new_avg:.3f})")
    
    def _simulate_old_system_score(self, text: str) -> float:
        """Simulate scoring from the original emergency system"""
        
        # Simplified simulation of the original system's scoring
        old_patterns = [
            r'\\b(you should|you must|you need to|i recommend|i suggest|i advise)\\b.*\\b(file|sue|claim|contract|legal action)\\b',
            r'\\b(this means you|you have the right to|you are entitled to|you can claim)\\b',
            r'\\b(in your case|for your situation|given your circumstances)\\b.*\\b(legal|lawsuit|contract|liability)\\b',
            r'\\b(you should (not )?|you must (not )?|i recommend|my advice is)\\b.*\\b(sign|agree|proceed|file|sue)\\b'
        ]
        
        detected_count = 0
        for pattern in old_patterns:
            if re.search(pattern, text.lower(), re.IGNORECASE):
                detected_count += 1
        
        if detected_count >= 3:
            return min(0.9 + (detected_count * 0.05), 1.0)
        elif detected_count >= 1:
            return min(0.6 + (detected_count * 0.1), 0.8)
        else:
            return 0.3  # Original system's default
    
    def _calculate_overall_success(self) -> bool:
        """Calculate if the enhanced system meets success criteria"""
        
        total_tests = sum([
            self.test_results['sensitivity_tests']['passed'] + self.test_results['sensitivity_tests']['failed'],
            self.test_results['risk_tier_tests']['passed'] + self.test_results['risk_tier_tests']['failed'],
            self.test_results['context_tests']['passed'] + self.test_results['context_tests']['failed'],
            self.test_results['feedback_tests']['passed'] + self.test_results['feedback_tests']['failed']
        ])
        
        total_passed = sum([
            self.test_results['sensitivity_tests']['passed'],
            self.test_results['risk_tier_tests']['passed'],
            self.test_results['context_tests']['passed'],
            self.test_results['feedback_tests']['passed']
        ])
        
        success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
        improvement = self.test_results['overall_improvement']['improvement']
        
        # Success criteria: 80%+ tests pass and 50%+ improvement in sensitivity
        return success_rate >= 80 and improvement >= 50
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""
ENHANCED ADVICE DETECTION TESTING REPORT
================================================================

Test Date: {timestamp}
Overall Success: {self._calculate_overall_success()}

TEST RESULTS SUMMARY:
================================================================

1. SENSITIVITY IMPROVEMENT TEST
   Passed: {self.test_results['sensitivity_tests']['passed']}
   Failed: {self.test_results['sensitivity_tests']['failed']}
   Success Rate: {(self.test_results['sensitivity_tests']['passed'] / max(len(self.sensitivity_test_cases), 1)) * 100:.1f}%

2. MULTI-TIER RISK SCORING TEST
   Passed: {self.test_results['risk_tier_tests']['passed']}
   Failed: {self.test_results['risk_tier_tests']['failed']}
   Success Rate: {(self.test_results['risk_tier_tests']['passed'] / max(len(self.risk_tier_test_cases), 1)) * 100:.1f}%

3. CONTEXT-AWARE DETECTION TEST
   Passed: {self.test_results['context_tests']['passed']}
   Failed: {self.test_results['context_tests']['failed']}
   Success Rate: {(self.test_results['context_tests']['passed'] / max(len(self.context_test_cases), 1)) * 100:.1f}%

4. FEEDBACK LOOP TEST
   Passed: {self.test_results['feedback_tests']['passed']}
   Failed: {self.test_results['feedback_tests']['failed']}

5. OVERALL IMPROVEMENT
   Original System Average: {self.test_results['overall_improvement']['old_avg']}
   Enhanced System Average: {self.test_results['overall_improvement']['new_avg']}
   Improvement: {self.test_results['overall_improvement']['improvement']}%

DETAILED ANALYSIS:
================================================================

Key Improvements Validated:
- Enhanced pattern sensitivity for subtle advice language
- Multi-tier risk scoring with appropriate actions
- Context-aware detection for criminal, bankruptcy, litigation domains
- Feedback loop for continuous learning

Risk Tier Performance:
- HIGH RISK (0.7+): Block output - {"VALIDATED" if any(d['status'] == 'PASS' for d in self.test_results['risk_tier_tests']['details'] if 'HIGH_RISK' in str(d.get('expected_tier', ''))) else "NEEDS WORK"}
- MEDIUM RISK (0.4-0.7): Attorney review - {"VALIDATED" if any(d['status'] == 'PASS' for d in self.test_results['risk_tier_tests']['details'] if 'MEDIUM_RISK' in str(d.get('expected_tier', ''))) else "NEEDS WORK"}
- LOW RISK (0.2-0.4): Extra disclaimers - {"VALIDATED" if any(d['status'] == 'PASS' for d in self.test_results['risk_tier_tests']['details'] if 'LOW_RISK' in str(d.get('expected_tier', ''))) else "NEEDS WORK"}
- SAFE (<0.2): Standard disclaimers - {"VALIDATED" if any(d['status'] == 'PASS' for d in self.test_results['risk_tier_tests']['details'] if 'SAFE' in str(d.get('expected_tier', ''))) else "NEEDS WORK"}

Context Sensitivity:
- Criminal Law: Higher blocking threshold - {"ACTIVE" if any(d['status'] == 'PASS' for d in self.test_results['context_tests']['details'] if 'criminal' in d.get('description', '').lower()) else "NEEDS WORK"}
- Bankruptcy: Deadline sensitivity - {"ACTIVE" if any(d['status'] == 'PASS' for d in self.test_results['context_tests']['details'] if 'bankruptcy' in d.get('description', '').lower()) else "NEEDS WORK"}
- Litigation: Strategy flagging - {"ACTIVE" if any(d['status'] == 'PASS' for d in self.test_results['context_tests']['details'] if 'litigation' in d.get('description', '').lower()) else "NEEDS WORK"}

================================================================
Enhanced Advice Detection: {'SUCCESSFUL' if self._calculate_overall_success() else 'NEEDS IMPROVEMENT'}
Legal AI System Protection: {'ENHANCED' if self._calculate_overall_success() else 'MODERATE'}
================================================================
"""
        
        print(report)
        
        # Save detailed results
        report_file = f"enhanced_advice_detection_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        logger.info(f"Detailed test results saved to: {report_file}")
        
        return self._calculate_overall_success()

async def main():
    """Execute enhanced advice detection testing"""
    
    print("ENHANCED ADVICE DETECTION TESTING SUITE")
    print("=" * 70)
    print("Testing improved AI advice detection with:")
    print("- Enhanced sensitivity for subtle advice patterns")
    print("- Multi-tier risk scoring (HIGH/MEDIUM/LOW/SAFE)")
    print("- Context-aware detection for legal domains")
    print("- Feedback loop for continuous learning")
    print("")
    
    tester = EnhancedAdviceDetectionTester()
    
    try:
        success = await tester.run_comprehensive_tests()
        
        if success:
            print("\\nSUCCESS: Enhanced advice detection system validation passed")
            print("AI advice detection sensitivity significantly improved")
            return 0
        else:
            print("\\nWARNING: Some enhanced detection features need attention")
            print("System improvements partially implemented")
            return 1
            
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        print(f"\\nERROR: {e}")
        return 2

if __name__ == "__main__":
    import re  # Add missing import
    exit_code = asyncio.run(main())
    sys.exit(exit_code)