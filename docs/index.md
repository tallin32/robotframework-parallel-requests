# robotframework-parallel-requests

A Robot Framework library for batching and parallelizing HTTP requests with `httpx` and a thread pool.

## Why this library

- Run many API requests concurrently inside Robot Framework tests.
- Keep a familiar RequestsLibrary-style keyword surface.
- Retrieve response objects directly for advanced assertions.

## Installation

```bash
pip install robotframework-parallel-requests
```

## Core idea

Queue requests first, then wait once:

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

    Parallel Shutdown
```

## Links

- GitHub repository: https://github.com/tallin32/robotframework-parallel-requests
- PyPI package: https://pypi.org/project/robotframework-parallel-requests/
- TestPyPI package: https://test.pypi.org/project/robotframework-parallel-requests/
