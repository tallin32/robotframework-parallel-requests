from threading import Lock
from typing import Dict, Any, Optional


class ResponseStore:
    """Simple in-memory store for responses and exceptions keyed by id."""

    def __init__(self):
        self._responses: Dict[str, Any] = {}
        self._lock = Lock()

    def set_response(self, id: str, value: Any) -> None:
        with self._lock:
            self._responses[id] = value

    def get(self, id: str) -> Optional[Any]:
        with self._lock:
            return self._responses.get(id)

    def has(self, id: str) -> bool:
        with self._lock:
            return id in self._responses

    def __contains__(self, id: str) -> bool:
        return self.has(id)

    def all_ids(self):
        with self._lock:
            return list(self._responses.keys())

    def clear(self):
        with self._lock:
            self._responses.clear()
