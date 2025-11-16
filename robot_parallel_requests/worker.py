from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue, Empty
from threading import Event
from typing import Optional
import time

from .tasks import RequestTask
from .response_store import ResponseStore


class WorkerPool:
    def __init__(self, transport, max_workers: int = 5):
        self.transport = transport
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._store = ResponseStore()
        self._futures: dict[str, Future] = {}

    def submit(self, task: RequestTask) -> str:
        future = self._executor.submit(self._run_task, task)
        self._futures[task.id] = future
        return task.id

    def _run_task(self, task: RequestTask):
        try:
            resp = self.transport.send(task)
            self._store.set_response(task.id, resp)
        except Exception as exc:
            self._store.set_response(task.id, exc)

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
