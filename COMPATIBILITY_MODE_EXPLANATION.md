# COMPATIBILITY_MODE_EXPLANATION.md

## How Compatibility Stubs Work

You asked: "For the compatibility stubs; how are those rerouted to the 'parallel' equivalents?"

Here's the complete answer:

### 1. LSP Stubs vs Runtime Routing

There are **two separate mechanisms**:

#### LSP Discovery Stubs (`compat_stubs.py`)
These are **static Python functions** that exist purely for IDE/language-server indexing:
```python
def Create_Session(*args, **kwargs):
    """Create Session - compatibility stub for LSPs"""
    raise NotImplementedError("...")
```

**Purpose:** When your IDE's language server scans the `robot_parallel_requests` package, it finds these function definitions and can offer autocomplete suggestions for keyword names like `Create_Session`.

**At runtime:** These stubs are **never called** directly. If someone tries to call them, they raise `NotImplementedError`.

#### Keyword Routing via `run_keyword()` (`library.py`)
The actual runtime routing uses Robot Framework's `run_keyword()` hook:

```python
class ParallelRequests:
    def get_keyword_names(self):
        """Expose keywords to Robot Framework"""
        keywords = ["Parallel Create Session", ...]
        if self.export_non_prefixed_keywords:
            keywords += ["Create Session", "Queue Request", ...]  # Non-prefixed names
        return keywords
    
    def run_keyword(self, name: str, args):
        """Route calls to appropriate method"""
        # If name is "Create Session", look it up in KEYWORD_ALIASES
        if name in KEYWORD_ALIASES:
            method_name = KEYWORD_ALIASES[name]  # Maps to "Parallel_Create_Session"
        else:
            method_name = name.replace(" ", "_")
        
        method = getattr(self, method_name)
        return method(*args)
```

### 2. Routing Flow

**With `export_non_prefixed_keywords=False` (default):**

```
Robot Test
    ↓
Parallel Queue Request
    ↓
Robot: get_keyword_names() → ["Parallel Queue Request", ...]
    ↓
Robot: run_keyword("Parallel Queue Request", args)
    ↓
Library: run_keyword() → name = "Parallel Queue Request"
    ↓
method_name = "Parallel_Queue_Request"
    ↓
self.Parallel_Queue_Request(*args)  ← executed
```

**With `export_non_prefixed_keywords=True`:**

```
Robot Test
    ↓
Queue Request  ← non-prefixed name used
    ↓
Robot: get_keyword_names() → ["Parallel Queue Request", "Queue Request", ...]
    ↓
Robot: run_keyword("Queue Request", args)
    ↓
Library: run_keyword() → name = "Queue Request"
    ↓
# Look up in KEYWORD_ALIASES
method_name = KEYWORD_ALIASES["Queue Request"]  # Returns "Parallel_Queue_Request"
    ↓
self.Parallel_Queue_Request(*args)  ← executed (same method!)
```

### 3. Why This Approach?

**Option A (Dynamic method binding):**
```python
setattr(self, "Create_Session", self.Parallel_Create_Session)
```
**Cons:** Doesn't work well with Robot's keyword discovery; LSPs won't see it.

**Option B (run_keyword routing) - What we use:**
```python
def run_keyword(self, name, args):
    method = self.KEYWORD_ALIASES.get(name) or name
    return getattr(self, method.replace(" ", "_"))(*args)
```
**Pros:**
- Works seamlessly with Robot's keyword discovery
- LSPs can index both prefixed and non-prefixed names
- Single method implementation serves both names
- Clean separation: LSP stubs for indexing, `run_keyword()` for routing

### 4. LSP Support

**Without `compat_stubs.py`:**
- LSP scans `library.py` and finds `Parallel_Create_Session`, `Parallel_Queue_Request`, etc.
- LSP does NOT find `Create_Session` (it's not a method or function, it's a string in `KEYWORD_ALIASES`)

**With `compat_stubs.py`:**
- LSP finds both `Parallel_Queue_Request` (method) AND `Create_Session` (function stub)
- LSP can autocomplete and show documentation for both
- At runtime, the function stubs are never called; only `run_keyword()` dispatch happens

### 5. Example: Using Non-Prefixed Keywords

Robot test with `export_non_prefixed_keywords=True`:

```robot
*** Settings ***
Library    robot_parallel_requests.ParallelRequests    export_non_prefixed_keywords=True

*** Test Cases ***
My Test
    Create Session    # Non-prefixed keyword
    ${id}=    Queue Request    GET    https://example.com
    Wait For All Requests
    ${body}=    Get Response Body    ${id}
```

**At runtime:**
1. Robot Framework calls `get_keyword_names()` → returns both prefixed and non-prefixed
2. Robot Framework calls `run_keyword("Create Session", [...])`
3. Library's `run_keyword()` looks up "Create Session" in `KEYWORD_ALIASES` → finds "Parallel_Create_Session"
4. Executes `self.Parallel_Create_Session(...)`
5. Same happens for `Queue Request`, `Get Response Body`, etc.

### 6. Summary

| Mechanism | Purpose | Used By | Location |
|-----------|---------|---------|----------|
| **LSP Stubs** | IDE autocomplete | Language servers | `compat_stubs.py` |
| **KEYWORD_ALIASES** | Map non-prefixed to prefixed | `run_keyword()` | `library.py` |
| **run_keyword()** | Route calls at runtime | Robot Framework | `library.py` |
| **get_keyword_names()** | Expose keyword list | Robot Framework | `library.py` |

**Result:** Non-prefixed keywords work seamlessly in Robot tests AND LSPs can discover them for autocomplete, all while maintaining a single method implementation!
