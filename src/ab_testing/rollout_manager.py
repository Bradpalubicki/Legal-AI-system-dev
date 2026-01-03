"""
Rollout Management for A/B Testing

Advanced rollout management system for gradual experiment deployment,
traffic ramping, and automated rollback mechanisms.
"""

import asyncio
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import statistics
import math

class RolloutStrategy(str, Enum):
    """Rollout strategy types"""
    IMMEDIATE = "immediate"
    GRADUAL = "gradual"
    CANARY = "canary"
    BLUE_GREEN = "blue_green"
    RING_BASED = "ring_based"
    GEOGRAPHIC = "geographic"
    DEMOGRAPHIC = "demographic"
    FEATURE_FLAG = "feature_flag"

class RolloutStatus(str, Enum):
    """Rollout status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"

class RolloutPhase(str, Enum):
    """Rollout phase types"""
    PREPARATION = "preparation"
    CANARY_PHASE = "canary_phase"
    GRADUAL_ROLLOUT = "gradual_rollout"
    FULL_DEPLOYMENT = "full_deployment"
    MONITORING = "monitoring"
    CLEANUP = "cleanup"

@dataclass
class RolloutPlan:
    """Rollout plan configuration"""
    plan_id: str
    experiment_id: str
    name: str
    description: str
    strategy: RolloutStrategy
    phases: List[Dict[str, Any]]
    success_criteria: Dict[str, Any]
    rollback_criteria: Dict[str, Any]
    traffic_increment: float = 10.0  # Percentage
    phase_duration: int = 3600  # seconds
    monitoring_window: int = 1800  # seconds
    auto_advance: bool = True
    auto_rollback: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class RolloutState:
    """Current rollout state"""
    plan_id: str
    status: RolloutStatus
    current_phase: int
    current_traffic: float
    start_time: datetime
    last_updated: datetime
    metrics_snapshot: Optional[Dict[str, float]] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None

@dataclass
class RolloutEvent:
    """Rollout event record"""
    event_id: str
    plan_id: str
    event_type: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)

class RolloutManager:
    """
    Advanced rollout management system for A/B testing experiments.
    
    Provides automated rollout execution, traffic ramping, monitoring,
    and rollback capabilities with multiple deployment strategies.
    """
    
    def __init__(self, metrics_collector=None, experiment_monitor=None):
        self.rollout_plans: Dict[str, RolloutPlan] = {}
        self.rollout_states: Dict[str, RolloutState] = {}
        self.rollout_history: List[RolloutEvent] = []
        
        # Dependencies
        self.metrics_collector = metrics_collector
        self.experiment_monitor = experiment_monitor
        
        # Rollout handlers
        self.strategy_handlers: Dict[RolloutStrategy, Callable] = {
            RolloutStrategy.GRADUAL: self._execute_gradual_rollout,
            RolloutStrategy.CANARY: self._execute_canary_rollout,
            RolloutStrategy.BLUE_GREEN: self._execute_blue_green_rollout,
            RolloutStrategy.RING_BASED: self._execute_ring_based_rollout,
            RolloutStrategy.GEOGRAPHIC: self._execute_geographic_rollout
        }
        
        # Background tasks
        self._rollout_task = None
        self._monitoring_task = None
        self._is_running = False
        
        # Traffic management
        self.traffic_controllers: Dict[str, Callable] = {}
        
        # Notification handlers
        self.notification_handlers: List[Callable] = []
    
    async def start(self):
        """Start the rollout management system."""
        if self._is_running:
            return
        
        self._is_running = True
        self._rollout_task = asyncio.create_task(self._rollout_execution_loop())
        self._monitoring_task = asyncio.create_task(self._rollout_monitoring_loop())
    
    async def stop(self):
        """Stop the rollout management system."""
        self._is_running = False
        
        if self._rollout_task:
            self._rollout_task.cancel()
            try:
                await self._rollout_task
            except asyncio.CancelledError:
                pass
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def create_rollout_plan(
        self,
        experiment_id: str,
        name: str,
        description: str,
        strategy: RolloutStrategy,
        target_traffic: float = 100.0,
        phases: Optional[List[Dict[str, Any]]] = None,
        success_criteria: Optional[Dict[str, Any]] = None,
        rollback_criteria: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Create a new rollout plan."""
        plan_id = f"rollout_{experiment_id}_{int(datetime.utcnow().timestamp())}"
        
        # Default phases based on strategy
        if phases is None:
            phases = self._generate_default_phases(strategy, target_traffic)
        
        # Default success criteria
        if success_criteria is None:
            success_criteria = {
                'min_conversion_rate': 0.01,
                'max_error_rate': 0.05,
                'min_sample_size': 1000
            }
        
        # Default rollback criteria
        if rollback_criteria is None:
            rollback_criteria = {
                'max_error_rate': 0.10,
                'min_conversion_rate_threshold': 0.5,  # 50% of baseline
                'max_response_time': 5000
            }
        
        plan = RolloutPlan(
            plan_id=plan_id,
            experiment_id=experiment_id,
            name=name,
            description=description,
            strategy=strategy,
            phases=phases,
            success_criteria=success_criteria,
            rollback_criteria=rollback_criteria,
            **kwargs
        )
        
        self.rollout_plans[plan_id] = plan
        
        # Create initial state
        self.rollout_states[plan_id] = RolloutState(
            plan_id=plan_id,
            status=RolloutStatus.PLANNED,
            current_phase=0,
            current_traffic=0.0,
            start_time=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        await self._log_rollout_event(
            plan_id, "plan_created", f"Rollout plan created: {name}"
        )
        
        return plan_id
    
    async def start_rollout(self, plan_id: str) -> bool:
        """Start executing a rollout plan."""
        if plan_id not in self.rollout_plans:
            return False
        
        state = self.rollout_states[plan_id]
        if state.status != RolloutStatus.PLANNED:
            return False
        
        # Update state
        state.status = RolloutStatus.IN_PROGRESS
        state.start_time = datetime.utcnow()
        state.last_updated = datetime.utcnow()
        
        await self._log_rollout_event(
            plan_id, "rollout_started", "Rollout execution started"
        )
        
        return True
    
    async def pause_rollout(self, plan_id: str) -> bool:
        """Pause a rollout."""
        if plan_id not in self.rollout_states:
            return False
        
        state = self.rollout_states[plan_id]
        if state.status != RolloutStatus.IN_PROGRESS:
            return False
        
        state.status = RolloutStatus.PAUSED
        state.last_updated = datetime.utcnow()
        
        await self._log_rollout_event(
            plan_id, "rollout_paused", "Rollout execution paused"
        )
        
        return True
    
    async def resume_rollout(self, plan_id: str) -> bool:
        """Resume a paused rollout."""
        if plan_id not in self.rollout_states:
            return False
        
        state = self.rollout_states[plan_id]
        if state.status != RolloutStatus.PAUSED:
            return False
        
        state.status = RolloutStatus.IN_PROGRESS
        state.last_updated = datetime.utcnow()
        
        await self._log_rollout_event(
            plan_id, "rollout_resumed", "Rollout execution resumed"
        )
        
        return True
    
    async def rollback(self, plan_id: str, reason: str = "") -> bool:
        """Rollback a rollout to previous state."""
        if plan_id not in self.rollout_plans:
            return False
        
        state = self.rollout_states[plan_id]
        plan = self.rollout_plans[plan_id]
        
        # Execute rollback
        try:
            await self._execute_rollback(plan, state)
            
            state.status = RolloutStatus.ROLLED_BACK
            state.last_updated = datetime.utcnow()
            
            await self._log_rollout_event(
                plan_id, "rollout_rolled_back", f"Rollout rolled back: {reason}"
            )
            
            # Send notifications
            await self._send_rollout_notification(
                plan_id, "rollback", f"Rollout {plan.name} has been rolled back: {reason}"
            )
            
            return True
            
        except Exception as e:
            await self._log_rollout_event(
                plan_id, "rollback_failed", f"Rollback failed: {str(e)}"
            )
            return False
    
    async def get_rollout_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get current rollout status."""
        if plan_id not in self.rollout_plans:
            return None
        
        plan = self.rollout_plans[plan_id]
        state = self.rollout_states[plan_id]
        
        # Get recent events
        recent_events = [
            event for event in self.rollout_history[-20:]
            if event.plan_id == plan_id
        ]
        
        # Calculate progress
        progress_percentage = 0.0
        if state.current_phase < len(plan.phases):
            phase_progress = (state.current_phase / len(plan.phases)) * 100
            traffic_progress = (state.current_traffic / 100.0) * (100 / len(plan.phases))
            progress_percentage = phase_progress + traffic_progress
        else:
            progress_percentage = 100.0
        
        return {
            'plan_id': plan_id,
            'experiment_id': plan.experiment_id,
            'name': plan.name,
            'strategy': plan.strategy.value,
            'status': state.status.value,
            'current_phase': state.current_phase,
            'total_phases': len(plan.phases),
            'current_traffic': state.current_traffic,
            'progress_percentage': progress_percentage,
            'start_time': state.start_time.isoformat(),
            'last_updated': state.last_updated.isoformat(),
            'metrics_snapshot': state.metrics_snapshot,
            'recent_events': [
                {
                    'type': event.event_type,
                    'message': event.message,
                    'timestamp': event.timestamp.isoformat()
                }
                for event in recent_events
            ],
            'errors': state.errors or [],
            'warnings': state.warnings or []
        }
    
    async def get_rollout_metrics(
        self,
        plan_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """Get rollout performance metrics."""
        if plan_id not in self.rollout_plans:
            return None
        
        plan = self.rollout_plans[plan_id]
        
        if not self.metrics_collector:
            return None
        
        # Get metrics from the experiment
        metrics = await self.metrics_collector.get_experiment_metrics(
            plan.experiment_id, start_time, end_time
        )
        
        # Calculate rollout-specific metrics
        rollout_metrics = {
            'experiment_metrics': metrics,
            'rollout_duration': 0,
            'traffic_ramp_rate': 0,
            'phase_success_rate': 0,
            'rollback_count': 0
        }
        
        state = self.rollout_states[plan_id]
        if state.start_time:
            rollout_metrics['rollout_duration'] = (
                datetime.utcnow() - state.start_time
            ).total_seconds()
        
        # Count rollback events
        rollback_events = [
            event for event in self.rollout_history
            if event.plan_id == plan_id and event.event_type == "rollout_rolled_back"
        ]
        rollout_metrics['rollback_count'] = len(rollback_events)
        
        return rollout_metrics
    
    async def register_traffic_controller(
        self,
        experiment_id: str,
        controller_func: Callable[[str, float], bool]
    ) -> bool:
        """Register a traffic controller for an experiment."""
        self.traffic_controllers[experiment_id] = controller_func
        return True
    
    async def register_notification_handler(
        self,
        handler_func: Callable[[str, str, str], None]
    ) -> bool:
        """Register a notification handler."""
        self.notification_handlers.append(handler_func)
        return True
    
    def _generate_default_phases(
        self,
        strategy: RolloutStrategy,
        target_traffic: float
    ) -> List[Dict[str, Any]]:
        """Generate default phases based on strategy."""
        phases = []
        
        if strategy == RolloutStrategy.IMMEDIATE:
            phases = [
                {
                    'name': 'immediate_deployment',
                    'traffic_percentage': target_traffic,
                    'duration_seconds': 60,
                    'success_criteria': {'min_sample_size': 100}
                }
            ]
        
        elif strategy == RolloutStrategy.GRADUAL:
            # 10% increments
            for i in range(1, int(target_traffic / 10) + 1):
                traffic = min(i * 10, target_traffic)
                phases.append({
                    'name': f'gradual_phase_{i}',
                    'traffic_percentage': traffic,
                    'duration_seconds': 3600,  # 1 hour per phase
                    'success_criteria': {
                        'min_sample_size': max(100, int(traffic * 10)),
                        'max_error_rate': 0.05
                    }
                })
        
        elif strategy == RolloutStrategy.CANARY:
            phases = [
                {
                    'name': 'canary_phase',
                    'traffic_percentage': 5.0,
                    'duration_seconds': 1800,  # 30 minutes
                    'success_criteria': {
                        'min_sample_size': 500,
                        'max_error_rate': 0.02,
                        'min_conversion_rate': 0.01
                    }
                },
                {
                    'name': 'full_deployment',
                    'traffic_percentage': target_traffic,
                    'duration_seconds': 3600,
                    'success_criteria': {
                        'min_sample_size': 1000,
                        'max_error_rate': 0.05
                    }
                }
            ]
        
        elif strategy == RolloutStrategy.RING_BASED:
            ring_percentages = [1, 5, 25, 50, target_traffic]
            for i, percentage in enumerate(ring_percentages, 1):
                phases.append({
                    'name': f'ring_{i}',
                    'traffic_percentage': percentage,
                    'duration_seconds': 1800,  # 30 minutes per ring
                    'success_criteria': {
                        'min_sample_size': max(50, int(percentage * 20)),
                        'max_error_rate': 0.05
                    }
                })
        
        return phases
    
    async def _rollout_execution_loop(self):
        """Background rollout execution loop."""
        while self._is_running:
            try:
                # Process active rollouts
                for plan_id, state in self.rollout_states.items():
                    if state.status == RolloutStatus.IN_PROGRESS:
                        await self._process_rollout_step(plan_id)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Rollout execution loop error: {e}")
                await asyncio.sleep(60)
    
    async def _rollout_monitoring_loop(self):
        """Background rollout monitoring loop."""
        while self._is_running:
            try:
                # Monitor active rollouts for rollback conditions
                for plan_id, state in self.rollout_states.items():
                    if state.status == RolloutStatus.IN_PROGRESS:
                        await self._check_rollback_conditions(plan_id)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Rollout monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    async def _process_rollout_step(self, plan_id: str):
        """Process a single rollout step."""
        plan = self.rollout_plans[plan_id]
        state = self.rollout_states[plan_id]
        
        if state.current_phase >= len(plan.phases):
            # Rollout completed
            state.status = RolloutStatus.COMPLETED
            state.last_updated = datetime.utcnow()
            
            await self._log_rollout_event(
                plan_id, "rollout_completed", "Rollout completed successfully"
            )
            
            await self._send_rollout_notification(
                plan_id, "completion", f"Rollout {plan.name} completed successfully"
            )
            return
        
        current_phase = plan.phases[state.current_phase]
        
        # Check if current phase duration has elapsed
        phase_start_time = state.last_updated
        phase_duration = timedelta(seconds=current_phase.get('duration_seconds', 3600))
        
        if datetime.utcnow() - phase_start_time >= phase_duration:
            # Check phase success criteria
            if await self._check_phase_success_criteria(plan_id, current_phase):
                # Advance to next phase
                await self._advance_to_next_phase(plan_id)
            else:
                # Phase failed, handle accordingly
                await self._handle_phase_failure(plan_id, current_phase)
    
    async def _check_phase_success_criteria(
        self,
        plan_id: str,
        phase: Dict[str, Any]
    ) -> bool:
        """Check if current phase meets success criteria."""
        plan = self.rollout_plans[plan_id]
        success_criteria = phase.get('success_criteria', {})
        
        if not self.metrics_collector:
            return True  # Assume success if no metrics collector
        
        # Get current metrics
        current_metrics = await self.metrics_collector.get_experiment_metrics(
            plan.experiment_id
        )
        
        # Check each criterion
        for criterion, threshold in success_criteria.items():
            if not await self._evaluate_success_criterion(
                criterion, threshold, current_metrics
            ):
                return False
        
        return True
    
    async def _evaluate_success_criterion(
        self,
        criterion: str,
        threshold: Any,
        metrics: Dict[str, Any]
    ) -> bool:
        """Evaluate a single success criterion."""
        if criterion == 'min_sample_size':
            total_samples = sum(
                variant_metrics.get('sample_size', {}).get('value', 0)
                for variant_metrics in metrics.values()
            )
            return total_samples >= threshold
        
        elif criterion == 'max_error_rate':
            max_error_rate = max(
                variant_metrics.get('error_rate', {}).get('value', 0)
                for variant_metrics in metrics.values()
            )
            return max_error_rate <= threshold
        
        elif criterion == 'min_conversion_rate':
            min_conversion_rate = min(
                variant_metrics.get('conversion_rate', {}).get('value', 1.0)
                for variant_metrics in metrics.values()
            )
            return min_conversion_rate >= threshold
        
        # Add more criteria as needed
        return True
    
    async def _advance_to_next_phase(self, plan_id: str):
        """Advance rollout to the next phase."""
        plan = self.rollout_plans[plan_id]
        state = self.rollout_states[plan_id]
        
        state.current_phase += 1
        state.last_updated = datetime.utcnow()
        
        if state.current_phase < len(plan.phases):
            next_phase = plan.phases[state.current_phase]
            target_traffic = next_phase.get('traffic_percentage', 0)
            
            # Update traffic allocation
            await self._update_traffic_allocation(plan.experiment_id, target_traffic)
            
            state.current_traffic = target_traffic
            
            await self._log_rollout_event(
                plan_id, 
                "phase_advanced", 
                f"Advanced to phase {state.current_phase + 1}: {next_phase.get('name', 'Unnamed')}"
            )
    
    async def _handle_phase_failure(self, plan_id: str, phase: Dict[str, Any]):
        """Handle phase failure."""
        plan = self.rollout_plans[plan_id]
        
        if plan.auto_rollback:
            await self.rollback(plan_id, f"Phase {phase.get('name', 'unknown')} failed success criteria")
        else:
            # Pause rollout for manual intervention
            await self.pause_rollout(plan_id)
            
            await self._log_rollout_event(
                plan_id,
                "phase_failed",
                f"Phase {phase.get('name', 'unknown')} failed success criteria"
            )
    
    async def _check_rollback_conditions(self, plan_id: str):
        """Check if rollback conditions are met."""
        plan = self.rollout_plans[plan_id]
        rollback_criteria = plan.rollback_criteria
        
        if not rollback_criteria or not self.metrics_collector:
            return
        
        # Get current metrics
        current_metrics = await self.metrics_collector.get_experiment_metrics(
            plan.experiment_id
        )
        
        # Check rollback criteria
        for criterion, threshold in rollback_criteria.items():
            if await self._should_rollback_for_criterion(
                criterion, threshold, current_metrics
            ):
                await self.rollback(plan_id, f"Rollback criterion triggered: {criterion}")
                return
    
    async def _should_rollback_for_criterion(
        self,
        criterion: str,
        threshold: Any,
        metrics: Dict[str, Any]
    ) -> bool:
        """Check if a rollback criterion is met."""
        if criterion == 'max_error_rate':
            max_error_rate = max(
                variant_metrics.get('error_rate', {}).get('value', 0)
                for variant_metrics in metrics.values()
            )
            return max_error_rate > threshold
        
        elif criterion == 'min_conversion_rate_threshold':
            # Check if conversion rate dropped below X% of baseline
            control_conversion = metrics.get('control', {}).get('conversion_rate', {}).get('value', 0)
            
            for variant_id, variant_metrics in metrics.items():
                if variant_id == 'control':
                    continue
                
                variant_conversion = variant_metrics.get('conversion_rate', {}).get('value', 0)
                
                if control_conversion > 0:
                    ratio = variant_conversion / control_conversion
                    if ratio < threshold:
                        return True
        
        elif criterion == 'max_response_time':
            max_response_time = max(
                variant_metrics.get('response_time', {}).get('value', 0)
                for variant_metrics in metrics.values()
            )
            return max_response_time > threshold
        
        return False
    
    async def _update_traffic_allocation(self, experiment_id: str, traffic_percentage: float):
        """Update traffic allocation for an experiment."""
        if experiment_id in self.traffic_controllers:
            controller = self.traffic_controllers[experiment_id]
            await controller(experiment_id, traffic_percentage)
    
    async def _execute_rollback(self, plan: RolloutPlan, state: RolloutState):
        """Execute rollback logic."""
        # Reset traffic to 0% for the experiment variant
        await self._update_traffic_allocation(plan.experiment_id, 0.0)
        
        # Reset state
        state.current_traffic = 0.0
        state.current_phase = 0
    
    # Strategy-specific execution methods
    async def _execute_gradual_rollout(self, plan: RolloutPlan, state: RolloutState):
        """Execute gradual rollout strategy."""
        # Default gradual rollout is handled by the general phase progression
        pass
    
    async def _execute_canary_rollout(self, plan: RolloutPlan, state: RolloutState):
        """Execute canary rollout strategy."""
        # Canary rollout uses specific phases with stricter success criteria
        pass
    
    async def _execute_blue_green_rollout(self, plan: RolloutPlan, state: RolloutState):
        """Execute blue-green rollout strategy."""
        # Blue-green involves parallel environments
        # This would require more complex infrastructure coordination
        pass
    
    async def _execute_ring_based_rollout(self, plan: RolloutPlan, state: RolloutState):
        """Execute ring-based rollout strategy."""
        # Ring-based rollout uses user cohorts/segments
        pass
    
    async def _execute_geographic_rollout(self, plan: RolloutPlan, state: RolloutState):
        """Execute geographic rollout strategy."""
        # Geographic rollout targets specific regions
        pass
    
    async def _log_rollout_event(
        self,
        plan_id: str,
        event_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log a rollout event."""
        event = RolloutEvent(
            event_id=f"{plan_id}_{event_type}_{int(datetime.utcnow().timestamp())}",
            plan_id=plan_id,
            event_type=event_type,
            message=message,
            details=details or {}
        )
        
        self.rollout_history.append(event)
        
        # Keep only recent history
        cutoff_time = datetime.utcnow() - timedelta(days=30)
        self.rollout_history = [
            e for e in self.rollout_history
            if e.timestamp > cutoff_time
        ]
    
    async def _send_rollout_notification(
        self,
        plan_id: str,
        notification_type: str,
        message: str
    ):
        """Send rollout notification."""
        for handler in self.notification_handlers:
            try:
                await handler(plan_id, notification_type, message)
            except Exception as e:
                print(f"Failed to send rollout notification: {e}")