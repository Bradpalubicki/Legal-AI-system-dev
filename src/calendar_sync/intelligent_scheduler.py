"""
Intelligent Scheduling Optimizer for Legal Calendar Management

Advanced scheduling algorithms that optimize legal calendar arrangements considering
travel time, conflicts, priorities, and legal-specific constraints.
"""

from typing import List, Dict, Any, Optional, Union, Tuple, Set
from datetime import datetime, timedelta, time
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
import json
from abc import ABC, abstractmethod
import numpy as np
from scipy.optimize import minimize
import networkx as nx
from itertools import combinations, permutations

from .hearing_detector import HearingEvent, HearingType, HearingStatus, Location
from .travel_time_calculator import TravelTimeCalculator, TravelTimeRequest, TransportMode, Location as TravelLocation
from .advanced_conflict_detection import AdvancedConflictDetector, ResourceRequirement, ResourceType

logger = logging.getLogger(__name__)


class SchedulingObjective(Enum):
    """Scheduling optimization objectives."""
    MINIMIZE_CONFLICTS = "minimize_conflicts"
    MINIMIZE_TRAVEL_TIME = "minimize_travel_time"
    MAXIMIZE_EFFICIENCY = "maximize_efficiency"
    BALANCE_WORKLOAD = "balance_workload"
    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_SATISFACTION = "maximize_satisfaction"


class SchedulingConstraintType(Enum):
    """Types of scheduling constraints."""
    HARD = "hard"           # Must be satisfied
    SOFT = "soft"           # Preferred but can be violated with penalty
    PREFERENCE = "preference"  # Nice to have


@dataclass
class SchedulingSlot:
    """Represents an available scheduling slot."""
    slot_id: str
    start_time: datetime
    end_time: datetime
    location: Location
    available_resources: Set[str]
    capacity: int = 1  # Number of events that can be scheduled
    cost: float = 0.0  # Cost of using this slot
    preferences: Dict[str, float] = field(default_factory=dict)  # Preference scores
    
    @property
    def duration_minutes(self) -> int:
        """Get slot duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)
    
    def overlaps_with(self, other: 'SchedulingSlot') -> bool:
        """Check if this slot overlaps with another."""
        return (self.start_time < other.end_time and 
                other.start_time < self.end_time)
    
    def can_accommodate(self, event: HearingEvent) -> bool:
        """Check if slot can accommodate an event."""
        event_duration = 60  # Default 1 hour
        if event.end_time:
            event_duration = int((event.end_time - event.date_time).total_seconds() / 60)
        
        return (self.duration_minutes >= event_duration and
                self.capacity > 0)


@dataclass
class SchedulingConstraint:
    """Represents a scheduling constraint."""
    constraint_id: str
    constraint_type: SchedulingConstraintType
    description: str
    weight: float = 1.0
    
    # Constraint definition
    applies_to: List[str] = field(default_factory=list)  # Event IDs or types
    time_constraints: Optional[Dict[str, Any]] = None
    resource_constraints: Optional[Dict[str, Any]] = None
    location_constraints: Optional[Dict[str, Any]] = None
    
    # Penalty for violation
    violation_penalty: float = 100.0
    
    def evaluate(self, schedule: 'Schedule') -> Tuple[bool, float]:
        """Evaluate constraint against a schedule."""
        # This would be implemented based on specific constraint types
        return True, 0.0


@dataclass
class SchedulingObjectiveFunction:
    """Defines the objective function for optimization."""
    primary_objective: SchedulingObjective
    secondary_objectives: List[SchedulingObjective] = field(default_factory=list)
    objective_weights: Dict[SchedulingObjective, float] = field(default_factory=dict)
    
    def evaluate(self, schedule: 'Schedule') -> float:
        """Evaluate the objective function for a schedule."""
        total_score = 0.0
        
        # Primary objective
        primary_score = self._evaluate_single_objective(self.primary_objective, schedule)
        primary_weight = self.objective_weights.get(self.primary_objective, 1.0)
        total_score += primary_score * primary_weight
        
        # Secondary objectives
        for objective in self.secondary_objectives:
            score = self._evaluate_single_objective(objective, schedule)
            weight = self.objective_weights.get(objective, 0.5)
            total_score += score * weight
        
        return total_score
    
    def _evaluate_single_objective(self, objective: SchedulingObjective, schedule: 'Schedule') -> float:
        """Evaluate a single objective."""
        if objective == SchedulingObjective.MINIMIZE_CONFLICTS:
            return -len(schedule.conflicts)  # Negative because we want to minimize
        elif objective == SchedulingObjective.MINIMIZE_TRAVEL_TIME:
            return -schedule.total_travel_time_minutes
        elif objective == SchedulingObjective.MAXIMIZE_EFFICIENCY:
            return schedule.efficiency_score
        elif objective == SchedulingObjective.BALANCE_WORKLOAD:
            return -schedule.workload_variance
        else:
            return 0.0


@dataclass
class Schedule:
    """Represents a complete schedule."""
    schedule_id: str
    assignments: Dict[str, str]  # event_id -> slot_id mapping
    events: List[HearingEvent]
    slots: List[SchedulingSlot]
    
    # Calculated properties
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    total_travel_time_minutes: int = 0
    efficiency_score: float = 0.0
    workload_variance: float = 0.0
    constraint_violations: List[Dict[str, Any]] = field(default_factory=list)
    objective_score: float = 0.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    optimization_method: str = "unknown"
    optimization_time_seconds: float = 0.0
    
    def get_assigned_events(self) -> List[Tuple[HearingEvent, SchedulingSlot]]:
        """Get list of (event, slot) pairs for assigned events."""
        assigned = []
        slot_lookup = {slot.slot_id: slot for slot in self.slots}
        
        for event in self.events:
            if event.hearing_id in self.assignments:
                slot_id = self.assignments[event.hearing_id]
                if slot_id in slot_lookup:
                    assigned.append((event, slot_lookup[slot_id]))
        
        return assigned
    
    def get_unassigned_events(self) -> List[HearingEvent]:
        """Get list of unassigned events."""
        assigned_event_ids = set(self.assignments.keys())
        return [event for event in self.events 
                if event.hearing_id not in assigned_event_ids]
    
    def is_valid(self) -> bool:
        """Check if schedule is valid (no hard constraint violations)."""
        hard_violations = [v for v in self.constraint_violations 
                          if v.get('constraint_type') == 'hard']
        return len(hard_violations) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schedule to dictionary."""
        return {
            'schedule_id': self.schedule_id,
            'assignments': self.assignments,
            'total_events': len(self.events),
            'assigned_events': len(self.assignments),
            'unassigned_events': len(self.get_unassigned_events()),
            'conflicts': len(self.conflicts),
            'total_travel_time_minutes': self.total_travel_time_minutes,
            'efficiency_score': self.efficiency_score,
            'workload_variance': self.workload_variance,
            'constraint_violations': len(self.constraint_violations),
            'objective_score': self.objective_score,
            'is_valid': self.is_valid(),
            'created_at': self.created_at.isoformat(),
            'optimization_method': self.optimization_method,
            'optimization_time_seconds': self.optimization_time_seconds
        }


class SchedulingAlgorithm(ABC):
    """Abstract base class for scheduling algorithms."""
    
    @abstractmethod
    async def optimize(self, events: List[HearingEvent], 
                      slots: List[SchedulingSlot],
                      constraints: List[SchedulingConstraint],
                      objective: SchedulingObjectiveFunction) -> Schedule:
        """Optimize schedule for given events, slots, constraints, and objective."""
        pass
    
    @abstractmethod
    def get_algorithm_name(self) -> str:
        """Get algorithm name."""
        pass


class GreedySchedulingAlgorithm(SchedulingAlgorithm):
    """Greedy scheduling algorithm that assigns events to best available slots."""
    
    def __init__(self, travel_calculator: TravelTimeCalculator):
        self.travel_calculator = travel_calculator
    
    async def optimize(self, events: List[HearingEvent],
                      slots: List[SchedulingSlot],
                      constraints: List[SchedulingConstraint],
                      objective: SchedulingObjectiveFunction) -> Schedule:
        """Optimize using greedy algorithm."""
        start_time = datetime.now()
        
        # Sort events by priority (trials first, then by date)
        priority_map = {
            HearingType.TRIAL: 1,
            HearingType.ORAL_ARGUMENT: 2,
            HearingType.MOTION_HEARING: 3,
            HearingType.HEARING: 4,
            HearingType.STATUS_CONFERENCE: 5
        }
        
        sorted_events = sorted(events, key=lambda e: (
            priority_map.get(e.hearing_type, 10),
            e.date_time
        ))
        
        # Initialize schedule
        assignments = {}
        available_slots = {slot.slot_id: slot for slot in slots}
        
        # Assign events greedily
        for event in sorted_events:
            best_slot = await self._find_best_slot(
                event, list(available_slots.values()), 
                assignments, objective
            )
            
            if best_slot:
                assignments[event.hearing_id] = best_slot.slot_id
                
                # Reduce slot capacity or remove if fully used
                available_slots[best_slot.slot_id].capacity -= 1
                if available_slots[best_slot.slot_id].capacity <= 0:
                    del available_slots[best_slot.slot_id]
        
        # Create and evaluate schedule
        schedule = Schedule(
            schedule_id=f"greedy_{datetime.now().timestamp()}",
            assignments=assignments,
            events=events,
            slots=slots,
            optimization_method="greedy",
            optimization_time_seconds=(datetime.now() - start_time).total_seconds()
        )
        
        await self._evaluate_schedule(schedule, objective, constraints)
        return schedule
    
    async def _find_best_slot(self, event: HearingEvent, 
                             available_slots: List[SchedulingSlot],
                             current_assignments: Dict[str, str],
                             objective: SchedulingObjectiveFunction) -> Optional[SchedulingSlot]:
        """Find the best slot for an event."""
        compatible_slots = []
        
        # Filter compatible slots
        for slot in available_slots:
            if self._is_slot_compatible(event, slot):
                compatible_slots.append(slot)
        
        if not compatible_slots:
            return None
        
        # Score each compatible slot
        slot_scores = []
        for slot in compatible_slots:
            score = await self._score_slot_for_event(event, slot, current_assignments, objective)
            slot_scores.append((slot, score))
        
        # Return slot with best score
        slot_scores.sort(key=lambda x: x[1], reverse=True)
        return slot_scores[0][0]
    
    def _is_slot_compatible(self, event: HearingEvent, slot: SchedulingSlot) -> bool:
        """Check if slot is compatible with event."""
        # Check if slot can accommodate event duration
        if not slot.can_accommodate(event):
            return False
        
        # Check if event time preferences match slot
        if event.date_time:
            # Prefer slots close to event's preferred time
            time_diff = abs((slot.start_time - event.date_time).total_seconds() / 3600)
            if time_diff > 24:  # Don't schedule more than 24 hours away from preference
                return False
        
        # Check location compatibility
        if event.location and slot.location:
            # For now, just check if it's the same court system
            if (hasattr(event.location, 'court_name') and 
                hasattr(slot.location, 'court_name')):
                if event.location.court_name != slot.location.court_name:
                    return False
        
        return True
    
    async def _score_slot_for_event(self, event: HearingEvent, slot: SchedulingSlot,
                                   current_assignments: Dict[str, str],
                                   objective: SchedulingObjectiveFunction) -> float:
        """Score how good a slot is for an event."""
        score = 0.0
        
        # Time preference score
        if event.date_time:
            time_diff_hours = abs((slot.start_time - event.date_time).total_seconds() / 3600)
            time_score = max(0, 100 - time_diff_hours * 5)  # Penalty for time difference
            score += time_score
        
        # Location preference score
        location_score = slot.preferences.get('location', 50)  # Default neutral score
        score += location_score
        
        # Resource availability score
        if slot.available_resources:
            resource_score = len(slot.available_resources) * 10
            score += resource_score
        
        # Cost consideration (lower cost is better)
        cost_score = max(0, 100 - slot.cost)
        score += cost_score
        
        # Travel time consideration (if applicable)
        travel_score = await self._calculate_travel_score(event, slot, current_assignments)
        score += travel_score
        
        return score
    
    async def _calculate_travel_score(self, event: HearingEvent, slot: SchedulingSlot,
                                     current_assignments: Dict[str, str]) -> float:
        """Calculate travel-related score for slot assignment."""
        # This is a simplified version - in practice would calculate actual travel times
        # For now, return neutral score
        return 0.0
    
    async def _evaluate_schedule(self, schedule: Schedule, 
                               objective: SchedulingObjectiveFunction,
                               constraints: List[SchedulingConstraint]):
        """Evaluate and update schedule metrics."""
        # Calculate conflicts (simplified)
        schedule.conflicts = await self._detect_schedule_conflicts(schedule)
        
        # Calculate travel times (simplified)
        schedule.total_travel_time_minutes = await self._calculate_total_travel_time(schedule)
        
        # Calculate efficiency score
        schedule.efficiency_score = self._calculate_efficiency_score(schedule)
        
        # Calculate workload variance
        schedule.workload_variance = self._calculate_workload_variance(schedule)
        
        # Evaluate constraints
        schedule.constraint_violations = self._evaluate_constraints(schedule, constraints)
        
        # Calculate objective score
        schedule.objective_score = objective.evaluate(schedule)
    
    async def _detect_schedule_conflicts(self, schedule: Schedule) -> List[Dict[str, Any]]:
        """Detect conflicts in the schedule."""
        conflicts = []
        assigned_pairs = schedule.get_assigned_events()
        
        # Check for time conflicts
        for i, (event1, slot1) in enumerate(assigned_pairs):
            for j, (event2, slot2) in enumerate(assigned_pairs[i+1:], i+1):
                if slot1.overlaps_with(slot2):
                    conflicts.append({
                        'type': 'time_overlap',
                        'event1': event1.hearing_id,
                        'event2': event2.hearing_id,
                        'slot1': slot1.slot_id,
                        'slot2': slot2.slot_id
                    })
        
        return conflicts
    
    async def _calculate_total_travel_time(self, schedule: Schedule) -> int:
        """Calculate total travel time for schedule."""
        # Simplified calculation - would use actual travel time calculator
        return len(schedule.get_assigned_events()) * 30  # 30 minutes average
    
    def _calculate_efficiency_score(self, schedule: Schedule) -> float:
        """Calculate efficiency score."""
        total_events = len(schedule.events)
        assigned_events = len(schedule.assignments)
        
        if total_events == 0:
            return 100.0
        
        assignment_rate = assigned_events / total_events
        conflict_penalty = len(schedule.conflicts) * 10
        
        return max(0, assignment_rate * 100 - conflict_penalty)
    
    def _calculate_workload_variance(self, schedule: Schedule) -> float:
        """Calculate workload variance across resources."""
        # Simplified - would calculate actual variance across judges, courtrooms, etc.
        return 0.0  # Neutral score for now
    
    def _evaluate_constraints(self, schedule: Schedule, 
                            constraints: List[SchedulingConstraint]) -> List[Dict[str, Any]]:
        """Evaluate constraint violations."""
        violations = []
        
        for constraint in constraints:
            is_satisfied, penalty = constraint.evaluate(schedule)
            
            if not is_satisfied:
                violations.append({
                    'constraint_id': constraint.constraint_id,
                    'constraint_type': constraint.constraint_type.value,
                    'description': constraint.description,
                    'penalty': penalty
                })
        
        return violations
    
    def get_algorithm_name(self) -> str:
        """Get algorithm name."""
        return "Greedy Scheduling Algorithm"


class GeneticAlgorithmScheduler(SchedulingAlgorithm):
    """Genetic algorithm for schedule optimization."""
    
    def __init__(self, travel_calculator: TravelTimeCalculator,
                 population_size: int = 100,
                 generations: int = 50,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.8):
        self.travel_calculator = travel_calculator
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
    
    async def optimize(self, events: List[HearingEvent],
                      slots: List[SchedulingSlot],
                      constraints: List[SchedulingConstraint],
                      objective: SchedulingObjectiveFunction) -> Schedule:
        """Optimize using genetic algorithm."""
        start_time = datetime.now()
        
        # Initialize population
        population = await self._initialize_population(events, slots, objective)
        
        best_schedule = max(population, key=lambda s: s.objective_score)
        
        # Evolve population
        for generation in range(self.generations):
            # Selection
            selected = self._selection(population)
            
            # Crossover
            offspring = await self._crossover(selected, events, slots, objective)
            
            # Mutation
            mutated = await self._mutation(offspring, slots, objective)
            
            # Combine and select next generation
            combined = population + mutated
            population = sorted(combined, key=lambda s: s.objective_score, reverse=True)[:self.population_size]
            
            # Track best schedule
            generation_best = population[0]
            if generation_best.objective_score > best_schedule.objective_score:
                best_schedule = generation_best
            
            logger.debug(f"Generation {generation}: Best score = {generation_best.objective_score:.2f}")
        
        # Finalize best schedule
        best_schedule.optimization_method = "genetic_algorithm"
        best_schedule.optimization_time_seconds = (datetime.now() - start_time).total_seconds()
        
        await self._evaluate_schedule_detailed(best_schedule, objective, constraints)
        return best_schedule
    
    async def _initialize_population(self, events: List[HearingEvent],
                                   slots: List[SchedulingSlot],
                                   objective: SchedulingObjectiveFunction) -> List[Schedule]:
        """Initialize population with random schedules."""
        population = []
        
        for i in range(self.population_size):
            # Create random assignment
            assignments = {}
            available_slots = {slot.slot_id: slot for slot in slots}
            shuffled_events = events.copy()
            np.random.shuffle(shuffled_events)
            
            for event in shuffled_events:
                compatible_slots = [
                    slot for slot in available_slots.values()
                    if self._is_compatible(event, slot)
                ]
                
                if compatible_slots:
                    chosen_slot = np.random.choice(compatible_slots)
                    assignments[event.hearing_id] = chosen_slot.slot_id
                    
                    # Update slot capacity
                    available_slots[chosen_slot.slot_id].capacity -= 1
                    if available_slots[chosen_slot.slot_id].capacity <= 0:
                        del available_slots[chosen_slot.slot_id]
            
            # Create schedule
            schedule = Schedule(
                schedule_id=f"ga_init_{i}",
                assignments=assignments,
                events=events,
                slots=slots
            )
            
            # Quick evaluation
            schedule.objective_score = objective.evaluate(schedule)
            population.append(schedule)
        
        return population
    
    def _is_compatible(self, event: HearingEvent, slot: SchedulingSlot) -> bool:
        """Check basic compatibility between event and slot."""
        return slot.can_accommodate(event)
    
    def _selection(self, population: List[Schedule]) -> List[Schedule]:
        """Select parents for reproduction using tournament selection."""
        selected = []
        tournament_size = 5
        
        for _ in range(len(population) // 2):
            # Tournament selection
            tournament = np.random.choice(population, tournament_size, replace=False)
            winner = max(tournament, key=lambda s: s.objective_score)
            selected.append(winner)
        
        return selected
    
    async def _crossover(self, parents: List[Schedule], events: List[HearingEvent],
                        slots: List[SchedulingSlot],
                        objective: SchedulingObjectiveFunction) -> List[Schedule]:
        """Create offspring through crossover."""
        offspring = []
        
        for i in range(0, len(parents) - 1, 2):
            if np.random.random() < self.crossover_rate:
                parent1, parent2 = parents[i], parents[i + 1]
                child1, child2 = await self._single_point_crossover(parent1, parent2, events, slots)
                
                # Evaluate children
                child1.objective_score = objective.evaluate(child1)
                child2.objective_score = objective.evaluate(child2)
                
                offspring.extend([child1, child2])
        
        return offspring
    
    async def _single_point_crossover(self, parent1: Schedule, parent2: Schedule,
                                     events: List[HearingEvent],
                                     slots: List[SchedulingSlot]) -> Tuple[Schedule, Schedule]:
        """Perform single-point crossover."""
        event_ids = list(parent1.assignments.keys())
        if len(event_ids) < 2:
            return parent1, parent2
        
        # Random crossover point
        crossover_point = np.random.randint(1, len(event_ids))
        
        # Create children
        child1_assignments = {}
        child2_assignments = {}
        
        # First part from parent1/parent2
        for i, event_id in enumerate(event_ids):
            if i < crossover_point:
                if event_id in parent1.assignments:
                    child1_assignments[event_id] = parent1.assignments[event_id]
                if event_id in parent2.assignments:
                    child2_assignments[event_id] = parent2.assignments[event_id]
            else:
                if event_id in parent2.assignments:
                    child1_assignments[event_id] = parent2.assignments[event_id]
                if event_id in parent1.assignments:
                    child2_assignments[event_id] = parent1.assignments[event_id]
        
        # Create child schedules
        child1 = Schedule(
            schedule_id=f"ga_child_{datetime.now().timestamp()}_1",
            assignments=child1_assignments,
            events=events,
            slots=slots
        )
        
        child2 = Schedule(
            schedule_id=f"ga_child_{datetime.now().timestamp()}_2",
            assignments=child2_assignments,
            events=events,
            slots=slots
        )
        
        return child1, child2
    
    async def _mutation(self, offspring: List[Schedule], slots: List[SchedulingSlot],
                       objective: SchedulingObjectiveFunction) -> List[Schedule]:
        """Mutate offspring."""
        mutated = []
        
        for schedule in offspring:
            if np.random.random() < self.mutation_rate:
                mutated_schedule = await self._mutate_schedule(schedule, slots)
                mutated_schedule.objective_score = objective.evaluate(mutated_schedule)
                mutated.append(mutated_schedule)
            else:
                mutated.append(schedule)
        
        return mutated
    
    async def _mutate_schedule(self, schedule: Schedule, slots: List[SchedulingSlot]) -> Schedule:
        """Mutate a single schedule."""
        new_assignments = schedule.assignments.copy()
        
        if new_assignments:
            # Random mutation: reassign random event to random compatible slot
            event_id = np.random.choice(list(new_assignments.keys()))
            
            # Find compatible slots for this event
            event = next(e for e in schedule.events if e.hearing_id == event_id)
            compatible_slots = [slot for slot in slots if self._is_compatible(event, slot)]
            
            if compatible_slots:
                new_slot = np.random.choice(compatible_slots)
                new_assignments[event_id] = new_slot.slot_id
        
        # Create mutated schedule
        mutated = Schedule(
            schedule_id=f"ga_mutated_{datetime.now().timestamp()}",
            assignments=new_assignments,
            events=schedule.events,
            slots=schedule.slots
        )
        
        return mutated
    
    async def _evaluate_schedule_detailed(self, schedule: Schedule,
                                        objective: SchedulingObjectiveFunction,
                                        constraints: List[SchedulingConstraint]):
        """Detailed schedule evaluation."""
        # Use the same evaluation as greedy algorithm
        greedy_evaluator = GreedySchedulingAlgorithm(self.travel_calculator)
        await greedy_evaluator._evaluate_schedule(schedule, objective, constraints)
    
    def get_algorithm_name(self) -> str:
        """Get algorithm name."""
        return f"Genetic Algorithm (pop={self.population_size}, gen={self.generations})"


class IntelligentScheduler:
    """Main intelligent scheduler that combines multiple algorithms."""
    
    def __init__(self, travel_calculator: TravelTimeCalculator):
        self.travel_calculator = travel_calculator
        self.conflict_detector = AdvancedConflictDetector()
        
        # Available algorithms
        self.algorithms: Dict[str, SchedulingAlgorithm] = {
            'greedy': GreedySchedulingAlgorithm(travel_calculator),
            'genetic': GeneticAlgorithmScheduler(travel_calculator)
        }
        
        # Default constraints and objectives
        self.default_constraints = self._create_default_constraints()
        self.default_objective = self._create_default_objective()
    
    def _create_default_constraints(self) -> List[SchedulingConstraint]:
        """Create default scheduling constraints."""
        return [
            SchedulingConstraint(
                constraint_id="no_double_booking",
                constraint_type=SchedulingConstraintType.HARD,
                description="No resource can be double-booked",
                weight=1000.0
            ),
            SchedulingConstraint(
                constraint_id="business_hours",
                constraint_type=SchedulingConstraintType.SOFT,
                description="Prefer business hours scheduling",
                weight=50.0
            ),
            SchedulingConstraint(
                constraint_id="judge_availability",
                constraint_type=SchedulingConstraintType.HARD,
                description="Judge must be available",
                weight=500.0
            ),
            SchedulingConstraint(
                constraint_id="travel_time_reasonable",
                constraint_type=SchedulingConstraintType.SOFT,
                description="Travel time between events should be reasonable",
                weight=100.0
            )
        ]
    
    def _create_default_objective(self) -> SchedulingObjectiveFunction:
        """Create default objective function."""
        return SchedulingObjectiveFunction(
            primary_objective=SchedulingObjective.MINIMIZE_CONFLICTS,
            secondary_objectives=[
                SchedulingObjective.MINIMIZE_TRAVEL_TIME,
                SchedulingObjective.MAXIMIZE_EFFICIENCY
            ],
            objective_weights={
                SchedulingObjective.MINIMIZE_CONFLICTS: 1.0,
                SchedulingObjective.MINIMIZE_TRAVEL_TIME: 0.7,
                SchedulingObjective.MAXIMIZE_EFFICIENCY: 0.5
            }
        )
    
    async def optimize_schedule(self, events: List[HearingEvent],
                              available_slots: List[SchedulingSlot],
                              algorithm: str = "auto",
                              constraints: Optional[List[SchedulingConstraint]] = None,
                              objective: Optional[SchedulingObjectiveFunction] = None) -> Schedule:
        """Optimize schedule using specified or automatic algorithm selection."""
        
        # Use defaults if not provided
        if constraints is None:
            constraints = self.default_constraints
        if objective is None:
            objective = self.default_objective
        
        # Select algorithm
        if algorithm == "auto":
            algorithm = self._select_best_algorithm(events, available_slots)
        
        if algorithm not in self.algorithms:
            logger.warning(f"Algorithm {algorithm} not available, using greedy")
            algorithm = "greedy"
        
        # Generate available slots if not provided
        if not available_slots:
            available_slots = await self._generate_available_slots(events)
        
        logger.info(f"Optimizing schedule for {len(events)} events using {algorithm} algorithm")
        
        # Run optimization
        scheduler = self.algorithms[algorithm]
        schedule = await scheduler.optimize(events, available_slots, constraints, objective)
        
        logger.info(f"Schedule optimization completed: "
                   f"{len(schedule.assignments)}/{len(events)} events assigned, "
                   f"score: {schedule.objective_score:.2f}")
        
        return schedule
    
    def _select_best_algorithm(self, events: List[HearingEvent], 
                             slots: List[SchedulingSlot]) -> str:
        """Select the best algorithm based on problem characteristics."""
        num_events = len(events)
        num_slots = len(slots)
        
        # For small problems, genetic algorithm can find better solutions
        if num_events <= 20 and num_slots <= 50:
            return "genetic"
        # For larger problems, use greedy for speed
        else:
            return "greedy"
    
    async def _generate_available_slots(self, events: List[HearingEvent]) -> List[SchedulingSlot]:
        """Generate available scheduling slots based on events."""
        slots = []
        
        # Get date range from events
        if not events:
            return slots
        
        start_date = min(event.date_time for event in events).date()
        end_date = max(event.date_time for event in events).date() + timedelta(days=7)
        
        # Generate slots for each day
        current_date = start_date
        slot_id_counter = 0
        
        while current_date <= end_date:
            # Generate slots for business hours (9 AM to 5 PM)
            for hour in range(9, 17):
                for minute in [0, 30]:  # 30-minute slots
                    slot_start = datetime.combine(current_date, time(hour, minute))
                    slot_end = slot_start + timedelta(minutes=30)
                    
                    slot = SchedulingSlot(
                        slot_id=f"slot_{slot_id_counter}",
                        start_time=slot_start,
                        end_time=slot_end,
                        location=Location(name=f"Courtroom {(slot_id_counter % 10) + 1}"),
                        available_resources={"judge", "courtroom", "court_reporter"},
                        capacity=1
                    )
                    
                    slots.append(slot)
                    slot_id_counter += 1
            
            current_date += timedelta(days=1)
        
        return slots
    
    async def compare_algorithms(self, events: List[HearingEvent],
                               available_slots: List[SchedulingSlot],
                               algorithms: List[str] = None) -> Dict[str, Schedule]:
        """Compare multiple algorithms on the same problem."""
        
        if algorithms is None:
            algorithms = list(self.algorithms.keys())
        
        results = {}
        
        for algorithm in algorithms:
            if algorithm in self.algorithms:
                logger.info(f"Testing {algorithm} algorithm...")
                schedule = await self.optimize_schedule(
                    events, available_slots, algorithm=algorithm
                )
                results[algorithm] = schedule
        
        return results
    
    async def suggest_optimal_slots(self, event: HearingEvent,
                                  existing_schedule: Schedule,
                                  num_suggestions: int = 5) -> List[Tuple[SchedulingSlot, float]]:
        """Suggest optimal slots for a new event given existing schedule."""
        
        # Find available slots
        used_slot_ids = set(existing_schedule.assignments.values())
        available_slots = [
            slot for slot in existing_schedule.slots 
            if slot.slot_id not in used_slot_ids and slot.can_accommodate(event)
        ]
        
        # Score each available slot
        slot_scores = []
        
        for slot in available_slots:
            # Create temporary assignment
            temp_assignments = existing_schedule.assignments.copy()
            temp_assignments[event.hearing_id] = slot.slot_id
            
            temp_schedule = Schedule(
                schedule_id="temp",
                assignments=temp_assignments,
                events=existing_schedule.events + [event],
                slots=existing_schedule.slots
            )
            
            # Evaluate temporary schedule
            score = await self._score_slot_assignment(event, slot, temp_schedule)
            slot_scores.append((slot, score))
        
        # Sort by score and return top suggestions
        slot_scores.sort(key=lambda x: x[1], reverse=True)
        return slot_scores[:num_suggestions]
    
    async def _score_slot_assignment(self, event: HearingEvent, 
                                   slot: SchedulingSlot, 
                                   schedule: Schedule) -> float:
        """Score the assignment of an event to a slot."""
        score = 0.0
        
        # Time preference score
        if event.date_time:
            time_diff = abs((slot.start_time - event.date_time).total_seconds() / 3600)
            score += max(0, 100 - time_diff * 10)  # Penalty for time difference
        
        # Check for conflicts
        conflicts = await self.conflict_detector.detect_advanced_conflicts(schedule.events)
        conflict_penalty = len(conflicts) * 50
        score -= conflict_penalty
        
        # Location compatibility
        if event.location and slot.location:
            if hasattr(event.location, 'court_name') and hasattr(slot.location, 'name'):
                if event.location.court_name in slot.location.name:
                    score += 30  # Bonus for same courthouse
        
        return score
    
    def get_scheduling_statistics(self, schedule: Schedule) -> Dict[str, Any]:
        """Get comprehensive statistics about a schedule."""
        assigned_events = schedule.get_assigned_events()
        unassigned_events = schedule.get_unassigned_events()
        
        # Calculate resource utilization
        resource_usage = {}
        for event, slot in assigned_events:
            for resource in slot.available_resources:
                resource_usage[resource] = resource_usage.get(resource, 0) + 1
        
        # Calculate time distribution
        time_distribution = {}
        for event, slot in assigned_events:
            hour = slot.start_time.hour
            time_distribution[hour] = time_distribution.get(hour, 0) + 1
        
        # Calculate event type distribution
        type_distribution = {}
        for event in schedule.events:
            event_type = event.hearing_type.value
            type_distribution[event_type] = type_distribution.get(event_type, 0) + 1
        
        return {
            'total_events': len(schedule.events),
            'assigned_events': len(assigned_events),
            'unassigned_events': len(unassigned_events),
            'assignment_rate': len(assigned_events) / max(len(schedule.events), 1) * 100,
            'conflicts': len(schedule.conflicts),
            'constraint_violations': len(schedule.constraint_violations),
            'objective_score': schedule.objective_score,
            'efficiency_score': schedule.efficiency_score,
            'total_travel_time': schedule.total_travel_time_minutes,
            'resource_utilization': resource_usage,
            'time_distribution': time_distribution,
            'event_type_distribution': type_distribution,
            'optimization_method': schedule.optimization_method,
            'optimization_time': schedule.optimization_time_seconds
        }


# Example usage
async def example_intelligent_scheduling():
    """Example usage of the intelligent scheduler."""
    
    from .travel_time_calculator import TravelTimeCalculator
    
    # Initialize components
    travel_calculator = TravelTimeCalculator()
    scheduler = IntelligentScheduler(travel_calculator)
    
    # Create sample events
    events = [
        HearingEvent(
            hearing_id="trial_1",
            case_number="CASE001",
            case_title="Smith v. Jones",
            hearing_type=HearingType.TRIAL,
            date_time=datetime(2024, 1, 15, 9, 0),
            end_time=datetime(2024, 1, 15, 17, 0),  # All day trial
            judge="Judge Johnson",
            status=HearingStatus.SCHEDULED
        ),
        HearingEvent(
            hearing_id="motion_1",
            case_number="CASE002",
            case_title="Brown v. Davis",
            hearing_type=HearingType.MOTION_HEARING,
            date_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 11, 0),
            judge="Judge Miller",
            status=HearingStatus.SCHEDULED
        ),
        HearingEvent(
            hearing_id="status_1",
            case_number="CASE003",
            case_title="Wilson v. Anderson",
            hearing_type=HearingType.STATUS_CONFERENCE,
            date_time=datetime(2024, 1, 15, 14, 0),
            end_time=datetime(2024, 1, 15, 14, 30),
            judge="Judge Johnson",
            status=HearingStatus.SCHEDULED
        ),
        HearingEvent(
            hearing_id="hearing_1",
            case_number="CASE004",
            case_title="Taylor v. Clark",
            hearing_type=HearingType.HEARING,
            date_time=datetime(2024, 1, 16, 9, 0),
            end_time=datetime(2024, 1, 16, 10, 0),
            judge="Judge White",
            status=HearingStatus.SCHEDULED
        )
    ]
    
    print("Intelligent Legal Scheduling System")
    print("=" * 50)
    
    # Optimize schedule using automatic algorithm selection
    print("Optimizing schedule with automatic algorithm selection...")
    schedule = await scheduler.optimize_schedule(events)
    
    print(f"\nOptimization Results:")
    print(f"Algorithm: {schedule.optimization_method}")
    print(f"Optimization time: {schedule.optimization_time_seconds:.2f} seconds")
    print(f"Events assigned: {len(schedule.assignments)}/{len(events)}")
    print(f"Objective score: {schedule.objective_score:.2f}")
    print(f"Conflicts: {len(schedule.conflicts)}")
    
    # Show assignments
    print(f"\nEvent Assignments:")
    print("-" * 30)
    assigned_events = schedule.get_assigned_events()
    for event, slot in assigned_events:
        print(f"• {event.case_title} ({event.hearing_type.value})")
        print(f"  → {slot.start_time.strftime('%Y-%m-%d %H:%M')} - {slot.end_time.strftime('%H:%M')}")
        print(f"  → {slot.location.name}")
        print()
    
    unassigned = schedule.get_unassigned_events()
    if unassigned:
        print(f"Unassigned Events ({len(unassigned)}):")
        for event in unassigned:
            print(f"• {event.case_title} ({event.hearing_type.value})")
    
    # Compare algorithms
    print("\nComparing Algorithms:")
    print("-" * 30)
    comparison_results = await scheduler.compare_algorithms(events)
    
    for algorithm, result in comparison_results.items():
        print(f"{algorithm.upper()}: "
              f"Score={result.objective_score:.2f}, "
              f"Assigned={len(result.assignments)}/{len(events)}, "
              f"Conflicts={len(result.conflicts)}, "
              f"Time={result.optimization_time_seconds:.2f}s")
    
    # Get detailed statistics
    print("\nDetailed Statistics:")
    print("-" * 30)
    stats = scheduler.get_scheduling_statistics(schedule)
    print(json.dumps(stats, indent=2))
    
    # Test slot suggestions for a new event
    new_event = HearingEvent(
        hearing_id="new_1",
        case_number="CASE005",
        case_title="New Case",
        hearing_type=HearingType.MOTION_HEARING,
        date_time=datetime(2024, 1, 16, 11, 0),
        status=HearingStatus.SCHEDULED
    )
    
    print(f"\nSlot Suggestions for New Event:")
    print("-" * 40)
    suggestions = await scheduler.suggest_optimal_slots(new_event, schedule)
    
    for i, (slot, score) in enumerate(suggestions, 1):
        print(f"{i}. {slot.start_time.strftime('%Y-%m-%d %H:%M')} - {slot.end_time.strftime('%H:%M')}")
        print(f"   Location: {slot.location.name}")
        print(f"   Score: {score:.1f}")
        print()


if __name__ == "__main__":
    asyncio.run(example_intelligent_scheduling())