#!/usr/bin/env python3
"""
Memory Management System
Legal AI System - Advanced Memory Monitoring and Leak Prevention

This module provides comprehensive memory management, monitoring, and
leak detection to ensure optimal system performance and stability.
"""

import gc
import sys
import psutil
import logging
import tracemalloc
import threading
import time
import weakref
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import functools

# Setup logging
logger = logging.getLogger('memory_management')

class MemoryState(str, Enum):
    """Memory usage states"""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AllocationCategory(str, Enum):
    """Memory allocation categories"""
    SYSTEM = "system"
    AI_MODEL = "ai_model"
    DATABASE = "database"
    CACHE = "cache"
    USER_DATA = "user_data"
    TEMPORARY = "temporary"

@dataclass
class MemorySnapshot:
    """Memory usage snapshot"""
    timestamp: datetime
    total_memory: int
    available_memory: int
    used_memory: int
    memory_percent: float
    process_memory: int
    gc_objects: int
    memory_state: MemoryState

@dataclass
class MemoryLeak:
    """Memory leak detection result"""
    leak_id: str
    function_name: str
    file_name: str
    line_number: int
    leak_size: int
    leak_rate: float  # bytes per second
    first_detected: datetime
    last_detected: datetime
    object_count: int
    severity: str

class MemoryManager:
    """
    Comprehensive memory management system with leak detection and cleanup
    """

    def __init__(self):
        self.logger = logger
        self.monitoring_enabled = True
        self.snapshots: List[MemorySnapshot] = []
        self.detected_leaks: List[MemoryLeak] = []
        self.memory_thresholds = {
            MemoryState.WARNING: 75.0,   # 75% memory usage
            MemoryState.CRITICAL: 85.0,  # 85% memory usage
            MemoryState.EMERGENCY: 95.0  # 95% memory usage
        }

        # Object tracking
        self.tracked_objects: Dict[str, List[weakref.ref]] = {}
        self.allocation_tracker: Dict[str, int] = {}

        # Start memory monitoring
        tracemalloc.start()
        self._start_monitoring_thread()

        # Initialize garbage collection optimization
        self._optimize_gc()

    def _start_monitoring_thread(self):
        """Start background memory monitoring thread"""
        def monitor_memory():
            while self.monitoring_enabled:
                try:
                    self._take_memory_snapshot()
                    self._detect_memory_leaks()
                    time.sleep(30)  # Monitor every 30 seconds
                except Exception as e:
                    self.logger.error(f"Memory monitoring error: {e}")

        thread = threading.Thread(target=monitor_memory, daemon=True)
        thread.start()

    def _take_memory_snapshot(self):
        """Take a memory usage snapshot"""
        try:
            # System memory info
            memory = psutil.virtual_memory()

            # Process memory info
            process = psutil.Process()
            process_memory = process.memory_info().rss

            # Garbage collection info
            gc_objects = len(gc.get_objects())

            # Determine memory state
            memory_state = self._determine_memory_state(memory.percent)

            snapshot = MemorySnapshot(
                timestamp=datetime.now(),
                total_memory=memory.total,
                available_memory=memory.available,
                used_memory=memory.used,
                memory_percent=memory.percent,
                process_memory=process_memory,
                gc_objects=gc_objects,
                memory_state=memory_state
            )

            self.snapshots.append(snapshot)

            # Keep only last 1000 snapshots
            if len(self.snapshots) > 1000:
                self.snapshots = self.snapshots[-1000:]

            # Take action based on memory state
            if memory_state != MemoryState.NORMAL:
                self._handle_memory_pressure(snapshot)

        except Exception as e:
            self.logger.error(f"Failed to take memory snapshot: {e}")

    def _determine_memory_state(self, memory_percent: float) -> MemoryState:
        """Determine memory state based on usage percentage"""
        if memory_percent >= self.memory_thresholds[MemoryState.EMERGENCY]:
            return MemoryState.EMERGENCY
        elif memory_percent >= self.memory_thresholds[MemoryState.CRITICAL]:
            return MemoryState.CRITICAL
        elif memory_percent >= self.memory_thresholds[MemoryState.WARNING]:
            return MemoryState.WARNING
        else:
            return MemoryState.NORMAL

    def _handle_memory_pressure(self, snapshot: MemorySnapshot):
        """Handle high memory usage situations"""
        self.logger.warning(f"Memory pressure detected: {snapshot.memory_state.value} "
                           f"({snapshot.memory_percent:.1f}%)")

        if snapshot.memory_state == MemoryState.EMERGENCY:
            self.emergency_cleanup()
        elif snapshot.memory_state == MemoryState.CRITICAL:
            self.force_garbage_collection()
            self.cleanup_caches()
        elif snapshot.memory_state == MemoryState.WARNING:
            self.force_garbage_collection()

    def _detect_memory_leaks(self):
        """Detect potential memory leaks using tracemalloc"""
        try:
            if not tracemalloc.is_tracing():
                return

            # Get current tracemalloc snapshot
            current_snapshot = tracemalloc.take_snapshot()

            # Analyze top memory allocations
            top_stats = current_snapshot.statistics('lineno')

            for stat in top_stats[:10]:  # Check top 10 allocations
                self._analyze_allocation_for_leaks(stat)

        except Exception as e:
            self.logger.error(f"Memory leak detection error: {e}")

    def _analyze_allocation_for_leaks(self, stat):
        """Analyze a memory allocation for potential leaks"""
        try:
            allocation_key = f"{stat.traceback.format()}"
            current_size = stat.size

            # Track allocation growth
            if allocation_key in self.allocation_tracker:
                previous_size = self.allocation_tracker[allocation_key]
                growth = current_size - previous_size

                # If allocation grew significantly, flag as potential leak
                if growth > 1024 * 1024:  # 1MB growth threshold
                    self._flag_potential_leak(stat, growth)

            self.allocation_tracker[allocation_key] = current_size

        except Exception as e:
            self.logger.error(f"Allocation analysis error: {e}")

    def _flag_potential_leak(self, stat, growth):
        """Flag a potential memory leak"""
        try:
            leak_id = f"leak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Extract frame information
            frame = stat.traceback[0] if stat.traceback else None
            function_name = frame.filename.split('/')[-1] if frame else "unknown"
            file_name = frame.filename if frame else "unknown"
            line_number = frame.lineno if frame else 0

            leak = MemoryLeak(
                leak_id=leak_id,
                function_name=function_name,
                file_name=file_name,
                line_number=line_number,
                leak_size=growth,
                leak_rate=growth / 30.0,  # bytes per second (30s interval)
                first_detected=datetime.now(),
                last_detected=datetime.now(),
                object_count=stat.count,
                severity="medium" if growth < 10 * 1024 * 1024 else "high"
            )

            self.detected_leaks.append(leak)
            self.logger.warning(f"Potential memory leak detected: {leak_id} "
                               f"({growth / 1024 / 1024:.1f}MB growth)")

        except Exception as e:
            self.logger.error(f"Leak flagging error: {e}")

    def _optimize_gc(self):
        """Optimize garbage collection settings"""
        # Tune garbage collection thresholds
        gc.set_threshold(700, 10, 10)

        # Enable garbage collection debugging in development
        if __debug__:
            gc.set_debug(gc.DEBUG_UNCOLLECTABLE)

    def force_garbage_collection(self) -> Dict[str, int]:
        """Force garbage collection and return statistics"""
        try:
            # Force collection of all generations
            collected = {
                "gen0": gc.collect(0),
                "gen1": gc.collect(1),
                "gen2": gc.collect(2)
            }

            total_collected = sum(collected.values())
            self.logger.info(f"Garbage collection completed: {total_collected} objects collected")

            return collected

        except Exception as e:
            self.logger.error(f"Garbage collection error: {e}")
            return {"error": 0}

    def cleanup_caches(self):
        """Clean up various caches to free memory"""
        try:
            # Clear Python caches
            sys.intern.__dict__.clear()

            # Clear any application-specific caches
            self._clear_application_caches()

            self.logger.info("Cache cleanup completed")

        except Exception as e:
            self.logger.error(f"Cache cleanup error: {e}")

    def _clear_application_caches(self):
        """Clear application-specific caches"""
        # This would clear application-specific caches
        # For now, just a placeholder
        pass

    def emergency_cleanup(self):
        """Emergency memory cleanup procedures"""
        try:
            self.logger.critical("Emergency memory cleanup initiated")

            # Force aggressive garbage collection
            for i in range(3):
                self.force_garbage_collection()

            # Clear all caches
            self.cleanup_caches()

            # Clear tracking data
            self.snapshots = self.snapshots[-100:]  # Keep only last 100 snapshots
            self.detected_leaks = self.detected_leaks[-50:]  # Keep only last 50 leaks

            # Clear weak references
            for category in self.tracked_objects:
                self.tracked_objects[category] = [ref for ref in self.tracked_objects[category] if ref() is not None]

            self.logger.critical("Emergency cleanup completed")

        except Exception as e:
            self.logger.error(f"Emergency cleanup error: {e}")

    def track_object(self, obj: Any, category: AllocationCategory = AllocationCategory.SYSTEM):
        """Track an object for memory monitoring"""
        try:
            if category.value not in self.tracked_objects:
                self.tracked_objects[category.value] = []

            # Use weak reference to avoid preventing garbage collection
            weak_ref = weakref.ref(obj)
            self.tracked_objects[category.value].append(weak_ref)

        except Exception as e:
            self.logger.error(f"Object tracking error: {e}")

    def untrack_object(self, obj: Any, category: AllocationCategory = AllocationCategory.SYSTEM):
        """Remove an object from tracking"""
        try:
            if category.value in self.tracked_objects:
                # Remove weak references to the object
                self.tracked_objects[category.value] = [
                    ref for ref in self.tracked_objects[category.value]
                    if ref() is not obj
                ]

        except Exception as e:
            self.logger.error(f"Object untracking error: {e}")

    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        try:
            if not self.snapshots:
                return {"error": "No memory snapshots available"}

            latest_snapshot = self.snapshots[-1]

            # Calculate trends
            if len(self.snapshots) >= 2:
                previous_snapshot = self.snapshots[-2]
                memory_trend = latest_snapshot.memory_percent - previous_snapshot.memory_percent
                object_trend = latest_snapshot.gc_objects - previous_snapshot.gc_objects
            else:
                memory_trend = 0
                object_trend = 0

            # Count tracked objects
            tracked_count = {}
            for category, refs in self.tracked_objects.items():
                tracked_count[category] = len([ref for ref in refs if ref() is not None])

            return {
                "current_memory_usage": {
                    "total_mb": latest_snapshot.total_memory / 1024 / 1024,
                    "used_mb": latest_snapshot.used_memory / 1024 / 1024,
                    "available_mb": latest_snapshot.available_memory / 1024 / 1024,
                    "percent": latest_snapshot.memory_percent,
                    "state": latest_snapshot.memory_state.value
                },
                "process_memory_mb": latest_snapshot.process_memory / 1024 / 1024,
                "gc_objects": latest_snapshot.gc_objects,
                "trends": {
                    "memory_change_percent": memory_trend,
                    "object_count_change": object_trend
                },
                "tracked_objects": tracked_count,
                "detected_leaks": len(self.detected_leaks),
                "total_snapshots": len(self.snapshots)
            }

        except Exception as e:
            self.logger.error(f"Statistics generation error: {e}")
            return {"error": str(e)}

    def get_leak_report(self) -> List[Dict[str, Any]]:
        """Get detailed memory leak report"""
        return [asdict(leak) for leak in self.detected_leaks]

    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring_enabled = False
        tracemalloc.stop()

# Global memory manager instance
memory_manager = MemoryManager()

def monitor_memory_usage(category: AllocationCategory = AllocationCategory.SYSTEM):
    """Decorator to monitor memory usage of functions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Track memory before function execution
            start_memory = psutil.Process().memory_info().rss

            try:
                result = func(*args, **kwargs)

                # Track memory after function execution
                end_memory = psutil.Process().memory_info().rss
                memory_delta = end_memory - start_memory

                # Log significant memory changes
                if abs(memory_delta) > 10 * 1024 * 1024:  # 10MB threshold
                    logger.info(f"Function {func.__name__} memory change: "
                               f"{memory_delta / 1024 / 1024:.1f}MB")

                return result

            except Exception as e:
                # Still log memory usage on error
                end_memory = psutil.Process().memory_info().rss
                memory_delta = end_memory - start_memory
                logger.error(f"Function {func.__name__} failed with memory change: "
                            f"{memory_delta / 1024 / 1024:.1f}MB")
                raise

        return wrapper
    return decorator

def cleanup_on_exit():
    """Cleanup function to be called on application exit"""
    try:
        memory_manager.force_garbage_collection()
        memory_manager.cleanup_caches()
        memory_manager.stop_monitoring()
        logger.info("Memory cleanup on exit completed")
    except Exception as e:
        logger.error(f"Cleanup on exit error: {e}")

# Context manager for memory-sensitive operations
class MemoryContext:
    """Context manager for memory-sensitive operations"""

    def __init__(self, category: AllocationCategory = AllocationCategory.TEMPORARY):
        self.category = category
        self.start_memory = 0
        self.objects_to_track = []

    def __enter__(self):
        self.start_memory = psutil.Process().memory_info().rss
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            # Cleanup tracked objects
            for obj in self.objects_to_track:
                memory_manager.untrack_object(obj, self.category)

            # Force garbage collection
            memory_manager.force_garbage_collection()

            # Log memory usage
            end_memory = psutil.Process().memory_info().rss
            memory_delta = end_memory - self.start_memory

            if abs(memory_delta) > 1024 * 1024:  # 1MB threshold
                logger.info(f"Memory context completed with change: "
                           f"{memory_delta / 1024 / 1024:.1f}MB")

        except Exception as e:
            logger.error(f"Memory context cleanup error: {e}")

    def track(self, obj: Any):
        """Track an object in this context"""
        self.objects_to_track.append(obj)
        memory_manager.track_object(obj, self.category)

# Example usage and testing
@monitor_memory_usage(AllocationCategory.TEMPORARY)
def memory_intensive_function():
    """Example memory-intensive function"""
    # Create a large list
    large_list = [i for i in range(100000)]
    return len(large_list)

def validate_memory_management():
    """Validate memory management system"""
    try:
        # Test memory monitoring
        with MemoryContext(AllocationCategory.TEMPORARY) as ctx:
            test_data = list(range(50000))
            ctx.track(test_data)

        # Test memory-monitored function
        result = memory_intensive_function()

        # Get memory statistics
        stats = memory_manager.get_memory_statistics()

        print("Memory management validation completed")
        print(f"Memory usage: {stats['current_memory_usage']['percent']:.1f}%")
        print(f"Process memory: {stats['process_memory_mb']:.1f}MB")
        print(f"GC objects: {stats['gc_objects']}")

        return True

    except Exception as e:
        print(f"Memory management validation failed: {e}")
        return False

if __name__ == "__main__":
    # Test the memory management system
    print("Testing Memory Management System...")
    print("=" * 50)

    if validate_memory_management():
        print("✓ Memory management system working correctly")

        # Display detailed statistics
        stats = memory_manager.get_memory_statistics()
        print(f"\nDetailed Memory Statistics:")
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
    else:
        print("✗ Memory management system validation failed")