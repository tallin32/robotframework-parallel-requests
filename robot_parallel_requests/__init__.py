"""robot_parallel_requests package

This package exposes the `ParallelRequests` library class used by Robot Framework.

By default we export the class at the package level so users can import either:

```
Library    robot_parallel_requests.ParallelRequests
```

As a convenience, we also provide a module-level alias named ``robot_parallel_requests``
pointing to the class so importing the package name alone may work with some Robot
Framework import behaviours (see README). The explicit import above is still the
recommended, unambiguous form.
"""

from .library import ParallelRequests

# Convenience alias: allow `Library    robot_parallel_requests` in addition to
# the explicit `robot_parallel_requests.ParallelRequests` form. This is optional
# but can be helpful for users who expect to import libraries by package name.
robot_parallel_requests = ParallelRequests

__all__ = ["ParallelRequests", "robot_parallel_requests"]
