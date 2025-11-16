from typing import Dict, Any, Optional


class ResponseStore:
    """Simple in-memory store for responses and exceptions keyed by id."""

    def __init__(self):
        self._responses: Dict[str, Any] = {}

    def set_response(self, id: str, value: Any) -> None:
        self._responses[id] = value

    def get(self, id: str) -> Optional[Any]:
        return self._responses.get(id)

    def all_ids(self):
        return list(self._responses.keys())

    def clear(self):
        self._responses.clear()
