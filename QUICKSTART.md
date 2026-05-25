# QUICKSTART.md

## 5-Minute Setup

### 1. Install

```bash
cd robotframework-parallel-requests
pip install -r requirements.txt
```

### 2. Run Tests

```bash
pytest tests/ -v
```

Expected: **17 tests pass** ✓

### 3. Use in Robot Tests

Create a test file `test_parallel.robot`:

```robot
*** Settings ***
Library    robot_parallel_requests.ParallelRequests    worker_count=5

*** Test Cases ***
Queue Three Requests And Retrieve
    Parallel Create Session    base_url=https://httpbin.org
    ${id1}=    Parallel Queue Request    GET    /get
    ${id2}=    Parallel Queue Request    GET    /delay/1
    ${id3}=    Parallel Queue Request    GET    /status/201
    
    Parallel Wait For All Requests    timeout=30
    
    ${status1}=    Parallel Get Response Status    ${id1}
    Log    Status 1: ${status1}
    
    ${response}=    Parallel Get Response Object    ${id3}
    Log    Response 3 code: ${response.status_code}
    
    Parallel Shutdown
```

Run it:
```bash
robot test_parallel.robot
```

---

## Use Case Examples

### Example 1: Rate Limit Testing

Test that an API rate-limits after N requests:

```robot
*** Settings ***
Library    robot_parallel_requests.ParallelRequests    worker_count=10

*** Test Cases ***
Find Rate Limit
    Parallel Create Session    base_url=https://api.example.com
    
    # Queue 101 requests
    @{ids}=    Create List
    FOR    ${i}    IN RANGE    101
        ${id}=    Parallel Queue Request    POST    /api/favorite-restaurants
        Append To List    @{ids}    ${id}
    END
    
    Parallel Wait For All Requests    timeout=60
    
    # Check results
    ${success_count}=    Set Variable    0
    ${error_count}=    Set Variable    0
    FOR    ${id}    IN    @{ids}
        ${status}=    Parallel Get Response Status    ${id}
        IF    ${status} == 200
            ${success_count}=    Evaluate    ${success_count} + 1
        ELSE
            ${error_count}=    Evaluate    ${error_count} + 1
        END
    END
    
    Log    Success: ${success_count}, Errors: ${error_count}
    Should Be Equal As Numbers    ${error_count}    1
    
    Parallel Shutdown
```

### Example 2: Parallel User Profile Fetch

Fetch 100 user profiles in parallel:

```robot
*** Settings ***
Library    robot_parallel_requests.ParallelRequests    worker_count=20

*** Test Cases ***
Fetch Bulk Profiles
    Parallel Create Session    base_url=https://api.example.com
    
    @{ids}=    Create List
    FOR    ${user_id}    IN RANGE    100
        ${id}=    Parallel Queue Request    GET    /users/${user_id}
        Append To List    @{ids}    ${id}
    END
    
    Parallel Wait For All Requests    timeout=30
    
    # All should be 200 OK
    FOR    ${id}    IN    @{ids}
        ${status}=    Parallel Get Response Status    ${id}
        Should Be Equal    ${status}    200
    END
    
    Parallel Shutdown
```

### Example 3: Direct Response Object Access

Use the raw response for complex assertions:

```robot
*** Settings ***
Library    robot_parallel_requests.ParallelRequests

*** Test Cases ***
Advanced Assertions
    Parallel Create Session
    ${id}=    Parallel Queue Request    GET    https://httpbin.org/headers
    Parallel Wait For All Requests
    
    ${resp}=    Parallel Get Response Object    ${id}
    
    # Access response attributes directly
    Should Contain    ${resp.headers['user-agent']}    python-httpx
    Should Be True    ${resp.elapsed.total_seconds()} < 10
    
    ${json}=    Parallel Get Response JSON    ${id}
    Log    ${json}
    
    Parallel Shutdown
```

---

## Keyword Reference (Quick)

| Keyword | Args | Returns | Purpose |
|---------|------|---------|---------|
| `Parallel Create Session` | alias, base_url?, headers? | — | Create session with defaults |
| `Parallel Queue Request` | method, url, id?, \*\*kwargs | id (str) | Queue request, get ID |
| `Parallel Start Workers` | — | — | No-op (workers ready on init) |
| `Parallel Wait For All Requests` | timeout? | — | Block until all complete |
| `Parallel Get Response Object` | id | httpx.Response | Get raw response or Exception |
| `Parallel Get Response Status` | id | status_code (int) | Get HTTP status |
| `Parallel Get Response Body` | id | body (str) | Get response body text |
| `Parallel Get Response JSON` | id | dict/list | Get parsed JSON |
| `Parallel Set Worker Count` | count | — | Adjust thread pool size |
| `Parallel Shutdown` | — | — | Stop pool and clean up |

---

## Library Options

### Prefixed Only (Default, Recommended)

```robot
Library    robot_parallel_requests.ParallelRequests
# Keywords: Parallel Create Session, Parallel Queue Request, ...
```

### Custom Worker Count

```robot
Library    robot_parallel_requests.ParallelRequests    worker_count=20
# 20 concurrent worker threads (default: 5)
```

---

## Error Handling

If a request fails, the exception is captured and stored in the response handle:

```robot
${id}=    Parallel Queue Request    GET    https://invalid-domain-xyz.invalid
Parallel Wait For All Requests
${resp}=    Parallel Get Response Object    ${id}

# ${resp} is an Exception, not a Response
Run Keyword If    isinstance(${resp}, Exception)    Log    Request failed
```

For cleaner error handling, check status codes:

```robot
${resp}=    Parallel Get Response Object    ${id}
Run Keyword Unless    ${resp.status_code} == 200    Fail    Request failed
```

---

## Troubleshooting

### Keywords not found
- Ensure `robot_parallel_requests` is installed in the Robot Framework Python environment.
- Check that the library is imported: `Library    robot_parallel_requests.ParallelRequests`

### Tests timeout
- Increase `timeout` in `Parallel Wait For All Requests`.
- Check that endpoints are reachable.
- Reduce `worker_count` if hitting rate limits on target API.

### Request failures
- Use `Parallel Get Response Object` to inspect the raw exception.
- Check network/proxy settings.

---

## Next Steps

1. Review `README.md` for full API documentation.
2. Check `ARCHITECTURE.md` for design details.
3. Look at `examples/parallel_requests.robot` for more test examples.
4. Run `pytest tests/ -v` to explore test patterns.

---

## Contributing / Future Work

See `ARCHITECTURE.md` for roadmap (rate limiting v1.1, async transport v1.2+, etc.).
