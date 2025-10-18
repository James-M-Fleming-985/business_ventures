import asyncio
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis.asyncio as redis
from functools import wraps
import logging

from app.core.config import settings
from app.core.exceptions import RateLimitExceeded

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter with Redis backend."""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        max_requests: int = 100,
        time_window: int = 60,
        burst_size: Optional[int] = None
    ):
        self.redis = redis_client
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst_size = burst_size or max_requests
        
    async def check_rate_limit(
        self,
        identifier: str,
        cost: int = 1
    ) -> Dict[str, Any]:
        """Check if request is within rate limits."""
        key = f"rate_limit:{identifier}"
        current_time = time.time()
        
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, current_time - self.time_window)
        pipe.zcard(key)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.expire(key, self.time_window + 1)
        
        results = await pipe.execute()
        current_requests = results[1]
        
        if current_requests >= self.max_requests:
            retry_after = await self._get_retry_after(key)
            raise RateLimitExceeded(
                message=f"Rate limit exceeded: {current_requests}/{self.max_requests}",
                retry_after=retry_after
            )
        
        return {
            "current": current_requests,
            "limit": self.max_requests,
            "remaining": self.max_requests - current_requests,
            "reset": int(current_time + self.time_window)
        }
    
    async def _get_retry_after(self, key: str) -> int:
        """Calculate retry after seconds."""
        oldest_request = await self.redis.zrange(key, 0, 0, withscores=True)
        if oldest_request:
            oldest_time = oldest_request[0][1]
            retry_after = int(oldest_time + self.time_window - time.time())
            return max(1, retry_after)
        return self.time_window


class SlidingWindowRateLimiter(RateLimiter):
    """Sliding window rate limiter for more accurate limiting."""
    
    async def check_rate_limit(
        self,
        identifier: str,
        cost: int = 1
    ) -> Dict[str, Any]:
        """Check rate limit with sliding window."""
        key = f"sliding:{identifier}"
        current_time = time.time()
        window_start = current_time - self.time_window
        
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, "-inf", window_start)
        pipe.zcount(key, window_start, current_time)
        
        for _ in range(cost):
            pipe.zadd(key, {f"{current_time}:{_}": current_time})
            
        pipe.expire(key, self.time_window * 2)
        
        results = await pipe.execute()
        current_count = results[1]
        
        if current_count + cost > self.max_requests:
            retry_after = await self._get_retry_after(key)
            raise RateLimitExceeded(
                message=f"Rate limit exceeded: {current_count + cost}/{self.max_requests}",
                retry_after=retry_after
            )
        
        return {
            "current": current_count + cost,
            "limit": self.max_requests,
            "remaining": max(0, self.max_requests - current_count - cost),
            "reset": int(current_time + self.time_window)
        }


class AdaptiveRateLimiter(SlidingWindowRateLimiter):
    """Adaptive rate limiter that adjusts based on response times."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response_threshold_ms = 1000
        self.reduction_factor = 0.8
        
    async def record_response_time(
        self,
        identifier: str,
        response_time_ms: float
    ):
        """Record response time and adapt limits."""
        key = f"response_times:{identifier}"
        
        await self.redis.lpush(key, response_time_ms)
        await self.redis.ltrim(key, 0, 99)
        await self.redis.expire(key, 3600)
        
        if response_time_ms > self.response_threshold_ms:
            await self._reduce_limit(identifier)
    
    async def _reduce_limit(self, identifier: str):
        """Temporarily reduce rate limit for identifier."""
        key = f"reduced_limit:{identifier}"
        current_limit = await self.redis.get(key)
        
        if current_limit:
            new_limit = int(float(current_limit) * self.reduction_factor)
        else:
            new_limit = int(self.max_requests * self.reduction_factor)
        
        await self.redis.setex(key, 300, max(10, new_limit))
        logger.info(f"Reduced rate limit for {identifier} to {new_limit}")
    
    async def get_current_limit(self, identifier: str) -> int:
        """Get current limit for identifier."""
        key = f"reduced_limit:{identifier}"
        reduced_limit = await self.redis.get(key)
        
        if reduced_limit:
            return int(reduced_limit)
        return self.max_requests


def rate_limit(
    max_requests: int = 100,
    time_window: int = 60,
    identifier_func: Optional[callable] = None
):
    """Decorator for rate limiting endpoints."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from app.core.dependencies import get_redis
            
            redis_client = await get_redis()
            limiter = RateLimiter(
                redis_client,
                max_requests=max_requests,
                time_window=time_window
            )
            
            identifier = "default"
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            
            await limiter.check_rate_limit(identifier)
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class RateLimitManager:
    """Manages multiple rate limiters with different strategies."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.limiters: Dict[str, RateLimiter] = {}
        
    def register_limiter(
        self,
        name: str,
        limiter_class: type[RateLimiter],
        **config
    ):
        """Register a rate limiter."""
        self.limiters[name] = limiter_class(self.redis, **config)
        
    async def check_limit(
        self,
        limiter_name: str,
        identifier: str,
        cost: int = 1
    ) -> Dict[str, Any]:
        """Check rate limit using named limiter."""
        if limiter_name not in self.limiters:
            raise ValueError(f"Unknown limiter: {limiter_name}")
            
        return await self.limiters[limiter_name].check_rate_limit(
            identifier,
            cost
        )
    
    async def get_all_limits(
        self,
        identifier: str
    ) -> Dict[str, Dict[str, Any]]:
        """Get rate limit info for all limiters."""
        results = {}
        
        for name, limiter in self.limiters.items():
            try:
                results[name] = await limiter.check_rate_limit(
                    identifier,
                    cost=0
                )
            except RateLimitExceeded as e:
                results[name] = {
                    "exceeded": True,
                    "retry_after": e.retry_after
                }
        
        return results