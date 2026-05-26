Batch Retrieve All Responses
    [Documentation]    Demonstrates batch retrieval of all responses after waiting for all requests.
    Parallel Create Session    alias=httpbin    base_url=https://httpbin.org
    ${id_list}=    Create List
    :FOR    ${i}    IN RANGE    5
        ${id}=    Parallel Queue Request    GET    https://httpbin.org/get
        Append To List    ${id_list}    ${id}
    ${responses}=    Parallel Wait For All And Get Responses    timeout=30
    # responses is a list of httpx.Response or Exception objects in submission order
    :FOR    ${resp}    IN    @{responses}
    LOG    ${resp.json()}
        Should Be Equal As Integers    ${resp.status_code}    200
    Parallel Shutdown
    # This pattern is useful for rate limit or bulk operation tests
*** Settings ***
Library    robot_parallel_requests.ParallelRequests

*** Test Cases ***
Queue Multiple Requests And Wait
    [Documentation]    Demonstrates queuing multiple requests and waiting for all to complete.
    Parallel Create Session    alias=httpbin    base_url=https://httpbin.org
    ${id1}=    Parallel Queue Request    GET    https://httpbin.org/get
    ${id2}=    Parallel Queue Request    GET    https://httpbin.org/delay/1
    ${id3}=    Parallel Queue Request    GET    https://httpbin.org/status/200
    Parallel Wait For All Requests    timeout=30
    
    ${status1}=    Parallel Get Response Status    ${id1}
    Should Be Equal As Integers    ${status1}    200
    
    ${status2}=    Parallel Get Response Status    ${id2}
    Should Be Equal As Integers    ${status2}    200
    
    ${body}=    Parallel Get Response Body    ${id1}
    Should Contain    ${body}    "url"
    
    Parallel Shutdown

Get Response Object For Direct Assertions
    [Documentation]    Demonstrates retrieving the underlying response object for advanced assertions.
    Parallel Create Session    alias=default
    ${id}=    Parallel Queue Request    GET    https://httpbin.org/json
    Parallel Wait For All Requests    timeout=30
    
    ${response}=    Parallel Get Response Object    ${id}
    # Can now use response object directly
    Should Be Equal As Integers    ${response.status_code}    200
    
    ${json_data}=    Parallel Get Response JSON    ${id}
    Log    ${json_data}
    
    Parallel Shutdown

Test Multiple Requests In Parallel
    [Documentation]    Shows that requests run in parallel and complete faster than sequential.
    Parallel Create Session
    # Queue several requests with delays
    ${id1}=    Parallel Queue Request    GET    https://httpbin.org/delay/1
    ${id2}=    Parallel Queue Request    GET    https://httpbin.org/delay/1
    ${id3}=    Parallel Queue Request    GET    https://httpbin.org/delay/1
    
    Parallel Wait For All Requests    timeout=30
    # All should complete in ~1 second (parallel) not ~3 seconds (sequential)
    
    ${status1}=    Parallel Get Response Status    ${id1}
    ${status2}=    Parallel Get Response Status    ${id2}
    ${status3}=    Parallel Get Response Status    ${id3}
    
    Should Be Equal As Integers    ${status1}    200
    Should Be Equal As Integers    ${status2}    200
    Should Be Equal As Integers    ${status3}    200
    
    Parallel Shutdown
