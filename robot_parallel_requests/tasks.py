from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import uuid


@dataclass
class RequestTask:
    method: str
    url: str
    kwargs: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_name: Optional[str] = None
