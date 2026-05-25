"""Rate limiting utilities using token bucket algorithm."""
import time
import threading
from typing import Optional


class TokenBucket:
    """Token bucket rate limiter for controlling request rates."""
    
    def __init__(self, rate: float, burst_size: Optional[int] = None):
        """
        Initialize token bucket.
        
        Args:
            rate: Tokens per second (e.g., 1.75 for 105 requests/minute)
            burst_size: Maximum tokens that can accumulate (defaults to rate)
        """
        self.rate = rate
        self.burst_size = burst_size or int(rate) + 1
        self.tokens = float(self.burst_size)
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def acquire(self, tokens: int = 1, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            blocking: If True, wait until tokens available
            timeout: Maximum time to wait if blocking
            
        Returns:
            True if tokens acquired, False otherwise
        """
        deadline = None if timeout is None else time.time() + timeout
        
        while True:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_update
                
                # Add tokens based on elapsed time
                self.tokens = min(self.burst_size, self.tokens + elapsed * self.rate)
                self.last_update = now
                
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True
                
                if not blocking:
                    return False
                
                if deadline and now >= deadline:
                    return False
                
                # Calculate wait time
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.rate
                
            # Release lock while sleeping
            if deadline:
                wait_time = min(wait_time, deadline - time.time())
            
            if wait_time > 0:
                time.sleep(wait_time)
            else:
                return False
