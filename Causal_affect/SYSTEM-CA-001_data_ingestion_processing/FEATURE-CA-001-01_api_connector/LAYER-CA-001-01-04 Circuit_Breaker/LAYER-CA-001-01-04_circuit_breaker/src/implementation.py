```python
import time
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance.
    
    Monitors failures and prevents cascading failures by opening the circuit
    after a threshold of consecutive failures. Implements exponential backoff
    and automatic recovery testing.
    """
    
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 5.0,
        expected_exception: type = Exception,
        name: Optional[str] = None
    ):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            recovery_timeout: Seconds to wait before transitioning to HALF_OPEN
            expected_exception: Exception type to catch
            name: Optional name for the circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name or "CircuitBreaker"
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._last_attempt_time = None
        self._backoff_multiplier = 1
        
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
    
    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result if successful
            
        Raises:
            Exception: Original exception or CircuitOpenError
        """
        # Check if we should transition from OPEN to HALF_OPEN
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and \
               time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._backoff_multiplier = 1
            else:
                # Apply exponential backoff
                if self._last_attempt_time:
                    backoff_time = min(0.1 * (2 ** (self._backoff_multiplier - 1)), 60.0)
                    if time.time() - self._last_attempt_time < backoff_time:
                        raise CircuitOpenError(f"Circuit {self.name} is OPEN")
                self._last_attempt_time = time.time()
                self._backoff_multiplier += 1
                raise CircuitOpenError(f"Circuit {self.name} is OPEN")
        
        try:
            # Attempt to execute the function
            result = func(*args, **kwargs)
            
            # Successful execution
            if self._state == CircuitState.HALF_OPEN:
                # Recovery successful, close the circuit
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._last_failure_time = None
                self._backoff_multiplier = 1
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0
                
            return result
            
        except self.expected_exception as e:
            # Handle expected exceptions
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                # Recovery failed, reopen circuit
                self._state = CircuitState.OPEN
            elif self._state == CircuitState.CLOSED:
                # Check if we should open the circuit
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    
            raise e
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator interface for circuit breaker.
        
        Args:
            func: Function to wrap
            
        Returns:
            Wrapped function
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def reset(self):
        """Reset circuit breaker to initial state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._last_attempt_time = None
        self._backoff_multiplier = 1


class CircuitOpenError(Exception):
    """Raised when circuit is open and requests are being rejected."""
    pass


# Create a default circuit breaker instance
default_circuit_breaker = CircuitBreaker()


def with_circuit_breaker(
    failure_threshold: int = 3,
    recovery_timeout: float = 5.0,
    expected_exception: type = Exception,
    name: Optional[str] = None
) -> Callable:
    """Decorator factory for circuit breaker.
    
    Args:
        failure_threshold: Number of consecutive failures before opening circuit
        recovery_timeout: Seconds to wait before transitioning to HALF_OPEN
        expected_exception: Exception type to catch
        name: Optional name for the circuit breaker
        
    Returns:
        Decorator function
    """
    circuit_breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exception=expected_exception,
        name=name
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return circuit_breaker.call(func, *args, **kwargs)
        wrapper.circuit_breaker = circuit_breaker
        return wrapper
    
    return decorator
```