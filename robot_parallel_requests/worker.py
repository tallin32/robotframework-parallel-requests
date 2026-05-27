from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue, Empty
from threading import Event
from typing import Optional
import time

from .tasks import RequestTask
from .response_store import ResponseStore
from .metrics import MetricsCollector, RequestMetric
from .retry import retry_with_backoff


class WorkerPool:
    def __init__(self, transport, max_workers: int = 5, metrics_collector: Optional[MetricsCollector] = None):
        self.transport = transport
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._store = ResponseStore()
        self._futures: dict[str, Future] = {}
        self.metrics_collector = metrics_collector

    def submit(self, task: RequestTask) -> str:
        future = self._executor.submit(self._run_task, task)
        self._futures[task.id] = future
        return task.id

    def _run_task(self, task: RequestTask):
        if task.rate_limiter:
            task.rate_limiter.acquire()

        start_time = time.time()
        metric = RequestMetric(
            request_id=task.id,
            method=task.method,
            url=task.url,
            timestamp=start_time
        )
        
        try:
            # Apply retry policy if configured
            if task.retry_policy:
                resp = retry_with_backoff(self.transport.send, task.retry_policy, task)
            else:
                resp = self.transport.send(task)
            
            duration = time.time() - start_time
            metric.duration = duration
            
            if hasattr(resp, 'status_code'):
                metric.status_code = resp.status_code
            
            self._store.set_response(task.id, resp)
            
        except Exception as exc:
            duration = time.time() - start_time
            metric.duration = duration
            metric.error = str(exc)
            self._store.set_response(task.id, exc)
        
        finally:
            if self.metrics_collector:
                self.metrics_collector.record_request(metric)

    def get_response(self, id: str):
        return self._store.get(id)

    def wait_all(self, timeout: Optional[float] = None):
        # Robot Framework may pass timeout as a string; convert if needed
        if timeout is not None and not isinstance(timeout, float):
            try:
                timeout = float(timeout)
            except Exception:
                raise ValueError(f"Timeout must be a float or convertible to float, got: {timeout!r}")
        start = time.time()
        for fid, fut in list(self._futures.items()):
            remaining = None
            if timeout is not None:
                elapsed = time.time() - start
                remaining = max(0, timeout - elapsed)
            try:
                fut.result(timeout=remaining)
            except Exception:
                pass

    def shutdown(self):
        try:
            self._executor.shutdown(wait=True)
        except Exception:
            pass
        try:
            if hasattr(self.transport, "close"):
                self.transport.close()
        except Exception:
            pass
