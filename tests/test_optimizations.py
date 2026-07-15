import time
import httpx
import respx
import pytest

from robot_parallel_requests.library import ParallelRequests
from robot_parallel_requests.retry import RetryPolicy, retry_with_backoff
from robot_parallel_requests.transport.httpx_sync import limits_for_workers, HttpxSyncTransport


def test_default_session_applied_when_session_omitted():
    lib = ParallelRequests(worker_count=2)
    lib.Parallel_Create_Session(alias="default", base_url="https://example.org/v1", headers={"X-Base": "1"})

    with respx.mock:
        route = respx.get("https://example.org/v1/users").mock(return_value=httpx.Response(200, json={"ok": True}))
        rid = lib.Parallel_GET("/users")
        lib.Parallel_Wait_For_All_Requests(timeout=5)
        assert lib.Parallel_Get_Response_Status(rid) == 200
        assert route.called
        assert route.calls[0].request.headers.get("X-Base") == "1"

    lib.Parallel_Shutdown()


def test_non_default_session_still_requires_explicit_alias():
    lib = ParallelRequests(worker_count=2)
    lib.Parallel_Create_Session(alias="api", base_url="https://example.org")

    with respx.mock:
        # Without session=, relative URL is not resolved against a non-default alias.
        rid = lib.Parallel_GET("/users")
        lib.Parallel_Wait_For_All_Requests(timeout=5)
        result = lib.Parallel_Get_Response_Object(rid)
        assert isinstance(result, Exception)

    lib.Parallel_Shutdown()


def test_queue_many_dicts_and_pairs():
    lib = ParallelRequests(worker_count=3)
    lib.Parallel_Create_Session(alias="default", base_url="https://example.org")

    with respx.mock:
        respx.get("https://example.org/a").mock(return_value=httpx.Response(200, json={"id": "a"}))
        respx.get("https://example.org/b").mock(return_value=httpx.Response(200, json={"id": "b"}))
        respx.post("https://example.org/c").mock(return_value=httpx.Response(201, json={"id": "c"}))

        ids = lib.Parallel_Queue_Many(
            [
                {"method": "GET", "url": "/a"},
                ["GET", "/b"],
                {"method": "POST", "url": "/c", "json": {"x": 1}},
            ]
        )
        responses = lib.Parallel_Wait_For_All_And_Get_Responses(timeout=5)
        assert len(ids) == 3
        assert [r.json()["id"] for r in responses] == ["a", "b", "c"]

    lib.Parallel_Shutdown()


def test_fail_on_timeout_raises():
    lib = ParallelRequests(worker_count=1, fail_on_timeout=True)

    with respx.mock:
        def slow_response(request):
            time.sleep(1.5)
            return httpx.Response(200)

        respx.get("https://example.org/slow").mock(side_effect=slow_response)
        lib.Parallel_GET("https://example.org/slow")
        lib.Parallel_GET("https://example.org/slow")

        with pytest.raises(TimeoutError, match="did not complete within timeout"):
            lib.Parallel_Wait_For_All_Requests(timeout=0.5)

    lib.Parallel_Shutdown()


def test_fail_on_timeout_keyword_override():
    lib = ParallelRequests(worker_count=1, fail_on_timeout=False)

    with respx.mock:
        def slow_response(request):
            time.sleep(1.2)
            return httpx.Response(200)

        respx.get("https://example.org/slow").mock(side_effect=slow_response)
        for _ in range(2):
            lib.Parallel_GET("https://example.org/slow")

        with pytest.raises(TimeoutError):
            lib.Parallel_Wait_For_All_Requests(timeout=0.4, fail_on_timeout=True)

    lib.Parallel_Shutdown()


def test_unknown_response_id_raises_keyerror():
    lib = ParallelRequests(worker_count=1)
    with pytest.raises(KeyError, match="Unknown response id"):
        lib.Parallel_Get_Response_Object("missing-id")
    lib.Parallel_Shutdown()


def test_not_ready_response_raises_lookuperror():
    lib = ParallelRequests(worker_count=1)

    with respx.mock:
        def slow_response(request):
            time.sleep(2)
            return httpx.Response(200)

        respx.get("https://example.org/slow").mock(side_effect=slow_response)
        rid = lib.Parallel_GET("https://example.org/slow")

        with pytest.raises(LookupError, match="not ready yet"):
            lib.Parallel_Get_Response_Object(rid)

        lib.Parallel_Wait_For_All_Requests(timeout=5)
        assert lib.Parallel_Get_Response_Status(rid) == 200

    lib.Parallel_Shutdown()


def test_limits_scale_with_worker_count():
    limits = limits_for_workers(10)
    assert limits.max_connections >= 10
    assert limits.max_keepalive_connections >= 10

    transport = HttpxSyncTransport(max_workers=8)
    assert transport._limits.max_connections >= 8
    transport.close()

    lib = ParallelRequests(worker_count=12)
    assert lib.transport._limits.max_keepalive_connections >= 12
    lib.Parallel_Set_Worker_Count(25)
    assert lib.transport._limits.max_connections >= 25
    lib.Parallel_Shutdown()


def test_retry_retries_transport_errors_by_default(monkeypatch):
    policy = RetryPolicy(max_retries=2, backoff_factor=2.0, jitter=0)
    calls = {"n": 0}

    def flaky(_task=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise httpx.ConnectError("boom")
        return httpx.Response(200)

    monkeypatch.setattr("robot_parallel_requests.retry.time.sleep", lambda _t: None)
    result, retries = retry_with_backoff(flaky, policy)
    assert result.status_code == 200
    assert retries == 2
    assert calls["n"] == 3


def test_retry_jitter_adds_variance(monkeypatch):
    policy = RetryPolicy(max_retries=1, backoff_factor=2.0, jitter=0.5)
    sleeps = []
    monkeypatch.setattr("robot_parallel_requests.retry.time.sleep", lambda t: sleeps.append(t))
    monkeypatch.setattr("robot_parallel_requests.retry.random.random", lambda: 1.0)

    def always_429():
        return httpx.Response(429)

    # Exhaust retries; last response returned without final sleep after attempt==max
    result, retries = retry_with_backoff(always_429, policy)
    assert result.status_code == 429
    assert retries == 1
    # base = 2**0 == 1, jitter adds 0.5 * 1 => 1.5
    assert sleeps == [1.5]


def test_shutdown_idempotent_with_listener_flag():
    lib = ParallelRequests(worker_count=1)
    lib.Parallel_Shutdown()
    lib.Parallel_Shutdown()
    assert lib._shutdown_done is True
