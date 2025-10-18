```python
import time
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import statistics


class MetricsCollector:
    """A thread-safe metrics collection system for tracking various application metrics."""
    
    def __init__(self):
        """Initialize the MetricsCollector with storage for different metric types."""
        self._counters = defaultdict(int)
        self._gauges = defaultdict(float)
        self._timers = defaultdict(list)
        self._histograms = defaultdict(list)
        self._rates = defaultdict(lambda: deque(maxlen=1000))
        self._lock = threading.RLock()
        self._timer_contexts = {}
    
    def increment(self, name: str, value: int = 1) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: The name of the counter metric
            value: The amount to increment by (default: 1)
        """
        with self._lock:
            self._counters[name] += value
    
    def decrement(self, name: str, value: int = 1) -> None:
        """
        Decrement a counter metric.
        
        Args:
            name: The name of the counter metric
            value: The amount to decrement by (default: 1)
        """
        with self._lock:
            self._counters[name] -= value
    
    def gauge(self, name: str, value: float) -> None:
        """
        Set a gauge metric to a specific value.
        
        Args:
            name: The name of the gauge metric
            value: The value to set
        """
        with self._lock:
            self._gauges[name] = value
    
    def timing(self, name: str, duration: float) -> None:
        """
        Record a timing measurement.
        
        Args:
            name: The name of the timing metric
            duration: The duration in milliseconds
        """
        with self._lock:
            self._timers[name].append(duration)
    
    def timer(self, name: str):
        """
        Context manager for timing operations.
        
        Args:
            name: The name of the timer metric
            
        Returns:
            A context manager that records timing when exited
        """
        return TimerContext(self, name)
    
    def histogram(self, name: str, value: float) -> None:
        """
        Record a value in a histogram.
        
        Args:
            name: The name of the histogram metric
            value: The value to record
        """
        with self._lock:
            self._histograms[name].append(value)
    
    def rate(self, name: str) -> None:
        """
        Record an event for rate calculation.
        
        Args:
            name: The name of the rate metric
        """
        with self._lock:
            self._rates[name].append(time.time())
    
    def get_counter(self, name: str) -> int:
        """
        Get the current value of a counter.
        
        Args:
            name: The name of the counter metric
            
        Returns:
            The current counter value
        """
        with self._lock:
            return self._counters.get(name, 0)
    
    def get_gauge(self, name: str) -> Optional[float]:
        """
        Get the current value of a gauge.
        
        Args:
            name: The name of the gauge metric
            
        Returns:
            The current gauge value or None if not set
        """
        with self._lock:
            return self._gauges.get(name)
    
    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """
        Get statistics for a timer metric.
        
        Args:
            name: The name of the timer metric
            
        Returns:
            Dictionary with min, max, mean, and percentile statistics
        """
        with self._lock:
            values = self._timers.get(name, [])
            if not values:
                return {}
            
            sorted_values = sorted(values)
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'p95': self._percentile(sorted_values, 95),
                'p99': self._percentile(sorted_values, 99)
            }
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """
        Get statistics for a histogram metric.
        
        Args:
            name: The name of the histogram metric
            
        Returns:
            Dictionary with count, min, max, mean, and percentile statistics
        """
        with self._lock:
            values = self._histograms.get(name, [])
            if not values:
                return {}
            
            sorted_values = sorted(values)
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'p50': self._percentile(sorted_values, 50),
                'p95': self._percentile(sorted_values, 95),
                'p99': self._percentile(sorted_values, 99)
            }
    
    def get_rate(self, name: str, window_seconds: int = 60) -> float:
        """
        Get the rate of events per second over a time window.
        
        Args:
            name: The name of the rate metric
            window_seconds: The time window in seconds (default: 60)
            
        Returns:
            Events per second rate
        """
        with self._lock:
            timestamps = list(self._rates.get(name, []))
            if not timestamps:
                return 0.0
            
            now = time.time()
            cutoff = now - window_seconds
            recent_timestamps = [ts for ts in timestamps if ts >= cutoff]
            
            if not recent_timestamps:
                return 0.0
            
            if len(recent_timestamps) == 1:
                return 1.0 / window_seconds
            
            time_range = now - min(recent_timestamps)
            if time_range == 0:
                return 0.0
                
            return len(recent_timestamps) / time_range
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all collected metrics.
        
        Returns:
            Dictionary containing all metrics organized by type
        """
        with self._lock:
            result = {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'timers': {},
                'histograms': {},
                'rates': {}
            }
            
            # Add timer statistics
            for name in self._timers:
                stats = self.get_timer_stats(name)
                if stats:
                    result['timers'][name] = stats
            
            # Add histogram statistics
            for name in self._histograms:
                stats = self.get_histogram_stats(name)
                if stats:
                    result['histograms'][name] = stats
            
            # Add rates
            for name in self._rates:
                rate = self.get_rate(name)
                if rate > 0:
                    result['rates'][name] = rate
            
            return result
    
    def reset(self) -> None:
        """Reset all metrics to their initial state."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._timers.clear()
            self._histograms.clear()
            self._rates.clear()
    
    def reset_metric(self, name: str) -> None:
        """
        Reset a specific metric.
        
        Args:
            name: The name of the metric to reset
        """
        with self._lock:
            self._counters.pop(name, None)
            self._gauges.pop(name, None)
            self._timers.pop(name, None)
            self._histograms.pop(name, None)
            self._rates.pop(name, None)
    
    def _percentile(self, sorted_values: List[float], percentile: float) -> float:
        """
        Calculate the percentile value from a sorted list.
        
        Args:
            sorted_values: List of values sorted in ascending order
            percentile: The percentile to calculate (0-100)
            
        Returns:
            The percentile value
        """
        if not sorted_values:
            return 0.0
        
        index = (len(sorted_values) - 1) * percentile / 100
        lower = int(index)
        upper = lower + 1
        
        if upper >= len(sorted_values):
            return sorted_values[-1]
        
        weight = index - lower
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


class TimerContext:
    """Context manager for timing operations."""
    
    def __init__(self, collector: MetricsCollector, name: str):
        """
        Initialize the timer context.
        
        Args:
            collector: The MetricsCollector instance
            name: The name of the timer metric
        """
        self.collector = collector
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        """Start the timer."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer and record the duration."""
        if self.start_time is not None:
            duration = (time.time() - self.start_time) * 1000  # Convert to milliseconds
            self.collector.timing(self.name, duration)
```