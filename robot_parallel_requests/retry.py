"""Retry logic with exponential backoff."""
import time
from typing import List, Optional, Callable, Any
from dataclasses import dataclass


@dataclass
class RetryPolicy:
    """Configuration for retry behavior with exponential backoff."""
    max_retries: int = 3
    backoff_factor: float = 2.0
    retry_statuses: List[int] = None
    retry_exceptions: List[type] = None
    
    def __post_init__(self):
        if self.retry_statuses is None:
            self.retry_statuses = [429, 500, 502, 503, 504]
        if self.retry_exceptions is None:
            self.retry_exceptions = []
    
    def should_retry(self, attempt: int, status_code: Optional[int] = None, exception: Optional[Exception] = None) -> bool:
        """Determine if a request should be retried."""
        if attempt >= self.max_retries:
            return False
        
        if status_code and status_code in self.retry_statuses:
            return True
        
        if exception and any(isinstance(exception, exc_type) for exc_type in self.retry_exceptions):
            return True
        
        return False
    
    def get_wait_time(self, attempt: int) -> float:
        """Calculate wait time before retry using exponential backoff."""
        return self.backoff_factor ** attempt


def retry_with_backoff(func: Callable, policy: RetryPolicy, *args, **kwargs) -> Any:
    """
    Execute function with retry and exponential backoff.
    
    Args:
        func: Function to execute
        policy: Retry policy configuration
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Result from successful function execution
        
    Raises:
        Last exception if all retries exhausted
    """
    attempt = 0
    last_exception = None
    
    while attempt <= policy.max_retries:
        try:
            result = func(*args, **kwargs)
            
            # Check if result has status_code (httpx.Response)
            if hasattr(result, 'status_code'):
                if policy.should_retry(attempt, status_code=result.status_code):
                    wait_time = policy.get_wait_time(attempt)
                    time.sleep(wait_time)
                    attempt += 1
                    continue
            
            return result
            
        except Exception as exc:
            last_exception = exc
            if policy.should_retry(attempt, exception=exc):
                wait_time = policy.get_wait_time(attempt)
                time.sleep(wait_time)
                attempt += 1
                continue
            raise
    
    # If we exhausted retries, raise last exception or return last result
    if last_exception:
        raise last_exception
