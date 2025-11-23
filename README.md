# robotframework-parallel-requests

A Robot Framework library for parallelized HTTP requests using `httpx` and ThreadPool.

**Queue multiple HTTP requests and run them in parallel**, then retrieve responses by ID or await all responses. Designed for testing scenarios like rate limiting, bulk API operations, and performance validation.

## Status

⚠️ **Beta** — Core functionality stable; API may evolve.

## Features

- **Parallelized requests**: Queue up multiple HTTP requests and execute them concurrently using ThreadPoolExecutor.
- **RequestsLibrary-like API**: Keywords mirror RequestsLibrary for familiarity (with `Parallel ` prefix).
- **Direct response access**: Retrieve the underlying `httpx.Response` object for advanced assertions.
- **Simple session management**: Create named sessions with base URLs and default headers.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Comparison with RequestsLibrary](#comparison-with-requestslibrary)
- [Keywords Reference](#keywords)
- [Library Initialization](#library-initialization)
- [Use Cases](#use-cases)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Architecture](#architecture)
- [Testing](#testing)

## Installation

**From PyPI (when released):**
```bash
pip install robotframework-parallel-requests
```

**Development/Local Installation:**
```bash
pip install -r requirements.txt
```

**Prerequisites:**
- Python 3.8+
- Robot Framework 4.0+

**Dependencies:**
- `httpx>=0.23.0` - Async HTTP client
- `robotframework>=4.0` - Robot Framework core
- `pytest>=7.0` - Testing (dev only)
- `respx>=0.20.0` - httpx mocking (dev only)

## Quick Start

### Basic Usage

```robot
*** Settings ***
Library    robot_parallel_requests

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

## Comparison with RequestsLibrary

| Feature | robot_parallel_requests | RequestsLibrary |
|---------|------------------------|-----------------|
| **Parallel/Async Requests** | ✅ Native ThreadPoolExecutor | ❌ Sequential only |
| **Queue Multiple Requests** | ✅ Yes, with ID-based retrieval | ❌ No |
| **Bulk Operations** | ✅ Optimized | ❌ Requires loops + waits |
| **Rate Limiting Tests** | ✅ Workable, with forthcoming enhancements | ⚠️ Difficult/slow |
| **API Compatibility** | Similar keywords (with `Parallel ` prefix) | —  |
| **Direct Response Objects** | ✅ `httpx.Response` access | ✅ `requests.Response` access |
| **Session Management** | ✅ Named sessions | ✅ Named sessions |

**When to use robot_parallel_requests:**
- Testing APIs with rate limits, quotas, or concurrency requirements
- Bulk operations (e.g., creating 100 records in parallel)
- Performance/load testing within Robot Framework
- Simulating real-world parallel client behavior
Optimizing tests that make many requests in succession

**When to stick with RequestsLibrary:**
- Simple sequential API testing
- Lightweight HTTP assertions
- No parallel workload requirements
- But feel free to use both—we're good with that

## Error Handling

When a request fails (network error, timeout, invalid URL), the exception is stored in the response store:

```robot
*** Test Cases ***
Handle Request Failures
    Parallel Create Session
    ${id1}=    Parallel Queue Request    GET    https://httpbin.org/delay/2    timeout=1
    ${id2}=    Parallel Queue Request    GET    https://invalid-domain-12345.com
    
    Parallel Wait For All Requests    timeout=10
    
    # Check if response is an exception
    ${resp}=    Parallel Get Response Object    ${id1}
    Run Keyword If    '${type(resp).__name__}' == 'ReadTimeout'    Log    Request timed out
    
    # For a regular response, status code is safe
    ${resp2}=    Parallel Get Response Object    ${id2}
    Run Keyword If    '${type(resp2).__name__}' == 'ConnectError'    Log    Request failed: ${resp2}
    
    Parallel Shutdown
```

**Safe Patterns:**
- Always call `Parallel Wait For All Requests` before retrieving responses
- Use `Parallel Get Response Object` and check the exception type if needed
- Use `Run Keyword If` with type checks for conditional error handling

## Best Practices

**Library Scope:**
- This library sets `ROBOT_LIBRARY_SCOPE = "TEST"` so each test gets a fresh instance and resources are always isolated.
- This is the most idiomatic and robust approach for libraries managing connections, pools, or other stateful resources.

**Shutdown Handling:**
- ❌ **Bad:** Calling `Parallel Shutdown` in individual tests causes `cannot schedule new futures after shutdown` errors in subsequent tests.
- ✅ **Good:** Use `Test Teardown` or rely on the automatic cleanup when the test scope ends.

**Worker Count:**
- Default `worker_count=5` is suitable for most scenarios.
- For high-throughput tests, increase to 10-20.
- For I/O-heavy operations, ThreadPoolExecutor can handle 50+ safely.

**Timeout Handling:**
- Always set explicit timeouts in `Parallel Wait For All Requests` to prevent hanging tests.
- Individual request timeouts (via `timeout=` parameter in `Queue Request`) affect only that request.

**If you override library scope:**
- Use `Suite Teardown` to call shutdown/cleanup keywords.
- Avoid calling shutdown in individual tests unless you fully understand the implications.

## Keywords

### Session Management

**Parallel Create Session**
- **Arguments:** `alias` (str), `base_url` (str, optional), `headers` (dict, optional)
- **Description:** Create a named session with optional base URL and default headers.

**Parallel Shutdown**
- **Description:** Shutdown worker pool and close transport.

### Request Queuing

**Parallel Queue Request**
- **Arguments:** `method` (str), `url` (str), `id` (str, optional), `**kwargs` (headers, json, data, params, etc.)
- **Returns:** Response ID (string)
- **Description:** Queue a request to be processed by the worker pool. Returns a response ID for later retrieval.

**Parallel Start Workers**
- **Description:** Start worker pool (workers are ready on init; this is a no-op in MVP).

**Parallel Wait For All Requests**
- **Arguments:** `timeout` (float, optional, seconds)
- **Description:** Block until all queued requests complete or timeout expires.

### Response Retrieval

**Parallel Get Response Object**
- **Arguments:** `id` (str)
- **Returns:** `httpx.Response` object (or Exception if request failed)
- **Description:** Retrieve the underlying response object for direct assertions.

**Parallel Get Response Status**
- **Arguments:** `id` (str)
- **Returns:** Status code (int)

**Parallel Get Response Body**
- **Arguments:** `id` (str)
- **Returns:** Response body as string

**Parallel Get Response JSON**
- **Arguments:** `id` (str)
- **Returns:** Parsed JSON (dict/list)

### Configuration

**Parallel Set Worker Count**
- **Arguments:** `count` (int)
- **Description:** Adjust the number of concurrent worker threads.

## Library Initialization

### Arguments

- `worker_count` (int, default: `5`): Number of worker threads in the pool.

### Examples

```robot
# Default: 5 worker threads
Library    robot_parallel_requests

# High concurrency: 20 worker threads
Library    robot_parallel_requestsworker_count=20
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
- **`library.py`**: Robot Framework library with keywords.

## Future Enhancements

- **Async transport** (`transport/httpx_async.py`) using `httpx.AsyncClient` for high-concurrency scenarios (10k+ concurrent requests).
- **Rate limiting** (v1.1): `Set Rate Limit` keyword with token-bucket algorithm.
- **Retry/backoff policies** (v1.1): `Set Retry Policy` keyword.
- **Metrics and reporting**: Request counts, latencies, error rates.
- **Per-session request queues**: Advanced session management.

## Contributing

Contributions are welcome! To get started:
Contributions are welcome! For public/open-source contributions we recommend the
fork → pull request workflow (standard GitHub flow). This keeps the main
repository protected while making it easy for outside contributors to propose
changes.

Quick contribution steps (fork → PR):

1. Fork the repository on GitHub to your account.
2. Clone your fork and add the upstream remote:

```powershell
git clone git@github.com:your-username/robotframework-parallel-requests.git
cd robotframework-parallel-requests
git remote add upstream git@github.com:tallin32/robotframework-parallel-requests.git
```

3. Create a feature branch, make changes, run tests locally:

```powershell
git checkout -b feature/my-feature
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest tests/ -v
```

4. Push your branch to your fork and open a pull request against
`tallin32/robotframework-parallel-requests:main`:

```powershell
git push origin feature/my-feature
# then open a PR on GitHub from your branch into tallin32:main
```

Maintainer workflow (recommended for this repo):

- Protect the `main` branch and require all changes via Pull Requests.
- Require at least one reviewer and passing CI before merging.

What to include in a PR:

- A clear summary of the change and why it is needed.
- Testing notes (how you ran tests locally, what CI should run).
- If the change affects the public API, include README/docs updates.

If you'd rather be added as a collaborator (for frequent contributors), reach
out and we can add you as a repo collaborator so you can push branches directly
— but merges should still go through PRs.

If you want, I can add a `CONTRIBUTING.md` and a PR template to this repo (recommended); I can create those now.

## License

MIT (see LICENSE if present).

