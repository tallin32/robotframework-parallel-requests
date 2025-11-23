from typing import Optional, Any
from .tasks import RequestTask
from .transport.httpx_sync import HttpxSyncTransport
from .worker import WorkerPool


class ParallelRequests:
    """Robot Framework library exposing parallelized request keywords.

    All keywords are exposed with a `Parallel ` prefix (e.g. `Parallel Create Session`)
    to clearly signal parallel execution semantics.
    
    Args:
        worker_count: Number of worker threads. Default is 5.
    """

    ROBOT_LIBRARY_SCOPE = "TEST"

    def __init__(self, worker_count: int = 5):
        self.transport = HttpxSyncTransport()
        self.worker = WorkerPool(self.transport, max_workers=worker_count)

    def Parallel_Create_Session(self, alias: str = "default", base_url: Optional[str] = None, headers: Optional[dict] = None):
        """Parallel Create Session    alias    base_url=None    headers=None

        Create a named session (stored internally). For MVP this is a light wrapper that adjusts base URL and headers.
        """
        # For now, store base_url and headers on the transport in a simple way
        setattr(self.transport, "base_url", base_url)
        if headers:
            existing = getattr(self.transport, "default_headers", {}) or {}
            existing.update(headers)
            setattr(self.transport, "default_headers", existing)

    def Parallel_Queue_Request(self, method: str, url: str, id: Optional[str] = None, **kwargs) -> str:
        """Parallel Queue Request    method    url    id=None    **kwargs

        Queue a request to be sent by the worker pool. Returns a response id.
        """
        task = RequestTask(method=method, url=url, kwargs=kwargs)
        if id:
            task.id = id
        rid = self.worker.submit(task)
        return rid

    def Parallel_Start_Workers(self):
        """Parallel Start Workers  (workers are started lazily in MVP)"""
        # No-op for MVP since ThreadPool is ready on init
        return


    def Parallel_Wait_For_All_Requests(self, timeout: Optional[float] = None):
        """Parallel Wait For All Requests    timeout=None

        Wait for all queued requests to finish (optionally with timeout seconds)."""
        self.worker.wait_all(timeout=timeout)

    def Parallel_Wait_For_All_And_Get_Responses(self, timeout: Optional[float] = None):
        """Parallel Wait For All And Get Responses    timeout=None

        Wait for all queued requests to finish (optionally with timeout seconds) and return a list of response objects (or exceptions) in submission order.
        """
        self.worker.wait_all(timeout=timeout)
        # Return all responses in submission order
        return [self.worker.get_response(fid) for fid in self.worker._futures.keys()]

    def Parallel_Get_Response_Object(self, id: str) -> Any:
        """Parallel Get Response Object    id

        Return the underlying httpx.Response or an Exception for the given id."""
        return self.worker.get_response(id)

    def Parallel_Get_Response_Status(self, id: str):
        resp = self.worker.get_response(id)
        if isinstance(resp, Exception):
            raise resp
        return getattr(resp, "status_code", None)

    def Parallel_Get_Response_Body(self, id: str):
        resp = self.worker.get_response(id)
        if isinstance(resp, Exception):
            raise resp
        return resp.text

    def Parallel_Get_Response_JSON(self, id: str):
        resp = self.worker.get_response(id)
        if isinstance(resp, Exception):
            raise resp
        return resp.json()

    def Parallel_Set_Worker_Count(self, count: int):
        """Parallel Set Worker Count    count

        Adjust worker count (will recreate pool on next init in MVP)."""
        # For MVP, recreate worker
        self.worker.shutdown()
        self.worker = WorkerPool(self.transport, max_workers=count)

    def Parallel_Shutdown(self):
        """Parallel Shutdown

        Shutdown the worker pool and transport clients."""
        self.worker.shutdown()
