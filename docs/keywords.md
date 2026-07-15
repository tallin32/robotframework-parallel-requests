# Keywords

This page is a concise map of the most commonly used keywords.

## Session

- `Parallel Create Session`
- `Parallel Shutdown`

## Queue and execution

- `Parallel Queue Request`
- `Parallel Queue Many`
- `Parallel Wait For All Requests`
- `Parallel Wait For All And Get Responses`

## Convenience HTTP methods

- `Parallel GET`
- `Parallel POST`
- `Parallel PUT`
- `Parallel DELETE`
- `Parallel PATCH`
- `Parallel HEAD`
- `Parallel OPTIONS`

## Responses

- `Parallel Get Response Object`
- `Parallel Get Response Status`
- `Parallel Get Response Body`
- `Parallel Get Response JSON`

## Performance and resilience

- `Parallel Set Worker Count`
- `Parallel Set Rate Limit` — throttles at HTTP send time; default burst is `requests + 1`
- `Parallel Clear Rate Limit`
- `Parallel Set Retry Policy` — status + transport errors; backoff with jitter
- `Parallel Clear Retry Policy`
- `Parallel Get Metrics`
- `Parallel Clear Metrics`

## Behavioral notes

- Omitting `session=` uses the `default` session when one exists.
- Custom request `id` values must be unique; duplicates raise `ValueError`.
- `Parallel Wait For All And Get Responses` returns only the batch queued since the previous wait.
- Wait timeouts warn by default; pass `fail_on_timeout=${True}` (or library init) to raise `TimeoutError`.
- Shutdown runs automatically at end of each test via the library listener.

For full keyword docs generated from the library, use Robot Libdoc locally:

```bash
python -m robot.libdoc robot_parallel_requests.ParallelRequests libdoc.html
```
