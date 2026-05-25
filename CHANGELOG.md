# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Session edge-case tests for unknown aliases, base URL bypass on absolute URLs, and header precedence.
- Lifecycle tests for idempotent shutdown and worker reconfiguration behavior.
### Changed
- Unknown session aliases now fail fast with an explicit error.
- Worker reconfiguration now recreates transport and preserves metrics collection wiring.
- Publish workflow now uses GitHub OIDC trusted publishing for PyPI/TestPyPI instead of long-lived API token secrets.
### Fixed
### Deprecated
### Removed
### Security

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
- Metrics `requests_per_second` based on timestamp span of recorded requests.
- Status code counts omit errors without HTTP responses (exceptions recorded separately).
- Designed to remain backward-compatible within 0.x; breaking keyword changes will bump minor version.
