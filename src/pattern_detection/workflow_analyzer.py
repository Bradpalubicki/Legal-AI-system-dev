"""
Workflow Analyzer Module

Comprehensive workflow analysis system for optimizing legal processes,
identifying bottlenecks, and improving efficiency in case management.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, and_, or_
import logging
from collections import defaultdict, deque
import asyncio
import json
import networkx as nx
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class WorkflowPattern(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    ITERATIVE = "iterative"
    CONDITIONAL = "conditional"
    CYCLICAL = "cyclical"
    BOTTLENECK = "bottleneck"
    BYPASS = "bypass"
    ESCALATION = "escalation"

@dataclass
class ProcessStep:
    id: Optional[int] = None
    step_name: str = ""
    step_type: str = ""  # document_review, research, drafting, filing, etc.
    duration_minutes: Optional[float] = None
    assigned_role: Optional[str] = None
    assigned_attorney_id: Optional[int] = None
    prerequisites: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    complexity_score: float = 1.0
    automation_potential: float = 0.0  # 0-1 scale
    error_rate: float = 0.0
    rework_frequency: float = 0.0
    cost_per_execution: Optional[float] = None
    quality_score: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowMetrics:
    workflow_id: str = ""
    total_steps: int = 0
    total_duration_hours: float = 0.0
    avg_step_duration: float = 0.0
    critical_path_duration: float = 0.0
    bottleneck_steps: List[str] = field(default_factory=list)
    parallel_efficiency: float = 0.0  # How well parallel tasks are utilized
    rework_rate: float = 0.0
    automation_score: float = 0.0
    cost_efficiency: float = 0.0
    quality_score: float = 0.0
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    step_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    cycle_time: float = 0.0  # End-to-end completion time
    throughput: float = 0.0  # Cases completed per time unit
    error_hotspots: List[str] = field(default_factory=list)
    optimization_opportunities: List[str] = field(default_factory=list)
    calculated_at: datetime = field(default_factory=datetime.utcnow)

class WorkflowAnalyzer:
    def __init__(self):
        self.workflow_cache: Dict[str, WorkflowMetrics] = {}
        self.process_graphs: Dict[str, nx.DiGraph] = {}
        self.step_patterns: Dict[str, List[WorkflowPattern]] = {}
        self.optimization_rules = {
            'max_parallel_steps': 5,
            'bottleneck_threshold': 1.5,  # Steps taking 1.5x avg duration
            'automation_threshold': 0.7,  # Steps with >70% automation potential
            'quality_threshold': 0.8,  # Minimum acceptable quality score
            'cost_efficiency_target': 0.85
        }

    async def analyze_workflow(
        self,
        workflow_id: str,
        case_ids: Optional[List[int]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        db: Optional[AsyncSession] = None
    ) -> WorkflowMetrics:
        """Analyze complete workflow for optimization opportunities."""
        try:
            # Get workflow steps data
            steps_data = await self._get_workflow_steps(workflow_id, case_ids, date_range, db)
            
            if not steps_data:
                return WorkflowMetrics(workflow_id=workflow_id)
            
            # Create process graph
            process_graph = await self._build_process_graph(steps_data)
            self.process_graphs[workflow_id] = process_graph
            
            # Calculate comprehensive metrics
            metrics = await self._calculate_workflow_metrics(workflow_id, steps_data, process_graph)
            
            # Identify patterns
            patterns = await self._identify_workflow_patterns(process_graph, steps_data)
            self.step_patterns[workflow_id] = patterns
            
            # Find optimization opportunities
            optimizations = await self._identify_optimization_opportunities(metrics, patterns, steps_data)
            metrics.optimization_opportunities = optimizations
            
            # Cache results
            self.workflow_cache[workflow_id] = metrics
            
            logger.info(f"Analyzed workflow {workflow_id} with {metrics.total_steps} steps")
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing workflow {workflow_id}: {e}")
            return WorkflowMetrics(workflow_id=workflow_id)

    async def identify_bottlenecks(
        self,
        workflow_id: str,
        threshold_multiplier: float = 1.5
    ) -> List[Dict[str, Any]]:
        """Identify bottleneck steps in workflow."""
        try:
            if workflow_id not in self.workflow_cache:
                return []
            
            metrics = self.workflow_cache[workflow_id]
            process_graph = self.process_graphs.get(workflow_id)
            
            if not process_graph:
                return []
            
            bottlenecks = []
            avg_duration = metrics.avg_step_duration
            
            for node in process_graph.nodes():
                node_data = process_graph.nodes[node]
                duration = node_data.get('duration_minutes', 0) / 60.0  # Convert to hours
                
                if duration > avg_duration * threshold_multiplier:
                    # Calculate impact of this bottleneck
                    predecessors = list(process_graph.predecessors(node))
                    successors = list(process_graph.successors(node))
                    
                    bottlenecks.append({
                        'step_name': node,
                        'duration_hours': duration,
                        'delay_factor': duration / avg_duration,
                        'predecessors': predecessors,
                        'successors': successors,
                        'impact_score': len(successors) * (duration / avg_duration),
                        'parallel_potential': len(predecessors) > 1,
                        'automation_potential': node_data.get('automation_potential', 0),
                        'suggestions': await self._generate_bottleneck_solutions(node, node_data, process_graph)
                    })
            
            # Sort by impact score
            bottlenecks.sort(key=lambda x: x['impact_score'], reverse=True)
            
            return bottlenecks
            
        except Exception as e:
            logger.error(f"Error identifying bottlenecks: {e}")
            return []

    async def optimize_parallel_execution(
        self,
        workflow_id: str,
        max_parallel_tasks: int = 5
    ) -> Dict[str, Any]:
        """Analyze and optimize parallel task execution."""
        try:
            process_graph = self.process_graphs.get(workflow_id)
            if not process_graph:
                return {}
            
            # Find tasks that can be parallelized
            parallelizable_groups = []
            visited = set()
            
            for node in nx.topological_sort(process_graph):
                if node in visited:
                    continue
                
                # Find nodes with same dependencies (can run in parallel)
                parallel_candidates = []
                node_predecessors = set(process_graph.predecessors(node))
                
                for other_node in process_graph.nodes():
                    if other_node != node and other_node not in visited:
                        other_predecessors = set(process_graph.predecessors(other_node))
                        
                        # Can run in parallel if they have same or compatible dependencies
                        if node_predecessors == other_predecessors:
                            parallel_candidates.append(other_node)
                
                if parallel_candidates:
                    parallel_candidates.append(node)
                    parallelizable_groups.append({
                        'group_id': len(parallelizable_groups),
                        'tasks': parallel_candidates,
                        'dependencies': list(node_predecessors),
                        'total_duration': sum([
                            process_graph.nodes[task].get('duration_minutes', 0) 
                            for task in parallel_candidates
                        ]),
                        'max_duration': max([
                            process_graph.nodes[task].get('duration_minutes', 0) 
                            for task in parallel_candidates
                        ])
                    })
                    visited.update(parallel_candidates)
                else:
                    visited.add(node)
            
            # Calculate optimization benefits
            current_total_time = sum([
                process_graph.nodes[node].get('duration_minutes', 0) 
                for node in process_graph.nodes()
            ])
            
            optimized_time = 0
            for group in parallelizable_groups:
                optimized_time += group['max_duration']  # Parallel execution time
            
            # Add sequential tasks
            sequential_time = sum([
                process_graph.nodes[node].get('duration_minutes', 0)
                for node in process_graph.nodes()
                if not any(node in group['tasks'] for group in parallelizable_groups)
            ])
            
            optimized_time += sequential_time
            
            optimization_result = {
                'current_duration_minutes': current_total_time,
                'optimized_duration_minutes': optimized_time,
                'time_savings_minutes': current_total_time - optimized_time,
                'efficiency_gain_percent': ((current_total_time - optimized_time) / current_total_time * 100) if current_total_time > 0 else 0,
                'parallelizable_groups': parallelizable_groups,
                'recommendations': await self._generate_parallel_recommendations(parallelizable_groups, max_parallel_tasks)
            }
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Error optimizing parallel execution: {e}")
            return {}

    async def analyze_automation_potential(
        self,
        workflow_id: str,
        automation_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """Analyze steps for automation potential."""
        try:
            process_graph = self.process_graphs.get(workflow_id)
            if not process_graph:
                return {}
            
            automation_candidates = []
            
            for node in process_graph.nodes():
                node_data = process_graph.nodes[node]
                automation_score = node_data.get('automation_potential', 0)
                
                if automation_score >= automation_threshold:
                    duration = node_data.get('duration_minutes', 0)
                    frequency = node_data.get('frequency', 1)  # How often this step occurs
                    error_rate = node_data.get('error_rate', 0)
                    
                    # Calculate automation ROI factors
                    time_savings = duration * frequency * 52  # Yearly time savings
                    cost_savings = time_savings * 2.0  # Assume $2/minute saved cost
                    error_reduction_value = error_rate * 1000  # Assume $1000 per error avoided
                    
                    automation_candidates.append({
                        'step_name': node,
                        'automation_score': automation_score,
                        'current_duration_minutes': duration,
                        'frequency_per_week': frequency,
                        'error_rate': error_rate,
                        'annual_time_savings_hours': time_savings / 60,
                        'estimated_cost_savings': cost_savings + error_reduction_value,
                        'complexity': node_data.get('complexity_score', 1),
                        'tools_needed': await self._suggest_automation_tools(node, node_data),
                        'implementation_effort': await self._estimate_automation_effort(node, node_data)
                    })
            
            # Sort by cost savings potential
            automation_candidates.sort(key=lambda x: x['estimated_cost_savings'], reverse=True)
            
            # Calculate overall automation metrics
            total_automatable_time = sum([
                candidate['annual_time_savings_hours'] for candidate in automation_candidates
            ])
            
            total_cost_savings = sum([
                candidate['estimated_cost_savings'] for candidate in automation_candidates
            ])
            
            automation_analysis = {
                'automation_candidates': automation_candidates,
                'total_annual_time_savings_hours': total_automatable_time,
                'total_estimated_cost_savings': total_cost_savings,
                'automation_coverage_percent': (len(automation_candidates) / len(process_graph.nodes()) * 100) if process_graph.nodes() else 0,
                'recommended_priorities': automation_candidates[:5],  # Top 5 priorities
                'implementation_roadmap': await self._create_automation_roadmap(automation_candidates)
            }
            
            return automation_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing automation potential: {e}")
            return {}

    async def track_workflow_performance(
        self,
        workflow_id: str,
        performance_period_days: int = 30
    ) -> Dict[str, Any]:
        """Track workflow performance over time."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=performance_period_days)
            
            # Get historical performance data
            historical_metrics = []
            
            # Simulate weekly performance tracking
            current_date = start_date
            while current_date <= end_date:
                week_end = min(current_date + timedelta(days=7), end_date)
                
                # Get metrics for this week (mock data for now)
                weekly_metrics = await self._get_weekly_metrics(workflow_id, current_date, week_end)
                if weekly_metrics:
                    historical_metrics.append(weekly_metrics)
                
                current_date = week_end
            
            if not historical_metrics:
                return {}
            
            # Calculate performance trends
            performance_analysis = {
                'period_days': performance_period_days,
                'data_points': len(historical_metrics),
                'metrics_history': historical_metrics,
                'trends': {
                    'cycle_time': await self._calculate_trend([m['cycle_time'] for m in historical_metrics]),
                    'throughput': await self._calculate_trend([m['throughput'] for m in historical_metrics]),
                    'quality_score': await self._calculate_trend([m['quality_score'] for m in historical_metrics]),
                    'cost_efficiency': await self._calculate_trend([m['cost_efficiency'] for m in historical_metrics]),
                    'error_rate': await self._calculate_trend([m['error_rate'] for m in historical_metrics])
                },
                'performance_summary': await self._summarize_performance(historical_metrics),
                'alerts': await self._generate_performance_alerts(historical_metrics),
                'recommendations': await self._generate_performance_recommendations(historical_metrics)
            }
            
            return performance_analysis
            
        except Exception as e:
            logger.error(f"Error tracking workflow performance: {e}")
            return {}

    async def compare_workflows(
        self,
        workflow_ids: List[str],
        comparison_metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare multiple workflows for best practices identification."""
        try:
            if not comparison_metrics:
                comparison_metrics = ['cycle_time', 'throughput', 'quality_score', 'cost_efficiency', 'automation_score']
            
            workflow_comparisons = {}
            
            for workflow_id in workflow_ids:
                if workflow_id in self.workflow_cache:
                    metrics = self.workflow_cache[workflow_id]
                    
                    workflow_comparisons[workflow_id] = {
                        'total_steps': metrics.total_steps,
                        'cycle_time': metrics.cycle_time,
                        'throughput': metrics.throughput,
                        'quality_score': metrics.quality_score,
                        'cost_efficiency': metrics.cost_efficiency,
                        'automation_score': metrics.automation_score,
                        'error_rate': metrics.rework_rate,
                        'parallel_efficiency': metrics.parallel_efficiency
                    }
            
            if not workflow_comparisons:
                return {}
            
            # Calculate rankings
            rankings = {}
            for metric in comparison_metrics:
                if metric in ['error_rate']:  # Lower is better
                    rankings[metric] = sorted(
                        workflow_comparisons.items(),
                        key=lambda x: x[1].get(metric, float('inf'))
                    )
                else:  # Higher is better
                    rankings[metric] = sorted(
                        workflow_comparisons.items(),
                        key=lambda x: x[1].get(metric, 0),
                        reverse=True
                    )
            
            # Identify best practices
            best_practices = {}
            for metric, ranked_workflows in rankings.items():
                if ranked_workflows:
                    best_workflow_id = ranked_workflows[0][0]
                    best_practices[metric] = {
                        'workflow_id': best_workflow_id,
                        'value': ranked_workflows[0][1].get(metric, 0),
                        'practices': await self._extract_best_practices(best_workflow_id, metric)
                    }
            
            comparison_result = {
                'workflows_compared': workflow_ids,
                'comparison_data': workflow_comparisons,
                'rankings': rankings,
                'best_practices': best_practices,
                'improvement_opportunities': await self._identify_improvement_opportunities(workflow_comparisons, rankings),
                'overall_champion': await self._determine_overall_champion(rankings)
            }
            
            return comparison_result
            
        except Exception as e:
            logger.error(f"Error comparing workflows: {e}")
            return {}

    async def _get_workflow_steps(
        self,
        workflow_id: str,
        case_ids: Optional[List[int]],
        date_range: Optional[Tuple[datetime, datetime]],
        db: Optional[AsyncSession]
    ) -> List[ProcessStep]:
        """Get workflow steps data from database."""
        try:
            # Mock data generation for demonstration
            steps = []
            
            # Legal case workflow example
            if workflow_id == 'case_intake':
                mock_steps = [
                    ProcessStep(
                        step_name="Initial Client Consultation",
                        step_type="consultation",
                        duration_minutes=60,
                        assigned_role="attorney",
                        prerequisites=[],
                        dependencies=[],
                        automation_potential=0.2,
                        error_rate=0.05,
                        quality_score=0.9
                    ),
                    ProcessStep(
                        step_name="Conflict Check",
                        step_type="verification",
                        duration_minutes=15,
                        assigned_role="paralegal",
                        prerequisites=["Initial Client Consultation"],
                        automation_potential=0.9,
                        error_rate=0.01,
                        quality_score=0.95
                    ),
                    ProcessStep(
                        step_name="Retainer Agreement",
                        step_type="documentation",
                        duration_minutes=30,
                        assigned_role="attorney",
                        prerequisites=["Conflict Check"],
                        automation_potential=0.7,
                        error_rate=0.02,
                        quality_score=0.85
                    ),
                    ProcessStep(
                        step_name="Case File Setup",
                        step_type="administration",
                        duration_minutes=20,
                        assigned_role="legal_assistant",
                        prerequisites=["Retainer Agreement"],
                        automation_potential=0.8,
                        error_rate=0.03,
                        quality_score=0.9
                    ),
                    ProcessStep(
                        step_name="Initial Research",
                        step_type="research",
                        duration_minutes=120,
                        assigned_role="attorney",
                        prerequisites=["Case File Setup"],
                        automation_potential=0.3,
                        error_rate=0.1,
                        quality_score=0.8
                    )
                ]
                steps.extend(mock_steps)
            
            elif workflow_id == 'document_review':
                mock_steps = [
                    ProcessStep(
                        step_name="Document Collection",
                        step_type="collection",
                        duration_minutes=45,
                        assigned_role="paralegal",
                        automation_potential=0.6,
                        error_rate=0.05
                    ),
                    ProcessStep(
                        step_name="Document Indexing",
                        step_type="organization",
                        duration_minutes=90,
                        assigned_role="legal_assistant",
                        prerequisites=["Document Collection"],
                        automation_potential=0.95,
                        error_rate=0.02
                    ),
                    ProcessStep(
                        step_name="Relevance Review",
                        step_type="analysis",
                        duration_minutes=180,
                        assigned_role="attorney",
                        prerequisites=["Document Indexing"],
                        automation_potential=0.4,
                        error_rate=0.15
                    ),
                    ProcessStep(
                        step_name="Privilege Review",
                        step_type="analysis",
                        duration_minutes=120,
                        assigned_role="attorney",
                        prerequisites=["Relevance Review"],
                        automation_potential=0.2,
                        error_rate=0.08
                    )
                ]
                steps.extend(mock_steps)
            
            return steps
            
        except Exception as e:
            logger.error(f"Error getting workflow steps: {e}")
            return []

    async def _build_process_graph(self, steps_data: List[ProcessStep]) -> nx.DiGraph:
        """Build directed graph representation of workflow."""
        try:
            graph = nx.DiGraph()
            
            # Add nodes
            for step in steps_data:
                graph.add_node(
                    step.step_name,
                    step_type=step.step_type,
                    duration_minutes=step.duration_minutes,
                    assigned_role=step.assigned_role,
                    automation_potential=step.automation_potential,
                    error_rate=step.error_rate,
                    quality_score=step.quality_score,
                    complexity_score=step.complexity_score,
                    rework_frequency=step.rework_frequency
                )
            
            # Add edges based on prerequisites
            for step in steps_data:
                for prerequisite in step.prerequisites:
                    if prerequisite in graph.nodes():
                        graph.add_edge(prerequisite, step.step_name)
            
            return graph
            
        except Exception as e:
            logger.error(f"Error building process graph: {e}")
            return nx.DiGraph()

    async def _calculate_workflow_metrics(
        self,
        workflow_id: str,
        steps_data: List[ProcessStep],
        process_graph: nx.DiGraph
    ) -> WorkflowMetrics:
        """Calculate comprehensive workflow metrics."""
        try:
            metrics = WorkflowMetrics(workflow_id=workflow_id)
            
            if not steps_data:
                return metrics
            
            # Basic metrics
            metrics.total_steps = len(steps_data)
            total_duration = sum([step.duration_minutes or 0 for step in steps_data])
            metrics.total_duration_hours = total_duration / 60.0
            metrics.avg_step_duration = total_duration / len(steps_data) if steps_data else 0
            
            # Critical path analysis
            if process_graph.nodes():
                try:
                    critical_path = nx.dag_longest_path(process_graph, weight='duration_minutes')
                    critical_path_duration = nx.dag_longest_path_length(process_graph, weight='duration_minutes')
                    metrics.critical_path_duration = critical_path_duration / 60.0  # Convert to hours
                except:
                    metrics.critical_path_duration = metrics.total_duration_hours
            
            # Identify bottlenecks
            avg_duration = metrics.avg_step_duration
            bottlenecks = []
            for step in steps_data:
                if (step.duration_minutes or 0) > avg_duration * 1.5:
                    bottlenecks.append(step.step_name)
            metrics.bottleneck_steps = bottlenecks
            
            # Calculate parallel efficiency
            sequential_duration = metrics.critical_path_duration
            total_work = metrics.total_duration_hours
            metrics.parallel_efficiency = sequential_duration / total_work if total_work > 0 else 0
            
            # Quality and error metrics
            error_rates = [step.error_rate for step in steps_data if step.error_rate is not None]
            if error_rates:
                metrics.rework_rate = sum(error_rates) / len(error_rates)
            
            quality_scores = [step.quality_score for step in steps_data if step.quality_score is not None]
            if quality_scores:
                metrics.quality_score = sum(quality_scores) / len(quality_scores)
            
            # Automation score
            automation_scores = [step.automation_potential for step in steps_data if step.automation_potential is not None]
            if automation_scores:
                metrics.automation_score = sum(automation_scores) / len(automation_scores)
            
            # Resource utilization
            resource_usage = defaultdict(float)
            for step in steps_data:
                if step.assigned_role and step.duration_minutes:
                    resource_usage[step.assigned_role] += step.duration_minutes
            
            total_resource_time = sum(resource_usage.values())
            if total_resource_time > 0:
                metrics.resource_utilization = {
                    role: time / total_resource_time 
                    for role, time in resource_usage.items()
                }
            
            # Cycle time and throughput (simplified)
            metrics.cycle_time = metrics.critical_path_duration
            metrics.throughput = 8.0 / metrics.cycle_time if metrics.cycle_time > 0 else 0  # Cases per day
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating workflow metrics: {e}")
            return WorkflowMetrics(workflow_id=workflow_id)

    async def _identify_workflow_patterns(
        self,
        process_graph: nx.DiGraph,
        steps_data: List[ProcessStep]
    ) -> List[WorkflowPattern]:
        """Identify patterns in workflow structure."""
        try:
            patterns = []
            
            # Check for sequential pattern
            if nx.is_path(process_graph):
                patterns.append(WorkflowPattern.SEQUENTIAL)
            
            # Check for parallel patterns
            parallel_nodes = []
            for node in process_graph.nodes():
                predecessors = list(process_graph.predecessors(node))
                if len(predecessors) == 0:  # Starting nodes
                    successors = list(process_graph.successors(node))
                    if len(successors) > 1:
                        parallel_nodes.extend(successors)
            
            if parallel_nodes:
                patterns.append(WorkflowPattern.PARALLEL)
            
            # Check for cycles (iterative processes)
            if not nx.is_directed_acyclic_graph(process_graph):
                patterns.append(WorkflowPattern.CYCLICAL)
            
            # Check for bottlenecks
            node_degrees = dict(process_graph.degree())
            max_degree = max(node_degrees.values()) if node_degrees else 0
            avg_degree = sum(node_degrees.values()) / len(node_degrees) if node_degrees else 0
            
            if max_degree > avg_degree * 2:
                patterns.append(WorkflowPattern.BOTTLENECK)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error identifying workflow patterns: {e}")
            return []

    async def _identify_optimization_opportunities(
        self,
        metrics: WorkflowMetrics,
        patterns: List[WorkflowPattern],
        steps_data: List[ProcessStep]
    ) -> List[str]:
        """Identify optimization opportunities."""
        try:
            opportunities = []
            
            # Bottleneck opportunities
            if metrics.bottleneck_steps:
                opportunities.append(f"Address bottlenecks in: {', '.join(metrics.bottleneck_steps[:3])}")
            
            # Automation opportunities
            high_automation_steps = [
                step.step_name for step in steps_data 
                if step.automation_potential > 0.7
            ]
            if high_automation_steps:
                opportunities.append(f"Automate high-potential steps: {', '.join(high_automation_steps[:3])}")
            
            # Parallel execution opportunities
            if metrics.parallel_efficiency < 0.6:
                opportunities.append("Improve parallel task execution")
            
            # Quality improvements
            if metrics.quality_score < 0.8:
                opportunities.append("Implement quality control measures")
            
            # Error reduction
            if metrics.rework_rate > 0.1:
                opportunities.append("Reduce error rates and rework")
            
            # Resource balancing
            if metrics.resource_utilization:
                max_util = max(metrics.resource_utilization.values())
                min_util = min(metrics.resource_utilization.values())
                if max_util - min_util > 0.4:
                    opportunities.append("Balance resource utilization across roles")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error identifying optimization opportunities: {e}")
            return []

    # Additional helper methods for completeness...
    
    async def _generate_bottleneck_solutions(
        self, 
        step_name: str, 
        step_data: Dict[str, Any], 
        process_graph: nx.DiGraph
    ) -> List[str]:
        """Generate solutions for bottleneck steps."""
        solutions = []
        
        automation_potential = step_data.get('automation_potential', 0)
        if automation_potential > 0.5:
            solutions.append("Consider automation or tool enhancement")
        
        predecessors = list(process_graph.predecessors(step_name))
        if len(predecessors) > 1:
            solutions.append("Parallelize prerequisite tasks")
        
        solutions.append("Add additional resources or staff")
        solutions.append("Break down into smaller sub-tasks")
        
        return solutions

    async def _generate_parallel_recommendations(
        self, 
        parallelizable_groups: List[Dict[str, Any]], 
        max_parallel_tasks: int
    ) -> List[str]:
        """Generate recommendations for parallel execution."""
        recommendations = []
        
        for group in parallelizable_groups[:3]:  # Top 3 groups
            if len(group['tasks']) > max_parallel_tasks:
                recommendations.append(f"Batch parallel group {group['group_id']} into smaller chunks")
            else:
                recommendations.append(f"Execute {len(group['tasks'])} tasks in parallel for group {group['group_id']}")
        
        return recommendations

    async def _suggest_automation_tools(self, step_name: str, step_data: Dict[str, Any]) -> List[str]:
        """Suggest automation tools for specific steps."""
        tools = []
        step_type = step_data.get('step_type', '')
        
        if 'document' in step_type.lower():
            tools.extend(['Document automation software', 'Template systems'])
        if 'research' in step_type.lower():
            tools.extend(['AI research assistants', 'Legal databases with API integration'])
        if 'filing' in step_type.lower():
            tools.extend(['E-filing systems', 'Court integration APIs'])
        if 'verification' in step_type.lower():
            tools.extend(['Automated verification systems', 'Database lookups'])
        
        return tools

    async def _estimate_automation_effort(self, step_name: str, step_data: Dict[str, Any]) -> str:
        """Estimate effort required for automation."""
        complexity = step_data.get('complexity_score', 1)
        automation_potential = step_data.get('automation_potential', 0)
        
        if complexity <= 2 and automation_potential > 0.8:
            return "Low effort"
        elif complexity <= 5 and automation_potential > 0.6:
            return "Medium effort"
        else:
            return "High effort"

    async def _create_automation_roadmap(self, automation_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create implementation roadmap for automation."""
        roadmap = []
        
        # Phase 1: Quick wins (low effort, high savings)
        phase1 = [c for c in automation_candidates if c['implementation_effort'] == 'Low effort'][:3]
        if phase1:
            roadmap.append({
                'phase': 1,
                'timeline': '1-2 months',
                'tasks': [c['step_name'] for c in phase1],
                'expected_savings': sum([c['estimated_cost_savings'] for c in phase1])
            })
        
        # Phase 2: Medium effort wins
        phase2 = [c for c in automation_candidates if c['implementation_effort'] == 'Medium effort'][:3]
        if phase2:
            roadmap.append({
                'phase': 2,
                'timeline': '3-6 months',
                'tasks': [c['step_name'] for c in phase2],
                'expected_savings': sum([c['estimated_cost_savings'] for c in phase2])
            })
        
        return roadmap

    async def _get_weekly_metrics(self, workflow_id: str, start_date: datetime, end_date: datetime) -> Optional[Dict[str, Any]]:
        """Get weekly performance metrics (mock implementation)."""
        # Mock data for demonstration
        return {
            'week_start': start_date,
            'week_end': end_date,
            'cycle_time': np.random.normal(4.5, 0.5),  # hours
            'throughput': np.random.normal(2.0, 0.3),  # cases per day
            'quality_score': np.random.normal(0.85, 0.05),
            'cost_efficiency': np.random.normal(0.8, 0.1),
            'error_rate': np.random.normal(0.05, 0.02)
        }

    async def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend for a series of values."""
        if len(values) < 2:
            return {'direction': 'insufficient_data'}
        
        # Simple linear trend
        x = list(range(len(values)))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.01:
            direction = 'increasing'
        elif slope < -0.01:
            direction = 'decreasing'
        else:
            direction = 'stable'
        
        return {
            'direction': direction,
            'slope': float(slope),
            'current_value': values[-1],
            'change_percent': ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
        }

    async def _summarize_performance(self, historical_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize overall performance."""
        if not historical_metrics:
            return {}
        
        latest = historical_metrics[-1]
        earliest = historical_metrics[0]
        
        return {
            'current_cycle_time': latest['cycle_time'],
            'current_throughput': latest['throughput'],
            'current_quality_score': latest['quality_score'],
            'cycle_time_change': latest['cycle_time'] - earliest['cycle_time'],
            'throughput_change': latest['throughput'] - earliest['throughput'],
            'quality_change': latest['quality_score'] - earliest['quality_score'],
            'overall_trend': 'improving' if latest['quality_score'] > earliest['quality_score'] else 'declining'
        }

    async def _generate_performance_alerts(self, historical_metrics: List[Dict[str, Any]]) -> List[str]:
        """Generate performance alerts."""
        alerts = []
        
        if not historical_metrics:
            return alerts
        
        latest = historical_metrics[-1]
        
        if latest['quality_score'] < 0.7:
            alerts.append("Quality score below acceptable threshold")
        
        if latest['error_rate'] > 0.1:
            alerts.append("Error rate elevated above normal levels")
        
        if len(historical_metrics) > 1:
            previous = historical_metrics[-2]
            if latest['cycle_time'] > previous['cycle_time'] * 1.2:
                alerts.append("Cycle time increased significantly")
        
        return alerts

    async def _generate_performance_recommendations(self, historical_metrics: List[Dict[str, Any]]) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        if not historical_metrics:
            return recommendations
        
        latest = historical_metrics[-1]
        
        if latest['quality_score'] < 0.8:
            recommendations.append("Implement additional quality control checkpoints")
        
        if latest['cycle_time'] > 6:
            recommendations.append("Review process for bottlenecks and optimization opportunities")
        
        if latest['throughput'] < 1.5:
            recommendations.append("Consider resource allocation adjustments")
        
        return recommendations

    async def _extract_best_practices(self, workflow_id: str, metric: str) -> List[str]:
        """Extract best practices from top-performing workflow."""
        # Mock best practices based on metric
        practices_map = {
            'cycle_time': [
                'Efficient task sequencing',
                'Minimal handoff delays',
                'Streamlined approval processes'
            ],
            'quality_score': [
                'Comprehensive review checkpoints',
                'Standardized quality criteria',
                'Regular training updates'
            ],
            'automation_score': [
                'High automation tool adoption',
                'Streamlined digital workflows',
                'Minimal manual interventions'
            ]
        }
        
        return practices_map.get(metric, ['Process optimization', 'Best practice implementation'])

    async def _identify_improvement_opportunities(
        self, 
        workflow_comparisons: Dict[str, Dict[str, Any]], 
        rankings: Dict[str, List[Tuple[str, Dict[str, Any]]]]
    ) -> List[str]:
        """Identify improvement opportunities across workflows."""
        opportunities = []
        
        for metric, ranked_workflows in rankings.items():
            if len(ranked_workflows) > 1:
                best_value = ranked_workflows[0][1].get(metric, 0)
                worst_value = ranked_workflows[-1][1].get(metric, 0)
                
                if metric == 'error_rate':  # Lower is better
                    if worst_value > best_value * 2:
                        opportunities.append(f"Significant opportunity to reduce {metric}")
                else:  # Higher is better
                    if best_value > worst_value * 1.5:
                        opportunities.append(f"Opportunity to improve {metric} in underperforming workflows")
        
        return opportunities

    async def _determine_overall_champion(self, rankings: Dict[str, List[Tuple[str, Dict[str, Any]]]]) -> Optional[str]:
        """Determine overall best performing workflow."""
        workflow_scores = defaultdict(int)
        
        for metric, ranked_workflows in rankings.items():
            for i, (workflow_id, _) in enumerate(ranked_workflows):
                score = len(ranked_workflows) - i  # Higher rank = higher score
                workflow_scores[workflow_id] += score
        
        if workflow_scores:
            return max(workflow_scores.items(), key=lambda x: x[1])[0]
        
        return None