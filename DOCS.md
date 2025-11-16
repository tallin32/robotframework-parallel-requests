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
  - Compatibility modes explained
  - Extension points for adding new transports or keywords
  - MVP vs future enhancements
  - Testing strategy
  - Known limitations

### 🔄 Compatibility Mode Explained
- **[COMPATIBILITY_MODE_EXPLANATION.md](COMPATIBILITY_MODE_EXPLANATION.md)** — How keyword routing works
  - LSP stubs vs runtime routing
  - Complete routing flow diagrams
  - Why this approach works
  - Examples of both prefixed and non-prefixed usage

## Files Overview

### Core Library
```
robot_parallel_requests/
  __init__.py              - Package entry point (exports ParallelRequests)
  library.py               - Robot Framework library class with keywords
  tasks.py                 - RequestTask dataclass
  response_store.py        - Response storage by ID
  worker.py                - ThreadPoolExecutor worker pool
  compat_stubs.py          - LSP-friendly keyword stubs
  transport/
    base.py                - Abstract transport interface
    httpx_sync.py          - Synchronous httpx transport (MVP)
    httpx_async_future.py  - Future async transport skeleton
```

### Tests & Examples
```
tests/
  test_core.py             - 9 unit tests (worker, transport, library)
  test_compat.py           - 3 tests for compatibility mode
  conftest.py              - pytest fixtures

examples/
  parallel_requests.robot  - 3 example Robot test cases
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
| COMPATIBILITY_MODE_EXPLANATION.md | Power users | How LSP stubs + routing works |

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
1. Read [COMPATIBILITY_MODE_EXPLANATION.md](COMPATIBILITY_MODE_EXPLANATION.md)

### "I want to run tests and understand test structure"
1. See [QUICKSTART.md](QUICKSTART.md) - "Run Tests"
2. Review [tests/test_core.py](tests/test_core.py) for patterns

## Project Status

**MVP Status: ✅ Complete**

- ✅ ThreadPoolExecutor + httpx sync transport
- ✅ 10 prefixed keywords + optional non-prefixed
- ✅ LSP-friendly stubs for IDE autocomplete
- ✅ Response retrieval by ID
- ✅ Session management
- ✅ Error capture and handling
- ✅ 12 comprehensive unit tests
- ✅ Full documentation

**Future Enhancements (v1.1+):**
- Rate limiting
- Retry/backoff policies
- Metrics
- Async httpx transport for high concurrency
- Per-session queuing

---

**Last Updated:** November 16, 2025
