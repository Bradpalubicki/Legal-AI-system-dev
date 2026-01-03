"""
Traffic Splitting and User Assignment for A/B Testing

Handles traffic allocation, user assignment to experiment variants,
and traffic split strategies for A/B testing experiments.
"""

import hashlib
import random
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict
import asyncio
import json

class SplitMethod(str, Enum):
    """Traffic split methods"""
    RANDOM = "random"
    HASH_BASED = "hash_based"
    WEIGHTED = "weighted"
    GEOGRAPHIC = "geographic"
    DEMOGRAPHIC = "demographic"
    BEHAVIORAL = "behavioral"
    TIME_BASED = "time_based"
    STICKY = "sticky"

@dataclass
class TrafficAllocation:
    """Traffic allocation configuration"""
    variant_id: str
    percentage: float
    conditions: Optional[Dict[str, Any]] = None
    priority: int = 0
    
    def __post_init__(self):
        if self.percentage < 0 or self.percentage > 100:
            raise ValueError("Percentage must be between 0 and 100")

@dataclass
class UserAssignment:
    """User assignment to experiment variant"""
    user_id: str
    experiment_id: str
    variant_id: str
    assignment_time: datetime
    assignment_method: SplitMethod
    assignment_hash: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    is_sticky: bool = True

@dataclass
class SplitRule:
    """Traffic split rule configuration"""
    rule_id: str
    name: str
    condition: Dict[str, Any]
    allocation: Dict[str, float]
    priority: int = 0
    is_active: bool = True

class TrafficSplitter:
    """
    Advanced traffic splitting system for A/B testing experiments.
    
    Provides multiple split strategies including random, hash-based,
    weighted, and condition-based traffic allocation.
    """
    
    def __init__(self):
        self.assignments: Dict[str, UserAssignment] = {}
        self.split_rules: Dict[str, List[SplitRule]] = defaultdict(list)
        self.allocation_cache: Dict[str, Dict[str, TrafficAllocation]] = {}
        
    async def assign_user_to_variant(
        self,
        user_id: str,
        experiment_id: str,
        variants: List[Dict[str, Any]],
        split_method: SplitMethod = SplitMethod.HASH_BASED,
        user_context: Optional[Dict[str, Any]] = None,
        force_variant: Optional[str] = None
    ) -> UserAssignment:
        """
        Assign a user to an experiment variant.
        
        Args:
            user_id: Unique user identifier
            experiment_id: Experiment identifier
            variants: List of available variants with allocation percentages
            split_method: Method to use for traffic splitting
            user_context: Additional user context for conditional splits
            force_variant: Force assignment to specific variant (for testing)
            
        Returns:
            UserAssignment object with assignment details
        """
        assignment_key = f"{user_id}:{experiment_id}"
        
        # Check for existing sticky assignment
        if assignment_key in self.assignments:
            existing = self.assignments[assignment_key]
            if existing.is_sticky:
                return existing
        
        # Force assignment if specified
        if force_variant:
            variant = next((v for v in variants if v['id'] == force_variant), None)
            if not variant:
                raise ValueError(f"Variant {force_variant} not found in experiment")
            
            assignment = UserAssignment(
                user_id=user_id,
                experiment_id=experiment_id,
                variant_id=force_variant,
                assignment_time=datetime.utcnow(),
                assignment_method=split_method,
                context=user_context
            )
            self.assignments[assignment_key] = assignment
            return assignment
        
        # Apply split rules first
        rule_variant = await self._apply_split_rules(
            user_id, experiment_id, variants, user_context
        )
        if rule_variant:
            assignment = UserAssignment(
                user_id=user_id,
                experiment_id=experiment_id,
                variant_id=rule_variant,
                assignment_time=datetime.utcnow(),
                assignment_method=split_method,
                context=user_context
            )
            self.assignments[assignment_key] = assignment
            return assignment
        
        # Standard traffic splitting
        variant_id = await self._split_traffic(
            user_id, experiment_id, variants, split_method, user_context
        )
        
        assignment_hash = None
        if split_method == SplitMethod.HASH_BASED:
            assignment_hash = self._generate_assignment_hash(user_id, experiment_id)
        
        assignment = UserAssignment(
            user_id=user_id,
            experiment_id=experiment_id,
            variant_id=variant_id,
            assignment_time=datetime.utcnow(),
            assignment_method=split_method,
            assignment_hash=assignment_hash,
            context=user_context
        )
        
        self.assignments[assignment_key] = assignment
        return assignment
    
    async def _split_traffic(
        self,
        user_id: str,
        experiment_id: str,
        variants: List[Dict[str, Any]],
        split_method: SplitMethod,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Split traffic based on the specified method."""
        
        if split_method == SplitMethod.RANDOM:
            return self._random_split(variants)
        
        elif split_method == SplitMethod.HASH_BASED:
            return self._hash_based_split(user_id, experiment_id, variants)
        
        elif split_method == SplitMethod.WEIGHTED:
            return self._weighted_split(variants, user_context)
        
        elif split_method == SplitMethod.GEOGRAPHIC:
            return self._geographic_split(variants, user_context)
        
        elif split_method == SplitMethod.DEMOGRAPHIC:
            return self._demographic_split(variants, user_context)
        
        elif split_method == SplitMethod.BEHAVIORAL:
            return self._behavioral_split(variants, user_context)
        
        elif split_method == SplitMethod.TIME_BASED:
            return self._time_based_split(variants)
        
        else:
            # Default to hash-based
            return self._hash_based_split(user_id, experiment_id, variants)
    
    def _random_split(self, variants: List[Dict[str, Any]]) -> str:
        """Randomly assign user to variant based on allocation percentages."""
        total_weight = sum(v.get('allocation', 0) for v in variants)
        if total_weight == 0:
            return random.choice(variants)['id']
        
        rand = random.uniform(0, total_weight)
        cumulative = 0
        
        for variant in variants:
            cumulative += variant.get('allocation', 0)
            if rand <= cumulative:
                return variant['id']
        
        return variants[-1]['id']
    
    def _hash_based_split(
        self, 
        user_id: str, 
        experiment_id: str, 
        variants: List[Dict[str, Any]]
    ) -> str:
        """Hash-based consistent assignment."""
        hash_input = f"{user_id}:{experiment_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        hash_bucket = hash_value % 10000  # 0-9999 for fine-grained percentages
        
        cumulative = 0
        for variant in sorted(variants, key=lambda x: x['id']):
            allocation = variant.get('allocation', 0)
            cumulative += allocation * 100  # Convert to basis points
            if hash_bucket < cumulative:
                return variant['id']
        
        return variants[0]['id']
    
    def _weighted_split(
        self, 
        variants: List[Dict[str, Any]], 
        user_context: Optional[Dict[str, Any]]
    ) -> str:
        """Weighted assignment based on user attributes."""
        if not user_context:
            return self._random_split(variants)
        
        # Calculate weights based on user context
        weighted_variants = []
        for variant in variants:
            weight = variant.get('allocation', 50)
            
            # Adjust weight based on user context
            if 'weight_factors' in variant:
                for factor, multiplier in variant['weight_factors'].items():
                    if factor in user_context:
                        weight *= multiplier
            
            weighted_variants.append({
                'id': variant['id'],
                'allocation': weight
            })
        
        return self._random_split(weighted_variants)
    
    def _geographic_split(
        self, 
        variants: List[Dict[str, Any]], 
        user_context: Optional[Dict[str, Any]]
    ) -> str:
        """Geographic-based assignment."""
        if not user_context or 'location' not in user_context:
            return self._random_split(variants)
        
        location = user_context['location']
        
        # Check for geographic targeting in variants
        for variant in variants:
            if 'geographic_targeting' in variant:
                targeting = variant['geographic_targeting']
                if self._matches_geographic_criteria(location, targeting):
                    return variant['id']
        
        return self._random_split(variants)
    
    def _demographic_split(
        self, 
        variants: List[Dict[str, Any]], 
        user_context: Optional[Dict[str, Any]]
    ) -> str:
        """Demographic-based assignment."""
        if not user_context:
            return self._random_split(variants)
        
        # Check demographic targeting
        for variant in variants:
            if 'demographic_targeting' in variant:
                targeting = variant['demographic_targeting']
                if self._matches_demographic_criteria(user_context, targeting):
                    return variant['id']
        
        return self._random_split(variants)
    
    def _behavioral_split(
        self, 
        variants: List[Dict[str, Any]], 
        user_context: Optional[Dict[str, Any]]
    ) -> str:
        """Behavioral-based assignment."""
        if not user_context or 'behavior' not in user_context:
            return self._random_split(variants)
        
        behavior = user_context['behavior']
        
        # Score variants based on behavioral targeting
        variant_scores = []
        for variant in variants:
            score = variant.get('allocation', 50)
            
            if 'behavioral_targeting' in variant:
                targeting = variant['behavioral_targeting']
                behavioral_score = self._calculate_behavioral_score(behavior, targeting)
                score *= behavioral_score
            
            variant_scores.append({
                'id': variant['id'],
                'allocation': score
            })
        
        return self._random_split(variant_scores)
    
    def _time_based_split(self, variants: List[Dict[str, Any]]) -> str:
        """Time-based assignment (e.g., different variants at different times)."""
        current_hour = datetime.utcnow().hour
        
        # Check for time-based targeting
        for variant in variants:
            if 'time_targeting' in variant:
                targeting = variant['time_targeting']
                if self._matches_time_criteria(current_hour, targeting):
                    return variant['id']
        
        return self._random_split(variants)
    
    async def _apply_split_rules(
        self,
        user_id: str,
        experiment_id: str,
        variants: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Apply custom split rules."""
        rules = self.split_rules.get(experiment_id, [])
        if not rules:
            return None
        
        # Sort rules by priority (higher first)
        sorted_rules = sorted(rules, key=lambda x: x.priority, reverse=True)
        
        for rule in sorted_rules:
            if not rule.is_active:
                continue
            
            if self._evaluate_rule_condition(rule.condition, user_context):
                # Apply rule allocation
                variant_allocations = []
                for variant_id, allocation in rule.allocation.items():
                    if any(v['id'] == variant_id for v in variants):
                        variant_allocations.append({
                            'id': variant_id,
                            'allocation': allocation
                        })
                
                if variant_allocations:
                    return self._random_split(variant_allocations)
        
        return None
    
    def _generate_assignment_hash(self, user_id: str, experiment_id: str) -> str:
        """Generate a hash for the assignment."""
        hash_input = f"{user_id}:{experiment_id}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def _matches_geographic_criteria(
        self, 
        location: Dict[str, Any], 
        targeting: Dict[str, Any]
    ) -> bool:
        """Check if location matches geographic targeting criteria."""
        if 'countries' in targeting:
            if location.get('country') not in targeting['countries']:
                return False
        
        if 'regions' in targeting:
            if location.get('region') not in targeting['regions']:
                return False
        
        if 'cities' in targeting:
            if location.get('city') not in targeting['cities']:
                return False
        
        return True
    
    def _matches_demographic_criteria(
        self, 
        user_context: Dict[str, Any], 
        targeting: Dict[str, Any]
    ) -> bool:
        """Check if user matches demographic targeting criteria."""
        for criterion, values in targeting.items():
            if criterion in user_context:
                if isinstance(values, list):
                    if user_context[criterion] not in values:
                        return False
                elif isinstance(values, dict):
                    # Range matching (e.g., age ranges)
                    user_value = user_context[criterion]
                    if 'min' in values and user_value < values['min']:
                        return False
                    if 'max' in values and user_value > values['max']:
                        return False
                else:
                    if user_context[criterion] != values:
                        return False
        
        return True
    
    def _calculate_behavioral_score(
        self, 
        behavior: Dict[str, Any], 
        targeting: Dict[str, Any]
    ) -> float:
        """Calculate behavioral targeting score."""
        score = 1.0
        
        for behavior_type, criteria in targeting.items():
            if behavior_type in behavior:
                user_behavior = behavior[behavior_type]
                
                if isinstance(criteria, dict) and 'weight' in criteria:
                    weight = criteria['weight']
                    if 'threshold' in criteria:
                        threshold = criteria['threshold']
                        if user_behavior >= threshold:
                            score *= weight
                    else:
                        # Linear scaling
                        score *= weight * (user_behavior / 100)
        
        return max(0.1, min(10.0, score))  # Clamp score between 0.1 and 10
    
    def _matches_time_criteria(
        self, 
        current_hour: int, 
        targeting: Dict[str, Any]
    ) -> bool:
        """Check if current time matches time targeting criteria."""
        if 'hours' in targeting:
            if current_hour not in targeting['hours']:
                return False
        
        if 'hour_ranges' in targeting:
            for hour_range in targeting['hour_ranges']:
                start, end = hour_range['start'], hour_range['end']
                if start <= current_hour <= end:
                    return True
            return False
        
        return True
    
    def _evaluate_rule_condition(
        self, 
        condition: Dict[str, Any], 
        user_context: Optional[Dict[str, Any]]
    ) -> bool:
        """Evaluate if a rule condition is met."""
        if not user_context:
            return False
        
        # Simple condition evaluation
        for key, expected_value in condition.items():
            if key not in user_context:
                return False
            
            user_value = user_context[key]
            
            if isinstance(expected_value, dict):
                # Range or complex condition
                if 'operator' in expected_value:
                    operator = expected_value['operator']
                    value = expected_value['value']
                    
                    if operator == 'eq' and user_value != value:
                        return False
                    elif operator == 'gt' and user_value <= value:
                        return False
                    elif operator == 'lt' and user_value >= value:
                        return False
                    elif operator == 'gte' and user_value < value:
                        return False
                    elif operator == 'lte' and user_value > value:
                        return False
                    elif operator == 'in' and user_value not in value:
                        return False
            elif user_value != expected_value:
                return False
        
        return True
    
    async def get_user_assignment(
        self, 
        user_id: str, 
        experiment_id: str
    ) -> Optional[UserAssignment]:
        """Get existing user assignment for an experiment."""
        assignment_key = f"{user_id}:{experiment_id}"
        return self.assignments.get(assignment_key)
    
    async def update_assignment_context(
        self,
        user_id: str,
        experiment_id: str,
        context: Dict[str, Any]
    ) -> bool:
        """Update the context of an existing assignment."""
        assignment_key = f"{user_id}:{experiment_id}"
        if assignment_key in self.assignments:
            assignment = self.assignments[assignment_key]
            if assignment.context:
                assignment.context.update(context)
            else:
                assignment.context = context
            return True
        return False
    
    async def add_split_rule(
        self,
        experiment_id: str,
        rule: SplitRule
    ) -> bool:
        """Add a custom split rule for an experiment."""
        self.split_rules[experiment_id].append(rule)
        # Sort by priority
        self.split_rules[experiment_id].sort(key=lambda x: x.priority, reverse=True)
        return True
    
    async def remove_split_rule(
        self,
        experiment_id: str,
        rule_id: str
    ) -> bool:
        """Remove a split rule."""
        rules = self.split_rules.get(experiment_id, [])
        original_count = len(rules)
        self.split_rules[experiment_id] = [r for r in rules if r.rule_id != rule_id]
        return len(self.split_rules[experiment_id]) < original_count
    
    async def get_assignment_statistics(
        self,
        experiment_id: str
    ) -> Dict[str, Any]:
        """Get assignment statistics for an experiment."""
        assignments = [
            a for a in self.assignments.values() 
            if a.experiment_id == experiment_id
        ]
        
        if not assignments:
            return {
                'total_assignments': 0,
                'variant_distribution': {},
                'assignment_methods': {}
            }
        
        # Variant distribution
        variant_counts = defaultdict(int)
        method_counts = defaultdict(int)
        
        for assignment in assignments:
            variant_counts[assignment.variant_id] += 1
            method_counts[assignment.assignment_method.value] += 1
        
        total = len(assignments)
        variant_distribution = {
            variant: {'count': count, 'percentage': (count / total) * 100}
            for variant, count in variant_counts.items()
        }
        
        assignment_methods = {
            method: {'count': count, 'percentage': (count / total) * 100}
            for method, count in method_counts.items()
        }
        
        return {
            'total_assignments': total,
            'variant_distribution': variant_distribution,
            'assignment_methods': assignment_methods,
            'assignments_over_time': self._get_assignments_over_time(assignments)
        }
    
    def _get_assignments_over_time(
        self,
        assignments: List[UserAssignment]
    ) -> List[Dict[str, Any]]:
        """Get assignment counts over time."""
        # Group by date
        daily_counts = defaultdict(int)
        for assignment in assignments:
            date_key = assignment.assignment_time.date().isoformat()
            daily_counts[date_key] += 1
        
        return [
            {'date': date, 'count': count}
            for date, count in sorted(daily_counts.items())
        ]