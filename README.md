# Gotchas & Best Practices

**Library Scope:**

By default, Robot Framework reuses the same library instance for all tests in a suite. This can cause issues if you call `Parallel Shutdown` in one test—subsequent tests will not be able to queue requests, resulting in errors like `cannot schedule new futures after shutdown`.

**Best Practice:**

- This library sets `ROBOT_LIBRARY_SCOPE = "TEST"` so each test gets a fresh instance and resources are always isolated. This is the most idiomatic and robust approach for libraries managing connections, pools, or other stateful resources.
- If you write your own Robot Framework libraries (e.g., for database/ORM access), consider using `ROBOT_LIBRARY_SCOPE = "TEST"` unless you have a strong reason to share state across tests.

**If you override the scope:**
- Use `Suite Teardown` or `Test Teardown` to call shutdown/cleanup keywords, and avoid calling shutdown in individual tests unless you know the implications.

# robot_parallel_requests

A Robot Framework library for parallelized HTTP requests using `httpx` and ThreadPool.

Queue multiple HTTP requests and run them in parallel, then retrieve responses by ID or await all responses. Designed for testing scenarios like rate limiting, bulk API operations, and performance validation.

## Features

- **Parallelized requests**: Queue up multiple HTTP requests and execute them concurrently using ThreadPoolExecutor.
- **RequestsLibrary-like API**: Keywords mirror RequestsLibrary for familiarity (with `Parallel ` prefix by default).
- **Direct response access**: Retrieve the underlying `httpx.Response` object for advanced assertions.
- **Keyword compatibility mode**: Optional non-prefixed keywords (`Create Session`, `Queue Request`) when no conflict risk exists.
- **Language server support**: LSP-friendly stubs enable IDE autocomplete for both prefixed and non-prefixed keywords.
- **Simple session management**: Create named sessions with base URLs and default headers.

## Installation

```bash
pip install -r requirements.txt
```

Dependencies:
- `httpx>=0.23.0` - HTTP client
- `robotframework>=4.0` - Robot Framework core
- `pytest>=7.0` - Testing (dev)
- `respx>=0.20.0` - httpx mocking (dev)

## Quick Start

### Basic Usage (Prefixed Keywords - Default)

```robot
*** Settings ***
Library    robot_parallel_requests.ParallelRequests

*** Test Cases ***
Queue And Wait For Responses
    Parallel Create Session    alias=default    base_url=https://api.example.com
    ${id1}=    Parallel Queue Request    GET    /users/1
    ${id2}=    Parallel Queue Request    GET    /users/2
    ${id3}=    Parallel Queue Request    GET    /users/3
    
    Parallel Wait For All Requests    timeout=30
    
    ${status1}=    Parallel Get Response Status    ${id1}
    Should Be Equal    ${status1}    200
    
    ${body}=    Parallel Get Response Body    ${id1}
    Log    ${body}
    
    Parallel Shutdown
```

### Using Response Objects Directly

```robot
*** Test Cases ***
Access Response Object
    Parallel Create Session
    ${id}=    Parallel Queue Request    GET    https://httpbin.org/json
    Parallel Wait For All Requests    timeout=30
    
    ${response}=    Parallel Get Response Object    ${id}
    # Now you have the underlying httpx.Response object
    Should Be Equal    ${response.status_code}    200
    ${json_data}=    Parallel Get Response JSON    ${id}
    Log    ${json_data}
    
    Parallel Shutdown
```

### Optional: Non-Prefixed Keywords (Compatibility Mode)

If you're not mixing RequestsLibrary and want shorter keyword names:

```robot
*** Settings ***
Library    robot_parallel_requests.ParallelRequests    export_non_prefixed_keywords=True

*** Test Cases ***
Using Non-Prefixed Keywords
    Create Session    alias=default
    ${id}=    Queue Request    GET    https://example.com/api
    Wait For All Requests    timeout=30
    ${body}=    Get Response Body    ${id}
    Shutdown
```

## Keywords

### Session Management

**Parallel Create Session** (or `Create Session` in compat mode)
- **Arguments:** `alias` (str), `base_url` (str, optional), `headers` (dict, optional)
- **Description:** Create a named session with optional base URL and default headers.

**Parallel Shutdown** (or `Shutdown`)
- **Description:** Shutdown worker pool and close transport.

### Request Queuing

**Parallel Queue Request** (or `Queue Request`)
- **Arguments:** `method` (str), `url` (str), `id` (str, optional), `**kwargs` (headers, json, data, params, etc.)
- **Returns:** Response ID (string)
- **Description:** Queue a request to be processed by the worker pool. Returns a response ID for later retrieval.

**Parallel Start Workers** (or `Start Workers`)
- **Description:** Start worker pool (workers are ready on init; this is a no-op in MVP).

**Parallel Wait For All Requests** (or `Wait For All Requests`)
- **Arguments:** `timeout` (float, optional, seconds)
- **Description:** Block until all queued requests complete or timeout expires.

### Response Retrieval

**Parallel Get Response Object** (or `Get Response Object`)
- **Arguments:** `id` (str)
- **Returns:** `httpx.Response` object (or Exception if request failed)
- **Description:** Retrieve the underlying response object for direct assertions.

**Parallel Get Response Status** (or `Get Response Status`)
- **Arguments:** `id` (str)
- **Returns:** Status code (int)

**Parallel Get Response Body** (or `Get Response Body`)
- **Arguments:** `id` (str)
- **Returns:** Response body as string

**Parallel Get Response JSON** (or `Get Response JSON`)
- **Arguments:** `id` (str)
- **Returns:** Parsed JSON (dict/list)

### Configuration

**Parallel Set Worker Count** (or `Set Worker Count`)
- **Arguments:** `count` (int)
- **Description:** Adjust the number of concurrent worker threads.

## Library Initialization

### Arguments

- `export_non_prefixed_keywords` (bool, default: `False`): If `True`, expose keywords without the `Parallel ` prefix (e.g., `Create Session` instead of `Parallel Create Session`).
- `worker_count` (int, default: `5`): Number of worker threads in the pool.

### Examples

```robot
# Default: Parallel-prefixed keywords
Library    robot_parallel_requests.ParallelRequests

# High concurrency
Library    robot_parallel_requests.ParallelRequests    worker_count=20

# Compatibility mode (non-prefixed)
Library    robot_parallel_requests.ParallelRequests    export_non_prefixed_keywords=True
```

## Use Cases

### 1. Rate Limiting Testing
Queue 101 requests (where the 101st should fail) to test error handling and rate limits:

```robot
*** Test Cases ***
Test Rate Limit With Bulk Requests
    Parallel Create Session
    :FOR    ${i}    IN RANGE    101
        ${id}=    Parallel Queue Request    POST    /api/favorite-restaurants    json={"name": "Restaurant ${i}"}
    \    ...
    
    Parallel Wait For All Requests    timeout=60
    
    # Verify 100 succeeded, 1 failed
    # ... retrieve and check statuses
```

### 2. Parallel API Calls
Fetch multiple user profiles in parallel:

```robot
*** Test Cases ***
Fetch Multiple User Profiles
    Parallel Create Session    base_url=https://api.example.com
    @{user_ids}=    Create List    1    2    3    4    5
    @{response_ids}=    Create List
    
    :FOR    ${user_id}    IN    @{user_ids}
        ${id}=    Parallel Queue Request    GET    /users/${user_id}
        Append To List    @{response_ids}    ${id}
    \
    
    Parallel Wait For All Requests    timeout=30
    
    :FOR    ${id}    IN    @{response_ids}
        ${resp}=    Parallel Get Response Object    ${id}
        Should Be Equal    ${resp.status_code}    200
    \
    
    Parallel Shutdown
```

### 3. Direct Response Assertions
Use the raw response object for complex assertions:

```robot
*** Test Cases ***
Advanced Response Assertions
    Parallel Create Session
    ${id}=    Parallel Queue Request    GET    https://httpbin.org/headers
    Parallel Wait For All Requests
    
    ${resp}=    Parallel Get Response Object    ${id}
    Should Contain    ${resp.headers['user-agent']}    python-httpx
    Should Be Equal As Numbers    ${resp.elapsed.total_seconds()}    ${0}    delta=5
    
    Parallel Shutdown
```

## Testing

Run unit tests:

```bash
pytest tests/ -v
```

Run example Robot tests (requires Robot Framework installed in venv):

```bash
robot examples/parallel_requests.robot
```

## Architecture

- **`tasks.py`**: `RequestTask` dataclass for queued requests.
- **`response_store.py`**: In-memory storage for responses by ID.
- **`transport/base.py`**: Abstract transport interface.
- **`transport/httpx_sync.py`**: Synchronous httpx-based transport.
- **`worker.py`**: ThreadPoolExecutor-based worker pool.
- **`library.py`**: Robot Framework library with keywords and routing.
- **`compat_stubs.py`**: LSP-friendly stubs for static analysis.

## Future Enhancements

- **Async transport** (`transport/httpx_async.py`) using `httpx.AsyncClient` for high-concurrency scenarios (10k+ concurrent requests).
- **Rate limiting** (v1.1): `Set Rate Limit` keyword with token-bucket algorithm.
- **Retry/backoff policies** (v1.1): `Set Retry Policy` keyword.
- **Metrics and reporting**: Request counts, latencies, error rates.
- **Per-session request queues**: Advanced session management.

## License

MIT (see LICENSE if present).

