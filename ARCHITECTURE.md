# ARCHITECTURE.md

## Design Overview

`robot_parallel_requests` provides parallelized HTTP request handling for Robot Framework tests through a ThreadPool-based architecture using `httpx` for transport.

## Core Components

### 1. RequestTask (`tasks.py`)

A dataclass representing a queued HTTP request:
- `method`: HTTP method (GET, POST, etc.)
- `url`: Target URL
- `kwargs`: httpx.Client.request kwargs (headers, json, data, etc.)
- `id`: Unique request ID (auto-generated or user-provided)
- `session_name`: Optional session reference (reserved for multi-session support)

### 2. ResponseStore (`response_store.py`)

Thread-safe in-memory store mapping response IDs to results:
- Stores either successful `httpx.Response` objects or exception instances
- Keyed by request ID for later retrieval

### 3. Transport Interface (`transport/base.py` and `transport/httpx_sync.py`)

**TransportBase** is an abstract interface for different HTTP clients:
```python
class TransportBase(ABC):
    def send(self, task: RequestTask): ...
```

**HttpxSyncTransport** is the MVP implementation:
- Wraps `httpx.Client` for synchronous HTTP requests
- Implements the `TransportBase` interface
- Can be swapped for an async variant later (`HttpxAsyncTransport` with event loop management)

### 4. WorkerPool (`worker.py`)

ThreadPoolExecutor-based request dispatcher:
- Accepts `RequestTask` objects via `submit()`
- Dispatches each task to a worker thread via the transport
- Stores responses/exceptions in `ResponseStore`
- Provides `wait_all(timeout)` to block until all tasks complete
- Tracks futures for robust timeout handling

**Key flow:**
1. `submit(task)` → add task to executor → return task.id
2. Worker thread calls `transport.send(task)` → returns `httpx.Response`
3. Response stored in `_store` under task.id
4. `wait_all()` blocks on all futures or timeout

### 5. Robot Library (`library.py`)

Exposes Robot keywords with keyword routing:

**Prefixed keywords** (always exported):
- `Parallel Create Session`, `Parallel Queue Request`, `Parallel Wait For All Requests`, etc.

**Non-prefixed aliases:** The library used to offer optional non-prefixed aliases (e.g. `Create Session`) and LSP stubs for IDE autocomplete. That compatibility mode has been removed: the library now exposes only the `Parallel `-prefixed keywords to avoid ambiguity and accidental conflicts with other libraries.

<!-- LSP compatibility stubs and runtime routing for non-prefixed keywords have been removed. -->

## Request Flow

```
Robot Test
    ↓
Parallel Queue Request (keyword)
    ↓
library.run_keyword("Parallel Queue Request", ["GET", "url"])
    ↓
library.Parallel_Queue_Request()
    ↓
worker.submit(RequestTask)
    ↓
ThreadPoolExecutor.submit(_run_task)
    ↓
worker thread: transport.send(task)
    ↓
httpx.Client.request() → httpx.Response
    ↓
response_store.set_response(id, response)
    ↓
Robot retrieves via Parallel Get Response Object, etc.
```

## Compatibility Modes

Compatibility/compat mode has been removed. The library now exposes only the `Parallel `-prefixed
keywords (e.g. `Parallel Create Session`, `Parallel Queue Request`) to avoid ambiguity and
accidental keyword conflicts with other Robot Framework libraries. This keeps the surface area
small and explicit for users who need parallel request semantics.

## Extension Points

### Adding a New Transport

1. Implement `TransportBase.send(task)`:
```python
class HttpxAsyncTransport(TransportBase):
    def send(self, task: RequestTask):
        # Return httpx.Response or raise
```

2. Update `library.py` to choose transport:
```python
if use_async:
    self.transport = HttpxAsyncTransport()
else:
    self.transport = HttpxSyncTransport()
```

3. If async, wrap the event loop in WorkerPool or provide an asyncio-aware runner.

### Adding Keywords

1. Add method to `ParallelRequests` class:
```python
def Parallel_New_Keyword(self, arg1, arg2):
    ...
```

2. Update `get_keyword_names()` if needed.
2. Update library documentation or keyword registry if needed.

## MVP vs Future Enhancements

### MVP (Current)
- ThreadPool + synchronous httpx transport
- Parallel (`Parallel_`) prefixed keywords
- Response retrieval (status, body, JSON, raw object)
- Worker count configuration
- Basic session management

### v1.1
- Rate limiting (tokens/sec, burst size)
- Retry/backoff policies (tenacity integration)
- Metrics (request count, latency histogram)

### Later
- Async httpx transport (high concurrency)
- Per-session queuing and management
- Advanced session options (cookies, auth, proxies)

## Testing Strategy

- **Unit tests** (`tests/test_core.py`): Use `respx` to mock httpx requests, validate worker pool and library behavior.
<!-- Compat tests removed (compat mode deprecated) -->
- **Integration tests** (optional): Run against httpbin or local test server.

## Known Limitations

1. **Event loop in async context:** If Robot tests run in an existing asyncio event loop, an async transport would need special handling. For now, ThreadPool + sync is safe.
2. **Per-request error details:** Errors are captured and stored; test author can retrieve raw exception from `Get Response Object`.
3. **Session isolation:** MVP doesn't isolate sessions per test; shared global pool. Can be enhanced in future.
