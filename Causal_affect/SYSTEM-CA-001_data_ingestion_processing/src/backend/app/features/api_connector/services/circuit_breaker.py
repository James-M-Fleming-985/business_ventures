import asyncio
import time
import logging
from typing import Optional, Dict, Any, Callable, TypeVar, Generic
from enum import Enum
from datetime import datetime, timedelta
import redis.asyncio as redis
from functools import wraps
from contextlib import asynccontextmanager

from app.core.exceptions import CircuitOpenError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker(Generic[T]):
    """Circuit breaker pattern implementation."""
    
    def __init__(
        self,
        name: str,
        redis_client: redis.Redis,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type[Exception] = Exception,
        success_threshold: int = 2
    ):
        self.name = name
        self.redis = redis_client
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        
    async def get_state(self) -> CircuitState:
        """Get current circuit state."""
        state = await self.redis.get(f"circuit:{self.name}:state")
        return CircuitState(state.decode()) if state else CircuitState.CLOSED
    
    async def _set_state(self, state: CircuitState):
        """Set circuit state."""
        await self.redis.set(f"circuit:{self.name}:state", state.value)
        logger.info(f"Circuit {self.name} state changed to {state.value}")
    
    async def _get_failure_count(self) -> int:
        """Get current failure count."""
        count = await self.redis.get(f"circuit:{self.name}:failures")
        return int(count) if count else 0
    
    async def _increment_failure_count(self):
        """Increment failure count."""
        key = f"circuit:{self.name}:failures"
        await self.redis.incr(key)
        await self.redis.expire(key, self.recovery_timeout * 2)
    
    async def _reset_failure_count(self):
        """Reset failure count."""
        await self.redis.delete(f"circuit:{self.name}:failures")
    
    async def _get_success_count(self) -> int:
        """Get success count in half-open state."""
        count = await self.redis.get(f"circuit:{self.name}:successes")
        return int(count) if count else 0
    
    async def _increment_success_count(self):
        """Increment success count."""
        key = f"circuit:{self.name}:successes"
        await self.redis.incr(key)
        await self.redis.expire(key, self.recovery_timeout)
    
    async def _reset_success_count(self):
        """Reset success count."""
        await self.redis.delete(f"circuit:{self.name}:successes")
    
    async def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        last_failure_time = await self.redis.get(f"circuit:{self.name}:last_failure")
        if not last_failure_time:
            return True
            
        last_failure = float(last_failure_time)
        return time.time() - last_failure >= self.recovery_timeout
    
    async def _record_failure(self):
        """Record a failure."""
        await self.redis.set(
            f"circuit:{self.name}:last_failure",
            time.time(),
            ex=self.recovery_timeout * 2
        )
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        state = await self.get_state()
        
        if state == CircuitState.OPEN:
            if await self._should_attempt_reset():
                await self._set_state(CircuitState.HALF_OPEN)
                await self._reset_success_count()
                state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError(f"Circuit {self.name} is OPEN")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await self._on_success(state)
            return result
        except self.expected_exception as e:
            await self._on_failure(state)
            raise e
    
    async def _on_success(self, state: CircuitState):
        """Handle successful call."""
        if state == CircuitState.HALF_OPEN:
            success_count = await self._get_success_count()
            await self._increment_success_count()
            
            if success_count + 1 >= self.success_threshold:
                await self._set_state(CircuitState.CLOSED)
                await self._reset_failure_count()
                await self._reset_success_count()
    
    async def _on_failure(self, state: CircuitState):
        """Handle failed call."""
        await self._record_failure()
        
        if state == CircuitState.HALF_OPEN:
            await self._set_state(CircuitState.OPEN)
            await self._reset_success_count()
        else:
            failure_count = await self._get_failure_count()
            await self._increment_failure_count()
            
            if failure_count + 1 >= self.failure_threshold:
                await self._set_state(CircuitState.OPEN)
    
    @asynccontextmanager
    async def context(self):
        """Context manager for circuit breaker."""
        state = await self.get_state()
        
        if state == CircuitState.OPEN:
            if await self._should_attempt_reset():
                await self._set_state(CircuitState.HALF_OPEN)
                await self._reset_success_count()
                state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError(f"Circuit {self.name} is OPEN")
        
        try:
            yield
            await self._on_success(state)
        except self.expected_exception as e:
            await self._on_failure(state)
            raise e
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        state = await self.get_state()
        failures = await self._get_failure_count()
        successes = await self._get_success_count()
        
        last_failure = await self.redis.get(f"circuit:{self.name}:last_failure")
        last_failure_time = None
        if last_failure:
            last_failure_time = datetime.fromtimestamp(float(last_failure)).isoformat()
        
        return {
            "name": self.name,
            "state": state.value,
            "failures": failures,
            "successes": successes,
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
            "last_failure_time": last_failure_time,
            "recovery_timeout": self.recovery_timeout
        }
    
    async def reset(self):
        """Manually reset circuit breaker."""
        await self._set_state(CircuitState.CLOSED)
        await self._reset_failure_count()
        await self._reset_success_count()
        await self.redis.delete(f"circuit:{self.name}:last_failure")


class AdaptiveCircuitBreaker(CircuitBreaker[T]):
    """Circuit breaker that adapts thresholds based on error rates."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_rate_window = 300  # 5 minutes
        self.min_calls_for_adaptation = 10
        
    async def _record_call(self, success: bool):
        """Record call for error rate calculation."""
        current_time = time.time()
        key = f"circuit:{self.name}:calls"
        
        value = f"{current_time}:{'1' if success else '0'}"
        await self.redis.zadd(key, {value: current_time})
        
        # Clean old entries
        await self.redis.zremrangebyscore(key, 0, current_time - self.error_rate_window)
        await self.redis.expire(key, self.error_rate_window * 2)
    
    async def _get_error_rate(self) -> Optional[float]:
        """Calculate current error rate."""
        current_time = time.time()
        key = f"circuit:{self.name}:calls"
        
        calls = await self.redis.zrangebyscore(
            key,
            current_time - self.error_rate_window,
            current_time
        )
        
        if len(calls) < self.min_calls_for_adaptation:
            return None
        
        failures = sum(1 for call in calls if call.decode().split(':')[1] == '0')
        return failures / len(calls)
    
    async def _adapt_thresholds(self):
        """Adapt thresholds based on error rate."""
        error_rate = await self._get_error_rate()
        
        if error_rate is None:
            return
        
        if error_rate > 0.5:
            # High error rate: be more conservative
            self.failure_threshold = max(3, self.failure_threshold - 1)
            self.recovery_timeout = min(300, self.recovery_timeout + 30)
        elif error_rate < 0.1:
            # Low error rate: be more lenient
            self.failure_threshold = min(10, self.failure_threshold + 1)
            self.recovery_timeout = max(30, self.recovery_timeout - 10)
    
    async def _on_success(self, state: CircuitState):
        """Handle successful call with adaptation."""
        await self._record_call(True)
        await self._adapt_thresholds()
        await super()._on_success(state)
    
    async def _on_failure(self, state: CircuitState):
        """Handle failed call with adaptation."""
        await self._record_call(False)
        await self._adapt_thresholds()
        await super()._on_failure(state)


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type[Exception] = Exception
):
    """Decorator for circuit breaker protection."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from app.core.dependencies import get_redis
            
            redis_client = await get_redis()
            breaker = CircuitBreaker(
                name=name,
                redis_client=redis_client,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                expected_exception=expected_exception
            )
            
            return await breaker.call(func, *args, **kwargs)
        
        return wrapper
    return decorator


class CircuitBreakerManager:
    """Manages multiple circuit breakers."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.breakers: Dict[str, CircuitBreaker] = {}
    
    def register_breaker(
        self,
        name: str,
        breaker_class: type[CircuitBreaker] = CircuitBreaker,
        **config
    ) -> CircuitBreaker:
        """Register a circuit breaker."""
        breaker = breaker_class(name=name, redis_client=self.redis, **config)
        self.breakers[name] = breaker
        return breaker
    
    async def get_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get a registered circuit breaker."""
        return self.breakers.get(name)
    
    async def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        stats = {}
        for name, breaker in self.breakers.items():
            stats[name] = await breaker.get_stats()
        return stats
    
    async def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self.breakers.values():
            await breaker.reset()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all circuits."""
        healthy_count = 0
        open_circuits = []
        
        for name, breaker in self.breakers.items():
            state = await breaker.get_state()
            if state == CircuitState.CLOSED:
                healthy_count += 1
            elif state == CircuitState.OPEN:
                open_circuits.append(name)
        
        total_circuits = len(self.breakers)
        health_percentage = (healthy_count / total_circuits * 100) if total_circuits > 0 else 100
        
        return {
            "healthy": healthy_count == total_circuits,
            "total_circuits": total_circuits,
            "healthy_circuits": healthy_count,
            "open_circuits": open_circuits,
            "health_percentage": health_percentage
        }