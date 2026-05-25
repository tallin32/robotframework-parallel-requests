import re
from pathlib import Path
from typing import Optional, Any, Dict

try:
    from importlib.metadata import PackageNotFoundError, version as get_installed_version
except ImportError:  # pragma: no cover
    from importlib_metadata import PackageNotFoundError, version as get_installed_version
from .tasks import RequestTask
from .transport.httpx_sync import HttpxSyncTransport
from .worker import WorkerPool
from .session import Session
from .rate_limiter import TokenBucket
from .retry import RetryPolicy
from .metrics import MetricsCollector


def _discover_library_version() -> str:
    """Resolve package version from installed metadata, then pyproject fallback."""
    try:
        return get_installed_version("robotframework-parallel-requests")
    except PackageNotFoundError:
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text(encoding="utf-8")
            match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
            if match:
                return match.group(1)
    return "0.0.0"


class ParallelRequests:
    """Robot Framework library exposing parallelized request keywords.

    All keywords are exposed with a `Parallel ` prefix (e.g. `Parallel Create Session`)
    to clearly signal parallel execution semantics.
    
    Args:
        worker_count: Number of worker threads. Default is 5.
    """

    ROBOT_LIBRARY_SCOPE = "TEST"
    ROBOT_LIBRARY_VERSION = _discover_library_version()
    ROBOT_LIBRARY_DOC_FORMAT = "REST"

    def __init__(self, worker_count: int = 5):
        self.transport = HttpxSyncTransport()
        self.sessions: Dict[str, Session] = {}
        self.rate_limiter: Optional[TokenBucket] = None
        self.retry_policy: Optional[RetryPolicy] = None
        self.metrics = MetricsCollector()
        self.worker = WorkerPool(self.transport, max_workers=worker_count, metrics_collector=self.metrics)

    def Parallel_Create_Session(self, alias: str = "default", base_url: Optional[str] = None, headers: Optional[dict] = None):
        """Parallel Create Session    alias    base_url=None    headers=None

        Create a named session with base URL and default headers.
        
        Args:
            alias: Session name for reference in requests
            base_url: Base URL prepended to relative URLs
            headers: Default headers merged with request headers
        """
        session = Session(alias=alias, base_url=base_url, headers=headers or {})
        self.sessions[alias] = session

    def Parallel_Queue_Request(self, method: str, url: str, session: Optional[str] = None, id: Optional[str] = None, **kwargs) -> str:
        """Parallel Queue Request    method    url    session=None    id=None    **kwargs

        Queue a request to be sent by the worker pool. Returns a response id.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: URL (can be relative if session has base_url)
            session: Session alias to use (optional)
            id: Custom response ID (optional, auto-generated if omitted)
            **kwargs: Additional httpx request parameters:
                - headers: dict of HTTP headers
                - params: dict of query parameters
                - json: JSON body data (auto-serialized)
                - data: form data or raw body
                - timeout: request timeout in seconds
                - follow_redirects: bool to follow redirects
                - auth: tuple of (username, password)
                - cookies: dict of cookies
        
        Example:
            ${id}=    Parallel Queue Request    GET    /users    session=api
            ${id}=    Parallel Queue Request    POST   /users    json={'name': 'John'}    headers={'X-API-Key': 'secret'}
        """
        # Apply rate limiting if configured
        if self.rate_limiter:
            self.rate_limiter.acquire()
        
        # Resolve session if provided
        if session:
            if session not in self.sessions:
                raise ValueError(f"Session alias not found: {session}")
            sess = self.sessions[session]
            url = sess.resolve_url(url)
            # Merge session headers with request headers
            request_headers = kwargs.get('headers', {})
            kwargs['headers'] = sess.merge_headers(request_headers)
        
        task = RequestTask(method=method, url=url, kwargs=kwargs)
        if id:
            task.id = id
        
        # Apply retry policy if configured
        if self.retry_policy:
            task.retry_policy = self.retry_policy
        
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
        """Parallel Get Response Status    id

        Return the HTTP status code for the given response ID.

        Raises the original exception if the request failed before a response was produced.
        Returns None if no status code attribute is present.
        """
        resp = self.worker.get_response(id)
        if isinstance(resp, Exception):
            raise resp
        return getattr(resp, "status_code", None)

    def Parallel_Get_Response_Body(self, id: str):
        """Parallel Get Response Body    id

        Return the response body (text) for the given response ID.

        Raises the original exception if the request failed.
        """
        resp = self.worker.get_response(id)
        if isinstance(resp, Exception):
            raise resp
        return resp.text

    def Parallel_Get_Response_JSON(self, id: str):
        """Parallel Get Response JSON    id

        Parse and return JSON payload for the given response ID.

        Raises the original exception if the request failed or a JSON decoding
        error if the body is not valid JSON.
        """
        resp = self.worker.get_response(id)
        if isinstance(resp, Exception):
            raise resp
        return resp.json()

    def Parallel_Set_Worker_Count(self, count: int):
        """Parallel Set Worker Count    count

        Adjust worker count (will recreate pool on next init in MVP)."""
        # Recreate worker and transport to avoid reusing a closed client.
        self.worker.shutdown()
        self.transport = HttpxSyncTransport()
        self.worker = WorkerPool(self.transport, max_workers=count, metrics_collector=self.metrics)

    def Parallel_Shutdown(self):
        """Parallel Shutdown

        Shutdown the worker pool and transport clients."""
        self.worker.shutdown()

    # HTTP Method Convenience Keywords
    
    def Parallel_GET(self, url: str, session: Optional[str] = None, id: Optional[str] = None, **kwargs) -> str:
        """Parallel GET    url    session=None    id=None    **kwargs
        
        Convenience keyword for GET requests. Equivalent to Parallel Queue Request with method=GET.
        """
        return self.Parallel_Queue_Request("GET", url, session=session, id=id, **kwargs)
    
    def Parallel_POST(self, url: str, session: Optional[str] = None, id: Optional[str] = None, **kwargs) -> str:
        """Parallel POST    url    session=None    id=None    **kwargs
        
        Convenience keyword for POST requests. Equivalent to Parallel Queue Request with method=POST.
        """
        return self.Parallel_Queue_Request("POST", url, session=session, id=id, **kwargs)
    
    def Parallel_PUT(self, url: str, session: Optional[str] = None, id: Optional[str] = None, **kwargs) -> str:
        """Parallel PUT    url    session=None    id=None    **kwargs
        
        Convenience keyword for PUT requests. Equivalent to Parallel Queue Request with method=PUT.
        """
        return self.Parallel_Queue_Request("PUT", url, session=session, id=id, **kwargs)
    
    def Parallel_DELETE(self, url: str, session: Optional[str] = None, id: Optional[str] = None, **kwargs) -> str:
        """Parallel DELETE    url    session=None    id=None    **kwargs
        
        Convenience keyword for DELETE requests. Equivalent to Parallel Queue Request with method=DELETE.
        """
        return self.Parallel_Queue_Request("DELETE", url, session=session, id=id, **kwargs)
    
    def Parallel_PATCH(self, url: str, session: Optional[str] = None, id: Optional[str] = None, **kwargs) -> str:
        """Parallel PATCH    url    session=None    id=None    **kwargs
        
        Convenience keyword for PATCH requests. Equivalent to Parallel Queue Request with method=PATCH.
        """
        return self.Parallel_Queue_Request("PATCH", url, session=session, id=id, **kwargs)
    
    def Parallel_HEAD(self, url: str, session: Optional[str] = None, id: Optional[str] = None, **kwargs) -> str:
        """Parallel HEAD    url    session=None    id=None    **kwargs
        
        Convenience keyword for HEAD requests. Equivalent to Parallel Queue Request with method=HEAD.
        """
        return self.Parallel_Queue_Request("HEAD", url, session=session, id=id, **kwargs)
    
    def Parallel_OPTIONS(self, url: str, session: Optional[str] = None, id: Optional[str] = None, **kwargs) -> str:
        """Parallel OPTIONS    url    session=None    id=None    **kwargs
        
        Convenience keyword for OPTIONS requests. Equivalent to Parallel Queue Request with method=OPTIONS.
        """
        return self.Parallel_Queue_Request("OPTIONS", url, session=session, id=id, **kwargs)
    
    # Rate Limiting & Retry Configuration
    
    def Parallel_Set_Rate_Limit(self, requests_per_second: float, burst_size: Optional[int] = None):
        """Parallel Set Rate Limit    requests_per_second    burst_size=None
        
        Configure rate limiting for queued requests using token bucket algorithm.
        
        Args:
            requests_per_second: Maximum requests per second (e.g., 1.75 for 105 req/min)
            burst_size: Maximum burst size (defaults to requests_per_second + 1)
        
        Example:
            # Limit to 105 requests per minute
            Parallel Set Rate Limit    1.75
            
            # Allow bursts of up to 10 requests
            Parallel Set Rate Limit    1.75    burst_size=10
        """
        self.rate_limiter = TokenBucket(rate=requests_per_second, burst_size=burst_size)
    
    def Parallel_Clear_Rate_Limit(self):
        """Parallel Clear Rate Limit
        
        Remove rate limiting configuration.
        """
        self.rate_limiter = None
    
    def Parallel_Set_Retry_Policy(self, max_retries: int = 3, backoff_factor: float = 2.0, retry_statuses: Optional[str] = None):
        """Parallel Set Retry Policy    max_retries=3    backoff_factor=2.0    retry_statuses=None
        
        Configure retry behavior with exponential backoff for failed requests.
        
        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for wait time between retries
            retry_statuses: Comma-separated status codes to retry (defaults to 429,500,502,503,504)
        
        Example:
            # Retry up to 3 times with 2x backoff on common error codes
            Parallel Set Retry Policy    max_retries=3    backoff_factor=2.0
            
            # Only retry on rate limit errors
            Parallel Set Retry Policy    max_retries=5    retry_statuses=429
        """
        statuses = None
        if retry_statuses:
            statuses = [int(s.strip()) for s in retry_statuses.split(',')]
        
        self.retry_policy = RetryPolicy(
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            retry_statuses=statuses
        )
    
    def Parallel_Clear_Retry_Policy(self):
        """Parallel Clear Retry Policy
        
        Remove retry policy configuration.
        """
        self.retry_policy = None
    
    # Metrics
    
    def Parallel_Get_Metrics(self) -> dict:
        """Parallel Get Metrics
        
        Get aggregated metrics summary for all completed requests.
        
        Returns dict with:
            - total_requests: Total number of requests
            - successful_requests: Requests with 2xx status
            - failed_requests: Requests with errors or 4xx/5xx status
            - avg_duration: Average request duration in seconds
            - min_duration: Minimum request duration
            - max_duration: Maximum request duration
            - requests_per_second: Actual request rate
            - status_code_counts: Dict of status code frequencies
        
        Example:
            ${metrics}=    Parallel Get Metrics
            Log    Total requests: ${metrics['total_requests']}
            Log    Success rate: ${metrics['successful_requests']} / ${metrics['total_requests']}
        """
        return self.metrics.get_summary()
    
    def Parallel_Clear_Metrics(self):
        """Parallel Clear Metrics
        
        Clear all collected metrics.
        """
        self.metrics.clear()
