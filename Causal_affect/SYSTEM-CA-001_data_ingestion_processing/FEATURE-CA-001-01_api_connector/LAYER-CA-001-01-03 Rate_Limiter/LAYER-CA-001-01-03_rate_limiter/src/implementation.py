```python
import time
import threading
from typing import Optional, Dict, Any
import redis
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_tokens: int
    refill_rate: float  # tokens per second
    refill_interval: float = 1.0  # seconds
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    key_prefix: str = 'rate_limiter'


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass


class TokenBucket(ABC):
    """Abstract base class for token bucket implementations."""
    
    @abstractmethod
    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens from the bucket."""
        pass
    
    @abstractmethod
    def get_tokens(self) -> float:
        """Get current number of tokens."""
        pass


class LocalTokenBucket(TokenBucket):
    """Thread-safe token bucket implementation for single process."""
    
    def __init__(self, max_tokens: int, refill_rate: float):
        """
        Initialize local token bucket.
        
        Args:
            max_tokens: Maximum number of tokens in bucket
            refill_rate: Rate of token refill (tokens per second)
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokens = float(max_tokens)
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def get_tokens(self) -> float:
        """Get current number of tokens."""
        with self.lock:
            self._refill()
            return self.tokens


class DistributedTokenBucket(TokenBucket):
    """Redis-based token bucket for distributed systems."""
    
    def __init__(self, config: RateLimitConfig, key: str):
        """
        Initialize distributed token bucket.
        
        Args:
            config: Rate limit configuration
            key: Unique key for this bucket
        """
        self.config = config
        self.key = f"{config.key_prefix}:{key}"
        self.redis_client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            password=config.redis_password,
            decode_responses=True
        )
        
        # Initialize bucket if it doesn't exist
        self._initialize_bucket()
    
    def _initialize_bucket(self) -> None:
        """Initialize bucket in Redis if it doesn't exist."""
        lua_script = """
        local key = KEYS[1]
        local max_tokens = tonumber(ARGV[1])
        local current_time = tonumber(ARGV[2])
        
        if redis.call('EXISTS', key) == 0 then
            redis.call('HMSET', key, 
                'tokens', max_tokens,
                'last_refill', current_time
            )
            redis.call('EXPIRE', key, 3600)
        end
        return 1
        """
        
        self.redis_client.eval(
            lua_script,
            1,
            self.key,
            self.config.max_tokens,
            time.time()
        )
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        # Lua script for atomic token consumption with refill
        lua_script = """
        local key = KEYS[1]
        local requested_tokens = tonumber(ARGV[1])
        local max_tokens = tonumber(ARGV[2])
        local refill_rate = tonumber(ARGV[3])
        local current_time = tonumber(ARGV[4])
        
        local bucket = redis.call('HGETALL', key)
        if #bucket == 0 then
            return 0
        end
        
        local current_tokens = tonumber(bucket[2])
        local last_refill = tonumber(bucket[4])
        
        -- Calculate refill
        local elapsed = current_time - last_refill
        local tokens_to_add = elapsed * refill_rate
        current_tokens = math.min(max_tokens, current_tokens + tokens_to_add)
        
        -- Check if we can consume
        if current_tokens >= requested_tokens then
            current_tokens = current_tokens - requested_tokens
            redis.call('HMSET', key,
                'tokens', current_tokens,
                'last_refill', current_time
            )
            redis.call('EXPIRE', key, 3600)
            return 1
        else
            -- Update refill time even if we can't consume
            redis.call('HMSET', key,
                'tokens', current_tokens,
                'last_refill', current_time
            )
            redis.call('EXPIRE', key, 3600)
            return 0
        end
        """
        
        result = self.redis_client.eval(
            lua_script,
            1,
            self.key,
            tokens,
            self.config.max_tokens,
            self.config.refill_rate,
            time.time()
        )
        
        return bool(result)
    
    def get_tokens(self) -> float:
        """Get current number of tokens."""
        # Lua script to get current tokens with refill
        lua_script = """
        local key = KEYS[1]
        local max_tokens = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local current_time = tonumber(ARGV[3])
        
        local bucket = redis.call('HGETALL', key)
        if #bucket == 0 then
            return max_tokens
        end
        
        local current_tokens = tonumber(bucket[2])
        local last_refill = tonumber(bucket[4])
        
        -- Calculate refill
        local elapsed = current_time - last_refill
        local tokens_to_add = elapsed * refill_rate
        current_tokens = math.min(max_tokens, current_tokens + tokens_to_add)
        
        return current_tokens
        """
        
        result = self.redis_client.eval(
            lua_script,
            1,
            self.key,
            self.config.max_tokens,
            self.config.refill_rate,
            time.time()
        )
        
        return float(result)


class RateLimiter:
    """Rate limiter implementation with support for distributed systems."""
    
    def __init__(self, config: RateLimitConfig, distributed: bool = False):
        """
        Initialize rate limiter.
        
        Args:
            config: Rate limit configuration
            distributed: Whether to use distributed (Redis) implementation
        """
        self.config = config
        self.distributed = distributed
        self.buckets: Dict[str, TokenBucket] = {}
        self.lock = threading.Lock()
    
    def _get_bucket(self, key: str) -> TokenBucket:
        """Get or create token bucket for given key."""
        with self.lock:
            if key not in self.buckets:
                if self.distributed:
                    self.buckets[key] = DistributedTokenBucket(self.config, key)
                else:
                    self.buckets[key] = LocalTokenBucket(
                        self.config.max_tokens,
                        self.config.refill_rate
                    )
            return self.buckets[key]
    
    def acquire(self, key: str = "default", tokens: int = 1) -> bool:
        """
        Attempt to acquire tokens for rate limiting.
        
        Args:
            key: Identifier for rate limit bucket
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens were acquired, False otherwise
        """
        bucket = self._get_bucket(key)
        return bucket.consume(tokens)
    
    def acquire_or_wait(self, key: str = "default", tokens: int = 1, 
                       timeout: Optional[float] = None) -> bool:
        """
        Attempt to acquire tokens, waiting if necessary.
        
        Args:
            key: Identifier for rate limit bucket
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait (seconds)
            
        Returns:
            True if tokens were acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            if self.acquire(key, tokens):
                return True
            
            if timeout and (time.time() - start_time) >= timeout:
                return False
            
            # Calculate wait time based on refill rate
            wait_time = tokens / self.config.refill_rate
            time.sleep(min(wait_time * 0.1, 0.1))  # Check frequently
    
    def check_limit(self, key: str = "default", tokens: int = 1) -> None:
        """
        Check rate limit and raise exception if exceeded.
        
        Args:
            key: Identifier for rate limit bucket
            tokens: Number of tokens to check
            
        Raises:
            RateLimitExceeded: If rate limit would be exceeded
        """
        if not self.acquire(key, tokens):
            raise RateLimitExceeded(f"Rate limit exceeded for key: {key}")
    
    def get_current_tokens(self, key: str = "default") -> float:
        """
        Get current number of tokens available.
        
        Args:
            key: Identifier for rate limit bucket
            
        Returns:
            Number of tokens available
        """
        bucket = self._get_bucket(key)
        return bucket.get_tokens()
    
    def reset(self, key: str = "default") -> None:
        """
        Reset rate limiter for given key.
        
        Args:
            key: Identifier for rate limit bucket
        """
        with self.lock:
            if key in self.buckets:
                if self.distributed:
                    # For distributed, reinitialize the bucket
                    self.buckets[key] = DistributedTokenBucket(self.config, key)
                else:
                    # For local, just reset the tokens
                    bucket = self.buckets[key]
                    bucket.tokens = float(bucket.max_tokens)
                    bucket.last_refill = time.time()


# Convenience functions for common use cases
def create_rate_limiter(max_requests_per_second: float, 
                       burst_size: Optional[int] = None,
                       distributed: bool = False,
                       redis_config: Optional[Dict[str, Any]] = None) -> RateLimiter:
    """
    Create a rate limiter with simplified configuration.
    
    Args:
        max_requests_per_second: Maximum sustained request rate
        burst_size: Maximum burst size (defaults to rate)
        distributed: Whether to use distributed implementation
        redis_config: Redis configuration for distributed mode
        
    Returns:
        Configured RateLimiter instance
    """
    if burst_size is None:
        burst_size = int(max_requests_per_second)
    
    config = RateLimitConfig(
        max_tokens=burst_size,
        refill_rate=max_requests_per_second
    )
    
    if redis_config:
        for key, value in redis_config.items():
            setattr(config, key, value)
    
    return RateLimiter(config, distributed=distributed)
```