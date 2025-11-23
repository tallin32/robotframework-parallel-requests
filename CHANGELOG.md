# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-16

### Added
- Initial MVP release: Parallelized HTTP requests using ThreadPoolExecutor + httpx.
- Batch response retrieval keyword: `Parallel Wait For All And Get Responses`.
- RequestsLibrary-compatible keyword API with `Parallel ` prefix.
 - RequestsLibrary-compatible keyword API with `Parallel ` prefix.
- Direct `httpx.Response` object access for advanced assertions.
- Session management with base URL and default headers.
- Configurable worker count and timeout support.
- Comprehensive unit tests (12 tests passing) with respx mocking.
- Full API documentation (README, QUICKSTART, ARCHITECTURE).
- Example Robot test suite with 3 test cases.

### Use Cases
- Rate limit testing: Queue 100+ requests and verify expected successes/failures.
- Bulk API operations: Parallel user profile fetches, bulk CRUD operations.
- Performance validation: Confirm response times under concurrent load.
- Error handling: Capture and assert on per-request exceptions.
- Advanced assertions: Use raw httpx.Response for complex checks.

### Notes
- Library uses `ROBOT_LIBRARY_SCOPE = "TEST"` for test isolation (idiomatic for stateful libraries).
- Timeout values are converted from Robot Framework strings to floats automatically.
- String status codes are compared using `Should Be Equal As Integers` in Robot tests.
