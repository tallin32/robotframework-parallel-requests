import httpx
from typing import Any, Optional
from ..tasks import RequestTask
from .base import TransportBase


def limits_for_workers(max_workers: int) -> httpx.Limits:
    """Size the connection pool so workers are not starved waiting for sockets."""
    workers = max(1, int(max_workers))
    # Keepalive slightly above workers so a rolling set of warm connections is available.
    keepalive = max(workers, min(workers + 5, workers * 2))
    max_connections = max(workers * 2, keepalive)
    return httpx.Limits(
        max_connections=max_connections,
        max_keepalive_connections=keepalive,
    )


class HttpxSyncTransport(TransportBase):
    def __init__(
        self,
        timeout: float = 30.0,
        max_workers: int = 5,
        limits: Optional[httpx.Limits] = None,
        http2: bool = False,
    ):
        self.max_workers = max(1, int(max_workers))
        self.http2 = bool(http2)
        self._limits = limits if limits is not None else limits_for_workers(self.max_workers)
        try:
            self._client = httpx.Client(
                timeout=timeout,
                limits=self._limits,
                http2=self.http2,
            )
        except ImportError as exc:
            if self.http2:
                raise ImportError(
                    "HTTP/2 support requires the optional 'h2' package. "
                    "Install with: pip install 'robotframework-parallel-requests[http2]'"
                ) from exc
            raise

    def send(self, task: RequestTask) -> Any:
        # task.kwargs expected to be compatible with httpx.Client.request
        resp = self._client.request(task.method, task.url, **task.kwargs)
        return resp

    def close(self):
        try:
            self._client.close()
        except Exception:
            pass
