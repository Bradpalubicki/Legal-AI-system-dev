"""
Real-time Metrics Collection System
Tracks all API calls, database queries, costs, and performance metrics
"""

import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Centralized metrics collection for monitoring dashboard
    Thread-safe singleton pattern for global metrics tracking
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True

        # Endpoint metrics: endpoint -> list of call records
        self.endpoint_calls: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Database query metrics
        self.db_queries: deque = deque(maxlen=500)

        # Error tracking
        self.errors: deque = deque(maxlen=500)

        # Cost tracking
        self.costs: Dict[str, float] = defaultdict(float)
        self.daily_cost = 0.0
        self.monthly_cost = 0.0

        # System metrics
        self.active_users: set = set()
        self.start_time = time.time()

        # WebSocket clients for real-time updates
        self.websocket_clients: List[Any] = []

        # Lock for thread safety
        self.data_lock = threading.Lock()

        logger.info("MetricsCollector initialized")

    def record_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Record an API call with all relevant metrics"""
        record = {
            'timestamp': datetime.utcnow().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'user_id': user_id,
            'error': error,
            'metadata': metadata or {},
            'cost': self._calculate_api_cost(duration_ms)
        }

        with self.data_lock:
            self.endpoint_calls[endpoint].append(record)

            # Track errors
            if status_code >= 400:
                self.errors.append(record)

            # Track users
            if user_id:
                self.active_users.add(user_id)

            # Accumulate costs
            self.daily_cost += record['cost']

        # Notify WebSocket clients (safely - don't crash if no event loop)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._broadcast_update('api_call', record))
        except RuntimeError:
            # No running event loop - skip broadcast
            pass

    def record_db_query(
        self,
        query_description: str,
        execution_time_ms: float,
        rows_affected: int,
        query_type: str = 'SELECT'
    ):
        """Record a database query execution"""
        cost = self._calculate_db_cost(query_type, rows_affected, execution_time_ms)

        record = {
            'timestamp': datetime.utcnow().isoformat(),
            'description': query_description,
            'execution_time_ms': execution_time_ms,
            'rows_affected': rows_affected,
            'query_type': query_type,
            'cost': cost,
            'frequency': self._calculate_frequency(query_description)
        }

        with self.data_lock:
            self.db_queries.append(record)
            self.daily_cost += cost

        # Notify WebSocket clients (safely - don't crash if no event loop)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._broadcast_update('db_query', record))
        except RuntimeError:
            pass

    def record_error(
        self,
        error_type: str,
        endpoint: str,
        message: str,
        stack_trace: Optional[str] = None,
        user_id: Optional[str] = None,
        request_data: Optional[Dict] = None
    ):
        """Record an error occurrence"""
        import uuid
        record = {
            'id': str(uuid.uuid4()),  # Unique error ID
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': error_type,
            'endpoint': endpoint,
            'message': message,
            'stack_trace': stack_trace,
            'user_id': user_id,
            'request_data': request_data,
            'status': 'unresolved',
            'acknowledged': False,
            'acknowledged_at': None,
            'acknowledged_by': None,
            'resolved': False,
            'resolved_at': None,
            'resolution': None
        }

        with self.data_lock:
            self.errors.append(record)

        # Notify WebSocket clients (safely - don't crash if no event loop)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._broadcast_update('error', record))
        except RuntimeError:
            pass

    def acknowledge_error(self, error_id: str, user_id: Optional[str] = None) -> bool:
        """Mark an error as acknowledged"""
        with self.data_lock:
            for error in self.errors:
                if error.get('id') == error_id:
                    error['acknowledged'] = True
                    error['acknowledged_at'] = datetime.utcnow().isoformat()
                    error['acknowledged_by'] = user_id
                    error['status'] = 'acknowledged'
                    return True
        return False

    def resolve_error(self, error_id: str, resolution: str, user_id: Optional[str] = None) -> bool:
        """Mark an error as resolved with a resolution description"""
        with self.data_lock:
            for error in self.errors:
                if error.get('id') == error_id:
                    error['resolved'] = True
                    error['resolved_at'] = datetime.utcnow().isoformat()
                    error['resolution'] = resolution
                    error['status'] = 'resolved'
                    return True
        return False

    def get_error_by_id(self, error_id: str) -> Optional[Dict]:
        """Get a specific error by ID"""
        with self.data_lock:
            for error in self.errors:
                if error.get('id') == error_id:
                    return error
        return None

    def get_endpoint_stats(self, time_window_hours: int = 1) -> List[Dict]:
        """Get statistics for all endpoints in the time window"""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)

        stats = []
        with self.data_lock:
            for endpoint, calls in self.endpoint_calls.items():
                # Filter calls within time window
                recent_calls = [
                    c for c in calls
                    if datetime.fromisoformat(c['timestamp']) > cutoff_time
                ]

                if not recent_calls:
                    continue

                # Calculate statistics
                durations = [c['duration_ms'] for c in recent_calls]
                errors = [c for c in recent_calls if c['status_code'] >= 400]

                avg_duration = sum(durations) / len(durations)
                status_info = self._get_endpoint_status(endpoint, durations, errors, recent_calls)

                stats.append({
                    'endpoint': endpoint,
                    'last_called': max(c['timestamp'] for c in recent_calls),
                    'avg_response_time': avg_duration,
                    'p95_response_time': self._percentile(durations, 95),
                    'p99_response_time': self._percentile(durations, 99),
                    'request_count': len(recent_calls),
                    'error_count': len(errors),
                    'error_rate': (len(errors) / len(recent_calls)) * 100,
                    'total_cost': sum(c['cost'] for c in recent_calls),
                    'status': status_info['status'],
                    'performance_note': status_info.get('note', None)
                })

        return sorted(stats, key=lambda x: x['request_count'], reverse=True)

    def get_db_query_stats(self, limit: int = 20) -> List[Dict]:
        """Get database query statistics"""
        with self.data_lock:
            queries = list(self.db_queries)[-limit:]

        # Group by description for aggregation
        grouped = defaultdict(list)
        for q in queries:
            grouped[q['description']].append(q)

        stats = []
        for description, query_list in grouped.items():
            execution_times = [q['execution_time_ms'] for q in query_list]

            stats.append({
                'description': description,
                'avg_execution_time': sum(execution_times) / len(execution_times),
                'max_execution_time': max(execution_times),
                'total_rows_affected': sum(q['rows_affected'] for q in query_list),
                'frequency': len(query_list),
                'total_cost': sum(q['cost'] for q in query_list),
                'cache_hit_rate': 0  # TODO: Implement cache tracking
            })

        return sorted(stats, key=lambda x: x['avg_execution_time'], reverse=True)

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        uptime_seconds = time.time() - self.start_time
        uptime_hours = uptime_seconds / 3600

        with self.data_lock:
            total_requests = sum(len(calls) for calls in self.endpoint_calls.values())
            total_errors = len(self.errors)

            # Calculate average response time across all endpoints
            all_durations = []
            for calls in self.endpoint_calls.values():
                all_durations.extend([c['duration_ms'] for c in calls])

            avg_response_time = sum(all_durations) / len(all_durations) if all_durations else 0

        return {
            'status': 'healthy' if total_errors < 10 else 'degraded',
            'uptime_hours': uptime_hours,
            'uptime_percentage': 99.9,  # TODO: Calculate from actual downtime
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate': (total_errors / total_requests * 100) if total_requests > 0 else 0,
            'avg_response_time': avg_response_time,
            'active_users': len(self.active_users),
            'daily_cost': round(self.daily_cost, 4),
            'monthly_cost_projection': round(self.daily_cost * 30, 2),
            'memory_usage_mb': 0,  # TODO: Implement actual memory tracking
            'cpu_usage_percent': 0,  # TODO: Implement actual CPU tracking
            'database_connections': 0,  # TODO: Implement connection pool tracking
            'queue_depth': 0  # TODO: Implement queue tracking
        }

    def get_recent_errors(self, limit: int = 20) -> List[Dict]:
        """Get recent errors for debugging"""
        with self.data_lock:
            return list(self.errors)[-limit:]

    def get_cost_breakdown(self, group_by: str = 'operation') -> Dict[str, float]:
        """Get cost breakdown by operation or service"""
        breakdown = defaultdict(float)

        with self.data_lock:
            for endpoint, calls in self.endpoint_calls.items():
                for call in calls:
                    breakdown[endpoint] += call['cost']

        return dict(breakdown)

    def register_websocket_client(self, client):
        """Register a WebSocket client for real-time updates"""
        self.websocket_clients.append(client)
        logger.info(f"WebSocket client registered. Total clients: {len(self.websocket_clients)}")

    def unregister_websocket_client(self, client):
        """Unregister a WebSocket client"""
        if client in self.websocket_clients:
            self.websocket_clients.remove(client)
            logger.info(f"WebSocket client unregistered. Total clients: {len(self.websocket_clients)}")

    async def _broadcast_update(self, update_type: str, data: Dict):
        """Broadcast update to all connected WebSocket clients"""
        if not self.websocket_clients:
            return

        message = {
            'type': update_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Remove disconnected clients
        disconnected = []
        for client in self.websocket_clients:
            try:
                await client.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket client: {e}")
                disconnected.append(client)

        for client in disconnected:
            self.unregister_websocket_client(client)

    def _calculate_api_cost(self, duration_ms: float) -> float:
        """Calculate cost of an API call"""
        # API Gateway: $0.0000035 per request
        # Lambda/Functions: $0.0000002 per 100ms
        gateway_cost = 0.0000035
        compute_cost = (duration_ms / 100) * 0.0000002
        return gateway_cost + compute_cost

    def _calculate_db_cost(self, query_type: str, rows: int, duration_ms: float) -> float:
        """Calculate cost of a database query"""
        # Base query cost
        base_cost = 0.00012

        # Data transfer cost ($0.00008 per KB, estimate 1 KB per row)
        data_cost = rows * 0.00008

        # Write operations cost more
        if query_type in ['INSERT', 'UPDATE', 'DELETE']:
            base_cost *= 1.5

        return base_cost + data_cost

    def _calculate_frequency(self, query_description: str) -> int:
        """Calculate how often a query is called per hour"""
        cutoff_time = datetime.utcnow() - timedelta(hours=1)

        with self.data_lock:
            count = sum(
                1 for q in self.db_queries
                if q['description'] == query_description
                and datetime.fromisoformat(q['timestamp']) > cutoff_time
            )

        return count

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _get_endpoint_status(self, endpoint: str, durations: List[float], errors: List[Dict], all_calls: List[Dict]) -> dict:
        """Determine endpoint health status with explanatory notes"""
        avg_duration = sum(durations) / len(durations) if durations else 0
        error_rate = len(errors) / len(all_calls) if all_calls else 0

        # AI processing endpoints are expected to be slow - use different thresholds
        ai_endpoints = {
            '/api/v1/documents/analyze-text': 'AI document analysis (GPT-4/Claude processing)',
            '/api/v1/documents/extract-text': 'Document text extraction and OCR',
            '/api/v1/qa/ask': 'AI Q&A processing with context retrieval',
            '/api/v1/defense/build': 'AI-powered defense strategy generation',
            '/api/v1/research/search': 'Legal research with AI summarization'
        }

        # Find if this is an AI endpoint and get its description
        ai_description = None
        for ai_path, description in ai_endpoints.items():
            if ai_path in endpoint:
                ai_description = description
                break

        result = {'status': 'healthy', 'note': None}

        if ai_description:
            # For AI endpoints, only check error rate, not response time
            if error_rate > 0.1:
                result['status'] = 'critical'
                result['note'] = f'High error rate ({error_rate:.1f}%) - {ai_description}'
            elif error_rate > 0.05:
                result['status'] = 'warning'
                result['note'] = f'Elevated error rate ({error_rate:.1f}%) - {ai_description}'
            elif avg_duration > 30000:  # > 30 seconds
                result['status'] = 'slow'
                result['note'] = f'Response time {avg_duration/1000:.1f}s (expected for {ai_description})'
            elif avg_duration > 10000:  # > 10 seconds
                result['status'] = 'normal'
                result['note'] = f'Response time {avg_duration/1000:.1f}s (normal for {ai_description})'
            else:
                result['status'] = 'healthy'
                result['note'] = f'Performing well - {ai_description}'
        else:
            # Standard endpoints - use strict thresholds with explanations
            if error_rate > 0.1:
                result['status'] = 'critical'
                result['note'] = f'High error rate: {error_rate:.1f}% of requests failing'
            elif avg_duration > 2000:
                result['status'] = 'critical'
                result['note'] = f'Very slow response time: {avg_duration:.0f}ms (expected < 2000ms)'
            elif error_rate > 0.05:
                result['status'] = 'warning'
                result['note'] = f'Elevated error rate: {error_rate:.1f}%'
            elif avg_duration > 1000:
                result['status'] = 'warning'
                result['note'] = f'Slow response time: {avg_duration:.0f}ms (expected < 1000ms)'
            elif avg_duration > 200:
                result['status'] = 'normal'
                result['note'] = f'Response time: {avg_duration:.0f}ms'
            else:
                result['status'] = 'healthy'
                result['note'] = f'Fast response: {avg_duration:.0f}ms'

        return result


# Global metrics collector instance
metrics_collector = MetricsCollector()
