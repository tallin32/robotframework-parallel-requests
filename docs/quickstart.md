# Quickstart

## Prerequisites

- Python 3.8+
- Robot Framework 4.0+

## Install for local development

```bash
pip install -r requirements.txt
pip install -e .
```

## Basic usage

```robot
*** Settings ***
Library    robot_parallel_requests

*** Test Cases ***
Parallel Example
    Parallel Create Session    alias=api    base_url=https://httpbin.org
    ${id}=    Parallel Queue Request    GET    /json    session=api
    Parallel Wait For All Requests    timeout=30
    ${status}=    Parallel Get Response Status    ${id}
    Should Be Equal As Integers    ${status}    200
    Parallel Shutdown
```

## Local validation

```bash
pytest tests/ -q
robot tests/robot/local_api.robot
```
