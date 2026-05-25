"""Session management for parallel requests."""
from typing import Optional, Dict
from dataclasses import dataclass, field


@dataclass
class Session:
    """Represents a named session with base URL and default headers."""
    alias: str
    base_url: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    
    def resolve_url(self, url: str) -> str:
        """Resolve URL against base_url if relative."""
        if self.base_url and not url.startswith(('http://', 'https://')):
            # Remove leading slash from url if base_url ends with slash
            base = self.base_url.rstrip('/')
            url_part = url.lstrip('/')
            return f"{base}/{url_part}"
        return url
    
    def merge_headers(self, request_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Merge session headers with request-specific headers."""
        merged = self.headers.copy()
        if request_headers:
            merged.update(request_headers)
        return merged
