"""
Statistical Analyzer

Advanced statistical analysis system for A/B testing with comprehensive
statistical tests, power analysis, and effect size calculations.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
import logging
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2_contingency, fisher_exact
import warnings
from statsmodels.stats.power import ttest_power, ztost_power
from statsmodels.stats.proportion import proportions_ztest, proportion_confint
from statsmodels.stats.contingency_tables import mcnemar
import math

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

class TestMethod(Enum):
    TTEST_INDEPENDENT = "ttest_independent"
    TTEST_PAIRED = "ttest_paired"
    WELCH_TTEST = "welch_ttest"
    MANN_WHITNEY = "mann_whitney"
    WILCOXON_SIGNED_RANK = "wilcoxon_signed_rank"
    CHI_SQUARE = "chi_square"
    FISHER_EXACT = "fisher_exact"
    PROPORTION_Z_TEST = "proportion_z_test"
    MCNEMAR_TEST = "mcnemar_test"
    KOLMOGOROV_SMIRNOV = "kolmogorov_smirnov"
    ANDERSON_DARLING = "anderson_darling"
    BOOTSTRAP = "bootstrap"
    PERMUTATION = "permutation"
    BAYESIAN_T_TEST = "bayesian_t_test"

class EffectSizeMethod(Enum):
    COHEN_D = "cohen_d"
    HEDGES_G = "hedges_g"
    GLASS_DELTA = "glass_delta"
    CLIFF_DELTA = "cliff_delta"
    ETA_SQUARED = "eta_squared"
    OMEGA_SQUARED = "omega_squared"
    CRAMER_V = "cramer_v"
    ODDS_RATIO = "odds_ratio"
    RELATIVE_RISK = "relative_risk"

class CorrectionMethod(Enum):
    BONFERRONI = "bonferroni"
    HOLM = "holm"
    SIDAK = "sidak"
    BENJAMINI_HOCHBERG = "benjamini_hochberg"
    BENJAMINI_YEKUTIELI = "benjamini_yekutieli"

@dataclass
class StatisticalTest:
    test_id: str = ""
    test_method: TestMethod = TestMethod.TTEST_INDEPENDENT
    test_name: str = ""
    description: str = ""
    assumptions: List[str] = field(default_factory=list)
    required_sample_size: Optional[int] = None
    alpha_level: float = 0.05
    power_target: float = 0.8
    effect_size_target: float = 0.5
    two_sided: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class TestResult:
    test_id: str = ""
    test_method: TestMethod = TestMethod.TTEST_INDEPENDENT
    statistic: float = 0.0
    p_value: float = 1.0
    effect_size: float = 0.0
    effect_size_method: EffectSizeMethod = EffectSizeMethod.COHEN_D
    confidence_interval: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    degrees_of_freedom: Optional[float] = None
    sample_sizes: Dict[str, int] = field(default_factory=dict)
    group_statistics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    assumptions_met: Dict[str, bool] = field(default_factory=dict)
    power_achieved: float = 0.0
    is_significant: bool = False
    practical_significance: bool = False
    interpretation: str = ""
    recommendations: List[str] = field(default_factory=list)
    raw_data_summary: Dict[str, Any] = field(default_factory=dict)
    test_timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class PowerAnalysis:
    analysis_id: str = ""
    test_method: TestMethod = TestMethod.TTEST_INDEPENDENT
    effect_size: float = 0.0
    alpha: float = 0.05
    power: float = 0.8
    sample_size_per_group: int = 0
    total_sample_size: int = 0
    minimum_detectable_effect: float = 0.0
    power_curve_data: Optional[Dict[str, List[float]]] = None
    sensitivity_analysis: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class EffectSize:
    effect_size_method: EffectSizeMethod = EffectSizeMethod.COHEN_D
    value: float = 0.0
    confidence_interval: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    interpretation: str = ""  # negligible, small, medium, large
    practical_significance: bool = False
    business_impact: Optional[Dict[str, float]] = None

class StatisticalAnalyzer:
    def __init__(self):
        self.test_registry: Dict[str, StatisticalTest] = {}
        self.test_results_cache: Dict[str, TestResult] = {}
        self.power_analysis_cache: Dict[str, PowerAnalysis] = {}
        
        # Statistical configuration
        self.config = {
            'default_alpha': 0.05,
            'default_power': 0.8,
            'default_effect_size': 0.5,
            'bootstrap_iterations': 10000,
            'permutation_iterations': 10000,
            'confidence_level': 0.95,
            'multiple_comparison_correction': True,
            'assumption_checking_enabled': True,
            'practical_significance_threshold': 0.02,
            'minimum_sample_size': 30,
            'outlier_detection_enabled': True,
            'robust_statistics_fallback': True
        }
        
        # Effect size interpretations (Cohen's conventions)
        self.effect_size_interpretations = {
            EffectSizeMethod.COHEN_D: {
                'small': 0.2,
                'medium': 0.5,
                'large': 0.8
            },
            EffectSizeMethod.HEDGES_G: {
                'small': 0.2,
                'medium': 0.5,
                'large': 0.8
            },
            EffectSizeMethod.ETA_SQUARED: {
                'small': 0.01,
                'medium': 0.06,
                'large': 0.14
            },
            EffectSizeMethod.CRAMER_V: {
                'small': 0.1,
                'medium': 0.3,
                'large': 0.5
            }
        }

    async def register_test(
        self,
        test_id: str,
        test_method: TestMethod,
        test_name: str,
        description: str = "",
        alpha_level: float = 0.05,
        power_target: float = 0.8,
        effect_size_target: float = 0.5,
        two_sided: bool = True
    ) -> bool:
        """Register a statistical test configuration."""
        try:
            test = StatisticalTest(
                test_id=test_id,
                test_method=test_method,
                test_name=test_name,
                description=description,
                alpha_level=alpha_level,
                power_target=power_target,
                effect_size_target=effect_size_target,
                two_sided=two_sided,
                assumptions=self._get_test_assumptions(test_method)
            )
            
            self.test_registry[test_id] = test
            logger.info(f"Registered statistical test: {test_id} ({test_method.value})")
            return True
            
        except Exception as e:
            logger.error(f"Error registering test {test_id}: {e}")
            return False

    async def perform_statistical_test(
        self,
        test_id: str,
        group_a_data: List[float],
        group_b_data: List[float],
        test_method: Optional[TestMethod] = None,
        alpha: Optional[float] = None,
        alternative: str = 'two-sided'
    ) -> TestResult:
        """Perform a statistical test comparing two groups."""
        try:
            # Get test configuration
            if test_id in self.test_registry:
                test_config = self.test_registry[test_id]
                method = test_method or test_config.test_method
                alpha_level = alpha or test_config.alpha_level
            else:
                method = test_method or TestMethod.TTEST_INDEPENDENT
                alpha_level = alpha or self.config['default_alpha']
            
            # Validate data
            if not group_a_data or not group_b_data:
                raise ValueError("Both groups must have data")
            
            if len(group_a_data) < 2 or len(group_b_data) < 2:
                raise ValueError("Each group must have at least 2 data points")
            
            # Remove invalid values
            group_a_clean = [x for x in group_a_data if not (np.isnan(x) or np.isinf(x))]
            group_b_clean = [x for x in group_b_data if not (np.isnan(x) or np.isinf(x))]
            
            if not group_a_clean or not group_b_clean:
                raise ValueError("No valid data after cleaning")
            
            # Check assumptions if enabled
            assumptions_met = {}
            if self.config['assumption_checking_enabled']:
                assumptions_met = await self._check_test_assumptions(method, group_a_clean, group_b_clean)
            
            # Perform the statistical test
            test_result = await self._execute_statistical_test(
                method, group_a_clean, group_b_clean, alpha_level, alternative
            )
            
            # Calculate effect size
            effect_size_result = await self._calculate_effect_size(
                group_a_clean, group_b_clean, EffectSizeMethod.COHEN_D
            )
            
            # Calculate achieved power
            achieved_power = await self._calculate_achieved_power(
                method, effect_size_result.value, len(group_a_clean), len(group_b_clean), alpha_level
            )
            
            # Create comprehensive result
            result = TestResult(
                test_id=test_id,
                test_method=method,
                statistic=test_result['statistic'],
                p_value=test_result['p_value'],
                effect_size=effect_size_result.value,
                effect_size_method=effect_size_result.effect_size_method,
                confidence_interval=test_result.get('confidence_interval', (0.0, 0.0)),
                degrees_of_freedom=test_result.get('degrees_of_freedom'),
                sample_sizes={'group_a': len(group_a_clean), 'group_b': len(group_b_clean)},
                group_statistics={
                    'group_a': {
                        'mean': float(np.mean(group_a_clean)),
                        'std': float(np.std(group_a_clean, ddof=1)),
                        'median': float(np.median(group_a_clean)),
                        'min': float(np.min(group_a_clean)),
                        'max': float(np.max(group_a_clean))
                    },
                    'group_b': {
                        'mean': float(np.mean(group_b_clean)),
                        'std': float(np.std(group_b_clean, ddof=1)),
                        'median': float(np.median(group_b_clean)),
                        'min': float(np.min(group_b_clean)),
                        'max': float(np.max(group_b_clean))
                    }
                },
                assumptions_met=assumptions_met,
                power_achieved=achieved_power,
                is_significant=test_result['p_value'] < alpha_level,
                practical_significance=abs(effect_size_result.value) >= self.config['practical_significance_threshold']
            )
            
            # Generate interpretation and recommendations
            result.interpretation = await self._generate_interpretation(result)
            result.recommendations = await self._generate_recommendations(result, assumptions_met)
            
            # Cache result
            self.test_results_cache[f"{test_id}_{datetime.utcnow().timestamp()}"] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Error performing statistical test {test_id}: {e}")
            return TestResult(
                test_id=test_id,
                test_method=method,
                p_value=1.0,
                interpretation=f"Test failed: {str(e)}"
            )

    async def perform_power_analysis(
        self,
        test_method: TestMethod,
        effect_size: Optional[float] = None,
        alpha: Optional[float] = None,
        power: Optional[float] = None,
        sample_size: Optional[int] = None,
        solve_for: str = 'sample_size'
    ) -> PowerAnalysis:
        """Perform power analysis to determine sample size, power, or detectable effect size."""
        try:
            # Set defaults
            alpha_level = alpha or self.config['default_alpha']
            power_target = power or self.config['default_power']
            effect_size_target = effect_size or self.config['default_effect_size']
            
            analysis_id = f"power_{test_method.value}_{datetime.utcnow().timestamp()}"
            
            # Perform power calculations based on what we're solving for
            if solve_for == 'sample_size':
                if effect_size is None or power is None:
                    raise ValueError("Effect size and power must be specified to solve for sample size")
                
                sample_size_per_group = await self._calculate_sample_size(
                    test_method, effect_size, alpha_level, power
                )
                
                result = PowerAnalysis(
                    analysis_id=analysis_id,
                    test_method=test_method,
                    effect_size=effect_size,
                    alpha=alpha_level,
                    power=power,
                    sample_size_per_group=sample_size_per_group,
                    total_sample_size=sample_size_per_group * 2
                )
                
            elif solve_for == 'power':
                if effect_size is None or sample_size is None:
                    raise ValueError("Effect size and sample size must be specified to solve for power")
                
                achieved_power = await self._calculate_power(
                    test_method, effect_size, sample_size, alpha_level
                )
                
                result = PowerAnalysis(
                    analysis_id=analysis_id,
                    test_method=test_method,
                    effect_size=effect_size,
                    alpha=alpha_level,
                    power=achieved_power,
                    sample_size_per_group=sample_size,
                    total_sample_size=sample_size * 2
                )
                
            elif solve_for == 'effect_size':
                if power is None or sample_size is None:
                    raise ValueError("Power and sample size must be specified to solve for effect size")
                
                detectable_effect = await self._calculate_minimum_detectable_effect(
                    test_method, power, sample_size, alpha_level
                )
                
                result = PowerAnalysis(
                    analysis_id=analysis_id,
                    test_method=test_method,
                    effect_size=detectable_effect,
                    alpha=alpha_level,
                    power=power,
                    sample_size_per_group=sample_size,
                    total_sample_size=sample_size * 2,
                    minimum_detectable_effect=detectable_effect
                )
            else:
                raise ValueError(f"Invalid solve_for parameter: {solve_for}")
            
            # Generate power curve data
            result.power_curve_data = await self._generate_power_curve(
                test_method, alpha_level, result.sample_size_per_group
            )
            
            # Perform sensitivity analysis
            result.sensitivity_analysis = await self._perform_sensitivity_analysis(
                test_method, result.effect_size, alpha_level, result.power, result.sample_size_per_group
            )
            
            # Generate recommendations
            result.recommendations = await self._generate_power_analysis_recommendations(result)
            
            # Cache result
            self.power_analysis_cache[analysis_id] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Error performing power analysis: {e}")
            return PowerAnalysis(
                analysis_id=f"error_{datetime.utcnow().timestamp()}",
                test_method=test_method
            )

    async def calculate_effect_size(
        self,
        group_a_data: List[float],
        group_b_data: List[float],
        method: EffectSizeMethod = EffectSizeMethod.COHEN_D,
        confidence_level: float = 0.95
    ) -> EffectSize:
        """Calculate effect size with confidence interval."""
        try:
            # Clean data
            group_a_clean = [x for x in group_a_data if not (np.isnan(x) or np.isinf(x))]
            group_b_clean = [x for x in group_b_data if not (np.isnan(x) or np.isinf(x))]
            
            if not group_a_clean or not group_b_clean:
                raise ValueError("No valid data after cleaning")
            
            # Calculate effect size
            effect_size_result = await self._calculate_effect_size(group_a_clean, group_b_clean, method)
            
            # Calculate confidence interval using bootstrap
            ci_lower, ci_upper = await self._bootstrap_effect_size_ci(
                group_a_clean, group_b_clean, method, confidence_level
            )
            
            effect_size_result.confidence_interval = (ci_lower, ci_upper)
            
            # Determine interpretation
            effect_size_result.interpretation = self._interpret_effect_size(method, effect_size_result.value)
            
            # Determine practical significance
            effect_size_result.practical_significance = abs(effect_size_result.value) >= self.config['practical_significance_threshold']
            
            return effect_size_result
            
        except Exception as e:
            logger.error(f"Error calculating effect size: {e}")
            return EffectSize(method, 0.0, (0.0, 0.0), "error")

    async def perform_multiple_comparisons_correction(
        self,
        p_values: List[float],
        method: CorrectionMethod = CorrectionMethod.BENJAMINI_HOCHBERG,
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """Apply multiple comparisons correction to p-values."""
        try:
            p_array = np.array(p_values)
            n_comparisons = len(p_values)
            
            if method == CorrectionMethod.BONFERRONI:
                corrected_alpha = alpha / n_comparisons
                corrected_p_values = np.minimum(p_array * n_comparisons, 1.0)
                
            elif method == CorrectionMethod.HOLM:
                # Holm-Bonferroni method
                sorted_indices = np.argsort(p_array)
                corrected_p_values = np.zeros_like(p_array)
                
                for i, idx in enumerate(sorted_indices):
                    corrected_p_values[idx] = min(1.0, p_array[idx] * (n_comparisons - i))
                    
                # Ensure monotonicity
                sorted_corrected = corrected_p_values[sorted_indices]
                for i in range(1, len(sorted_corrected)):
                    if sorted_corrected[i] < sorted_corrected[i-1]:
                        sorted_corrected[i] = sorted_corrected[i-1]
                
                corrected_p_values[sorted_indices] = sorted_corrected
                corrected_alpha = alpha
                
            elif method == CorrectionMethod.SIDAK:
                corrected_alpha = 1 - (1 - alpha) ** (1/n_comparisons)
                corrected_p_values = 1 - (1 - p_array) ** n_comparisons
                
            elif method == CorrectionMethod.BENJAMINI_HOCHBERG:
                # Benjamini-Hochberg FDR control
                sorted_indices = np.argsort(p_array)
                corrected_p_values = np.zeros_like(p_array)
                
                for i, idx in enumerate(sorted_indices):
                    corrected_p_values[idx] = min(1.0, p_array[idx] * n_comparisons / (i + 1))
                
                # Ensure monotonicity (reverse)
                sorted_corrected = corrected_p_values[sorted_indices]
                for i in range(len(sorted_corrected) - 2, -1, -1):
                    if sorted_corrected[i] > sorted_corrected[i+1]:
                        sorted_corrected[i] = sorted_corrected[i+1]
                
                corrected_p_values[sorted_indices] = sorted_corrected
                corrected_alpha = alpha
                
            else:
                raise ValueError(f"Unknown correction method: {method}")
            
            # Determine significance
            is_significant = corrected_p_values < corrected_alpha
            
            result = {
                'method': method.value,
                'original_p_values': p_values,
                'corrected_p_values': corrected_p_values.tolist(),
                'corrected_alpha': corrected_alpha,
                'is_significant': is_significant.tolist(),
                'number_significant': int(np.sum(is_significant)),
                'family_wise_error_rate': alpha,
                'false_discovery_rate': alpha if method == CorrectionMethod.BENJAMINI_HOCHBERG else None
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying multiple comparisons correction: {e}")
            return {'error': str(e)}

    async def perform_sequential_testing(
        self,
        group_a_data: List[float],
        group_b_data: List[float],
        alpha: float = 0.05,
        beta: float = 0.2,
        effect_size: float = 0.5
    ) -> Dict[str, Any]:
        """Perform sequential probability ratio test for early stopping."""
        try:
            # Sequential testing boundaries (simplified SPRT)
            log_alpha = np.log(alpha)
            log_beta = np.log(beta)
            log_one_minus_beta = np.log(1 - beta)
            log_one_minus_alpha = np.log(1 - alpha)
            
            # Decision boundaries
            upper_boundary = log_one_minus_beta - log_alpha
            lower_boundary = log_beta - log_one_minus_alpha
            
            # Calculate current test statistic
            if len(group_a_data) < 10 or len(group_b_data) < 10:
                decision = "continue"
                reason = "Insufficient data for sequential testing"
            else:
                # Simplified: use t-test statistic
                statistic, p_value = stats.ttest_ind(group_b_data, group_a_data)
                log_likelihood_ratio = statistic  # Simplified approximation
                
                if log_likelihood_ratio >= upper_boundary:
                    decision = "stop_significant"
                    reason = "Significant effect detected"
                elif log_likelihood_ratio <= lower_boundary:
                    decision = "stop_not_significant"
                    reason = "Effect not significant, stop for futility"
                else:
                    decision = "continue"
                    reason = "Continue collecting data"
            
            result = {
                'decision': decision,
                'reason': reason,
                'current_sample_sizes': {
                    'group_a': len(group_a_data),
                    'group_b': len(group_b_data)
                },
                'boundaries': {
                    'upper': upper_boundary,
                    'lower': lower_boundary
                },
                'alpha_spending': alpha,
                'beta_spending': beta,
                'target_effect_size': effect_size
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in sequential testing: {e}")
            return {'decision': 'error', 'reason': str(e)}

    # Private helper methods
    
    def _get_test_assumptions(self, test_method: TestMethod) -> List[str]:
        """Get assumptions for a statistical test."""
        assumptions_map = {
            TestMethod.TTEST_INDEPENDENT: [
                "Normality of data in both groups",
                "Equal variances (homoscedasticity)",
                "Independence of observations"
            ],
            TestMethod.WELCH_TTEST: [
                "Normality of data in both groups",
                "Independence of observations"
            ],
            TestMethod.MANN_WHITNEY: [
                "Independence of observations",
                "Ordinal or continuous data"
            ],
            TestMethod.CHI_SQUARE: [
                "Independence of observations",
                "Expected frequency >= 5 in all cells"
            ],
            TestMethod.FISHER_EXACT: [
                "Independence of observations",
                "2x2 contingency table"
            ]
        }
        
        return assumptions_map.get(test_method, [])

    async def _check_test_assumptions(
        self,
        test_method: TestMethod,
        group_a: List[float],
        group_b: List[float]
    ) -> Dict[str, bool]:
        """Check statistical test assumptions."""
        try:
            assumptions = {}
            
            if test_method in [TestMethod.TTEST_INDEPENDENT, TestMethod.WELCH_TTEST, TestMethod.TTEST_PAIRED]:
                # Test normality using Shapiro-Wilk test
                if len(group_a) >= 3 and len(group_a) <= 5000:
                    _, p_a = stats.shapiro(group_a)
                    assumptions['normality_group_a'] = p_a > 0.05
                
                if len(group_b) >= 3 and len(group_b) <= 5000:
                    _, p_b = stats.shapiro(group_b)
                    assumptions['normality_group_b'] = p_b > 0.05
                
                assumptions['normality'] = assumptions.get('normality_group_a', True) and assumptions.get('normality_group_b', True)
                
                # Test equal variances using Levene's test
                if test_method == TestMethod.TTEST_INDEPENDENT:
                    _, p_levene = stats.levene(group_a, group_b)
                    assumptions['equal_variances'] = p_levene > 0.05
            
            # Check sample sizes
            assumptions['adequate_sample_size'] = len(group_a) >= 30 and len(group_b) >= 30
            
            return assumptions
            
        except Exception as e:
            logger.error(f"Error checking assumptions: {e}")
            return {}

    async def _execute_statistical_test(
        self,
        method: TestMethod,
        group_a: List[float],
        group_b: List[float],
        alpha: float,
        alternative: str
    ) -> Dict[str, Any]:
        """Execute the specified statistical test."""
        try:
            if method == TestMethod.TTEST_INDEPENDENT:
                statistic, p_value = stats.ttest_ind(group_b, group_a, equal_var=True)
                df = len(group_a) + len(group_b) - 2
                
                # Calculate confidence interval for difference in means
                pooled_std = np.sqrt(((len(group_a) - 1) * np.var(group_a, ddof=1) + 
                                    (len(group_b) - 1) * np.var(group_b, ddof=1)) / df)
                se_diff = pooled_std * np.sqrt(1/len(group_a) + 1/len(group_b))
                t_crit = stats.t.ppf(1 - alpha/2, df)
                mean_diff = np.mean(group_b) - np.mean(group_a)
                
                ci_lower = mean_diff - t_crit * se_diff
                ci_upper = mean_diff + t_crit * se_diff
                
                return {
                    'statistic': statistic,
                    'p_value': p_value,
                    'degrees_of_freedom': df,
                    'confidence_interval': (ci_lower, ci_upper)
                }
                
            elif method == TestMethod.WELCH_TTEST:
                statistic, p_value = stats.ttest_ind(group_b, group_a, equal_var=False)
                
                # Welch's degrees of freedom
                var_a = np.var(group_a, ddof=1)
                var_b = np.var(group_b, ddof=1)
                n_a, n_b = len(group_a), len(group_b)
                
                df = (var_a/n_a + var_b/n_b)**2 / ((var_a/n_a)**2/(n_a-1) + (var_b/n_b)**2/(n_b-1))
                
                return {
                    'statistic': statistic,
                    'p_value': p_value,
                    'degrees_of_freedom': df,
                    'confidence_interval': (0.0, 0.0)  # Placeholder
                }
                
            elif method == TestMethod.MANN_WHITNEY:
                statistic, p_value = stats.mannwhitneyu(
                    group_b, group_a, alternative=alternative
                )
                
                return {
                    'statistic': statistic,
                    'p_value': p_value
                }
                
            elif method == TestMethod.WILCOXON_SIGNED_RANK:
                # For paired data
                if len(group_a) != len(group_b):
                    raise ValueError("Wilcoxon signed-rank test requires paired data")
                
                differences = np.array(group_b) - np.array(group_a)
                statistic, p_value = stats.wilcoxon(differences, alternative=alternative)
                
                return {
                    'statistic': statistic,
                    'p_value': p_value
                }
                
            elif method == TestMethod.KOLMOGOROV_SMIRNOV:
                statistic, p_value = stats.ks_2samp(group_a, group_b)
                
                return {
                    'statistic': statistic,
                    'p_value': p_value
                }
                
            elif method == TestMethod.BOOTSTRAP:
                return await self._bootstrap_test(group_a, group_b, alpha)
                
            elif method == TestMethod.PERMUTATION:
                return await self._permutation_test(group_a, group_b, alpha)
            
            else:
                raise ValueError(f"Test method {method} not implemented")
                
        except Exception as e:
            logger.error(f"Error executing test {method}: {e}")
            return {'statistic': 0.0, 'p_value': 1.0}

    async def _calculate_effect_size(
        self,
        group_a: List[float],
        group_b: List[float],
        method: EffectSizeMethod
    ) -> EffectSize:
        """Calculate effect size between two groups."""
        try:
            mean_a = np.mean(group_a)
            mean_b = np.mean(group_b)
            
            if method == EffectSizeMethod.COHEN_D:
                # Cohen's d
                var_a = np.var(group_a, ddof=1)
                var_b = np.var(group_b, ddof=1)
                n_a, n_b = len(group_a), len(group_b)
                
                pooled_std = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
                
                if pooled_std == 0:
                    effect_size = 0.0
                else:
                    effect_size = (mean_b - mean_a) / pooled_std
                    
            elif method == EffectSizeMethod.HEDGES_G:
                # Hedges' g (bias-corrected Cohen's d)
                var_a = np.var(group_a, ddof=1)
                var_b = np.var(group_b, ddof=1)
                n_a, n_b = len(group_a), len(group_b)
                
                pooled_std = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
                
                if pooled_std == 0:
                    effect_size = 0.0
                else:
                    cohens_d = (mean_b - mean_a) / pooled_std
                    # Bias correction factor
                    j = 1 - (3 / (4 * (n_a + n_b - 2) - 1))
                    effect_size = cohens_d * j
                    
            elif method == EffectSizeMethod.GLASS_DELTA:
                # Glass's Δ (uses control group standard deviation)
                std_a = np.std(group_a, ddof=1)
                
                if std_a == 0:
                    effect_size = 0.0
                else:
                    effect_size = (mean_b - mean_a) / std_a
                    
            elif method == EffectSizeMethod.CLIFF_DELTA:
                # Cliff's delta (non-parametric effect size)
                n_a, n_b = len(group_a), len(group_b)
                dominance_count = 0
                
                for a_val in group_a:
                    for b_val in group_b:
                        if b_val > a_val:
                            dominance_count += 1
                        elif a_val > b_val:
                            dominance_count -= 1
                
                effect_size = dominance_count / (n_a * n_b)
                
            else:
                raise ValueError(f"Effect size method {method} not implemented")
            
            return EffectSize(
                effect_size_method=method,
                value=effect_size,
                interpretation=self._interpret_effect_size(method, effect_size)
            )
            
        except Exception as e:
            logger.error(f"Error calculating effect size: {e}")
            return EffectSize(method, 0.0, (0.0, 0.0), "error")

    def _interpret_effect_size(self, method: EffectSizeMethod, value: float) -> str:
        """Interpret effect size magnitude."""
        try:
            abs_value = abs(value)
            thresholds = self.effect_size_interpretations.get(method, {
                'small': 0.2, 'medium': 0.5, 'large': 0.8
            })
            
            if abs_value < thresholds['small']:
                return "negligible"
            elif abs_value < thresholds['medium']:
                return "small"
            elif abs_value < thresholds['large']:
                return "medium"
            else:
                return "large"
                
        except Exception:
            return "unknown"

    async def _calculate_sample_size(
        self,
        test_method: TestMethod,
        effect_size: float,
        alpha: float,
        power: float
    ) -> int:
        """Calculate required sample size per group."""
        try:
            if test_method in [TestMethod.TTEST_INDEPENDENT, TestMethod.WELCH_TTEST]:
                # Use power analysis for t-test
                sample_size = ttest_power(effect_size, power, alpha, alternative='two-sided')
                return max(30, int(np.ceil(sample_size)))
            else:
                # Generic approximation
                z_alpha = stats.norm.ppf(1 - alpha/2)
                z_beta = stats.norm.ppf(power)
                
                # Simplified calculation
                sample_size = 2 * ((z_alpha + z_beta) / effect_size) ** 2
                return max(30, int(np.ceil(sample_size)))
                
        except Exception as e:
            logger.error(f"Error calculating sample size: {e}")
            return 100

    async def _calculate_power(
        self,
        test_method: TestMethod,
        effect_size: float,
        sample_size: int,
        alpha: float
    ) -> float:
        """Calculate statistical power."""
        try:
            if test_method in [TestMethod.TTEST_INDEPENDENT, TestMethod.WELCH_TTEST]:
                power = ttest_power(effect_size, sample_size, alpha, alternative='two-sided')
                return min(1.0, max(0.0, power))
            else:
                # Generic approximation
                z_alpha = stats.norm.ppf(1 - alpha/2)
                z_effect = effect_size * np.sqrt(sample_size / 2)
                power = 1 - stats.norm.cdf(z_alpha - z_effect)
                return min(1.0, max(0.0, power))
                
        except Exception as e:
            logger.error(f"Error calculating power: {e}")
            return 0.5

    async def _calculate_achieved_power(
        self,
        test_method: TestMethod,
        effect_size: float,
        n_a: int,
        n_b: int,
        alpha: float
    ) -> float:
        """Calculate achieved statistical power."""
        try:
            # Use harmonic mean of sample sizes
            effective_n = 2 * n_a * n_b / (n_a + n_b)
            return await self._calculate_power(test_method, effect_size, int(effective_n), alpha)
        except Exception as e:
            logger.error(f"Error calculating achieved power: {e}")
            return 0.0

    async def _calculate_minimum_detectable_effect(
        self,
        test_method: TestMethod,
        power: float,
        sample_size: int,
        alpha: float
    ) -> float:
        """Calculate minimum detectable effect size."""
        try:
            z_alpha = stats.norm.ppf(1 - alpha/2)
            z_beta = stats.norm.ppf(power)
            
            # Simplified calculation
            mde = (z_alpha + z_beta) / np.sqrt(sample_size / 2)
            return mde
            
        except Exception as e:
            logger.error(f"Error calculating minimum detectable effect: {e}")
            return 0.5

    async def _bootstrap_test(
        self,
        group_a: List[float],
        group_b: List[float],
        alpha: float
    ) -> Dict[str, Any]:
        """Perform bootstrap hypothesis test."""
        try:
            n_bootstrap = self.config['bootstrap_iterations']
            observed_diff = np.mean(group_b) - np.mean(group_a)
            
            # Pool data for null hypothesis
            pooled_data = group_a + group_b
            n_a, n_b = len(group_a), len(group_b)
            
            # Bootstrap under null hypothesis
            bootstrap_diffs = []
            for _ in range(n_bootstrap):
                # Resample without replacement
                resampled = np.random.choice(pooled_data, size=n_a + n_b, replace=False)
                boot_a = resampled[:n_a]
                boot_b = resampled[n_a:]
                
                bootstrap_diffs.append(np.mean(boot_b) - np.mean(boot_a))
            
            # Calculate p-value
            bootstrap_diffs = np.array(bootstrap_diffs)
            p_value = np.mean(np.abs(bootstrap_diffs) >= abs(observed_diff))
            
            return {
                'statistic': observed_diff,
                'p_value': p_value,
                'bootstrap_iterations': n_bootstrap
            }
            
        except Exception as e:
            logger.error(f"Error in bootstrap test: {e}")
            return {'statistic': 0.0, 'p_value': 1.0}

    async def _permutation_test(
        self,
        group_a: List[float],
        group_b: List[float],
        alpha: float
    ) -> Dict[str, Any]:
        """Perform permutation test."""
        try:
            n_permutations = self.config['permutation_iterations']
            observed_diff = np.mean(group_b) - np.mean(group_a)
            
            # Combined data
            combined_data = np.array(group_a + group_b)
            n_a = len(group_a)
            
            # Permutation test
            permutation_diffs = []
            for _ in range(n_permutations):
                # Random permutation
                permuted_indices = np.random.permutation(len(combined_data))
                perm_a = combined_data[permuted_indices[:n_a]]
                perm_b = combined_data[permuted_indices[n_a:]]
                
                permutation_diffs.append(np.mean(perm_b) - np.mean(perm_a))
            
            # Calculate p-value
            permutation_diffs = np.array(permutation_diffs)
            p_value = np.mean(np.abs(permutation_diffs) >= abs(observed_diff))
            
            return {
                'statistic': observed_diff,
                'p_value': p_value,
                'permutation_iterations': n_permutations
            }
            
        except Exception as e:
            logger.error(f"Error in permutation test: {e}")
            return {'statistic': 0.0, 'p_value': 1.0}

    async def _bootstrap_effect_size_ci(
        self,
        group_a: List[float],
        group_b: List[float],
        method: EffectSizeMethod,
        confidence_level: float
    ) -> Tuple[float, float]:
        """Calculate confidence interval for effect size using bootstrap."""
        try:
            n_bootstrap = min(5000, self.config['bootstrap_iterations'])
            bootstrap_effects = []
            
            for _ in range(n_bootstrap):
                # Bootstrap samples
                boot_a = np.random.choice(group_a, size=len(group_a), replace=True)
                boot_b = np.random.choice(group_b, size=len(group_b), replace=True)
                
                # Calculate effect size
                effect = await self._calculate_effect_size(boot_a.tolist(), boot_b.tolist(), method)
                bootstrap_effects.append(effect.value)
            
            # Calculate confidence interval
            alpha = 1 - confidence_level
            lower_percentile = (alpha / 2) * 100
            upper_percentile = (1 - alpha / 2) * 100
            
            ci_lower = np.percentile(bootstrap_effects, lower_percentile)
            ci_upper = np.percentile(bootstrap_effects, upper_percentile)
            
            return (ci_lower, ci_upper)
            
        except Exception as e:
            logger.error(f"Error calculating bootstrap CI: {e}")
            return (0.0, 0.0)

    async def _generate_interpretation(self, result: TestResult) -> str:
        """Generate interpretation of statistical test results."""
        try:
            interpretation_parts = []
            
            # Statistical significance
            if result.is_significant:
                interpretation_parts.append(
                    f"The test result is statistically significant (p = {result.p_value:.4f} < α = {self.config['default_alpha']})"
                )
            else:
                interpretation_parts.append(
                    f"The test result is not statistically significant (p = {result.p_value:.4f} ≥ α = {self.config['default_alpha']})"
                )
            
            # Effect size interpretation
            effect_magnitude = self._interpret_effect_size(result.effect_size_method, result.effect_size)
            interpretation_parts.append(
                f"The effect size is {effect_magnitude} ({result.effect_size_method.value} = {result.effect_size:.3f})"
            )
            
            # Practical significance
            if result.practical_significance:
                interpretation_parts.append("The effect is practically significant")
            else:
                interpretation_parts.append("The effect may not be practically significant")
            
            # Power assessment
            if result.power_achieved < 0.8:
                interpretation_parts.append(
                    f"Statistical power is low ({result.power_achieved:.2f}), results should be interpreted cautiously"
                )
            
            return ". ".join(interpretation_parts) + "."
            
        except Exception as e:
            logger.error(f"Error generating interpretation: {e}")
            return "Unable to generate interpretation"

    async def _generate_recommendations(
        self,
        result: TestResult,
        assumptions_met: Dict[str, bool]
    ) -> List[str]:
        """Generate recommendations based on test results."""
        try:
            recommendations = []
            
            # Sample size recommendations
            total_n = sum(result.sample_sizes.values())
            if total_n < 60:
                recommendations.append("Consider collecting more data for more reliable results")
            
            # Power recommendations
            if result.power_achieved < 0.8:
                recommendations.append("Increase sample size to achieve adequate statistical power (≥0.8)")
            
            # Assumption violations
            if assumptions_met.get('normality', True) == False:
                recommendations.append("Consider using non-parametric tests due to normality violations")
            
            if assumptions_met.get('equal_variances', True) == False:
                recommendations.append("Consider using Welch's t-test due to unequal variances")
            
            # Effect size recommendations
            if abs(result.effect_size) < 0.2:
                recommendations.append("Effect size is small; ensure practical significance before implementation")
            
            # Multiple testing
            if len(recommendations) == 0:
                recommendations.append("Results appear robust; consider replication in independent samples")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Review results carefully due to analysis error"]

    # Additional methods for power curve generation, sensitivity analysis, etc. would be implemented here...