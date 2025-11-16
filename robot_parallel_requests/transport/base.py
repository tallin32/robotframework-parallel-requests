from abc import ABC, abstractmethod
from typing import Any
from ..tasks import RequestTask


class TransportBase(ABC):
    @abstractmethod
    def send(self, task: RequestTask):
        """Send a RequestTask and return a response-like object or raise."""
