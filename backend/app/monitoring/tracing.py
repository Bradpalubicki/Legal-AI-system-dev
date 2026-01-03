# =============================================================================
# Legal AI System - Distributed Tracing and APM
# =============================================================================
# Comprehensive distributed tracing system for tracking requests across
# legal document processing services, AI providers, and compliance workflows
# =============================================================================

import uuid
import time
import json
import asyncio
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import threading
from collections import defaultdict
import functools

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, DateTime, Float, Integer, JSON, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from ..database import get_db

logger = logging.getLogger(__name__)

# =============================================================================
# TRACE MODELS
# =============================================================================

Base = declarative_base()

class TraceSpan(Base):
    """Database model for storing trace spans."""
    __tablename__ = "trace_spans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(String(64), nullable=False, index=True)
    span_id = Column(String(32), nullable=False, index=True)
    parent_span_id = Column(String(32), nullable=True, index=True)
    
    # Span metadata
    operation_name = Column(String(255), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    component = Column(String(100), nullable=True)
    
    # Timing
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    duration_ms = Column(Float, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="ok")  # ok, error, timeout
    error_message = Column(Text, nullable=True)
    
    # Tags and metadata
    tags = Column(JSON, nullable=True)
    logs = Column(JSON, nullable=True)
    
    # Legal-specific fields
    client_id = Column(String(100), nullable=True, index=True)
    document_id = Column(String(100), nullable=True, index=True)
    document_type = Column(String(50), nullable=True)
    contains_pii = Column(Boolean, default=False)
    compliance_level = Column(String(20), nullable=True)  # public, confidential, restricted
    
    created_at = Column(DateTime, default=datetime.utcnow)

class TraceMetrics(Base):
    """Database model for storing trace-derived metrics."""
    __tablename__ = "trace_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(String(64), nullable=False, index=True)
    
    # Request metadata
    operation_name = Column(String(255), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    
    # Performance metrics
    total_duration_ms = Column(Float, nullable=False)
    span_count = Column(Integer, nullable=False)
    error_count = Column(Integer, nullable=False, default=0)
    
    # Service breakdown
    service_durations = Column(JSON, nullable=True)
    
    # Legal metrics
    document_processing_time_ms = Column(Float, nullable=True)
    ai_processing_time_ms = Column(Float, nullable=True)
    compliance_check_time_ms = Column(Float, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

# =============================================================================
# TRACE CONTEXT AND SPAN
# =============================================================================

@dataclass
class SpanContext:
    """Span context for distributed tracing."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)

@dataclass
class Span:
    """Represents a single trace span."""
    context: SpanContext
    operation_name: str
    service_name: str
    component: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = "ok"
    error_message: Optional[str] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    # Legal-specific attributes
    client_id: Optional[str] = None
    document_id: Optional[str] = None
    document_type: Optional[str] = None
    contains_pii: bool = False
    compliance_level: Optional[str] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.utcnow()
    
    def set_tag(self, key: str, value: Any):
        """Set a tag on the span."""
        self.tags[key] = value
    
    def set_error(self, error: Union[str, Exception]):
        """Mark the span as having an error."""
        self.status = "error"
        if isinstance(error, Exception):
            self.error_message = str(error)
            self.set_tag("error.type", type(error).__name__)
        else:
            self.error_message = error
        self.set_tag("error", True)
    
    def log_event(self, event: str, data: Optional[Dict[str, Any]] = None):
        """Log an event within the span."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event
        }
        if data:
            log_entry.update(data)
        self.logs.append(log_entry)
    
    def finish(self):
        """Finish the span."""
        if self.end_time is None:
            self.end_time = datetime.utcnow()
    
    def duration_ms(self) -> Optional[float]:
        """Get the span duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None
    
    def set_legal_context(
        self, 
        client_id: Optional[str] = None,
        document_id: Optional[str] = None,
        document_type: Optional[str] = None,
        contains_pii: bool = False,
        compliance_level: Optional[str] = None
    ):
        """Set legal-specific context on the span."""
        if client_id:
            self.client_id = client_id
            self.set_tag("legal.client_id", client_id)
        
        if document_id:
            self.document_id = document_id
            self.set_tag("legal.document_id", document_id)
        
        if document_type:
            self.document_type = document_type
            self.set_tag("legal.document_type", document_type)
        
        self.contains_pii = contains_pii
        self.set_tag("legal.contains_pii", contains_pii)
        
        if compliance_level:
            self.compliance_level = compliance_level
            self.set_tag("legal.compliance_level", compliance_level)

# =============================================================================
# TRACER IMPLEMENTATION
# =============================================================================

class Tracer:
    """Main tracer for creating and managing spans."""
    
    def __init__(self, service_name: str, component: Optional[str] = None):
        self.service_name = service_name
        self.component = component
        self._active_spans: Dict[str, Span] = {}
        self._context_stack = threading.local()
    
    def start_span(
        self,
        operation_name: str,
        parent_context: Optional[SpanContext] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> Span:
        """Start a new span."""
        # Generate span context
        if parent_context:
            trace_id = parent_context.trace_id
            parent_span_id = parent_context.span_id
        else:
            trace_id = self._generate_trace_id()
            parent_span_id = None
        
        span_id = self._generate_span_id()
        
        context = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            baggage=parent_context.baggage.copy() if parent_context else {}
        )
        
        # Create span
        span = Span(
            context=context,
            operation_name=operation_name,
            service_name=self.service_name,
            component=self.component
        )
        
        # Set initial tags
        if tags:
            span.tags.update(tags)
        
        # Store active span
        self._active_spans[span_id] = span
        
        return span
    
    def get_active_span(self) -> Optional[Span]:
        """Get the currently active span."""
        if hasattr(self._context_stack, 'span'):
            return self._context_stack.span
        return None
    
    def set_active_span(self, span: Optional[Span]):
        """Set the currently active span."""
        self._context_stack.span = span
    
    def finish_span(self, span: Span):
        """Finish and record a span."""
        span.finish()
        
        # Remove from active spans
        if span.context.span_id in self._active_spans:
            del self._active_spans[span.context.span_id]
        
        # Send to collector (implementation would vary)
        asyncio.create_task(self._record_span(span))
    
    async def _record_span(self, span: Span):
        """Record the span to storage."""
        try:
            # This would typically send to a tracing backend
            # For now, we'll store in our database
            await self._store_span_in_database(span)
            
        except Exception as e:
            logger.error(f"Failed to record span: {e}")
    
    async def _store_span_in_database(self, span: Span):
        """Store span in the database."""
        try:
            async with get_db() as db:
                trace_span = TraceSpan(
                    trace_id=span.context.trace_id,
                    span_id=span.context.span_id,
                    parent_span_id=span.context.parent_span_id,
                    operation_name=span.operation_name,
                    service_name=span.service_name,
                    component=span.component,
                    start_time=span.start_time,
                    end_time=span.end_time,
                    duration_ms=span.duration_ms(),
                    status=span.status,
                    error_message=span.error_message,
                    tags=span.tags,
                    logs=span.logs,
                    client_id=span.client_id,
                    document_id=span.document_id,
                    document_type=span.document_type,
                    contains_pii=span.contains_pii,
                    compliance_level=span.compliance_level
                )
                
                db.add(trace_span)
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to store span in database: {e}")
    
    def _generate_trace_id(self) -> str:
        """Generate a unique trace ID."""
        return uuid.uuid4().hex
    
    def _generate_span_id(self) -> str:
        """Generate a unique span ID."""
        return uuid.uuid4().hex[:16]

# =============================================================================
# CONTEXT MANAGERS AND DECORATORS
# =============================================================================

@contextmanager
def trace_operation(
    tracer: Tracer,
    operation_name: str,
    tags: Optional[Dict[str, Any]] = None,
    parent_context: Optional[SpanContext] = None
):
    """Context manager for tracing an operation."""
    span = tracer.start_span(operation_name, parent_context, tags)
    old_active_span = tracer.get_active_span()
    tracer.set_active_span(span)
    
    try:
        yield span
    except Exception as e:
        span.set_error(e)
        raise
    finally:
        tracer.finish_span(span)
        tracer.set_active_span(old_active_span)

@asynccontextmanager
async def async_trace_operation(
    tracer: Tracer,
    operation_name: str,
    tags: Optional[Dict[str, Any]] = None,
    parent_context: Optional[SpanContext] = None
):
    """Async context manager for tracing an operation."""
    span = tracer.start_span(operation_name, parent_context, tags)
    old_active_span = tracer.get_active_span()
    tracer.set_active_span(span)
    
    try:
        yield span
    except Exception as e:
        span.set_error(e)
        raise
    finally:
        tracer.finish_span(span)
        tracer.set_active_span(old_active_span)

def trace_function(
    operation_name: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None,
    service_name: str = "legal-ai-system"
):
    """Decorator for tracing function calls."""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer(service_name)
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            async with async_trace_operation(tracer, op_name, tags) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_tag("function.result_type", type(result).__name__)
                    return result
                except Exception as e:
                    span.set_tag("function.exception", str(e))
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer(service_name)
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with trace_operation(tracer, op_name, tags) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_tag("function.result_type", type(result).__name__)
                    return result
                except Exception as e:
                    span.set_tag("function.exception", str(e))
                    raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# =============================================================================
# LEGAL AI SPECIFIC TRACERS
# =============================================================================

class DocumentProcessingTracer:
    """Specialized tracer for document processing operations."""
    
    def __init__(self):
        self.tracer = get_tracer("document-processor")
    
    @asynccontextmanager
    async def trace_document_processing(
        self,
        document_id: str,
        document_type: str,
        client_id: str,
        operation: str,
        contains_pii: bool = False,
        compliance_level: str = "confidential"
    ):
        """Trace document processing with legal context."""
        tags = {
            "document.id": document_id,
            "document.type": document_type,
            "document.size_category": self._categorize_document_size(document_id),
            "legal.client_id": client_id,
            "legal.contains_pii": contains_pii,
            "legal.compliance_level": compliance_level
        }
        
        async with async_trace_operation(
            self.tracer,
            f"document.{operation}",
            tags
        ) as span:
            span.set_legal_context(
                client_id=client_id,
                document_id=document_id,
                document_type=document_type,
                contains_pii=contains_pii,
                compliance_level=compliance_level
            )
            
            span.log_event("document_processing_started", {
                "document_id": document_id,
                "operation": operation
            })
            
            try:
                yield span
                span.log_event("document_processing_completed")
            except Exception as e:
                span.log_event("document_processing_failed", {
                    "error": str(e)
                })
                raise
    
    def _categorize_document_size(self, document_id: str) -> str:
        """Categorize document by size for performance analysis."""
        # This would typically query the actual document size
        # For now, return a placeholder
        return "medium"

class AIServiceTracer:
    """Specialized tracer for AI service interactions."""
    
    def __init__(self):
        self.tracer = get_tracer("ai-service")
    
    @asynccontextmanager
    async def trace_ai_request(
        self,
        provider: str,
        model: str,
        operation: str,
        token_estimate: Optional[int] = None,
        context_contains_pii: bool = False
    ):
        """Trace AI service requests with cost and compliance tracking."""
        tags = {
            "ai.provider": provider,
            "ai.model": model,
            "ai.operation": operation,
            "ai.context_contains_pii": context_contains_pii
        }
        
        if token_estimate:
            tags["ai.estimated_tokens"] = token_estimate
        
        async with async_trace_operation(
            self.tracer,
            f"ai.{operation}",
            tags
        ) as span:
            start_time = time.time()
            span.log_event("ai_request_started", {
                "provider": provider,
                "model": model
            })
            
            try:
                yield span
                
                # Calculate and log performance metrics
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                span.set_tag("ai.response_time_ms", response_time)
                
                span.log_event("ai_request_completed", {
                    "response_time_ms": response_time
                })
                
            except Exception as e:
                span.log_event("ai_request_failed", {
                    "error": str(e)
                })
                
                # Categorize AI errors
                if "rate limit" in str(e).lower():
                    span.set_tag("ai.error_category", "rate_limit")
                elif "token" in str(e).lower():
                    span.set_tag("ai.error_category", "token_limit")
                else:
                    span.set_tag("ai.error_category", "general")
                
                raise

class ComplianceTracer:
    """Specialized tracer for compliance operations."""
    
    def __init__(self):
        self.tracer = get_tracer("compliance-checker")
    
    @asynccontextmanager
    async def trace_compliance_check(
        self,
        check_type: str,
        resource_type: str,
        resource_id: str,
        compliance_standards: List[str],
        client_id: Optional[str] = None
    ):
        """Trace compliance checking operations."""
        tags = {
            "compliance.check_type": check_type,
            "compliance.resource_type": resource_type,
            "compliance.resource_id": resource_id,
            "compliance.standards": ",".join(compliance_standards)
        }
        
        if client_id:
            tags["legal.client_id"] = client_id
        
        async with async_trace_operation(
            self.tracer,
            f"compliance.{check_type}",
            tags
        ) as span:
            span.log_event("compliance_check_started", {
                "check_type": check_type,
                "standards": compliance_standards
            })
            
            try:
                yield span
                span.log_event("compliance_check_completed")
            except Exception as e:
                span.log_event("compliance_check_failed", {
                    "error": str(e)
                })
                raise

# =============================================================================
# TRACE ANALYSIS AND METRICS
# =============================================================================

class TraceAnalyzer:
    """Analyzes traces to generate performance insights and metrics."""
    
    def __init__(self):
        self.performance_thresholds = {
            "document.extract_text": 5000,  # 5 seconds
            "document.analyze": 10000,      # 10 seconds
            "ai.summarize": 15000,          # 15 seconds
            "ai.classify": 5000,            # 5 seconds
            "compliance.privacy_scan": 3000  # 3 seconds
        }
    
    async def analyze_trace_performance(
        self,
        db: AsyncSession,
        trace_id: str
    ) -> Dict[str, Any]:
        """Analyze performance of a complete trace."""
        # Get all spans for the trace
        query = select(TraceSpan).where(
            TraceSpan.trace_id == trace_id
        ).order_by(TraceSpan.start_time)
        
        result = await db.execute(query)
        spans = result.scalars().all()
        
        if not spans:
            return {"error": "Trace not found"}
        
        # Calculate metrics
        total_duration = max(
            (span.end_time - span.start_time).total_seconds() * 1000
            for span in spans if span.end_time
        ) if spans else 0
        
        service_breakdown = defaultdict(float)
        operation_breakdown = defaultdict(list)
        
        for span in spans:
            if span.duration_ms:
                service_breakdown[span.service_name] += span.duration_ms
                operation_breakdown[span.operation_name].append(span.duration_ms)
        
        # Identify bottlenecks
        bottlenecks = []
        for operation, durations in operation_breakdown.items():
            avg_duration = sum(durations) / len(durations)
            threshold = self.performance_thresholds.get(operation, 10000)
            
            if avg_duration > threshold:
                bottlenecks.append({
                    "operation": operation,
                    "avg_duration_ms": avg_duration,
                    "threshold_ms": threshold,
                    "severity": "high" if avg_duration > threshold * 2 else "medium"
                })
        
        return {
            "trace_id": trace_id,
            "total_duration_ms": total_duration,
            "span_count": len(spans),
            "service_breakdown": dict(service_breakdown),
            "operation_breakdown": {
                op: {
                    "count": len(durations),
                    "avg_duration_ms": sum(durations) / len(durations),
                    "max_duration_ms": max(durations),
                    "min_duration_ms": min(durations)
                }
                for op, durations in operation_breakdown.items()
            },
            "bottlenecks": bottlenecks,
            "error_count": len([s for s in spans if s.status == "error"])
        }
    
    async def generate_service_metrics(
        self,
        db: AsyncSession,
        time_window: timedelta = timedelta(hours=24)
    ) -> Dict[str, Any]:
        """Generate service-level metrics from traces."""
        end_time = datetime.utcnow()
        start_time = end_time - time_window
        
        # Query spans in the time window
        query = select(TraceSpan).where(
            and_(
                TraceSpan.start_time >= start_time,
                TraceSpan.start_time <= end_time
            )
        )
        
        result = await db.execute(query)
        spans = result.scalars().all()
        
        # Calculate service metrics
        service_metrics = defaultdict(lambda: {
            "request_count": 0,
            "error_count": 0,
            "total_duration_ms": 0,
            "operations": defaultdict(lambda: {
                "count": 0,
                "error_count": 0,
                "total_duration_ms": 0
            })
        })
        
        for span in spans:
            service = span.service_name
            operation = span.operation_name
            
            service_metrics[service]["request_count"] += 1
            service_metrics[service]["operations"][operation]["count"] += 1
            
            if span.status == "error":
                service_metrics[service]["error_count"] += 1
                service_metrics[service]["operations"][operation]["error_count"] += 1
            
            if span.duration_ms:
                service_metrics[service]["total_duration_ms"] += span.duration_ms
                service_metrics[service]["operations"][operation]["total_duration_ms"] += span.duration_ms
        
        # Calculate averages and error rates
        for service, metrics in service_metrics.items():
            if metrics["request_count"] > 0:
                metrics["avg_duration_ms"] = metrics["total_duration_ms"] / metrics["request_count"]
                metrics["error_rate"] = metrics["error_count"] / metrics["request_count"]
            
            for operation, op_metrics in metrics["operations"].items():
                if op_metrics["count"] > 0:
                    op_metrics["avg_duration_ms"] = op_metrics["total_duration_ms"] / op_metrics["count"]
                    op_metrics["error_rate"] = op_metrics["error_count"] / op_metrics["count"]
        
        return dict(service_metrics)

# =============================================================================
# GLOBAL TRACER REGISTRY
# =============================================================================

_tracers: Dict[str, Tracer] = {}

def get_tracer(service_name: str, component: Optional[str] = None) -> Tracer:
    """Get or create a tracer for a service."""
    key = f"{service_name}:{component or 'default'}"
    
    if key not in _tracers:
        _tracers[key] = Tracer(service_name, component)
    
    return _tracers[key]

def init_tracing():
    """Initialize the tracing system."""
    logger.info("Initializing distributed tracing system")
    
    # Create default tracers for main services
    get_tracer("legal-ai-system", "api")
    get_tracer("document-processor")
    get_tracer("ai-service")
    get_tracer("compliance-checker")
    
    logger.info("Distributed tracing system initialized")

# Initialize on import
init_tracing()

# =============================================================================
# CONVENIENCE EXPORTS
# =============================================================================

document_tracer = DocumentProcessingTracer()
ai_tracer = AIServiceTracer()
compliance_tracer = ComplianceTracer()

__all__ = [
    "Tracer",
    "Span",
    "SpanContext",
    "TraceSpan",
    "TraceMetrics",
    "get_tracer",
    "trace_operation",
    "async_trace_operation",
    "trace_function",
    "document_tracer",
    "ai_tracer",
    "compliance_tracer",
    "TraceAnalyzer",
    "init_tracing"
]