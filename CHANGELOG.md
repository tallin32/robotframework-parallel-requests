# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0.dev2] - 2026-09-05

### Added
- Automatic use of the `default` session when `session=` is omitted.
- `Parallel Queue Many` for bulk enqueue of request specs.
- Library init options: `fail_on_timeout`, `http2`, `cancel_pending_on_timeout`.
- Optional `fail_on_timeout` argument on wait keywords (raises `TimeoutError`).
- Optional HTTP/2 via `http2=True` (extra: `pip install robotframework-parallel-requests[http2]`).
- Automatic pool/transport shutdown at end of each test via Robot listener.
- Default retries for transport errors (timeouts/network/protocol) plus backoff jitter.
- Session edge-case tests for unknown aliases, base URL bypass on absolute URLs, and header precedence.
- Lifecycle tests for idempotent shutdown and worker reconfiguration behavior.

### Changed
- httpx connection pool limits now scale with `worker_count` (and on `Parallel Set Worker Count`).
- Request duration metrics use `time.perf_counter()`.
- Unknown or not-ready response IDs raise clear `KeyError` / `LookupError` instead of returning `None`.
- Unknown session aliases now fail fast with an explicit error.
- Worker reconfiguration now recreates transport and preserves metrics collection wiring.
- Publish workflow now uses GitHub OIDC trusted publishing for PyPI/TestPyPI instead of long-lived API token secrets.
- Publish workflow now deploys through explicit GitHub environments (`testpypi` and `pypi`) for policy separation.
- Default rate-limit burst size now uses the user-facing `requests + 1` value rather than the converted tokens-per-second rate.
- Metrics now record retry counts, use completion timestamps for RPS, and treat 3xx responses as successful.
- Python 3.12 and 3.13 classifiers added to package metadata.

### Fixed
- `Parallel Wait For All Requests` now uses `concurrent.futures.wait()` with a correct shared timeout budget and logs a warning when requests remain incomplete.
- Rate limiter failures are captured in the response store; invalid zero/negative rates are rejected at configuration time.
- Client-side rate limiting now applies to each retry attempt, not only the initial send.
- Duplicate custom request IDs now fail fast instead of silently overwriting prior results.
- `Parallel Wait For All And Get Responses` now returns only the current pending batch instead of all requests ever submitted in the test.

## [0.1.0] - 2025-11-29

### Added
- Parallel execution of HTTP requests (ThreadPoolExecutor + httpx).
- Keyword surface prefixed with `Parallel ` (e.g. `Parallel GET`, `Parallel Queue Request`).
- Batch response retrieval keyword: `Parallel Wait For All And Get Responses`.
- Direct access to raw `httpx.Response` objects and convenience helpers for status/body/json.
- Session management (base URL resolution + header merging).
- Rate limiting via token bucket: `Parallel Set Rate Limit`, `Parallel Clear Rate Limit`.
- Retry policy with exponential backoff: `Parallel Set Retry Policy`, `Parallel Clear Retry Policy`.
- Metrics collection and aggregation: `Parallel Get Metrics`, `Parallel Clear Metrics`.
- Convenience HTTP method keywords: GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS.
- Per-request timeout handling (Robot string → float conversion).
- Worker pool reconfiguration via `Parallel Set Worker Count`.
- Batch wait keyword for synchronization: `Parallel Wait For All Requests`.
- Robust unit test suite (core + advanced scenarios) and Robot example suites.
- CI workflow (GitHub Actions) executing tests across Python versions and OS matrix.
- Architecture overview and Quickstart documentation.
- Test scope isolation (`ROBOT_LIBRARY_SCOPE = TEST`) to avoid cross-suite shutdown issues.

### Use Cases
- Rate limit validation (e.g. 429 handling & backoff effectiveness).
- High-volume API batch operations (create/update/delete across many items).
- Parallel data aggregation (fetching multiple detail endpoints concurrently).
- Resilience testing (simulated transient failures with retries/backoff).
- Observability & performance baselining using metrics summary.

### Notes
- `ROBOT_LIBRARY_SCOPE = TEST` chosen to prevent reuse after pool shutdown.
- Retry backoff formula: wait = `backoff_factor ** attempt` (attempt starts at 0).
- Token bucket rate limiter: effective min elapsed ≈ `(requests - burst) / rate`.
- Metrics `requests_per_second` based on start-to-last-completion span of recorded requests.
- Status code counts omit errors without HTTP responses (exceptions recorded separately).
- Designed to remain backward-compatible within 0.x; breaking keyword changes will bump minor version.
