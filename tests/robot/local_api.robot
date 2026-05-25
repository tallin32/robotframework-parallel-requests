*** Settings ***
Library    robot_parallel_requests.ParallelRequests    worker_count=8
Library    Collections
Test Teardown    Run Keyword And Ignore Error    Parallel Shutdown

*** Variables ***
${BASE_URL}    http://127.0.0.1:18080

*** Test Cases ***
Session Base URL Works Against Local API
    Parallel Create Session    alias=local    base_url=${BASE_URL}
    ${request_id}=    Parallel GET    /get    session=local

    Parallel Wait For All Requests    timeout=10

    ${status}=    Parallel Get Response Status    ${request_id}
    Should Be Equal As Integers    ${status}    200

    ${body}=    Parallel Get Response Body    ${request_id}
    Should Contain    ${body}    "path": "/get"

Convenience Methods Work With Local API
    Parallel Create Session    alias=local    base_url=${BASE_URL}

    ${id_get}=    Parallel GET    /get    session=local
    ${id_post}=    Parallel POST    /anything    session=local    json={'name': 'robot'}
    ${id_put}=    Parallel PUT    /anything    session=local    json={'update': true}
    ${id_delete}=    Parallel DELETE    /anything    session=local

    Parallel Wait For All Requests    timeout=10

    ${status_get}=    Parallel Get Response Status    ${id_get}
    ${status_post}=    Parallel Get Response Status    ${id_post}
    ${status_put}=    Parallel Get Response Status    ${id_put}
    ${status_delete}=    Parallel Get Response Status    ${id_delete}

    Should Be Equal As Integers    ${status_get}    200
    Should Be Equal As Integers    ${status_post}    200
    Should Be Equal As Integers    ${status_put}    200
    Should Be Equal As Integers    ${status_delete}    200

Metrics Reflect Success And Failure Statuses
    Parallel Clear Metrics
    Parallel Create Session    alias=local    base_url=${BASE_URL}

    ${ok_id}=    Parallel GET    /status/200    session=local
    ${not_found_id}=    Parallel GET    /status/404    session=local

    Parallel Wait For All Requests    timeout=10

    ${ok_status}=    Parallel Get Response Status    ${ok_id}
    ${not_found_status}=    Parallel Get Response Status    ${not_found_id}
    Should Be Equal As Integers    ${ok_status}    200
    Should Be Equal As Integers    ${not_found_status}    404

    ${metrics}=    Parallel Get Metrics
    Should Be Equal As Integers    ${metrics['total_requests']}    2
    Should Be Equal As Integers    ${metrics['successful_requests']}    1
    Should Be Equal As Integers    ${metrics['failed_requests']}    1

Query Params And Headers Are Passed Through
    Parallel Create Session    alias=local    base_url=${BASE_URL}

    ${params}=    Create Dictionary    source=robot
    ${headers}=    Create Dictionary    X-Test=robot
    ${request_id}=    Parallel Queue Request    GET    /get    session=local    params=${params}    headers=${headers}

    Parallel Wait For All Requests    timeout=10

    ${payload}=    Parallel Get Response JSON    ${request_id}
    Should Be Equal    ${payload['query']['source'][0]}    robot
    Should Be Equal    ${payload['headers']['X-Test']}    robot

Patch Head And Options Methods Work
    Parallel Create Session    alias=local    base_url=${BASE_URL}

    ${patch_id}=    Parallel PATCH    /anything    session=local    json={'patched': true}
    ${head_id}=    Parallel HEAD    /get    session=local
    ${options_id}=    Parallel OPTIONS    /anything    session=local

    Parallel Wait For All Requests    timeout=10

    ${patch_status}=    Parallel Get Response Status    ${patch_id}
    ${head_status}=    Parallel Get Response Status    ${head_id}
    ${options_status}=    Parallel Get Response Status    ${options_id}

    Should Be Equal As Integers    ${patch_status}    200
    Should Be Equal As Integers    ${head_status}    200
    Should Be Equal As Integers    ${options_status}    200

Retry Policy Retries Flaky Endpoint
    Parallel Create Session    alias=local    base_url=${BASE_URL}
    Parallel Set Retry Policy    max_retries=3    backoff_factor=1.05    retry_statuses=429

    ${params}=    Create Dictionary    failures=2    status=429    success_status=200
    ${request_id}=    Parallel Queue Request    GET    /flaky/retry-case    session=local    params=${params}

    Parallel Wait For All Requests    timeout=20

    ${status}=    Parallel Get Response Status    ${request_id}
    Should Be Equal As Integers    ${status}    200

    ${payload}=    Parallel Get Response JSON    ${request_id}
    Should Be Equal As Integers    ${payload['attempt']}    3

Parallel Requests Finish Faster Than Sequential Delay
    Parallel Create Session    alias=local    base_url=${BASE_URL}

    ${start}=    Evaluate    __import__('time').time()
    ${id1}=    Parallel GET    /delay/1    session=local
    ${id2}=    Parallel GET    /delay/1    session=local
    ${id3}=    Parallel GET    /delay/1    session=local

    Parallel Wait For All Requests    timeout=20
    ${elapsed}=    Evaluate    __import__('time').time() - ${start}

    ${status1}=    Parallel Get Response Status    ${id1}
    ${status2}=    Parallel Get Response Status    ${id2}
    ${status3}=    Parallel Get Response Status    ${id3}
    Should Be Equal As Integers    ${status1}    200
    Should Be Equal As Integers    ${status2}    200
    Should Be Equal As Integers    ${status3}    200
    Should Be True    ${elapsed} < 2.8

Rate Limiter Applies Backpressure
    Parallel Create Session    alias=local    base_url=${BASE_URL}
    Parallel Set Rate Limit    2.0    burst_size=1

    ${start}=    Evaluate    __import__('time').time()
    ${id1}=    Parallel GET    /get    session=local
    ${id2}=    Parallel GET    /get    session=local
    ${id3}=    Parallel GET    /get    session=local

    Parallel Wait For All Requests    timeout=20
    ${elapsed}=    Evaluate    __import__('time').time() - ${start}

    ${status1}=    Parallel Get Response Status    ${id1}
    ${status2}=    Parallel Get Response Status    ${id2}
    ${status3}=    Parallel Get Response Status    ${id3}
    Should Be Equal As Integers    ${status1}    200
    Should Be Equal As Integers    ${status2}    200
    Should Be Equal As Integers    ${status3}    200
    Should Be True    ${elapsed} >= 0.9
