```python
import logging
import time
import traceback
from enum import Enum
from typing import Callable, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker implementation for handling consecutive failures."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of consecutive failures before opening circuit
            timeout: Seconds before attempting to close circuit again
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
    
    def record_success(self):
        """Record a successful operation."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def record_failure(self):
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} consecutive failures")
    
    def can_execute(self) -> bool:
        """Check if operation can be executed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and \
               datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering half-open state")
                return True
            return False
        
        # HALF_OPEN state
        return True
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        return self.state == CircuitState.OPEN


class AnalyticsErrorHandler:
    """
    Error handler for analytics operations with retry logic,
    circuit breaker, and fallback mechanisms.
    """
    
    def __init__(self, provider: str = "default", fallback_provider: Optional[Callable] = None):
        """
        Initialize error handler.
        
        Args:
            provider: Name of the analytics provider
            fallback_provider: Fallback function to call when circuit opens
        """
        self.provider = provider
        self.fallback_provider = fallback_provider
        self.circuit_breaker = CircuitBreaker(failure_threshold=5)
        self.retry_delays = [1, 2, 4]
        self.alert_callbacks = []
    
    def add_alert_callback(self, callback: Callable):
        """Add a callback function for alerts."""
        self.alert_callbacks.append(callback)
    
    def _send_alert(self, error_type: str, message: str, details: dict):
        """Send alert to all registered callbacks."""
        alert_data = {
            "error_type": error_type,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "provider": self.provider
        }
        
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")
    
    def _log_error(self, operation: str, error: Exception, attempt: Optional[int] = None):
        """
        Log error with provider, operation, and stack trace.
        
        Args:
            operation: Name of the operation that failed
            error: The exception that occurred
            attempt: Retry attempt number if applicable
        """
        stack_trace = traceback.format_exc()
        log_message = f"Provider: {self.provider}, Operation: {operation}, Error: {str(error)}"
        
        if attempt is not None:
            log_message += f", Attempt: {attempt}"
        
        logger.error(log_message)
        logger.debug(f"Stack trace:\n{stack_trace}")
    
    def _is_authentication_error(self, error: Exception) -> bool:
        """Check if error is an authentication failure."""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        auth_keywords = [
            'auth', 'authentication', 'unauthorized', 'forbidden',
            '401', '403', 'credential', 'token', 'permission'
        ]
        
        return any(keyword in error_str or keyword in error_type 
                  for keyword in auth_keywords)
    
    def execute_with_retry(self, operation: str, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic and error handling.
        
        Args:
            operation: Name of the operation
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of the function execution
            
        Raises:
            Exception: If all retries fail
        """
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker is open for provider {self.provider}")
            if self.fallback_provider:
                logger.info(f"Triggering fallback provider for operation: {operation}")
                return self.fallback_provider(*args, **kwargs)
            else:
                raise Exception(f"Circuit breaker is open and no fallback provider available")
        
        last_error = None
        
        for attempt in range(len(self.retry_delays) + 1):
            try:
                result = func(*args, **kwargs)
                self.circuit_breaker.record_success()
                return result
            
            except Exception as error:
                last_error = error
                self._log_error(operation, error, attempt=attempt + 1)
                
                # Check for authentication errors
                if self._is_authentication_error(error):
                    self._send_alert(
                        "authentication_failure",
                        f"Authentication failed for provider {self.provider}",
                        {
                            "operation": operation,
                            "error": str(error),
                            "provider": self.provider
                        }
                    )
                
                # If this is the last attempt, break
                if attempt >= len(self.retry_delays):
                    break
                
                # Wait before retrying
                delay = self.retry_delays[attempt]
                logger.info(f"Retrying operation '{operation}' in {delay} seconds (attempt {attempt + 1})")
                time.sleep(delay)
        
        # All retries failed
        self.circuit_breaker.record_failure()
        
        # If circuit just opened and we have a fallback, use it
        if self.circuit_breaker.is_open() and self.fallback_provider:
            logger.info(f"Circuit opened, triggering fallback provider for operation: {operation}")
            return self.fallback_provider(*args, **kwargs)
        
        raise last_error
    
    def get_circuit_state(self) -> str:
        """Get the current circuit breaker state."""
        return self.circuit_breaker.state.value
    
    def get_failure_count(self) -> int:
        """Get the current failure count."""
        return self.circuit_breaker.failure_count
    
    def reset_circuit(self):
        """Reset the circuit breaker to closed state."""
        self.circuit_breaker.failure_count = 0
        self.circuit_breaker.state = CircuitState.CLOSED
        self.circuit_breaker.last_failure_time = None
```