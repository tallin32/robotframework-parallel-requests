import re
from pathlib import Path
from typing import Optional, Any, Dict, List, Sequence, Mapping
from robot.api import logger

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
        fail_on_timeout: If True, wait keywords raise when requests remain incomplete.
        http2: Enable HTTP/2 on the shared httpx client (requires the optional ``h2`` package).
        cancel_pending_on_timeout: Cancel futures that have not started when a wait times out.
    """

    ROBOT_LIBRARY_SCOPE = "TEST"
    ROBOT_LIBRARY_VERSION = _discover_library_version()
    ROBOT_LIBRARY_DOC_FORMAT = "REST"
    ROBOT_LIBRARY_LISTENER = "SELF"
    ROBOT_LISTENER_API_VERSION = 2

    def __init__(
        self,
        worker_count: int = 5,
        fail_on_timeout: bool = False,
        http2: bool = False,
        cancel_pending_on_timeout: bool = True,
    ):
        self.worker_count = int(worker_count)
        self.fail_on_timeout = bool(fail_on_timeout)
        self.http2 = bool(http2)
        self.cancel_pending_on_timeout = bool(cancel_pending_on_timeout)
        self.sessions: Dict[str, Session] = {}
        self.rate_limiter: Optional[TokenBucket] = None
        self.retry_policy: Optional[RetryPolicy] = None
        self.metrics = MetricsCollector()
        self.transport = self._build_transport(self.worker_count)
        self.worker = WorkerPool(
            self.transport,
            max_workers=self.worker_count,
            metrics_collector=self.metrics,
        )
        self._shutdown_done = False

    def _build_transport(self, worker_count: int) -> HttpxSyncTransport:
        return HttpxSyncTransport(max_workers=worker_count, http2=self.http2)

    def _end_test(self, name, attrs):  # Robot listener API
        self.Parallel_Shutdown()

    def _close(self):  # Robot library close hook
        self.Parallel_Shutdown()

    def _resolve_session_alias(self, session: Optional[str]) -> Optional[str]:
        if session:
            return session
        if "default" in self.sessions:
            return "default"
        return None

    def _apply_session(self, url: str, session: Optional[str], kwargs: dict) -> tuple:
        alias = self._resolve_session_alias(session)
        if not alias:
            return url, kwargs
        if alias not in self.sessions:
            raise ValueError(f"Session alias not found: {alias}")
        sess = self.sessions[alias]
        url = sess.resolve_url(url)
        request_headers = kwargs.get("headers", {})
        kwargs = dict(kwargs)
        kwargs["headers"] = sess.merge_headers(request_headers)
        return url, kwargs

    def Parallel_Create_Session(
        self,
        alias: str = "default",
        base_url: Optional[str] = None,
        headers: Optional[dict] = None,
    ):
        """Parallel Create Session    alias    base_url=None    headers=None

        Create a named session with base URL and default headers.

        When ``alias`` is ``default`` (the default), subsequent queue keywords
        use this session automatically if ``session=`` is omitted.

        Args:
            alias: Session name for reference in requests
            base_url: Base URL prepended to relative URLs
            headers: Default headers merged with request headers
        """
        session = Session(alias=alias, base_url=base_url, headers=headers or {})
        self.sessions[alias] = session
        logger.info(f"Session '{alias}' created with base_url='{base_url}' and headers={headers}")

    def Parallel_Queue_Request(
        self,
        method: str,
        url: str,
        session: Optional[str] = None,
        id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Parallel Queue Request    method    url    session=None    id=None    kwargs

        Queue a request to be sent by the worker pool and return a response id.

        method is the HTTP method (GET, POST, PUT, DELETE, etc.).
        url can be absolute or relative when a session base_url is provided.
        session is an optional session alias. If omitted and a ``default`` session
        exists, that session is used automatically.
        id is an optional custom response id.
        kwargs are forwarded to httpx.request (headers, params, json, data,
        timeout, follow_redirects, auth, cookies, and other valid httpx options).

        Example usage:
            Parallel Queue Request    GET    /users    session=api
            Parallel Queue Request    POST   /users    json={'name': 'John'}    headers={'X-API-Key': 'secret'}
        """
        resolved_session = self._resolve_session_alias(session)
        url, kwargs = self._apply_session(url, session, kwargs)

        task = RequestTask(method=method, url=url, kwargs=kwargs, session_name=resolved_session)
        if id:
            task.id = id

        # Rate limiting is enforced by workers at execution time, not enqueue time.
        if self.rate_limiter:
            task.rate_limiter = self.rate_limiter

        # Apply retry policy if configured
        if self.retry_policy:
            task.retry_policy = self.retry_policy

        rid = self.worker.submit(task)
        return rid

    def Parallel_Queue_Many(
        self,
        requests: Sequence[Any],
        session: Optional[str] = None,
    ) -> List[str]:
        """Parallel Queue Many    requests    session=None

        Queue many requests at once and return their response ids in order.

        ``requests`` is a list of specs. Each spec may be:

        - a mapping with ``method`` and ``url`` (plus optional ``id``, ``session``,
          and httpx kwargs such as ``headers``, ``json``, ``params``)
        - a two-item sequence ``[method, url]``

        The optional top-level ``session`` is used when a spec omits its own session.

        Example (Python-like list of dicts in Robot)::

            @{reqs}=    Create List
            ...    ${{"method": "GET", "url": "/users/1"}}
            ...    ${{"method": "GET", "url": "/users/2"}}
            ${ids}=    Parallel Queue Many    ${reqs}    session=api
        """
        if not isinstance(requests, Sequence) or isinstance(requests, (str, bytes)):
            raise TypeError(
                "requests must be a sequence of request specs (dicts or [method, url] pairs)"
            )

        ids: List[str] = []
        for index, spec in enumerate(requests):
            if isinstance(spec, Mapping):
                data = dict(spec)
                try:
                    method = data.pop("method")
                    url = data.pop("url")
                except KeyError as exc:
                    raise ValueError(
                        f"Request spec at index {index} missing required key: {exc.args[0]}"
                    ) from exc
                req_id = data.pop("id", None)
                req_session = data.pop("session", session)
                ids.append(
                    self.Parallel_Queue_Request(
                        method, url, session=req_session, id=req_id, **data
                    )
                )
            elif isinstance(spec, Sequence) and not isinstance(spec, (str, bytes)):
                if len(spec) < 2:
                    raise ValueError(
                        f"Request spec at index {index} must be [method, url], got: {spec!r}"
                    )
                method, url = spec[0], spec[1]
                ids.append(self.Parallel_Queue_Request(method, url, session=session))
            else:
                raise TypeError(
                    f"Unsupported request spec at index {index}: {type(spec).__name__}"
                )
        return ids

    def Parallel_Start_Workers(self):
        """Parallel Start Workers  (workers are started lazily in MVP)"""
        # No-op for MVP since ThreadPool is ready on init
        return

    def _wait_pending_and_warn(
        self,
        timeout: Optional[float] = None,
        fail_on_timeout: Optional[bool] = None,
    ) -> list:
        completed, incomplete, batch_ids = self.worker.wait_all(
            timeout=timeout,
            cancel_pending=self.cancel_pending_on_timeout,
        )
        if incomplete > 0:
            total = completed + incomplete
            message = (
                f"{incomplete} of {total} pending requests did not complete within "
                f"timeout={timeout!r}. Consider increasing the timeout."
            )
            should_fail = self.fail_on_timeout if fail_on_timeout is None else bool(fail_on_timeout)
            if should_fail:
                raise TimeoutError(message)
            logger.warn(message)
        return batch_ids

    def Parallel_Wait_For_All_Requests(
        self,
        timeout: Optional[float] = None,
        fail_on_timeout: Optional[bool] = None,
    ):
        """Parallel Wait For All Requests    timeout=None    fail_on_timeout=None

        Wait for all queued requests to finish (optionally with timeout seconds).

        By default logs a warning when the timeout expires. Pass
        ``fail_on_timeout=${True}`` (or set the library init argument) to raise
        ``TimeoutError`` instead. Futures that have not started yet are cancelled
        when a timeout occurs (configurable via ``cancel_pending_on_timeout``).
        """
        self._wait_pending_and_warn(timeout=timeout, fail_on_timeout=fail_on_timeout)

    def Parallel_Wait_For_All_And_Get_Responses(
        self,
        timeout: Optional[float] = None,
        fail_on_timeout: Optional[bool] = None,
    ):
        """Parallel Wait For All And Get Responses    timeout=None    fail_on_timeout=None

        Wait for all queued requests to finish (optionally with timeout seconds)
        and return a list of response objects (or exceptions) in submission order.
        """
        batch_ids = self._wait_pending_and_warn(timeout=timeout, fail_on_timeout=fail_on_timeout)
        return self.worker.get_responses_in_order(batch_ids)

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

        Adjust worker count (recreates pool and transport; connection limits follow)."""
        self.worker.shutdown()
        self._shutdown_done = False
        self.worker_count = int(count)
        self.transport = self._build_transport(self.worker_count)
        self.worker = WorkerPool(
            self.transport,
            max_workers=self.worker_count,
            metrics_collector=self.metrics,
        )

    def Parallel_Shutdown(self):
        """Parallel Shutdown

        Shutdown the worker pool and transport clients.

        Also invoked automatically at end of each test via the library listener.
        """
        if self._shutdown_done:
            return
        self.worker.shutdown()
        self._shutdown_done = True

    # HTTP Method Convenience Keywords

    def Parallel_GET(self, url: str, session: Optional[str] = None, id: Optional[str] = None, **kwargs) -> str:
        """Parallel GET    url    session=None    id=None    kwargs

        Convenience keyword for GET requests. Equivalent to Parallel Queue Request with method=GET.
        """
        return self.Parallel_Queue_Request("GET", url, session=session, id=id, **kwargs)

    def Parallel_POST(self, url: str, session: Optional[str] = None, id: Optional[str] = None, **kwargs) -> str:
        """Parallel POST    url    session=None    id=None    kwargs

        Convenience keyword for POST requests. Equivalent to Parallel Queue Request with method=POST.
        """
        return self.Parallel_Queue_Request("POST", url, session=session, id=id, **kwargs)

    def Parallel_PUT(self, url: str, session: Optional[str] = None, id: Optional[str] = None, **kwargs) -> str:
        """Parallel PUT    url    session=None    id=None    kwargs

        Convenience keyword for PUT requests. Equivalent to Parallel Queue Request with method=PUT.
        """
        return self.Parallel_Queue_Request("PUT", url, session=session, id=id, **kwargs)

    def Parallel_DELETE(self, url: str, session: Optional[str] = None, id: Optional[str] = None, **kwargs) -> str:
        """Parallel DELETE    url    session=None    id=None    kwargs

        Convenience keyword for DELETE requests. Equivalent to Parallel Queue Request with method=DELETE.
        """
        return self.Parallel_Queue_Request("DELETE", url, session=session, id=id, **kwargs)

    def Parallel_PATCH(self, url: str, session: Optional[str] = None, id: Optional[str] = None, **kwargs) -> str:
        """Parallel PATCH    url    session=None    id=None    kwargs

        Convenience keyword for PATCH requests. Equivalent to Parallel Queue Request with method=PATCH.
        """
        return self.Parallel_Queue_Request("PATCH", url, session=session, id=id, **kwargs)

    def Parallel_HEAD(self, url: str, session: Optional[str] = None, id: Optional[str] = None, **kwargs) -> str:
        """Parallel HEAD    url    session=None    id=None    kwargs

        Convenience keyword for HEAD requests. Equivalent to Parallel Queue Request with method=HEAD.
        """
        return self.Parallel_Queue_Request("HEAD", url, session=session, id=id, **kwargs)

    def Parallel_OPTIONS(self, url: str, session: Optional[str] = None, id: Optional[str] = None, **kwargs) -> str:
        """Parallel OPTIONS    url    session=None    id=None    kwargs

        Convenience keyword for OPTIONS requests. Equivalent to Parallel Queue Request with method=OPTIONS.
        """
        return self.Parallel_Queue_Request("OPTIONS", url, session=session, id=id, **kwargs)

    # Rate Limiting & Retry Configuration

    def Parallel_Set_Rate_Limit(self, requests: float, per: str = "second", burst_size: Optional[int] = None):
        """Parallel Set Rate Limit    requests    per="second"    burst_size=None

        Configure rate limiting for queued requests using token bucket algorithm.

        Args:
            requests: Maximum requests in the selected unit (e.g., 1.75 per second, 105 per minute)
            per: Time unit for rate limiting (e.g., "second", "minute")
            burst_size: Maximum burst size (defaults to requests + 1)

        Example usage:
            Parallel Set Rate Limit    1.75
            Parallel Set Rate Limit    1.75    burst_size=10
            Parallel Set Rate Limit    105    per="minute"
        """
        if requests <= 0:
            raise ValueError(f"Rate limit requests must be positive, got: {requests}")

        # Calculate rate in tokens per second based on 'per' unit
        unit_multipliers = {"second": 1, "minute": 1 / 60, "hour": 1 / 3600}
        if per not in unit_multipliers:
            raise ValueError(f"Unsupported time unit for rate limiting: {per}")

        if burst_size is None:
            burst_size = max(1, int(requests) + 1)

        rate = requests * unit_multipliers[per]
        self.rate_limiter = TokenBucket(rate=rate, burst_size=burst_size)

    def Parallel_Clear_Rate_Limit(self):
        """Parallel Clear Rate Limit

        Remove rate limiting configuration.
        """
        self.rate_limiter = None

    def Parallel_Set_Retry_Policy(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        retry_statuses: Optional[str] = None,
        jitter: float = 0.1,
    ):
        """Parallel Set Retry Policy    max_retries=3    backoff_factor=2.0    retry_statuses=None    jitter=0.1

        Configure retry behavior with exponential backoff for failed requests.

        By default retries status codes 429/500/502/503/504 and transport errors
        (timeouts, network errors, remote protocol errors). Wait time is
        ``backoff_factor ** attempt`` plus a small random jitter.

        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for wait time between retries
            retry_statuses: Comma-separated status codes to retry (defaults to 429,500,502,503,504)
            jitter: Fraction of base wait added as random jitter (0 disables)

        Example usage:
            Parallel Set Retry Policy    max_retries=3    backoff_factor=2.0
            Parallel Set Retry Policy    max_retries=5    retry_statuses=429    jitter=0
        """
        statuses = None
        if retry_statuses:
            statuses = [int(s.strip()) for s in retry_statuses.split(",")]

        self.retry_policy = RetryPolicy(
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            retry_statuses=statuses,
            jitter=float(jitter),
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
            - successful_requests: Requests with 2xx or 3xx status
            - failed_requests: Requests with errors or 4xx/5xx status
            - avg_duration: Average request duration in seconds
            - min_duration: Minimum request duration
            - max_duration: Maximum request duration
            - requests_per_second: Actual request rate in requests per second
            - status_code_counts: Dict of status code frequencies

        Example usage:
            ${metrics}=    Parallel Get Metrics
            Log    Total requests: ${metrics['total_requests']}
        """
        return self.metrics.get_summary()

    def Parallel_Clear_Metrics(self):
        """Parallel Clear Metrics

        Clear all collected metrics.
        """
        self.metrics.clear()
