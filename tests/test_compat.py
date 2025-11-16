"""Tests for compatibility mode and keyword routing."""
import respx
import httpx
import pytest
from robot_parallel_requests.library import ParallelRequests


def test_non_prefixed_keywords_disabled_by_default():
    """Test that non-prefixed keywords are not exposed by default."""
    lib = ParallelRequests(export_non_prefixed_keywords=False)
    keywords = lib.get_keyword_names()
    
    # Prefixed should be there
    assert any("Parallel" in kw for kw in keywords)
    # Non-prefixed should not
    assert "Create Session" not in keywords
    
    lib.Parallel_Shutdown()


def test_non_prefixed_keywords_via_run_keyword():
    """Test that non-prefixed keywords work via run_keyword when enabled."""
    with respx.mock:
        respx.get("https://example.org/api").mock(return_value=httpx.Response(201, json={"status": "created"}))
        
        lib = ParallelRequests(export_non_prefixed_keywords=True, worker_count=1)
        
        # Use non-prefixed names via run_keyword
        lib.run_keyword("Create Session", ["session_alias", "https://example.org"])
        rid = lib.run_keyword("Queue Request", ["GET", "https://example.org/api"])
        lib.run_keyword("Wait For All Requests", [5])
        
        resp_obj = lib.run_keyword("Get Response Object", [rid])
        assert resp_obj.status_code == 201
        assert resp_obj.json() == {"status": "created"}
        
        lib.Parallel_Shutdown()


def test_robot_keyword_name_normalization():
    """Test that Robot keyword names are normalized correctly."""
    lib = ParallelRequests(export_non_prefixed_keywords=True, worker_count=1)
    
    # Robot normalizes keyword names to spaces, we should handle that
    keywords = lib.get_keyword_names()
    
    # These should all be in the keyword list
    assert "Parallel Create Session" in keywords
    assert "Parallel Queue Request" in keywords
    assert "Create Session" in keywords
    assert "Queue Request" in keywords
    
    lib.Parallel_Shutdown()
