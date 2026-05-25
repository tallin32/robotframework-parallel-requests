"""Metrics collection for parallel requests."""
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class RequestMetric:
    """Metrics for a single request."""
    request_id: str
    method: str
    url: str
    status_code: Optional[int] = None
    duration: Optional[float] = None  # seconds
    timestamp: float = field(default_factory=time.time)
    error: Optional[str] = None
    retries: int = 0


class MetricsCollector:
    """Thread-safe metrics collection for parallel requests."""
    
    def __init__(self):
        self._metrics: List[RequestMetric] = []
        self._lock = Lock()
    
    def record_request(self, metric: RequestMetric):
        """Record a request metric."""
        with self._lock:
            self._metrics.append(metric)
    
    def get_metrics(self) -> List[RequestMetric]:
        """Get all collected metrics."""
        with self._lock:
            return self._metrics.copy()
    
    def get_summary(self) -> Dict:
        """Get aggregated metrics summary."""
        with self._lock:
            if not self._metrics:
                return {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'avg_duration': 0.0,
                    'min_duration': 0.0,
                    'max_duration': 0.0,
                    'requests_per_second': 0.0,
                }
            
            successful = [m for m in self._metrics if m.status_code and 200 <= m.status_code < 300]
            failed = [m for m in self._metrics if m.error or (m.status_code and m.status_code >= 400)]
            durations = [m.duration for m in self._metrics if m.duration is not None]
            
            # Calculate request rate
            if len(self._metrics) > 1:
                time_span = max(m.timestamp for m in self._metrics) - min(m.timestamp for m in self._metrics)
                requests_per_second = len(self._metrics) / time_span if time_span > 0 else 0.0
            else:
                requests_per_second = 0.0
            
            return {
                'total_requests': len(self._metrics),
                'successful_requests': len(successful),
                'failed_requests': len(failed),
                'avg_duration': sum(durations) / len(durations) if durations else 0.0,
                'min_duration': min(durations) if durations else 0.0,
                'max_duration': max(durations) if durations else 0.0,
                'requests_per_second': requests_per_second,
                'status_code_counts': self._count_status_codes(),
            }
    
    def _count_status_codes(self) -> Dict[int, int]:
        """Count occurrences of each status code."""
        counts = {}
        for metric in self._metrics:
            if metric.status_code:
                counts[metric.status_code] = counts.get(metric.status_code, 0) + 1
        return counts
    
    def clear(self):
        """Clear all collected metrics."""
        with self._lock:
            self._metrics.clear()
