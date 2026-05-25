*** Settings ***
Library    robot_parallel_requests.ParallelRequests    worker_count=10
Library    Collections

*** Test Cases ***
Test Session Management With Base URL
    [Documentation]    Demonstrates session management with base URL and headers
    Parallel Create Session    alias=httpbin    base_url=https://httpbin.org    headers={'User-Agent': 'RobotFramework'}
    
    # URLs are now relative to base_url
    ${id1}=    Parallel Queue Request    GET    /get    session=httpbin
    ${id2}=    Parallel Queue Request    GET    /delay/1    session=httpbin
    ${id3}=    Parallel Queue Request    POST    /post    session=httpbin    json={'test': 'data'}
    
    Parallel Wait For All Requests    timeout=30
    
    ${status1}=    Parallel Get Response Status    ${id1}
    Should Be Equal As Integers    ${status1}    200
    
    Parallel Shutdown

Test HTTP Method Convenience Keywords
    [Documentation]    Demonstrates GET, POST, PUT, DELETE convenience keywords
    Parallel Create Session    alias=api    base_url=https://httpbin.org
    
    ${id_get}=    Parallel GET    /get    session=api
    ${id_post}=    Parallel POST    /post    session=api    json={'name': 'John'}
    ${id_put}=    Parallel PUT    /put    session=api    json={'update': 'data'}
    ${id_delete}=    Parallel DELETE    /delete    session=api
    
    Parallel Wait For All Requests    timeout=30
    
    ${status_get}=    Parallel Get Response Status    ${id_get}
    Should Be Equal As Integers    ${status_get}    200
    
    Parallel Shutdown

Test Rate Limiting
    [Documentation]    Demonstrates rate limiting to 2 requests per second
    # Set rate limit: 2 requests per second
    Parallel Set Rate Limit    2.0    burst_size=5
    
    Parallel Create Session    alias=api    base_url=https://httpbin.org
    
    # Queue 10 requests - they will be rate-limited
    @{ids}=    Create List
    FOR    ${i}    IN RANGE    10
        ${id}=    Parallel GET    /get    session=api
        Append To List    ${ids}    ${id}
    END
    
    Parallel Wait For All Requests    timeout=60
    
    # All requests should succeed despite rate limiting
    FOR    ${id}    IN    @{ids}
        ${status}=    Parallel Get Response Status    ${id}
        Should Be Equal As Integers    ${status}    200
    END
    
    # Check metrics to verify rate limiting worked
    ${metrics}=    Parallel Get Metrics
    Log    Total requests: ${metrics['total_requests']}
    Log    Request rate: ${metrics['requests_per_second']} req/sec
    
    Parallel Clear Rate Limit
    Parallel Shutdown

Test Batch Response Retrieval
    [Documentation]    Demonstrates batch retrieval using Parallel Wait For All And Get Responses
    Parallel Create Session    alias=api    base_url=https://httpbin.org
    
    # Queue multiple requests
    FOR    ${i}    IN RANGE    5
        Parallel GET    /get    session=api
    END
    
    # Wait and get all responses in one call
    ${responses}=    Parallel Wait For All And Get Responses    timeout=30
    
    # Verify all responses
    FOR    ${resp}    IN    @{responses}
        Should Be Equal As Integers    ${resp.status_code}    200
    END
    
    Parallel Shutdown

Test Metrics Collection
    [Documentation]    Demonstrates metrics collection and reporting
    Parallel Clear Metrics
    Parallel Create Session    alias=api    base_url=https://httpbin.org
    
    # Make various requests
    ${id1}=    Parallel GET    /get    session=api
    ${id2}=    Parallel POST    /post    session=api    json={'test': 'data'}
    ${id3}=    Parallel GET    /status/404    session=api
    
    Parallel Wait For All Requests    timeout=30
    
    # Get metrics summary
    ${metrics}=    Parallel Get Metrics
    Log    Total requests: ${metrics['total_requests']}
    Log    Successful: ${metrics['successful_requests']}
    Log    Failed: ${metrics['failed_requests']}
    Log    Avg duration: ${metrics['avg_duration']} seconds
    Log    Min duration: ${metrics['min_duration']} seconds
    Log    Max duration: ${metrics['max_duration']} seconds
    Log    Requests/sec: ${metrics['requests_per_second']}
    
    Should Be Equal As Integers    ${metrics['total_requests']}    3
    Should Be Equal As Integers    ${metrics['successful_requests']}    2
    Should Be Equal As Integers    ${metrics['failed_requests']}    1
    
    Parallel Shutdown

Test Multiple Sessions
    [Documentation]    Demonstrates using multiple sessions simultaneously
    Parallel Create Session    alias=httpbin    base_url=https://httpbin.org    headers={'X-Source': 'httpbin'}
    Parallel Create Session    alias=postman    base_url=https://postman-echo.com    headers={'X-Source': 'postman'}
    
    # Queue requests to different APIs
    ${id1}=    Parallel GET    /get    session=httpbin
    ${id2}=    Parallel GET    /get    session=postman
    
    Parallel Wait For All Requests    timeout=30
    
    ${status1}=    Parallel Get Response Status    ${id1}
    ${status2}=    Parallel Get Response Status    ${id2}
    
    Should Be Equal As Integers    ${status1}    200
    Should Be Equal As Integers    ${status2}    200
    
    Parallel Shutdown
