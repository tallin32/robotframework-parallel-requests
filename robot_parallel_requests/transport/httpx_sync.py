import httpx
from typing import Any
from ..tasks import RequestTask
from .base import TransportBase


class HttpxSyncTransport(TransportBase):
    def __init__(self, timeout: float = 30.0):
        self._client = httpx.Client(timeout=timeout)

    def send(self, task: RequestTask) -> Any:
        # task.kwargs expected to be compatible with httpx.Client.request
        resp = self._client.request(task.method, task.url, **task.kwargs)
        return resp

    def close(self):
        try:
            self._client.close()
        except Exception:
            pass
