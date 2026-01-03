"""
Resource Optimizer Module

Advanced resource allocation and optimization system for legal practices,
managing attorney workloads, staff assignments, and capacity planning.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import logging
import numpy as np
import pandas as pd
from collections import defaultdict
import asyncio
import json
from scipy.optimize import linprog
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    ATTORNEY = "attorney"
    PARALEGAL = "paralegal"
    LEGAL_ASSISTANT = "legal_assistant"
    COURT_REPORTER = "court_reporter"
    INVESTIGATOR = "investigator"
    EXPERT_WITNESS = "expert_witness"
    CONSULTANT = "consultant"
    CONFERENCE_ROOM = "conference_room"
    EQUIPMENT = "equipment"
    SOFTWARE_LICENSE = "software_license"

class OptimizationType(Enum):
    WORKLOAD_BALANCING = "workload_balancing"
    SKILL_MATCHING = "skill_matching"
    COST_MINIMIZATION = "cost_minimization"
    UTILIZATION_MAXIMIZATION = "utilization_maximization"
    DEADLINE_OPTIMIZATION = "deadline_optimization"
    CAPACITY_PLANNING = "capacity_planning"

@dataclass
class ResourceAllocation:
    id: Optional[int] = None
    resource_type: ResourceType = ResourceType.ATTORNEY
    resource_id: int = 0
    resource_name: str = ""
    case_id: Optional[int] = None
    task_id: Optional[str] = None
    allocated_hours: float = 0.0
    allocation_start: datetime = field(default_factory=datetime.utcnow)
    allocation_end: Optional[datetime] = None
    hourly_rate: Optional[float] = None
    skill_requirements: List[str] = field(default_factory=list)
    skill_match_score: float = 0.0
    utilization_rate: float = 0.0
    efficiency_score: float = 0.0
    priority_level: int = 1  # 1-5 scale
    status: str = "planned"  # planned, active, completed, cancelled
    cost_estimate: Optional[float] = None
    actual_cost: Optional[float] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class OptimizationSuggestion:
    id: Optional[int] = None
    optimization_type: OptimizationType = OptimizationType.WORKLOAD_BALANCING
    resource_type: ResourceType = ResourceType.ATTORNEY
    current_allocation: Optional[ResourceAllocation] = None
    suggested_allocation: Optional[ResourceAllocation] = None
    expected_improvement: Dict[str, float] = field(default_factory=dict)
    confidence_score: float = 0.0
    cost_impact: float = 0.0
    time_impact: float = 0.0  # Hours saved/lost
    quality_impact: float = 0.0
    risk_level: str = "low"  # low, medium, high
    implementation_effort: str = "easy"  # easy, moderate, difficult
    justification: str = ""
    prerequisites: List[str] = field(default_factory=list)
    affected_cases: List[int] = field(default_factory=list)
    affected_resources: List[int] = field(default_factory=list)
    timeline: str = ""
    priority: int = 1  # 1-5 scale
    status: str = "pending"  # pending, approved, implemented, rejected
    feedback: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

class ResourceOptimizer:
    def __init__(self):
        self.resource_capacity: Dict[int, Dict[str, float]] = {}  # resource_id -> capacity metrics
        self.skill_matrix: Dict[int, Dict[str, float]] = {}  # resource_id -> skill_name -> proficiency
        self.historical_performance: Dict[int, Dict[str, float]] = {}  # resource_id -> metrics
        self.optimization_cache: Dict[str, List[OptimizationSuggestion]] = {}
        self.constraint_rules = {
            'max_daily_hours': 8,
            'max_weekly_hours': 40,
            'min_utilization_rate': 0.75,
            'max_utilization_rate': 0.95,
            'max_concurrent_cases': 15,
            'skill_match_threshold': 0.6,
            'cost_variance_threshold': 0.15
        }

    async def optimize_resource_allocation(
        self,
        optimization_type: OptimizationType,
        case_ids: Optional[List[int]] = None,
        resource_types: Optional[List[ResourceType]] = None,
        time_horizon_days: int = 30,
        db: Optional[AsyncSession] = None
    ) -> List[OptimizationSuggestion]:
        """Perform comprehensive resource allocation optimization."""
        try:
            # Get current allocations and requirements
            current_allocations = await self._get_current_allocations(case_ids, resource_types, db)
            resource_requirements = await self._analyze_resource_requirements(case_ids, time_horizon_days, db)
            available_resources = await self._get_available_resources(resource_types, time_horizon_days, db)
            
            suggestions = []
            
            if optimization_type == OptimizationType.WORKLOAD_BALANCING:
                suggestions.extend(
                    await self._optimize_workload_balancing(current_allocations, available_resources)
                )
            
            elif optimization_type == OptimizationType.SKILL_MATCHING:
                suggestions.extend(
                    await self._optimize_skill_matching(resource_requirements, available_resources)
                )
            
            elif optimization_type == OptimizationType.COST_MINIMIZATION:
                suggestions.extend(
                    await self._optimize_cost_minimization(current_allocations, available_resources)
                )
            
            elif optimization_type == OptimizationType.UTILIZATION_MAXIMIZATION:
                suggestions.extend(
                    await self._optimize_utilization(current_allocations, available_resources)
                )
            
            elif optimization_type == OptimizationType.DEADLINE_OPTIMIZATION:
                suggestions.extend(
                    await self._optimize_for_deadlines(current_allocations, resource_requirements, available_resources)
                )
            
            elif optimization_type == OptimizationType.CAPACITY_PLANNING:
                suggestions.extend(
                    await self._optimize_capacity_planning(resource_requirements, available_resources, time_horizon_days)
                )
            
            # Rank suggestions by expected value
            suggestions.sort(key=lambda x: x.confidence_score * sum(x.expected_improvement.values()), reverse=True)
            
            # Cache results
            cache_key = f"{optimization_type.value}_{datetime.utcnow().date()}"
            self.optimization_cache[cache_key] = suggestions
            
            logger.info(f"Generated {len(suggestions)} optimization suggestions for {optimization_type.value}")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error optimizing resource allocation: {e}")
            return []

    async def analyze_resource_utilization(
        self,
        resource_ids: Optional[List[int]] = None,
        analysis_period_days: int = 30,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Analyze current resource utilization patterns."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=analysis_period_days)
            
            # Get utilization data
            utilization_data = await self._get_utilization_data(resource_ids, start_date, end_date, db)
            
            analysis = {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'days': analysis_period_days
                },
                'overall_metrics': {},
                'by_resource': {},
                'by_resource_type': {},
                'trends': {},
                'bottlenecks': [],
                'underutilized': [],
                'recommendations': []
            }
            
            if not utilization_data:
                return analysis
            
            # Calculate overall metrics
            total_available_hours = sum([r['available_hours'] for r in utilization_data])
            total_allocated_hours = sum([r['allocated_hours'] for r in utilization_data])
            total_billable_hours = sum([r['billable_hours'] for r in utilization_data])
            
            analysis['overall_metrics'] = {
                'total_available_hours': total_available_hours,
                'total_allocated_hours': total_allocated_hours,
                'total_billable_hours': total_billable_hours,
                'utilization_rate': total_allocated_hours / total_available_hours if total_available_hours > 0 else 0,
                'billability_rate': total_billable_hours / total_allocated_hours if total_allocated_hours > 0 else 0,
                'efficiency_rate': total_billable_hours / total_available_hours if total_available_hours > 0 else 0
            }
            
            # Analyze by resource
            for resource in utilization_data:
                resource_id = resource['resource_id']
                utilization_rate = resource['allocated_hours'] / resource['available_hours'] if resource['available_hours'] > 0 else 0
                billability_rate = resource['billable_hours'] / resource['allocated_hours'] if resource['allocated_hours'] > 0 else 0
                
                analysis['by_resource'][resource_id] = {
                    'name': resource['name'],
                    'type': resource['type'],
                    'available_hours': resource['available_hours'],
                    'allocated_hours': resource['allocated_hours'],
                    'billable_hours': resource['billable_hours'],
                    'utilization_rate': utilization_rate,
                    'billability_rate': billability_rate,
                    'efficiency_score': utilization_rate * billability_rate,
                    'case_count': resource.get('case_count', 0),
                    'avg_hourly_rate': resource.get('avg_hourly_rate', 0)
                }
                
                # Identify bottlenecks (over-utilized)
                if utilization_rate > self.constraint_rules['max_utilization_rate']:
                    analysis['bottlenecks'].append({
                        'resource_id': resource_id,
                        'name': resource['name'],
                        'utilization_rate': utilization_rate,
                        'excess_hours': resource['allocated_hours'] - (resource['available_hours'] * self.constraint_rules['max_utilization_rate'])
                    })
                
                # Identify underutilized resources
                if utilization_rate < self.constraint_rules['min_utilization_rate']:
                    analysis['underutilized'].append({
                        'resource_id': resource_id,
                        'name': resource['name'],
                        'utilization_rate': utilization_rate,
                        'available_capacity': resource['available_hours'] * (self.constraint_rules['min_utilization_rate'] - utilization_rate)
                    })
            
            # Analyze by resource type
            by_type = defaultdict(lambda: {'available': 0, 'allocated': 0, 'billable': 0, 'count': 0})
            
            for resource in utilization_data:
                resource_type = resource['type']
                by_type[resource_type]['available'] += resource['available_hours']
                by_type[resource_type]['allocated'] += resource['allocated_hours']
                by_type[resource_type]['billable'] += resource['billable_hours']
                by_type[resource_type]['count'] += 1
            
            for resource_type, metrics in by_type.items():
                analysis['by_resource_type'][resource_type] = {
                    'resource_count': metrics['count'],
                    'total_available_hours': metrics['available'],
                    'total_allocated_hours': metrics['allocated'],
                    'total_billable_hours': metrics['billable'],
                    'avg_utilization_rate': metrics['allocated'] / metrics['available'] if metrics['available'] > 0 else 0,
                    'avg_billability_rate': metrics['billable'] / metrics['allocated'] if metrics['allocated'] > 0 else 0
                }
            
            # Generate recommendations
            analysis['recommendations'] = await self._generate_utilization_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing resource utilization: {e}")
            return {}

    async def predict_resource_needs(
        self,
        forecast_horizon_days: int = 90,
        case_growth_rate: float = 0.05,  # Monthly growth rate
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Predict future resource needs based on trends and projections."""
        try:
            # Get historical data
            historical_data = await self._get_historical_resource_data(forecast_horizon_days * 2, db)
            current_allocations = await self._get_current_allocations(None, None, db)
            
            # Calculate current resource metrics
            current_metrics = await self._calculate_current_resource_metrics(current_allocations)
            
            # Project future demand
            monthly_periods = forecast_horizon_days // 30
            projections = {}
            
            for resource_type in ResourceType:
                current_demand = current_metrics.get(resource_type.value, {}).get('total_hours', 0)
                
                projected_demand = []
                for month in range(1, monthly_periods + 1):
                    # Apply growth rate with some seasonality
                    seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * month / 12)  # 10% seasonal variation
                    growth_factor = (1 + case_growth_rate) ** month
                    
                    monthly_demand = current_demand * growth_factor * seasonal_factor
                    projected_demand.append(monthly_demand)
                
                projections[resource_type.value] = {
                    'current_monthly_demand': current_demand,
                    'projected_demand': projected_demand,
                    'peak_demand': max(projected_demand) if projected_demand else 0,
                    'avg_demand': sum(projected_demand) / len(projected_demand) if projected_demand else 0,
                    'growth_trend': 'increasing' if projected_demand and projected_demand[-1] > current_demand else 'stable'
                }
            
            # Calculate resource gaps
            resource_gaps = {}
            current_capacity = await self._get_current_resource_capacity(db)
            
            for resource_type, projection in projections.items():
                current_cap = current_capacity.get(resource_type, 0)
                peak_demand = projection['peak_demand']
                avg_demand = projection['avg_demand']
                
                resource_gaps[resource_type] = {
                    'current_capacity': current_cap,
                    'peak_demand': peak_demand,
                    'avg_demand': avg_demand,
                    'peak_gap': max(0, peak_demand - current_cap),
                    'avg_gap': max(0, avg_demand - current_cap),
                    'utilization_at_peak': peak_demand / current_cap if current_cap > 0 else float('inf'),
                    'recommended_capacity': peak_demand * 1.1  # 10% buffer
                }
            
            # Generate hiring recommendations
            hiring_recommendations = []
            for resource_type, gap_info in resource_gaps.items():
                if gap_info['peak_gap'] > 40:  # More than 40 hours gap (1 FTE)
                    additional_fte = np.ceil(gap_info['peak_gap'] / 160)  # Assuming 160 hours/month per FTE
                    hiring_recommendations.append({
                        'resource_type': resource_type,
                        'additional_fte_needed': additional_fte,
                        'urgency': 'high' if gap_info['utilization_at_peak'] > 1.2 else 'medium',
                        'estimated_cost': additional_fte * 8000,  # Estimated monthly cost per FTE
                        'timeline': '1-2 months' if additional_fte <= 2 else '2-4 months'
                    })
            
            prediction_result = {
                'forecast_period_days': forecast_horizon_days,
                'growth_assumptions': {
                    'case_growth_rate': case_growth_rate,
                    'seasonal_variation': 0.1
                },
                'demand_projections': projections,
                'resource_gaps': resource_gaps,
                'hiring_recommendations': hiring_recommendations,
                'cost_projections': await self._calculate_cost_projections(projections, current_capacity),
                'risk_assessment': await self._assess_capacity_risks(resource_gaps),
                'contingency_plans': await self._generate_contingency_plans(resource_gaps),
                'generated_at': datetime.utcnow()
            }
            
            return prediction_result
            
        except Exception as e:
            logger.error(f"Error predicting resource needs: {e}")
            return {}

    async def optimize_skill_assignments(
        self,
        case_requirements: List[Dict[str, Any]],
        available_resources: Optional[List[Dict[str, Any]]] = None,
        db: Optional[AsyncSession] = None
    ) -> List[OptimizationSuggestion]:
        """Optimize resource assignments based on skill matching."""
        try:
            if not available_resources:
                available_resources = await self._get_available_resources(None, 30, db)
            
            # Load skill matrices
            await self._load_skill_matrices(db)
            
            suggestions = []
            
            for case_req in case_requirements:
                case_id = case_req.get('case_id')
                required_skills = case_req.get('required_skills', [])
                required_hours = case_req.get('required_hours', 0)
                priority = case_req.get('priority', 1)
                
                if not required_skills:
                    continue
                
                # Score all available resources for this case
                resource_scores = []
                
                for resource in available_resources:
                    resource_id = resource['resource_id']
                    resource_skills = self.skill_matrix.get(resource_id, {})
                    
                    # Calculate skill match score
                    skill_match_score = await self._calculate_skill_match(required_skills, resource_skills)
                    
                    # Calculate availability score
                    available_hours = resource.get('available_hours', 0)
                    availability_score = min(1.0, available_hours / required_hours) if required_hours > 0 else 1.0
                    
                    # Calculate cost efficiency score
                    hourly_rate = resource.get('hourly_rate', 100)
                    avg_rate = np.mean([r.get('hourly_rate', 100) for r in available_resources])
                    cost_score = avg_rate / hourly_rate if hourly_rate > 0 else 1.0
                    
                    # Calculate historical performance score
                    performance_metrics = self.historical_performance.get(resource_id, {})
                    performance_score = performance_metrics.get('avg_quality_score', 0.8)
                    
                    # Combined score
                    combined_score = (
                        skill_match_score * 0.4 +
                        availability_score * 0.25 +
                        cost_score * 0.2 +
                        performance_score * 0.15
                    )
                    
                    resource_scores.append({
                        'resource_id': resource_id,
                        'resource_name': resource.get('name', ''),
                        'resource_type': resource.get('type', ''),
                        'combined_score': combined_score,
                        'skill_match_score': skill_match_score,
                        'availability_score': availability_score,
                        'cost_score': cost_score,
                        'performance_score': performance_score,
                        'hourly_rate': hourly_rate,
                        'available_hours': available_hours
                    })
                
                # Sort by combined score
                resource_scores.sort(key=lambda x: x['combined_score'], reverse=True)
                
                # Generate suggestions for top candidates
                for i, candidate in enumerate(resource_scores[:3]):  # Top 3 candidates
                    if candidate['combined_score'] > 0.6:  # Minimum threshold
                        
                        # Create allocation suggestion
                        suggested_allocation = ResourceAllocation(
                            resource_type=ResourceType(candidate['resource_type']),
                            resource_id=candidate['resource_id'],
                            resource_name=candidate['resource_name'],
                            case_id=case_id,
                            allocated_hours=min(required_hours, candidate['available_hours']),
                            hourly_rate=candidate['hourly_rate'],
                            skill_requirements=required_skills,
                            skill_match_score=candidate['skill_match_score'],
                            utilization_rate=min(required_hours, candidate['available_hours']) / candidate['available_hours'] if candidate['available_hours'] > 0 else 0,
                            efficiency_score=candidate['combined_score'],
                            priority_level=priority
                        )
                        
                        # Create optimization suggestion
                        suggestion = OptimizationSuggestion(
                            optimization_type=OptimizationType.SKILL_MATCHING,
                            resource_type=ResourceType(candidate['resource_type']),
                            suggested_allocation=suggested_allocation,
                            expected_improvement={
                                'skill_match': candidate['skill_match_score'],
                                'cost_efficiency': candidate['cost_score'],
                                'quality_expectation': candidate['performance_score']
                            },
                            confidence_score=candidate['combined_score'],
                            cost_impact=suggested_allocation.allocated_hours * candidate['hourly_rate'],
                            quality_impact=candidate['skill_match_score'] - 0.5,  # Improvement over baseline
                            risk_level='low' if candidate['combined_score'] > 0.8 else 'medium',
                            justification=f"High skill match ({candidate['skill_match_score']:.2f}) with good availability and performance history",
                            affected_cases=[case_id],
                            affected_resources=[candidate['resource_id']],
                            priority=5 - i  # Higher priority for better matches
                        )
                        
                        suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error optimizing skill assignments: {e}")
            return []

    async def track_allocation_performance(
        self,
        allocation_ids: Optional[List[int]] = None,
        tracking_period_days: int = 30,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Track performance of resource allocations."""
        try:
            # Get allocation performance data
            performance_data = await self._get_allocation_performance_data(allocation_ids, tracking_period_days, db)
            
            if not performance_data:
                return {}
            
            # Calculate performance metrics
            performance_analysis = {
                'tracking_period_days': tracking_period_days,
                'total_allocations': len(performance_data),
                'overall_metrics': {},
                'by_resource_type': {},
                'by_case': {},
                'top_performers': [],
                'underperformers': [],
                'optimization_opportunities': [],
                'trends': {}
            }
            
            # Overall metrics
            total_allocated_hours = sum([a['allocated_hours'] for a in performance_data])
            total_actual_hours = sum([a['actual_hours'] for a in performance_data])
            total_estimated_cost = sum([a['estimated_cost'] for a in performance_data])
            total_actual_cost = sum([a['actual_cost'] for a in performance_data])
            
            performance_analysis['overall_metrics'] = {
                'total_allocated_hours': total_allocated_hours,
                'total_actual_hours': total_actual_hours,
                'hours_variance': total_actual_hours - total_allocated_hours,
                'hours_variance_percent': ((total_actual_hours - total_allocated_hours) / total_allocated_hours * 100) if total_allocated_hours > 0 else 0,
                'total_estimated_cost': total_estimated_cost,
                'total_actual_cost': total_actual_cost,
                'cost_variance': total_actual_cost - total_estimated_cost,
                'cost_variance_percent': ((total_actual_cost - total_estimated_cost) / total_estimated_cost * 100) if total_estimated_cost > 0 else 0,
                'avg_efficiency_score': np.mean([a['efficiency_score'] for a in performance_data if a['efficiency_score']]),
                'avg_quality_score': np.mean([a['quality_score'] for a in performance_data if a['quality_score']])
            }
            
            # Identify top performers and underperformers
            for allocation in performance_data:
                efficiency = allocation['efficiency_score']
                quality = allocation['quality_score']
                combined_performance = (efficiency + quality) / 2
                
                allocation_summary = {
                    'allocation_id': allocation['allocation_id'],
                    'resource_name': allocation['resource_name'],
                    'case_id': allocation['case_id'],
                    'combined_performance': combined_performance,
                    'efficiency_score': efficiency,
                    'quality_score': quality
                }
                
                if combined_performance > 0.85:
                    performance_analysis['top_performers'].append(allocation_summary)
                elif combined_performance < 0.6:
                    performance_analysis['underperformers'].append(allocation_summary)
            
            # Sort performers
            performance_analysis['top_performers'].sort(key=lambda x: x['combined_performance'], reverse=True)
            performance_analysis['underperformers'].sort(key=lambda x: x['combined_performance'])
            
            # Generate optimization opportunities
            performance_analysis['optimization_opportunities'] = await self._identify_performance_optimization_opportunities(performance_data)
            
            return performance_analysis
            
        except Exception as e:
            logger.error(f"Error tracking allocation performance: {e}")
            return {}

    # Helper methods
    
    async def _get_current_allocations(
        self, 
        case_ids: Optional[List[int]], 
        resource_types: Optional[List[ResourceType]], 
        db: Optional[AsyncSession]
    ) -> List[ResourceAllocation]:
        """Get current resource allocations."""
        try:
            # Mock data for demonstration
            allocations = []
            
            for i in range(20):  # Mock 20 allocations
                allocation = ResourceAllocation(
                    id=i,
                    resource_type=np.random.choice(list(ResourceType)),
                    resource_id=np.random.randint(1, 20),
                    resource_name=f"Resource_{np.random.randint(1, 20)}",
                    case_id=np.random.randint(1, 10) if not case_ids else np.random.choice(case_ids),
                    allocated_hours=np.random.uniform(10, 80),
                    hourly_rate=np.random.uniform(100, 400),
                    skill_match_score=np.random.uniform(0.5, 1.0),
                    utilization_rate=np.random.uniform(0.6, 0.95),
                    efficiency_score=np.random.uniform(0.7, 0.95),
                    priority_level=np.random.randint(1, 6)
                )
                allocations.append(allocation)
            
            return allocations
            
        except Exception as e:
            logger.error(f"Error getting current allocations: {e}")
            return []

    async def _analyze_resource_requirements(
        self, 
        case_ids: Optional[List[int]], 
        time_horizon_days: int, 
        db: Optional[AsyncSession]
    ) -> List[Dict[str, Any]]:
        """Analyze resource requirements for cases."""
        try:
            requirements = []
            
            # Mock requirements
            for case_id in (case_ids or list(range(1, 11))):
                requirement = {
                    'case_id': case_id,
                    'required_skills': np.random.choice(['litigation', 'research', 'drafting', 'negotiation'], 
                                                      size=np.random.randint(1, 4), replace=False).tolist(),
                    'required_hours': np.random.uniform(20, 200),
                    'deadline': datetime.utcnow() + timedelta(days=np.random.randint(1, time_horizon_days)),
                    'priority': np.random.randint(1, 6),
                    'complexity': np.random.uniform(1, 10)
                }
                requirements.append(requirement)
            
            return requirements
            
        except Exception as e:
            logger.error(f"Error analyzing resource requirements: {e}")
            return []

    async def _get_available_resources(
        self, 
        resource_types: Optional[List[ResourceType]], 
        time_horizon_days: int, 
        db: Optional[AsyncSession]
    ) -> List[Dict[str, Any]]:
        """Get available resources."""
        try:
            resources = []
            
            # Mock resources
            for i in range(1, 21):  # Mock 20 resources
                resource_type = np.random.choice(list(ResourceType))
                
                resource = {
                    'resource_id': i,
                    'name': f"Resource_{i}",
                    'type': resource_type.value,
                    'available_hours': np.random.uniform(100, 300),
                    'hourly_rate': np.random.uniform(100, 400),
                    'skills': np.random.choice(['litigation', 'research', 'drafting', 'negotiation', 'trial_prep'], 
                                             size=np.random.randint(2, 5), replace=False).tolist(),
                    'experience_years': np.random.randint(1, 20),
                    'current_utilization': np.random.uniform(0.5, 0.9)
                }
                resources.append(resource)
            
            return resources
            
        except Exception as e:
            logger.error(f"Error getting available resources: {e}")
            return []

    async def _optimize_workload_balancing(
        self, 
        current_allocations: List[ResourceAllocation], 
        available_resources: List[Dict[str, Any]]
    ) -> List[OptimizationSuggestion]:
        """Optimize workload balancing across resources."""
        try:
            suggestions = []
            
            # Calculate current workload distribution
            workload_by_resource = defaultdict(float)
            for allocation in current_allocations:
                workload_by_resource[allocation.resource_id] += allocation.allocated_hours
            
            # Find overloaded and underloaded resources
            avg_workload = np.mean(list(workload_by_resource.values())) if workload_by_resource else 0
            std_workload = np.std(list(workload_by_resource.values())) if workload_by_resource else 0
            
            overloaded = []
            underloaded = []
            
            for resource_id, workload in workload_by_resource.items():
                if workload > avg_workload + std_workload:
                    overloaded.append((resource_id, workload))
                elif workload < avg_workload - std_workload:
                    underloaded.append((resource_id, workload))
            
            # Generate rebalancing suggestions
            for overloaded_resource_id, overloaded_workload in overloaded[:3]:  # Top 3 overloaded
                for underloaded_resource_id, underloaded_workload in underloaded[:3]:  # Top 3 underloaded
                    
                    # Find transferable allocations
                    transferable_allocations = [
                        a for a in current_allocations 
                        if a.resource_id == overloaded_resource_id and a.priority_level <= 3
                    ]
                    
                    if transferable_allocations:
                        best_transfer = min(transferable_allocations, key=lambda x: x.allocated_hours)
                        transfer_hours = min(best_transfer.allocated_hours, 
                                           (overloaded_workload - avg_workload) * 0.5)
                        
                        if transfer_hours > 5:  # Minimum transfer threshold
                            suggestion = OptimizationSuggestion(
                                optimization_type=OptimizationType.WORKLOAD_BALANCING,
                                resource_type=best_transfer.resource_type,
                                current_allocation=best_transfer,
                                expected_improvement={
                                    'workload_balance': 0.2,
                                    'utilization_improvement': 0.15
                                },
                                confidence_score=0.8,
                                time_impact=transfer_hours,
                                cost_impact=0,  # Neutral cost impact
                                risk_level='low',
                                justification=f"Transfer {transfer_hours:.1f} hours from overloaded to underloaded resource",
                                affected_resources=[overloaded_resource_id, underloaded_resource_id],
                                priority=3
                            )
                            suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error optimizing workload balancing: {e}")
            return []

    async def _optimize_skill_matching(
        self, 
        resource_requirements: List[Dict[str, Any]], 
        available_resources: List[Dict[str, Any]]
    ) -> List[OptimizationSuggestion]:
        """Optimize skill matching between requirements and resources."""
        # This would be implemented similar to optimize_skill_assignments but focused on existing allocations
        return await self.optimize_skill_assignments(resource_requirements, available_resources)

    async def _optimize_cost_minimization(
        self, 
        current_allocations: List[ResourceAllocation], 
        available_resources: List[Dict[str, Any]]
    ) -> List[OptimizationSuggestion]:
        """Optimize for cost minimization."""
        try:
            suggestions = []
            
            # Find high-cost allocations that could be reassigned
            high_cost_allocations = [
                a for a in current_allocations 
                if a.hourly_rate and a.hourly_rate > 300
            ]
            
            for allocation in high_cost_allocations:
                # Find lower-cost alternatives with similar skills
                alternatives = [
                    r for r in available_resources 
                    if (r['hourly_rate'] < allocation.hourly_rate * 0.8 and
                        r['type'] == allocation.resource_type.value and
                        r['available_hours'] >= allocation.allocated_hours)
                ]
                
                if alternatives:
                    best_alternative = min(alternatives, key=lambda x: x['hourly_rate'])
                    cost_savings = (allocation.hourly_rate - best_alternative['hourly_rate']) * allocation.allocated_hours
                    
                    if cost_savings > 1000:  # Minimum savings threshold
                        new_allocation = ResourceAllocation(
                            resource_type=allocation.resource_type,
                            resource_id=best_alternative['resource_id'],
                            resource_name=best_alternative['name'],
                            case_id=allocation.case_id,
                            allocated_hours=allocation.allocated_hours,
                            hourly_rate=best_alternative['hourly_rate'],
                            skill_requirements=allocation.skill_requirements,
                            priority_level=allocation.priority_level
                        )
                        
                        suggestion = OptimizationSuggestion(
                            optimization_type=OptimizationType.COST_MINIMIZATION,
                            resource_type=allocation.resource_type,
                            current_allocation=allocation,
                            suggested_allocation=new_allocation,
                            expected_improvement={
                                'cost_savings': cost_savings,
                                'cost_reduction_percent': (cost_savings / (allocation.hourly_rate * allocation.allocated_hours)) * 100
                            },
                            confidence_score=0.75,
                            cost_impact=-cost_savings,  # Negative = savings
                            risk_level='medium',
                            justification=f"Replace with lower-cost resource, saving ${cost_savings:.2f}",
                            affected_cases=[allocation.case_id],
                            affected_resources=[allocation.resource_id, best_alternative['resource_id']],
                            priority=4
                        )
                        suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error optimizing cost minimization: {e}")
            return []

    async def _optimize_utilization(
        self, 
        current_allocations: List[ResourceAllocation], 
        available_resources: List[Dict[str, Any]]
    ) -> List[OptimizationSuggestion]:
        """Optimize resource utilization."""
        try:
            suggestions = []
            
            # Find underutilized resources
            resource_utilization = {}
            for resource in available_resources:
                resource_id = resource['resource_id']
                current_workload = sum([
                    a.allocated_hours for a in current_allocations 
                    if a.resource_id == resource_id
                ])
                utilization = current_workload / resource['available_hours'] if resource['available_hours'] > 0 else 0
                resource_utilization[resource_id] = {
                    'utilization': utilization,
                    'available_capacity': resource['available_hours'] - current_workload,
                    'resource': resource
                }
            
            # Find resources with low utilization
            underutilized = [
                (rid, data) for rid, data in resource_utilization.items() 
                if data['utilization'] < self.constraint_rules['min_utilization_rate'] and data['available_capacity'] > 20
            ]
            
            for resource_id, util_data in underutilized:
                additional_hours = util_data['available_capacity'] * 0.7  # Use 70% of available capacity
                
                suggestion = OptimizationSuggestion(
                    optimization_type=OptimizationType.UTILIZATION_MAXIMIZATION,
                    resource_type=ResourceType(util_data['resource']['type']),
                    expected_improvement={
                        'utilization_increase': additional_hours / util_data['resource']['available_hours'],
                        'revenue_potential': additional_hours * util_data['resource']['hourly_rate']
                    },
                    confidence_score=0.7,
                    cost_impact=0,  # Revenue opportunity
                    time_impact=additional_hours,
                    risk_level='low',
                    justification=f"Increase utilization by {additional_hours:.1f} hours for underutilized resource",
                    affected_resources=[resource_id],
                    priority=3
                )
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error optimizing utilization: {e}")
            return []

    async def _optimize_for_deadlines(
        self, 
        current_allocations: List[ResourceAllocation], 
        resource_requirements: List[Dict[str, Any]], 
        available_resources: List[Dict[str, Any]]
    ) -> List[OptimizationSuggestion]:
        """Optimize resource allocation for deadline compliance."""
        try:
            suggestions = []
            
            # Identify urgent requirements
            now = datetime.utcnow()
            urgent_requirements = [
                req for req in resource_requirements 
                if req['deadline'] - now <= timedelta(days=7)  # Within 1 week
            ]
            
            for requirement in urgent_requirements:
                case_id = requirement['case_id']
                required_hours = requirement['required_hours']
                deadline = requirement['deadline']
                
                # Find fastest available resources (highest hourly capacity)
                suitable_resources = [
                    r for r in available_resources 
                    if (set(requirement['required_skills']).intersection(set(r['skills'])) and
                        r['available_hours'] >= required_hours * 0.5)
                ]
                
                if suitable_resources:
                    # Sort by combination of availability and skill match
                    suitable_resources.sort(
                        key=lambda x: (x['available_hours'], len(set(requirement['required_skills']).intersection(set(x['skills'])))),
                        reverse=True
                    )
                    
                    best_resource = suitable_resources[0]
                    
                    # Create high-priority allocation
                    urgent_allocation = ResourceAllocation(
                        resource_type=ResourceType(best_resource['type']),
                        resource_id=best_resource['resource_id'],
                        resource_name=best_resource['name'],
                        case_id=case_id,
                        allocated_hours=min(required_hours, best_resource['available_hours']),
                        hourly_rate=best_resource['hourly_rate'],
                        skill_requirements=requirement['required_skills'],
                        priority_level=5,  # Highest priority
                        allocation_end=deadline
                    )
                    
                    suggestion = OptimizationSuggestion(
                        optimization_type=OptimizationType.DEADLINE_OPTIMIZATION,
                        resource_type=ResourceType(best_resource['type']),
                        suggested_allocation=urgent_allocation,
                        expected_improvement={
                            'deadline_compliance': 0.9,
                            'on_time_delivery': 1.0
                        },
                        confidence_score=0.85,
                        cost_impact=urgent_allocation.allocated_hours * best_resource['hourly_rate'],
                        risk_level='medium',
                        implementation_effort='easy',
                        justification=f"Urgent allocation for deadline {deadline.strftime('%Y-%m-%d')}",
                        affected_cases=[case_id],
                        affected_resources=[best_resource['resource_id']],
                        priority=5,
                        timeline='immediate'
                    )
                    suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error optimizing for deadlines: {e}")
            return []

    async def _optimize_capacity_planning(
        self, 
        resource_requirements: List[Dict[str, Any]], 
        available_resources: List[Dict[str, Any]], 
        time_horizon_days: int
    ) -> List[OptimizationSuggestion]:
        """Optimize capacity planning."""
        try:
            suggestions = []
            
            # Calculate total demand by resource type
            demand_by_type = defaultdict(float)
            for req in resource_requirements:
                # Estimate resource type needed based on skills
                if 'litigation' in req['required_skills']:
                    demand_by_type[ResourceType.ATTORNEY.value] += req['required_hours']
                elif 'research' in req['required_skills']:
                    demand_by_type[ResourceType.PARALEGAL.value] += req['required_hours'] * 0.7
                    demand_by_type[ResourceType.ATTORNEY.value] += req['required_hours'] * 0.3
                else:
                    demand_by_type[ResourceType.ATTORNEY.value] += req['required_hours']
            
            # Calculate current capacity by resource type
            capacity_by_type = defaultdict(float)
            for resource in available_resources:
                capacity_by_type[resource['type']] += resource['available_hours']
            
            # Identify capacity gaps
            for resource_type, total_demand in demand_by_type.items():
                current_capacity = capacity_by_type.get(resource_type, 0)
                capacity_gap = total_demand - current_capacity
                
                if capacity_gap > 40:  # Significant gap (>1 FTE worth)
                    additional_fte = np.ceil(capacity_gap / 160)  # 160 hours per month per FTE
                    
                    suggestion = OptimizationSuggestion(
                        optimization_type=OptimizationType.CAPACITY_PLANNING,
                        resource_type=ResourceType(resource_type),
                        expected_improvement={
                            'capacity_increase': capacity_gap,
                            'demand_coverage': min(1.0, (current_capacity + capacity_gap) / total_demand)
                        },
                        confidence_score=0.8,
                        cost_impact=additional_fte * 8000 * (time_horizon_days / 30),  # Monthly cost estimate
                        risk_level='low',
                        implementation_effort='moderate',
                        justification=f"Add {additional_fte} FTE to meet projected demand of {total_demand:.0f} hours",
                        priority=4,
                        timeline=f"{int(additional_fte * 30)}-{int(additional_fte * 60)} days"
                    )
                    suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error optimizing capacity planning: {e}")
            return []

    # Additional helper methods would be implemented here for:
    # - _load_skill_matrices
    # - _calculate_skill_match  
    # - _get_utilization_data
    # - _generate_utilization_recommendations
    # - _get_historical_resource_data
    # - _calculate_current_resource_metrics
    # - _get_current_resource_capacity
    # - _calculate_cost_projections
    # - _assess_capacity_risks
    # - _generate_contingency_plans
    # - _get_allocation_performance_data
    # - _identify_performance_optimization_opportunities

    async def _load_skill_matrices(self, db: Optional[AsyncSession]) -> None:
        """Load skill matrices for resources."""
        # Mock skill matrices
        skills = ['litigation', 'research', 'drafting', 'negotiation', 'trial_prep']
        
        for resource_id in range(1, 21):
            self.skill_matrix[resource_id] = {
                skill: np.random.uniform(0.3, 1.0) for skill in skills
            }

    async def _calculate_skill_match(self, required_skills: List[str], resource_skills: Dict[str, float]) -> float:
        """Calculate skill match score."""
        if not required_skills:
            return 1.0
        
        matches = []
        for skill in required_skills:
            skill_level = resource_skills.get(skill, 0.0)
            matches.append(skill_level)
        
        return np.mean(matches) if matches else 0.0