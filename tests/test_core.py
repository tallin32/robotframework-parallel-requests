import respx
import httpx
import pytest
from robot_parallel_requests.transport.httpx_sync import HttpxSyncTransport
from robot_parallel_requests.tasks import RequestTask
from robot_parallel_requests.worker import WorkerPool
from robot_parallel_requests.library import ParallelRequests


def test_worker_submits_and_stores_response():
    """Test that worker pool submits tasks and stores responses."""
    with respx.mock:
        route = respx.get("https://example.org/test").mock(return_value=httpx.Response(200, json={"ok": True}))
        transport = HttpxSyncTransport()
        worker = WorkerPool(transport, max_workers=2)

        task = RequestTask(method="GET", url="https://example.org/test")
        rid = worker.submit(task)
        worker.wait_all(timeout=5)
        resp = worker.get_response(rid)
        assert resp is not None
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
        worker.shutdown()


def test_worker_handles_exception():
    """Test that worker pool captures exceptions."""
    with respx.mock:
        # Mock a route that raises an exception
        def raise_error(*args, **kwargs):
            raise ValueError("Test error")
        
        respx.get("https://example.org/error").side_effect = raise_error
        
        transport = HttpxSyncTransport()
        worker = WorkerPool(transport, max_workers=2)
        
        task = RequestTask(method="GET", url="https://example.org/error")
        rid = worker.submit(task)
        worker.wait_all(timeout=2)
        result = worker.get_response(rid)
        
        # Result should be an exception
        assert isinstance(result, Exception)
        worker.shutdown()


def test_multiple_parallel_requests():
    """Test submitting multiple requests in parallel."""
    with respx.mock:
        respx.get("https://example.org/1").mock(return_value=httpx.Response(200, json={"id": 1}))
        respx.get("https://example.org/2").mock(return_value=httpx.Response(200, json={"id": 2}))
        respx.get("https://example.org/3").mock(return_value=httpx.Response(200, json={"id": 3}))
        
        transport = HttpxSyncTransport()
        worker = WorkerPool(transport, max_workers=3)
        
        ids = []
        for i in range(1, 4):
            task = RequestTask(method="GET", url=f"https://example.org/{i}")
            rid = worker.submit(task)
            ids.append(rid)
        
        worker.wait_all(timeout=5)
        
        for i, rid in enumerate(ids, start=1):
            resp = worker.get_response(rid)
            assert resp.status_code == 200
            assert resp.json() == {"id": i}
        
        worker.shutdown()


def test_library_parallel_create_session():
    """Test ParallelRequests library Create Session keyword."""
    lib = ParallelRequests(worker_count=2)
    lib.Parallel_Create_Session(alias="default", base_url="https://example.org")
    # Should not raise
    lib.Parallel_Shutdown()


def test_library_queue_and_wait():
    """Test ParallelRequests library Queue Request and Wait keywords."""
    with respx.mock:
        respx.get("https://httpbin.org/get").mock(return_value=httpx.Response(200, text="OK"))
        
        lib = ParallelRequests(worker_count=2)
        rid = lib.Parallel_Queue_Request(method="GET", url="https://httpbin.org/get")
        assert rid is not None
        
        lib.Parallel_Wait_For_All_Requests(timeout=5)
        
        body = lib.Parallel_Get_Response_Body(rid)
        assert body == "OK"
        
        lib.Parallel_Shutdown()


def test_library_get_response_object():
    """Test ParallelRequests library Get Response Object keyword."""
    with respx.mock:
        respx.get("https://example.org/test").mock(return_value=httpx.Response(200, json={"test": "data"}))
        
        lib = ParallelRequests(worker_count=2)
        rid = lib.Parallel_Queue_Request(method="GET", url="https://example.org/test")
        lib.Parallel_Wait_For_All_Requests(timeout=5)
        
        resp_obj = lib.Parallel_Get_Response_Object(rid)
        assert isinstance(resp_obj, httpx.Response)
        assert resp_obj.status_code == 200
        assert resp_obj.json() == {"test": "data"}
        
        lib.Parallel_Shutdown()


def test_library_keyword_names_prefixed():
    """Test that library exposes Parallel_ prefixed keywords by default."""
    lib = ParallelRequests(export_non_prefixed_keywords=False)
    keywords = lib.get_keyword_names()
    
    assert "Parallel Create Session" in keywords
    assert "Parallel Queue Request" in keywords
    assert "Create Session" not in keywords
    
    lib.Parallel_Shutdown()


def test_library_keyword_names_non_prefixed():
    """Test that library exposes non-prefixed keywords when enabled."""
    lib = ParallelRequests(export_non_prefixed_keywords=True)
    keywords = lib.get_keyword_names()
    
    assert "Parallel Create Session" in keywords
    assert "Create Session" in keywords
    assert "Queue Request" in keywords
    
    lib.Parallel_Shutdown()


def test_library_run_keyword_routing():
    """Test that run_keyword routes to the correct method."""
    with respx.mock:
        respx.get("https://example.org/test").mock(return_value=httpx.Response(200, text="OK"))
        
        lib = ParallelRequests(export_non_prefixed_keywords=True, worker_count=2)
        
        # Call via non-prefixed name using run_keyword
        rid = lib.run_keyword("Queue Request", ["GET", "https://example.org/test"])
        lib.run_keyword("Wait For All Requests", [5])
        body = lib.run_keyword("Get Response Body", [rid])
        
        assert body == "OK"
        
        lib.Parallel_Shutdown()

