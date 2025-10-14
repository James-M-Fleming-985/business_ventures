```python
import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class Metric:
    name: str
    value: float
    timestamp: datetime
    provider: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_hash(self) -> str:
        """Generate unique hash for deduplication."""
        key = f"{self.name}:{self.value}:{self.timestamp.isoformat()}"
        return hashlib.md5(key.encode()).hexdigest()


@dataclass
class ProviderResult:
    provider_name: str
    status: ProviderStatus
    metrics: List[Metric] = field(default_factory=list)
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class AggregatedResult:
    metrics: List[Metric]
    provider_results: List[ProviderResult]
    total_duration: float
    successful_providers: int
    failed_providers: int
    deduplicated_count: int = 0


class AnalyticsProvider:
    """Base class for analytics providers."""
    
    def __init__(self, name: str, is_primary: bool = False):
        self.name = name
        self.is_primary = is_primary
    
    def collect_metrics(self) -> List[Metric]:
        """Collect metrics from provider. Override in subclass."""
        raise NotImplementedError


class AnalyticsAggregator:
    """Aggregates analytics from multiple providers with fallback support."""
    
    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        self.providers: List[AnalyticsProvider] = []
        self.primary_providers: List[AnalyticsProvider] = []
        self.secondary_providers: List[AnalyticsProvider] = []
    
    def add_provider(self, provider: AnalyticsProvider, is_primary: bool = True):
        """Add an analytics provider."""
        self.providers.append(provider)
        if is_primary:
            self.primary_providers.append(provider)
        else:
            self.secondary_providers.append(provider)
    
    def _collect_from_provider(self, provider: AnalyticsProvider) -> ProviderResult:
        """Collect metrics from a single provider with error handling."""
        start_time = time.time()
        try:
            metrics = provider.collect_metrics()
            duration = time.time() - start_time
            return ProviderResult(
                provider_name=provider.name,
                status=ProviderStatus.SUCCESS,
                metrics=metrics,
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Provider {provider.name} failed: {str(e)}")
            return ProviderResult(
                provider_name=provider.name,
                status=ProviderStatus.FAILED,
                error=str(e),
                duration=duration
            )
    
    def _deduplicate_metrics(self, metrics: List[Metric]) -> List[Metric]:
        """Deduplicate metrics based on name, value, and timestamp."""
        seen_hashes: Set[str] = set()
        deduplicated: List[Metric] = []
        
        for metric in metrics:
            metric_hash = metric.get_hash()
            if metric_hash not in seen_hashes:
                seen_hashes.add(metric_hash)
                deduplicated.append(metric)
        
        return deduplicated
    
    def _normalize_metrics(self, metrics: List[Metric]) -> List[Metric]:
        """Normalize metrics to unified schema."""
        normalized = []
        for metric in metrics:
            if not isinstance(metric.timestamp, datetime):
                metric.timestamp = datetime.now()
            normalized.append(metric)
        return normalized
    
    def collect_parallel(self) -> AggregatedResult:
        """Collect from all providers in parallel with fallback support."""
        start_time = time.time()
        all_metrics: List[Metric] = []
        provider_results: List[ProviderResult] = []
        
        providers_to_try = self.primary_providers.copy()
        
        with ThreadPoolExecutor(max_workers=len(self.providers)) as executor:
            try:
                futures = {
                    executor.submit(self._collect_from_provider, provider): provider
                    for provider in providers_to_try
                }
                
                for future in futures:
                    try:
                        result = future.result(timeout=self.timeout)
                        provider_results.append(result)
                        if result.status == ProviderStatus.SUCCESS:
                            all_metrics.extend(result.metrics)
                    except TimeoutError:
                        provider = futures[future]
                        logger.warning(f"Provider {provider.name} timed out")
                        provider_results.append(ProviderResult(
                            provider_name=provider.name,
                            status=ProviderStatus.TIMEOUT,
                            error="Timeout"
                        ))
                    except Exception as e:
                        provider = futures[future]
                        logger.error(f"Provider {provider.name} error: {str(e)}")
                        provider_results.append(ProviderResult(
                            provider_name=provider.name,
                            status=ProviderStatus.FAILED,
                            error=str(e)
                        ))
                
            except Exception as e:
                logger.error(f"Executor error: {str(e)}")
        
        failed_primary = [r for r in provider_results if r.status != ProviderStatus.SUCCESS]
        
        if failed_primary and self.secondary_providers:
            logger.info("Primary provider(s) failed, trying secondary providers")
            with ThreadPoolExecutor(max_workers=len(self.secondary_providers)) as executor:
                futures = {
                    executor.submit(self._collect_from_provider, provider): provider
                    for provider in self.secondary_providers
                }
                
                for future in futures:
                    try:
                        result = future.result(timeout=self.timeout)
                        provider_results.append(result)
                        if result.status == ProviderStatus.SUCCESS:
                            all_metrics.extend(result.metrics)
                    except Exception as e:
                        provider = futures[future]
                        logger.error(f"Secondary provider {provider.name} error: {str(e)}")
        
        original_count = len(all_metrics)
        all_metrics = self._normalize_metrics(all_metrics)
        all_metrics = self._deduplicate_metrics(all_metrics)
        deduplicated_count = original_count - len(all_metrics)
        
        total_duration = time.time() - start_time
        successful = sum(1 for r in provider_results if r.status == ProviderStatus.SUCCESS)
        failed = len(provider_results) - successful
        
        return AggregatedResult(
            metrics=all_metrics,
            provider_results=provider_results,
            total_duration=total_duration,
            successful_providers=successful,
            failed_providers=failed,
            deduplicated_count=deduplicated_count
        )
    
    async def collect_parallel_async(self) -> AggregatedResult:
        """Async version of parallel collection."""
        start_time = time.time()
        all_metrics: List[Metric] = []
        provider_results: List[ProviderResult] = []
        
        async def collect_async(provider: AnalyticsProvider) -> ProviderResult:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._collect_from_provider, provider)
        
        providers_to_try = self.primary_providers.copy()
        
        tasks = [collect_async(provider) for provider in providers_to_try]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Async collection error: {str(result)}")
                continue
            provider_results.append(result)
            if result.status == ProviderStatus.SUCCESS:
                all_metrics.extend(result.metrics)
        
        failed_primary = [r for r in provider_results if r.status != ProviderStatus.SUCCESS]
        
        if failed_primary and self.secondary_providers:
            logger.info("Primary provider(s) failed, trying secondary providers")
            tasks = [collect_async(provider) for provider in self.secondary_providers]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    continue
                provider_results.append(result)
                if result.status == ProviderStatus.SUCCESS:
                    all_metrics.extend(result.metrics)
        
        original_count = len(all_metrics)
        all_metrics = self._normalize_metrics(all_metrics)
        all_metrics = self._deduplicate_metrics(all_metrics)
        deduplicated_count = original_count - len(all_metrics)
        
        total_duration = time.time() - start_time
        successful = sum(1 for r in provider_results if r.status == ProviderStatus.SUCCESS)
        failed = len(provider_results) - successful
        
        return AggregatedResult(
            metrics=all_metrics,
            provider_results=provider_results,
            total_duration=total_duration,
            successful_providers=successful,
            failed_providers=failed,
            deduplicated_count=deduplicated_count
        )


class MockProvider(AnalyticsProvider):
    """Mock provider for testing."""
    
    def __init__(self, name: str, metrics: List[Metric], should_fail: bool = False, delay: float = 0):
        super().__init__(name)
        self._metrics = metrics
        self.should_fail = should_fail
        self.delay = delay
    
    def collect_metrics(self) -> List[Metric]:
        if self.delay > 0:
            time.sleep(self.delay)
        if self.should_fail:
            raise Exception(f"Provider {self.name} failed")
        return self._metrics
```