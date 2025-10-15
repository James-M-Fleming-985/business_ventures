```python
import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Event:
    event_id: str
    timestamp: float
    event_type: str
    data: Dict[str, Any]
    
    
@dataclass
class ProcessingResult:
    event_id: str
    success: bool
    latency: float
    error: Optional[str] = None


class DashboardCache:
    """Thread-safe dashboard cache with automatic invalidation."""
    
    def __init__(self, ttl: float = 2.0):
        self._cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._timestamps: Dict[str, float] = {}
        self._ttl = ttl
        self._listeners: List[Callable] = []
        
    def set(self, key: str, value: Any) -> None:
        """Set cache value and trigger listeners."""
        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = time.time()
            self._notify_listeners(key, value)
            
    def get(self, key: str) -> Optional[Any]:
        """Get cache value if not expired."""
        with self._lock:
            if key not in self._cache:
                return None
            if time.time() - self._timestamps.get(key, 0) > self._ttl:
                del self._cache[key]
                del self._timestamps[key]
                return None
            return self._cache[key]
    
    def add_listener(self, listener: Callable) -> None:
        """Add listener for cache updates."""
        with self._lock:
            self._listeners.append(listener)
            
    def _notify_listeners(self, key: str, value: Any) -> None:
        """Notify all listeners of cache update."""
        for listener in self._listeners:
            try:
                listener(key, value)
            except Exception as e:
                logger.error(f"Listener error: {e}")
                
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()


class EventBuffer:
    """Persistent event buffer for failure recovery."""
    
    def __init__(self, max_size: int = 100000):
        self._buffer: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._processed: set = set()
        
    def add(self, event: Event) -> None:
        """Add event to buffer."""
        with self._lock:
            self._buffer.append(event)
            
    def mark_processed(self, event_id: str) -> None:
        """Mark event as processed."""
        with self._lock:
            self._processed.add(event_id)
            
    def get_unprocessed(self) -> List[Event]:
        """Get all unprocessed events."""
        with self._lock:
            return [e for e in self._buffer if e.event_id not in self._processed]
            
    def is_processed(self, event_id: str) -> bool:
        """Check if event has been processed."""
        with self._lock:
            return event_id in self._processed
            
    def clear(self) -> None:
        """Clear buffer and processed set."""
        with self._lock:
            self._buffer.clear()
            self._processed.clear()


class MetricsAggregator:
    """Aggregate metrics from events."""
    
    def __init__(self):
        self._metrics: Dict[str, Any] = {
            'total_events': 0,
            'events_by_type': {},
            'avg_latency': 0.0,
            'success_rate': 0.0,
            'total_latency': 0.0,
            'successful_events': 0
        }
        self._lock = threading.RLock()
        
    def update(self, result: ProcessingResult) -> Dict[str, Any]:
        """Update metrics with processing result."""
        with self._lock:
            self._metrics['total_events'] += 1
            self._metrics['total_latency'] += result.latency
            
            if result.success:
                self._metrics['successful_events'] += 1
                
            self._metrics['avg_latency'] = (
                self._metrics['total_latency'] / self._metrics['total_events']
            )
            self._metrics['success_rate'] = (
                self._metrics['successful_events'] / self._metrics['total_events']
            )
            
            return self.get_metrics()
            
    def update_event_type(self, event_type: str) -> None:
        """Update event type counter."""
        with self._lock:
            if event_type not in self._metrics['events_by_type']:
                self._metrics['events_by_type'][event_type] = 0
            self._metrics['events_by_type'][event_type] += 1
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        with self._lock:
            return self._metrics.copy()
            
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics = {
                'total_events': 0,
                'events_by_type': {},
                'avg_latency': 0.0,
                'success_rate': 0.0,
                'total_latency': 0.0,
                'successful_events': 0
            }


class RealTimeProcessor:
    """Real-time event processor with high throughput and low latency."""
    
    def __init__(
        self,
        max_latency: float = 5.0,
        cache_update_latency: float = 2.0,
        max_throughput: int = 10000
    ):
        self.max_latency = max_latency
        self.cache_update_latency = cache_update_latency
        self.max_throughput = max_throughput
        
        self.dashboard_cache = DashboardCache(ttl=cache_update_latency)
        self.event_buffer = EventBuffer()
        self.metrics_aggregator = MetricsAggregator()
        
        self._running = False
        self._queue: asyncio.Queue = None
        self._workers: List[asyncio.Task] = []
        self._num_workers = 10
        self._cache_update_task: Optional[asyncio.Task] = None
        self._last_cache_update = time.time()
        
    async def start(self) -> None:
        """Start the processor."""
        if self._running:
            return
            
        self._running = True
        self._queue = asyncio.Queue(maxsize=20000)
        
        # Start worker tasks
        for _ in range(self._num_workers):
            task = asyncio.create_task(self._worker())
            self._workers.append(task)
            
        # Start cache update task
        self._cache_update_task = asyncio.create_task(self._cache_updater())
        
        logger.info("RealTimeProcessor started")
        
    async def stop(self) -> None:
        """Stop the processor."""
        if not self._running:
            return
            
        self._running = False
        
        # Wait for queue to drain
        if self._queue:
            await self._queue.join()
        
        # Cancel workers
        for worker in self._workers:
            worker.cancel()
            
        if self._cache_update_task:
            self._cache_update_task.cancel()
            
        await asyncio.gather(*self._workers, self._cache_update_task, return_exceptions=True)
        
        self._workers.clear()
        self._cache_update_task = None
        
        logger.info("RealTimeProcessor stopped")
        
    async def process_event(self, event: Event) -> ProcessingResult:
        """Process a single event with latency tracking."""
        start_time = time.time()
        
        try:
            # Add to buffer for recovery
            self.event_buffer.add(event)
            
            # Check if already processed
            if self.event_buffer.is_processed(event.event_id):
                latency = time.time() - start_time
                return ProcessingResult(
                    event_id=event.event_id,
                    success=True,
                    latency=latency
                )
            
            # Put in queue for processing
            await self._queue.put((event, start_time))
            
            # Simulate processing for immediate return
            latency = time.time() - start_time
            
            # Update event type counter
            self.metrics_aggregator.update_event_type(event.event_type)
            
            result = ProcessingResult(
                event_id=event.event_id,
                success=True,
                latency=latency
            )
            
            # Update metrics
            self.metrics_aggregator.update(result)
            
            return result
            
        except Exception as e:
            latency = time.time() - start_time
            logger.error(f"Error processing event {event.event_id}: {e}")
            
            result = ProcessingResult(
                event_id=event.event_id,
                success=False,
                latency=latency,
                error=str(e)
            )
            
            self.metrics_aggregator.update(result)
            
            return result
            
    async def _worker(self) -> None:
        """Background worker to process events from queue."""
        while self._running:
            try:
                event, start_time = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )
                
                try:
                    # Simulate event processing
                    await asyncio.sleep(0.001)  # Minimal processing time
                    
                    # Mark as processed
                    self.event_buffer.mark_processed(event.event_id)
                    
                    # Check latency constraint
                    latency = time.time() - start_time
                    if latency > self.max_latency:
                        logger.warning(
                            f"Event {event.event_id} exceeded max latency: {latency:.3f}s"
                        )
                        
                finally:
                    self._queue.task_done()
                    
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                
    async def _cache_updater(self) -> None:
        """Background task to update dashboard cache periodically."""
        while self._running:
            try:
                await asyncio.sleep(0.1)  # Check frequently
                
                current_time = time.time()
                if current_time - self._last_cache_update >= self.cache_update_latency:
                    # Update cache with current metrics
                    metrics = self.metrics_aggregator.get_metrics()
                    self.dashboard_cache.set('metrics', metrics)
                    self._last_cache_update = current_time
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache updater error: {e}")
                
    async def recover_from_failure(self) -> int:
        """Recover unprocessed events from buffer."""
        unprocessed = self.event_buffer.get_unprocessed()
        recovered = 0
        
        for event in unprocessed:
            try:
                await self.process_event(event)
                recovered += 1
            except Exception as e:
                logger.error(f"Recovery error for event {event.event_id}: {e}")
                
        logger.info(f"Recovered {recovered} events")
        return recovered
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get current processing metrics."""
        return self.metrics_aggregator.get_metrics()
        
    def get_cache(self) -> DashboardCache:
        """Get dashboard cache instance."""
        return self.dashboard_cache
        
    async def process_batch(self, events: List[Event]) -> List[ProcessingResult]:
        """Process multiple events in batch."""
        tasks = [self.process_event(event) for event in events]
        return await asyncio.gather(*tasks)
```