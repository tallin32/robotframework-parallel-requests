from dataclasses import dataclass, field
from typing import Any, Dict, Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from .rate_limiter import TokenBucket
    from .retry import RetryPolicy


@dataclass
class RequestTask:
    method: str
    url: str
    kwargs: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_name: Optional[str] = None
    rate_limiter: Optional['TokenBucket'] = None
    retry_policy: Optional['RetryPolicy'] = None
