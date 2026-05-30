import time
import httpx
import respx
import pytest

from robot_parallel_requests.library import ParallelRequests
from robot_parallel_requests.retry import RetryPolicy


def test_session_url_resolution_and_header_merge():
    lib = ParallelRequests(worker_count=2)
    lib.Parallel_Create_Session(alias="api", base_url="https://example.org/v1", headers={"X-Base": "1"})

    with respx.mock:
        route = respx.get("https://example.org/v1/users").mock(return_value=httpx.Response(200, json={"ok": True}))
        rid = lib.Parallel_GET("/users", session="api", headers={"X-Req": "2"})
        lib.Parallel_Wait_For_All_Requests(timeout=5)
        resp = lib.Parallel_Get_Response_Object(rid)
        assert resp.status_code == 200
        # Verify the request carried merged headers
        assert route.called
        sent_headers = route.calls[0].request.headers
        assert sent_headers.get("X-Base") == "1"
        assert sent_headers.get("X-Req") == "2"
    lib.Parallel_Shutdown()


def test_unknown_session_alias_fails_fast():
    lib = ParallelRequests(worker_count=2)

    with pytest.raises(ValueError, match="Session alias not found"):
        lib.Parallel_GET("/users", session="missing")

    lib.Parallel_Shutdown()


def test_absolute_url_bypasses_session_base_url():
    lib = ParallelRequests(worker_count=2)
    lib.Parallel_Create_Session(alias="api", base_url="https://example.org/v1")

    with respx.mock:
        route = respx.get("https://other.example.net/users").mock(return_value=httpx.Response(200, json={"ok": True}))
        rid = lib.Parallel_GET("https://other.example.net/users", session="api")
        lib.Parallel_Wait_For_All_Requests(timeout=5)
        resp = lib.Parallel_Get_Response_Object(rid)
        assert resp.status_code == 200
        assert route.called

    lib.Parallel_Shutdown()


def test_request_headers_override_session_headers():
    lib = ParallelRequests(worker_count=2)
    lib.Parallel_Create_Session(alias="api", base_url="https://example.org", headers={"X-Mode": "session", "X-Shared": "session"})

    with respx.mock:
        route = respx.get("https://example.org/users").mock(return_value=httpx.Response(200, json={"ok": True}))
        rid = lib.Parallel_GET("/users", session="api", headers={"X-Req": "request", "X-Shared": "request"})
        lib.Parallel_Wait_For_All_Requests(timeout=5)
        _ = lib.Parallel_Get_Response_Object(rid)

        sent_headers = route.calls[0].request.headers
        assert sent_headers.get("X-Mode") == "session"
        assert sent_headers.get("X-Req") == "request"
        assert sent_headers.get("X-Shared") == "request"

    lib.Parallel_Shutdown()


def test_convenience_methods_map_to_queue_request():
    lib = ParallelRequests(worker_count=2)
    with respx.mock:
        respx.get("https://example.org/get").mock(return_value=httpx.Response(200))
        respx.post("https://example.org/post").mock(return_value=httpx.Response(201))
        respx.put("https://example.org/put").mock(return_value=httpx.Response(204))
        respx.delete("https://example.org/delete").mock(return_value=httpx.Response(202))
        respx.patch("https://example.org/patch").mock(return_value=httpx.Response(200))
        respx.head("https://example.org/head").mock(return_value=httpx.Response(200))
        respx.options("https://example.org/options").mock(return_value=httpx.Response(200))

        ids = [
            lib.Parallel_GET("https://example.org/get"),
            lib.Parallel_POST("https://example.org/post"),
            lib.Parallel_PUT("https://example.org/put"),
            lib.Parallel_DELETE("https://example.org/delete"),
            lib.Parallel_PATCH("https://example.org/patch"),
            lib.Parallel_HEAD("https://example.org/head"),
            lib.Parallel_OPTIONS("https://example.org/options"),
        ]
        lib.Parallel_Wait_For_All_Requests(timeout=5)
        for rid in ids:
            resp = lib.Parallel_Get_Response_Object(rid)
            assert hasattr(resp, "status_code")
    lib.Parallel_Shutdown()


def test_retry_policy_success_after_retries(monkeypatch):
    lib = ParallelRequests(worker_count=1)
    # Configure retry policy with small max_retries
    lib.Parallel_Set_Retry_Policy(max_retries=2, backoff_factor=2.0, retry_statuses="429")

    call_count = {"n": 0}

    with respx.mock:
        def responder(request):
            call_count["n"] += 1
            if call_count["n"] < 3:  # first 2 attempts return 429
                return httpx.Response(429)
            return httpx.Response(200, json={"done": True})
        route = respx.get("https://example.org/retry").mock(side_effect=responder)

        # Monkeypatch time.sleep to avoid real waiting (retry_with_backoff uses retry.time.sleep)
        import robot_parallel_requests.retry as retry_module
        slept = []
        def fake_sleep(t):
            slept.append(t)
        monkeypatch.setattr(retry_module.time, "sleep", fake_sleep)

        rid = lib.Parallel_GET("https://example.org/retry")
        lib.Parallel_Wait_For_All_Requests(timeout=10)
        resp = lib.Parallel_Get_Response_Object(rid)
        assert resp.status_code == 200
        assert call_count["n"] == 3  # 2 retries then success
        # Expect two sleep calls (attempt 0 and 1)
        assert len(slept) == 2

        metrics = lib.Parallel_Get_Metrics()
        assert metrics["total_requests"] == 1
        recorded = lib.metrics.get_metrics()[0]
        assert recorded.retries == 2
    lib.Parallel_Shutdown()


def test_rate_limiter_enforces_minimum_elapsed_time():
    lib = ParallelRequests(worker_count=2)
    # Set rate to 2 req/sec, burst_size=1 so after first immediate, remaining 2 must space out ~1s total
    lib.Parallel_Set_Rate_Limit(requests=2.0, burst_size=1)

    with respx.mock:
        respx.get("https://example.org/a").mock(return_value=httpx.Response(200))
        respx.get("https://example.org/b").mock(return_value=httpx.Response(200))
        respx.get("https://example.org/c").mock(return_value=httpx.Response(200))

        start = time.time()
        lib.Parallel_GET("https://example.org/a")
        lib.Parallel_GET("https://example.org/b")
        lib.Parallel_GET("https://example.org/c")
        lib.Parallel_Wait_For_All_Requests(timeout=10)
        elapsed = time.time() - start

        expected_min = (3 - 1) / 2.0  # (requests - burst) / rate
        # Allow small tolerance for scheduling
        assert elapsed >= expected_min * 0.9
    lib.Parallel_Shutdown()


def test_rate_limiter_applies_on_execution_not_enqueue():
    lib = ParallelRequests(worker_count=1)
    lib.Parallel_Set_Rate_Limit(requests=1.0, burst_size=1)

    with respx.mock:
        respx.get("https://example.org/qa").mock(return_value=httpx.Response(200))
        respx.get("https://example.org/qb").mock(return_value=httpx.Response(200))
        respx.get("https://example.org/qc").mock(return_value=httpx.Response(200))

        enqueue_start = time.time()
        rid1 = lib.Parallel_GET("https://example.org/qa")
        rid2 = lib.Parallel_GET("https://example.org/qb")
        rid3 = lib.Parallel_GET("https://example.org/qc")
        enqueue_elapsed = time.time() - enqueue_start

        # Queuing should stay fast; throttling should happen in worker execution.
        assert enqueue_elapsed < 0.5

        exec_start = time.time()
        lib.Parallel_Wait_For_All_Requests(timeout=10)
        exec_elapsed = time.time() - exec_start

        assert exec_elapsed >= 1.6
        assert lib.Parallel_Get_Response_Status(rid1) == 200
        assert lib.Parallel_Get_Response_Status(rid2) == 200
        assert lib.Parallel_Get_Response_Status(rid3) == 200

    lib.Parallel_Shutdown()


def test_metrics_summary_counts_success_and_failure():
    lib = ParallelRequests(worker_count=2)
    with respx.mock:
        respx.get("https://example.org/ok").mock(return_value=httpx.Response(200))
        def failer(request):
            raise httpx.ConnectError("boom", request=request)
        respx.get("https://example.org/fail").mock(side_effect=failer)

        rid1 = lib.Parallel_GET("https://example.org/ok")
        rid2 = lib.Parallel_GET("https://example.org/fail")
        lib.Parallel_Wait_For_All_Requests(timeout=5)
        metrics = lib.Parallel_Get_Metrics()
        assert metrics["total_requests"] == 2
        assert metrics["successful_requests"] == 1
        assert metrics["failed_requests"] == 1
        assert metrics["status_code_counts"].get(200) == 1
    lib.Parallel_Shutdown()


def test_batch_response_retrieval_order():
    lib = ParallelRequests(worker_count=3)
    with respx.mock:
        respx.get("https://example.org/1").mock(return_value=httpx.Response(200, json={"id": 1}))
        respx.get("https://example.org/2").mock(return_value=httpx.Response(200, json={"id": 2}))
        respx.get("https://example.org/3").mock(return_value=httpx.Response(200, json={"id": 3}))

        lib.Parallel_GET("https://example.org/1")
        lib.Parallel_GET("https://example.org/2")
        lib.Parallel_GET("https://example.org/3")
        responses = lib.Parallel_Wait_For_All_And_Get_Responses(timeout=5)
        assert len(responses) == 3
        payloads = [r.json() for r in responses]
        assert payloads == [{"id": 1}, {"id": 2}, {"id": 3}]
    lib.Parallel_Shutdown()


def test_set_worker_count_recreates_pool_and_keeps_metrics():
    lib = ParallelRequests(worker_count=1)
    lib.Parallel_Set_Worker_Count(3)

    with respx.mock:
        respx.get("https://example.org/reconfigured").mock(return_value=httpx.Response(200, json={"ok": True}))
        rid = lib.Parallel_GET("https://example.org/reconfigured")
        lib.Parallel_Wait_For_All_Requests(timeout=5)

        resp = lib.Parallel_Get_Response_Object(rid)
        assert resp.status_code == 200

        metrics = lib.Parallel_Get_Metrics()
        assert metrics["total_requests"] == 1
        assert metrics["status_code_counts"].get(200) == 1

    lib.Parallel_Shutdown()


def test_shutdown_is_idempotent():
    lib = ParallelRequests(worker_count=1)
    lib.Parallel_Shutdown()
    lib.Parallel_Shutdown()


def test_wait_all_completes_serial_requests_with_shared_timeout():
    lib = ParallelRequests(worker_count=1)

    with respx.mock:
        def slow_response(request):
            time.sleep(0.5)
            return httpx.Response(200)
        respx.get("https://example.org/slow").mock(side_effect=slow_response)

        for _ in range(3):
            lib.Parallel_GET("https://example.org/slow")

        lib.Parallel_Wait_For_All_Requests(timeout=5)
        metrics = lib.Parallel_Get_Metrics()
        assert metrics["total_requests"] == 3

    lib.Parallel_Shutdown()


def test_wait_all_logs_warning_on_timeout(monkeypatch):
    lib = ParallelRequests(worker_count=1)
    warnings = []

    import robot_parallel_requests.library as library_module

    def capture_warn(message):
        warnings.append(message)

    monkeypatch.setattr(library_module.logger, "warn", capture_warn)

    with respx.mock:
        def slow_response(request):
            time.sleep(2)
            return httpx.Response(200)
        respx.get("https://example.org/slow").mock(side_effect=slow_response)

        for _ in range(3):
            lib.Parallel_GET("https://example.org/slow")

        lib.Parallel_Wait_For_All_Requests(timeout=1)

    assert warnings
    assert "did not complete within timeout" in warnings[0]

    lib.Parallel_Shutdown()


def test_duplicate_request_id_raises():
    lib = ParallelRequests(worker_count=2)

    with respx.mock:
        respx.get("https://example.org/a").mock(return_value=httpx.Response(200, text="a"))
        lib.Parallel_GET("https://example.org/a", id="dup-id")

        with pytest.raises(ValueError, match="Duplicate request id"):
            lib.Parallel_GET("https://example.org/a", id="dup-id")

    lib.Parallel_Shutdown()


def test_batch_response_retrieval_is_per_wait_batch():
    lib = ParallelRequests(worker_count=3)

    with respx.mock:
        respx.get("https://example.org/b1").mock(return_value=httpx.Response(200, json={"batch": 1}))
        respx.get("https://example.org/b2").mock(return_value=httpx.Response(200, json={"batch": 2}))
        respx.get("https://example.org/b3").mock(return_value=httpx.Response(200, json={"batch": 3}))
        respx.get("https://example.org/b4").mock(return_value=httpx.Response(200, json={"batch": 4}))

        lib.Parallel_GET("https://example.org/b1")
        batch1 = lib.Parallel_Wait_For_All_And_Get_Responses(timeout=5)
        assert len(batch1) == 1
        assert batch1[0].json()["batch"] == 1

        lib.Parallel_GET("https://example.org/b2")
        lib.Parallel_GET("https://example.org/b3")
        lib.Parallel_GET("https://example.org/b4")
        batch2 = lib.Parallel_Wait_For_All_And_Get_Responses(timeout=5)
        assert len(batch2) == 3
        assert [r.json()["batch"] for r in batch2] == [2, 3, 4]

    lib.Parallel_Shutdown()


def test_rate_limit_burst_default_uses_requests_not_converted_rate():
    lib = ParallelRequests()
    lib.Parallel_Set_Rate_Limit(requests=105, per="minute")
    assert lib.rate_limiter.burst_size == 106
    lib.Parallel_Shutdown()


def test_rate_limit_rejects_non_positive_requests():
    lib = ParallelRequests()
    with pytest.raises(ValueError, match="must be positive"):
        lib.Parallel_Set_Rate_Limit(0)
    lib.Parallel_Shutdown()


def test_rate_limit_applies_to_each_retry_attempt(monkeypatch):
    lib = ParallelRequests(worker_count=1)
    lib.Parallel_Set_Rate_Limit(requests=2.0, burst_size=1)
    lib.Parallel_Set_Retry_Policy(max_retries=2, backoff_factor=2.0, retry_statuses="429")

    call_count = {"n": 0}

    with respx.mock:
        def responder(request):
            call_count["n"] += 1
            if call_count["n"] < 3:
                return httpx.Response(429)
            return httpx.Response(200)

        respx.get("https://example.org/retry-rate").mock(side_effect=responder)

        import robot_parallel_requests.retry as retry_module

        monkeypatch.setattr(retry_module.time, "sleep", lambda _t: None)

        start = time.time()
        rid = lib.Parallel_GET("https://example.org/retry-rate")
        lib.Parallel_Wait_For_All_Requests(timeout=10)
        elapsed = time.time() - start

        assert lib.Parallel_Get_Response_Status(rid) == 200
        assert call_count["n"] == 3
        # Three throttled sends at 2 req/s with burst 1 -> ~1s minimum spacing
        assert elapsed >= 0.9

    lib.Parallel_Shutdown()


def test_metrics_counts_3xx_as_successful():
    lib = ParallelRequests(worker_count=1)

    with respx.mock:
        respx.get("https://example.org/redirect").mock(return_value=httpx.Response(302))
        lib.Parallel_GET("https://example.org/redirect")
        lib.Parallel_Wait_For_All_Requests(timeout=5)

        metrics = lib.Parallel_Get_Metrics()
        assert metrics["successful_requests"] == 1
        assert metrics["failed_requests"] == 0

    lib.Parallel_Shutdown()


def test_metrics_requests_per_second_uses_completion_span():
    lib = ParallelRequests(worker_count=1)

    with respx.mock:
        def slow_response(request):
            time.sleep(0.5)
            return httpx.Response(200)

        respx.get("https://example.org/rps").mock(side_effect=slow_response)
        lib.Parallel_GET("https://example.org/rps")
        lib.Parallel_GET("https://example.org/rps")
        lib.Parallel_Wait_For_All_Requests(timeout=5)

        metrics = lib.Parallel_Get_Metrics()
        # Two serial 0.5s requests -> ~2 requests over ~1s completion span
        assert 1.5 <= metrics["requests_per_second"] <= 3.0

    lib.Parallel_Shutdown()
