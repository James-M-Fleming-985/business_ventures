```python
import asyncio
import hashlib
import json
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import redis.asyncio as redis


@dataclass
class EventValidationResult:
    is_valid: bool
    error: Optional[str] = None


class EventCollector:
    """
    High-performance event collector that accepts, validates, and queues events to Redis.
    
    Handles 10K+ events/min with <100ms latency per event.
    """
    
    REQUIRED_FIELDS = {'event_type', 'user_id', 'timestamp'}
    MAX_EVENT_SIZE = 1024 * 1024  # 1MB
    
    def __init__(
        self,
        redis_url: str = 'redis://localhost:6379',
        queue_name: str = 'events',
        max_retries: int = 3,
        timeout: float = 0.1
    ):
        """
        Initialize the event collector.
        
        Args:
            redis_url: Redis connection URL
            queue_name: Name of the Redis queue for events
            max_retries: Maximum number of retries for Redis operations
            timeout: Timeout for Redis operations in seconds
        """
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.max_retries = max_retries
        self.timeout = timeout
        self._redis_client: Optional[redis.Redis] = None
        self._connection_lock = asyncio.Lock()
    
    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client with connection pooling."""
        if self._redis_client is None:
            async with self._connection_lock:
                if self._redis_client is None:
                    self._redis_client = await redis.from_url(
                        self.redis_url,
                        encoding='utf-8',
                        decode_responses=False,
                        socket_connect_timeout=self.timeout,
                        socket_timeout=self.timeout,
                        max_connections=50
                    )
        return self._redis_client
    
    def validate_event(self, event: Dict[str, Any]) -> EventValidationResult:
        """
        Validate event schema and structure.
        
        Args:
            event: Event dictionary to validate
            
        Returns:
            EventValidationResult with validation status and error message if invalid
        """
        if not isinstance(event, dict):
            return EventValidationResult(False, "Event must be a dictionary")
        
        missing_fields = self.REQUIRED_FIELDS - set(event.keys())
        if missing_fields:
            return EventValidationResult(
                False,
                f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        if not isinstance(event.get('event_type'), str) or not event['event_type']:
            return EventValidationResult(False, "event_type must be a non-empty string")
        
        if not isinstance(event.get('user_id'), (str, int)) or not str(event['user_id']):
            return EventValidationResult(False, "user_id must be a non-empty string or int")
        
        timestamp = event.get('timestamp')
        if not isinstance(timestamp, (int, float, str)):
            return EventValidationResult(False, "timestamp must be a number or ISO string")
        
        try:
            event_json = json.dumps(event)
            if len(event_json.encode('utf-8')) > self.MAX_EVENT_SIZE:
                return EventValidationResult(False, f"Event size exceeds {self.MAX_EVENT_SIZE} bytes")
        except (TypeError, ValueError) as e:
            return EventValidationResult(False, f"Event is not JSON serializable: {str(e)}")
        
        return EventValidationResult(True)
    
    def generate_event_id(self, event: Dict[str, Any]) -> str:
        """
        Generate a unique event ID based on event content and timestamp.
        
        Args:
            event: Event dictionary
            
        Returns:
            Unique event ID string
        """
        timestamp = time.time_ns()
        event_str = json.dumps(event, sort_keys=True)
        hash_input = f"{timestamp}:{event_str}".encode('utf-8')
        return hashlib.sha256(hash_input).hexdigest()[:16]
    
    async def collect_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect, validate, and queue an event to Redis.
        
        Args:
            event: Event dictionary to collect
            
        Returns:
            Dictionary with event_id and status
            
        Raises:
            ValueError: If event validation fails
            RuntimeError: If queuing to Redis fails after retries
        """
        start_time = time.time()
        
        validation_result = self.validate_event(event)
        if not validation_result.is_valid:
            raise ValueError(validation_result.error)
        
        event_id = self.generate_event_id(event)
        
        event_with_metadata = {
            'event_id': event_id,
            'collected_at': datetime.utcnow().isoformat(),
            **event
        }
        
        event_json = json.dumps(event_with_metadata)
        
        redis_client = await self._get_redis_client()
        
        for attempt in range(self.max_retries):
            try:
                await asyncio.wait_for(
                    redis_client.lpush(self.queue_name, event_json),
                    timeout=self.timeout
                )
                
                elapsed_time = (time.time() - start_time) * 1000
                
                return {
                    'event_id': event_id,
                    'status': 'queued',
                    'latency_ms': round(elapsed_time, 2)
                }
            except asyncio.TimeoutError:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Failed to queue event after {self.max_retries} attempts: timeout")
                await asyncio.sleep(0.01 * (attempt + 1))
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"Failed to queue event: {str(e)}")
                await asyncio.sleep(0.01 * (attempt + 1))
        
        raise RuntimeError(f"Failed to queue event after {self.max_retries} attempts")
    
    async def collect_events_batch(self, events: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """
        Collect multiple events in batch for higher throughput.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            List of results for each event
        """
        tasks = [self.collect_event(event) for event in events]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = []
        for result in results:
            if isinstance(result, Exception):
                output.append({
                    'status': 'failed',
                    'error': str(result)
                })
            else:
                output.append(result)
        
        return output
    
    async def close(self):
        """Close Redis connection and cleanup resources."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


async def main():
    """Example usage of EventCollector."""
    async with EventCollector() as collector:
        event = {
            'event_type': 'page_view',
            'user_id': 'user_123',
            'timestamp': time.time(),
            'page': '/home',
            'metadata': {'browser': 'chrome'}
        }
        
        try:
            result = await collector.collect_event(event)
            print(f"Event collected: {result}")
        except ValueError as e:
            print(f"Validation error: {e}")
        except RuntimeError as e:
            print(f"Collection error: {e}")


if __name__ == '__main__':
    asyncio.run(main())
```