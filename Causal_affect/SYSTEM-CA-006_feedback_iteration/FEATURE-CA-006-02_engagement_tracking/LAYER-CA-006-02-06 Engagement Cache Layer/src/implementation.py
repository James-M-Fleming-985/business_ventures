```python
import asyncio
import time
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
import threading


class EngagementCache:
    """
    Cache layer for engagement metrics with automatic expiration and database fallback.
    
    Provides fast access to engagement metrics with configurable TTL policies
    and transparent database fallback on cache misses.
    """
    
    def __init__(self, db_client: Optional[Any] = None):
        """
        Initialize the engagement cache.
        
        Args:
            db_client: Database client for fallback queries on cache miss
        """
        self.db_client = db_client
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._ttl_policies: Dict[str, int] = {
            'view_count': 5,
            'like_count': 10,
            'comment_count': 15,
            'share_count': 20,
            'engagement_rate': 30,
            'default': 60
        }
    
    def set_ttl_policy(self, metric_type: str, ttl_seconds: int) -> None:
        """
        Set TTL policy for a specific metric type.
        
        Args:
            metric_type: Type of metric (e.g., 'view_count', 'like_count')
            ttl_seconds: Time-to-live in seconds
        """
        with self._lock:
            self._ttl_policies[metric_type] = ttl_seconds
    
    def get_ttl_policy(self, metric_type: str) -> int:
        """
        Get TTL policy for a specific metric type.
        
        Args:
            metric_type: Type of metric
            
        Returns:
            TTL in seconds for the metric type
        """
        with self._lock:
            return self._ttl_policies.get(metric_type, self._ttl_policies['default'])
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """
        Check if a cache entry has expired.
        
        Args:
            cache_entry: Cache entry with 'timestamp' and 'ttl' keys
            
        Returns:
            True if expired, False otherwise
        """
        timestamp = cache_entry.get('timestamp', 0)
        ttl = cache_entry.get('ttl', 0)
        current_time = time.time()
        return (current_time - timestamp) > ttl
    
    def get(self, key: str, metric_type: Optional[str] = None) -> Optional[Any]:
        """
        Get a value from cache with automatic expiration check and database fallback.
        
        Args:
            key: Cache key
            metric_type: Type of metric for TTL policy
            
        Returns:
            Cached value or None if not found and no database fallback
        """
        start_time = time.time()
        
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not self._is_expired(entry):
                    return entry['value']
                else:
                    # Remove expired entry
                    del self._cache[key]
        
        # Cache miss - fallback to database if available
        if self.db_client is not None:
            try:
                value = self._fetch_from_database(key, metric_type)
                if value is not None:
                    # Cache the fetched value
                    self.set(key, value, metric_type)
                    return value
            except Exception:
                pass
        
        return None
    
    def set(self, key: str, value: Any, metric_type: Optional[str] = None) -> None:
        """
        Set a value in cache with TTL based on metric type.
        
        Args:
            key: Cache key
            value: Value to cache
            metric_type: Type of metric for TTL policy
        """
        ttl = self.get_ttl_policy(metric_type) if metric_type else self._ttl_policies['default']
        
        with self._lock:
            self._cache[key] = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl,
                'metric_type': metric_type
            }
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if key didn't exist
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()
    
    def _fetch_from_database(self, key: str, metric_type: Optional[str] = None) -> Optional[Any]:
        """
        Fetch value from database on cache miss.
        
        Args:
            key: Cache key
            metric_type: Type of metric
            
        Returns:
            Value from database or None if not found
        """
        if self.db_client is None:
            return None
        
        try:
            if hasattr(self.db_client, 'get_metric'):
                return self.db_client.get_metric(key, metric_type)
            elif hasattr(self.db_client, 'get'):
                return self.db_client.get(key)
            elif callable(self.db_client):
                return self.db_client(key, metric_type)
        except Exception:
            pass
        
        return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_entries = len(self._cache)
            expired_entries = sum(1 for entry in self._cache.values() if self._is_expired(entry))
            
            return {
                'total_entries': total_entries,
                'active_entries': total_entries - expired_entries,
                'expired_entries': expired_entries
            }
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if self._is_expired(entry)
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    async def get_async(self, key: str, metric_type: Optional[str] = None) -> Optional[Any]:
        """
        Async version of get method.
        
        Args:
            key: Cache key
            metric_type: Type of metric for TTL policy
            
        Returns:
            Cached value or None if not found
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, self.get, key, metric_type
        )
    
    async def set_async(self, key: str, value: Any, metric_type: Optional[str] = None) -> None:
        """
        Async version of set method.
        
        Args:
            key: Cache key
            value: Value to cache
            metric_type: Type of metric for TTL policy
        """
        await asyncio.get_event_loop().run_in_executor(
            None, self.set, key, value, metric_type
        )
    
    def has_key(self, key: str) -> bool:
        """
        Check if key exists in cache and is not expired.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists and not expired, False otherwise
        """
        with self._lock:
            if key not in self._cache:
                return False
            return not self._is_expired(self._cache[key])
    
    def get_remaining_ttl(self, key: str) -> Optional[float]:
        """
        Get remaining TTL for a cache key.
        
        Args:
            key: Cache key
            
        Returns:
            Remaining seconds until expiration, or None if key doesn't exist
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            timestamp = entry.get('timestamp', 0)
            ttl = entry.get('ttl', 0)
            elapsed = time.time() - timestamp
            remaining = ttl - elapsed
            
            return max(0.0, remaining)
    
    def refresh(self, key: str, metric_type: Optional[str] = None) -> bool:
        """
        Refresh a cache entry by fetching from database.
        
        Args:
            key: Cache key
            metric_type: Type of metric
            
        Returns:
            True if refresh successful, False otherwise
        """
        if self.db_client is None:
            return False
        
        try:
            value = self._fetch_from_database(key, metric_type)
            if value is not None:
                self.set(key, value, metric_type)
                return True
        except Exception:
            pass
        
        return False
```