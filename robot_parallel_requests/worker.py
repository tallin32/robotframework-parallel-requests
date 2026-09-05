from concurrent.futures import ThreadPoolExecutor, Future, wait, ALL_COMPLETED
from typing import Optional, List, Tuple
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
        self._pending_ids: List[str] = []
        self.metrics_collector = metrics_collector

    def submit(self, task: RequestTask) -> str:
        if task.id in self._futures or self._store.has(task.id):
            raise ValueError(f"Duplicate request id: {task.id}")

        future = self._executor.submit(self._run_task, task)
        self._futures[task.id] = future
        self._pending_ids.append(task.id)
        return task.id

    def _send_once(self, task: RequestTask):
        if task.rate_limiter:
            task.rate_limiter.acquire()
        return self.transport.send(task)

    def _run_task(self, task: RequestTask):
        start_time = time.perf_counter()
        wall_start = time.time()
        metric = RequestMetric(
            request_id=task.id,
            method=task.method,
            url=task.url,
            timestamp=wall_start,
        )
        retry_count = 0

        try:
            if task.retry_policy:
                resp, retry_count = retry_with_backoff(
                    self._send_once, task.retry_policy, task
                )
            else:
                resp = self._send_once(task)

            metric.duration = time.perf_counter() - start_time
            metric.retries = retry_count

            if hasattr(resp, 'status_code'):
                metric.status_code = resp.status_code

            self._store.set_response(task.id, resp)

        except Exception as exc:
            metric.duration = time.perf_counter() - start_time
            metric.retries = retry_count
            metric.error = str(exc)
            self._store.set_response(task.id, exc)

        finally:
            metric.completed_at = time.time()
            if self.metrics_collector:
                self.metrics_collector.record_request(metric)

    def get_response(self, id: str):
        if id not in self._futures and not self._store.has(id):
            raise KeyError(
                f"Unknown response id: {id!r}. Queue a request first or check the id."
            )
        if not self._store.has(id):
            future = self._futures.get(id)
            if future is not None and not future.done():
                raise LookupError(
                    f"Response for id {id!r} is not ready yet. "
                    f"Call Parallel Wait For All Requests first."
                )
            raise LookupError(f"No response stored for id: {id!r}")
        return self._store.get(id)

    def get_responses_in_order(self, ids: List[str]) -> list:
        # Soft lookup: incomplete timed-out ids may still be absent from the store.
        return [self._store.get(request_id) for request_id in ids]

    def wait_all(
        self,
        timeout: Optional[float] = None,
        cancel_pending: bool = True,
    ) -> Tuple[int, int, List[str]]:
        """Wait for pending requests. Returns (completed_count, incomplete_count, batch_ids)."""
        if timeout is not None and not isinstance(timeout, float):
            try:
                timeout = float(timeout)
            except Exception:
                raise ValueError(f"Timeout must be a float or convertible to float, got: {timeout!r}")

        batch_ids = list(self._pending_ids)
        if not batch_ids:
            return 0, 0, batch_ids

        pending_futures = [self._futures[request_id] for request_id in batch_ids]
        done, not_done = wait(pending_futures, timeout=timeout, return_when=ALL_COMPLETED)

        if cancel_pending and not_done:
            for future in not_done:
                future.cancel()

        completed_count = len(done)
        incomplete_count = len(not_done)
        self._pending_ids.clear()

        return completed_count, incomplete_count, batch_ids

    def shutdown(self):
        try:
            self._executor.shutdown(wait=True, cancel_futures=True)
        except TypeError:
            # cancel_futures added in Python 3.9
            try:
                self._executor.shutdown(wait=True)
            except Exception:
                pass
        except Exception:
            pass
        try:
            if hasattr(self.transport, "close"):
                self.transport.close()
        except Exception:
            pass
