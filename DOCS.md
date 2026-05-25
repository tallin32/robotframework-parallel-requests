# Documentation Index

## Quick Navigation

### 🚀 Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** — 5-minute setup and basic examples
  - Install, run tests, first Robot test
  - Use case examples (rate limiting, bulk operations)
  - Keyword quick reference
  - Troubleshooting

### 📖 Full Documentation
- **[README.md](README.md)** — Complete API documentation
  - Features overview
  - Installation
  - Keyword reference with arguments and returns
  - Library initialization options
  - Use cases in detail
  - Testing guide
  - Architecture overview
  - Future enhancements

### 🏗️ Architecture & Design
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Deep dive into design
  - Core components (RequestTask, ResponseStore, Transport, WorkerPool, Library)
  - Request flow diagram
  - Compatibility modes explained (removed - library exposes only prefixed keywords)
  - Extension points for adding new transports or keywords
  - MVP vs future enhancements
  - Testing strategy
  - Known limitations

<!-- Compatibility mode documentation removed. The library exposes only `Parallel `-prefixed keywords. -->

## Files Overview

### Core Library
```
robot_parallel_requests/
  __init__.py              - Package entry point (exports ParallelRequests)
  library.py               - Robot Framework library class with keywords
  tasks.py                 - RequestTask dataclass
  response_store.py        - Response storage by ID
  worker.py                - ThreadPoolExecutor worker pool
  # compat_stubs.py removed (was LSP-friendly keyword stubs)
  transport/
    base.py                - Abstract transport interface
    httpx_sync.py          - Synchronous httpx transport (MVP)
    httpx_async_future.py  - Future async transport skeleton
```

### Tests & Examples
```
tests/
  test_core.py             - Core unit tests
  test_advanced.py         - Advanced behavior tests (sessions, retry, metrics)
  conftest.py              - pytest fixtures
  robot/local_api.robot    - Robot integration tests against local test API

examples/
  parallel_requests.robot  - Core Robot example suite
  advanced_features.robot  - Advanced Robot example suite
```

### Configuration
```
pyproject.toml             - Project metadata and build config
requirements.txt           - Python dependencies
```

## What Each Document Covers

| Document | Audience | Content |
|----------|----------|---------|
| QUICKSTART.md | New users | 5-min setup, examples, keywords ref |
| README.md | All users | Full API, all features, all use cases |
| ARCHITECTURE.md | Contributors | Design, components, extensibility, roadmap |
| (Compatibility mode docs removed) | N/A | Compatibility mode was removed; library exposes only prefixed keywords |

## Common Tasks

### "I want to use this library"
1. Start with [QUICKSTART.md](QUICKSTART.md)
2. Then read [README.md](README.md) for full details
3. Review [examples/parallel_requests.robot](examples/parallel_requests.robot)

### "I want to understand how it works"
1. Read [README.md](README.md) Features section
2. Review [ARCHITECTURE.md](ARCHITECTURE.md)
3. Look at [robot_parallel_requests/library.py](robot_parallel_requests/library.py)

### "I want to add a new transport (async, etc.)"
1. Read [ARCHITECTURE.md](ARCHITECTURE.md) - "Extension Points"
2. See [robot_parallel_requests/transport/httpx_async_future.py](robot_parallel_requests/transport/httpx_async_future.py) for skeleton
3. Implement `TransportBase.send()` interface

### "I want to understand keyword routing and LSP support"
1. The library now exposes only `Parallel `-prefixed keywords. See `robot_parallel_requests/library.py` for the keyword implementation and `robot_parallel_requests/__init__.py` for package exports.

### "I want to run tests and understand test structure"
1. See [QUICKSTART.md](QUICKSTART.md) - "Run Tests"
2. Review [tests/test_core.py](tests/test_core.py) for patterns

## Project Status

**MVP Status: ✅ Complete**

- ✅ ThreadPoolExecutor + httpx sync transport
- ✅ Prefixed Robot keyword surface
- ✅ Response retrieval by ID
- ✅ Session management
- ✅ Rate limiting
- ✅ Retry/backoff policy
- ✅ Metrics collection
- ✅ Error capture and handling
- ✅ 17 passing pytest tests
- ✅ Full documentation

**Future Enhancements (v1.1+):**
- Async httpx transport for high concurrency
- Per-session queuing
- Circuit breaker / adaptive backoff refinements

---

**Last Updated:** May 25, 2026
