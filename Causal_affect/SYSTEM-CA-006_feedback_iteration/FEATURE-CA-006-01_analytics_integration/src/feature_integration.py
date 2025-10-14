"""
Multi-Source Analytics Integration Feature Orchestrator

This module provides the main integration layer for FEATURE-CA-006-01,
orchestrating interactions between Google Analytics, Mixpanel, Amplitude,
and the analytics aggregator with comprehensive error handling.
"""

from pathlib import Path
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import layer implementations
try:
    from LAYER_CA_006_01_01_Google_Analytics_Client.src.implementation import (
        GoogleAnalyticsClient
    )
except ImportError:
    from layer_ca_006_01_01_google_analytics_client.src.implementation import (
        GoogleAnalyticsClient
    )

try:
    from LAYER_CA_006_01_02_Mixpanel_Client.src.implementation import (
        MixpanelClient,
        AuthenticationError,
        FetchError
    )
except ImportError:
    from layer_ca_006_01_02_mixpanel_client.src.implementation import (
        MixpanelClient,
        AuthenticationError,
        FetchError
    )

try:
    from LAYER_CA_006_01_03_Amplitude_Client.src.implementation import (
        AmplitudeClient
    )
except ImportError:
    from layer_ca_006_01_03_amplitude_client.src.implementation import (
        AmplitudeClient
    )

try:
    from LAYER_CA_006_01_04_Analytics_Aggregator.src.implementation import (
        ProviderStatus,
        Metric,
        ProviderResult,
        AggregatedResult,
        AnalyticsProvider,
        AnalyticsAggregator,
        MockProvider
    )
except ImportError:
    from layer_ca_006_01_04_analytics_aggregator.src.implementation import (
        ProviderStatus,
        Metric,
        ProviderResult,
        AggregatedResult,
        AnalyticsProvider,
        AnalyticsAggregator,
        MockProvider
    )

try:
    from LAYER_CA_006_01_05_Analytics_Error_Handler.src.implementation import (
        CircuitState,
        CircuitBreaker,
        AnalyticsErrorHandler
    )
except ImportError:
    from layer_ca_006_01_05_analytics_error_handler.src.implementation import (
        CircuitState,
        CircuitBreaker,
        AnalyticsErrorHandler
    )


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeatureStatus(Enum):
    """Status of feature execution"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    DEGRADED = "degraded"


@dataclass
class ProviderConfig:
    """Configuration for individual analytics provider"""
    enabled: bool = True
    credentials: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 30
    retry_attempts: int = 3
    priority: int = 1  # Higher priority providers are queried first


@dataclass
class FeatureConfig:
    """Configuration for the Multi-Source Analytics Integration feature"""
    
    # Provider configurations
    google_analytics: ProviderConfig = field(default_factory=ProviderConfig)
    mixpanel: ProviderConfig = field(default_factory=ProviderConfig)
    amplitude: ProviderConfig = field(default_factory=ProviderConfig)
    
    # General settings
    enable_parallel_execution: bool = True
    max_workers: int = 3
    aggregation_enabled: bool = True
    error_handling_enabled: bool = True
    
    # Circuit breaker settings
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    
    # Retry settings
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    retry_backoff_max: float = 60.0
    
    # Fallback settings
    enable_fallback: bool = True
    fallback_to_mock: bool = False
    
    # Data settings
    default_date_range_days: int = 7
    enable_data_deduplication: bool = True
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        if self.max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        if self.default_date_range_days < 1:
            raise ValueError("default_date_range_days must be at least 1")
        if self.circuit_breaker_threshold < 1:
            raise ValueError("circuit_breaker_threshold must be at least 1")
        return True


@dataclass
class ProviderMetadata:
    """Metadata about provider execution"""
    name: str
    status: ProviderStatus
    execution_time_ms: float
    error_message: Optional[str] = None
    metrics_count: int = 0
    retry_count: int = 0


@dataclass
class FeatureResponse:
    """Unified response from feature orchestration"""
    
    status: FeatureStatus
    aggregated_data: Optional[AggregatedResult] = None
    provider_metadata: List[ProviderMetadata] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Raw provider data (optional)
    raw_provider_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        return {
            "status": self.status.value,
            "aggregated_data": self.aggregated_data.__dict__ if self.aggregated_data else None,
            "provider_metadata": [
                {
                    "name": pm.name,
                    "status": pm.status.value,
                    "execution_time_ms": pm.execution_time_ms,
                    "error_message": pm.error_message,
                    "metrics_count": pm.metrics_count,
                    "retry_count": pm.retry_count
                }
                for pm in self.provider_metadata
            ],
            "errors": self.errors,
            "warnings": self.warnings,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat()
        }
    
    def has_data(self) -> bool:
        """Check if response contains any data"""
        return self.aggregated_data is not None and len(self.aggregated_data.metrics) > 0
    
    def is_successful(self) -> bool:
        """Check if feature execution was successful"""
        return self.status in [FeatureStatus.SUCCESS, FeatureStatus.PARTIAL_SUCCESS]


class FeatureOrchestrator:
    """
    Main orchestrator for Multi-Source Analytics Integration feature.
    
    This class coordinates all analytics providers, handles errors gracefully,
    aggregates data from multiple sources, and provides a unified interface
    for analytics operations.
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize the feature orchestrator.
        
        Args:
            config: Feature configuration. If None, uses default configuration.
        """
        self.config = config or FeatureConfig()
        self.config.validate()
        
        self.logger = logging.getLogger(f"{__name__}.FeatureOrchestrator")
        self.logger.info("Initializing Multi-Source Analytics Integration Feature")
        
        # Initialize components
        self._initialized = False
        self._error_handler: Optional[AnalyticsErrorHandler] = None
        self._aggregator: Optional[AnalyticsAggregator] = None
        self._providers: Dict[str, Any] = {}
        
        # Initialize thread pool for parallel execution
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        
        # Initialize all layers
        self._initialize_layers()
    
    def _initialize_layers(self) -> None:
        """Initialize all layer implementations"""
        try:
            # Initialize error handler first (required by other components)
            if self.config.error_handling_enabled:
                self._initialize_error_handler()
            
            # Initialize analytics providers
            self._initialize_providers()
            
            # Initialize aggregator
            if self.config.aggregation_enabled:
                self._initialize_aggregator()
            
            self._initialized = True
            self.logger.info("All layers initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize layers: {str(e)}")
            raise RuntimeError(f"Layer initialization failed: {str(e)}")
    
    def _initialize_error_handler(self) -> None:
        """Initialize the analytics error handler"""
        try:
            self._error_handler = AnalyticsErrorHandler(
                max_retries=self.config.max_retries,
                backoff_base=self.config.retry_backoff_base,
                backoff_max=self.config.retry_backoff_max,
                circuit_breaker_threshold=self.config.circuit_breaker_threshold,
                circuit_breaker_timeout=self.config.circuit_breaker_timeout
            )
            self.logger.info("Error handler initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize error handler: {str(e)}")
            raise
    
    def _initialize_providers(self) -> None:
        """Initialize all analytics provider clients"""
        
        # Initialize Google Analytics
        if self.config.google_analytics.enabled:
            try:
                self._providers['google_analytics'] = GoogleAnalyticsClient(
                    **self.config.google_analytics.credentials
                )
                self.logger.info("Google Analytics client initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Google Analytics: {str(e)}")
                if not self.config.enable_fallback:
                    raise
        
        # Initialize Mixpanel
        if self.config.mixpanel.enabled:
            try:
                self._providers['mixpanel'] = MixpanelClient(
                    **self.config.mixpanel.credentials
                )
                self.logger.info("Mixpanel client initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Mixpanel: {str(e)}")
                if not self.config.enable_fallback:
                    raise
        
        # Initialize Amplitude
        if self.config.amplitude.enabled:
            try:
                self._providers['amplitude'] = AmplitudeClient(
                    **self.config.amplitude.credentials
                )
                self.logger.info("Amplitude client initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Amplitude: {str(e)}")
                if not self.config.enable_fallback:
                    raise
        
        # Add mock provider if fallback enabled and no providers available
        if self.config.fallback_to_mock and not self._providers:
            self._providers['mock'] = MockProvider()
            self.logger.warning("No providers available, using mock provider")
    
    def _initialize_aggregator(self) -> None:
        """Initialize the analytics aggregator"""
        try:
            # Convert provider clients to AnalyticsProvider wrappers
            providers_list = []
            
            for name, client in self._providers.items():
                if name != 'mock':
                    # Wrap client in AnalyticsProvider interface
                    provider = self._wrap_provider(name, client)
                    providers_list.append(provider)
                else:
                    providers_list.append(client)
            
            self._aggregator = AnalyticsAggregator(
                providers=providers_list,
                enable_deduplication=self.config.enable_data_deduplication
            )
            self.logger.info("Analytics aggregator initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize aggregator: {str(e)}")
            raise
    
    def _wrap_provider(self, name: str, client: Any) -> AnalyticsProvider:
        """
        Wrap a provider client in the AnalyticsProvider interface.
        
        Args:
            name: Provider name
            client: Provider client instance
            
        Returns:
            AnalyticsProvider wrapper
        """
        # This is a simplified wrapper - in production, you'd implement
        # full adapter pattern for each provider
        class ProviderWrapper(AnalyticsProvider):
            def __init__(self, provider_name: str, provider_client: Any):
                self.name = provider_name
                self.client = provider_client
            
            def fetch_metrics(self, start_date: datetime, end_date: datetime,
                            metrics: List[str]) -> ProviderResult:
                """Fetch metrics from the wrapped provider"""
                try:
                    # Call provider-specific method
                    data = self._fetch_from_client(start_date, end_date, metrics)
                    return ProviderResult(
                        provider_name=self.name,
                        status=ProviderStatus.SUCCESS,
                        metrics=data,
                        timestamp=datetime.now()
                    )
                except Exception as e:
                    return ProviderResult(
                        provider_name=self.name,
                        status=ProviderStatus.ERROR,
                        metrics=[],
                        error_message=str(e),
                        timestamp=datetime.now()
                    )
            
            def _fetch_from_client(self, start_date: datetime, end_date: datetime,
                                  metrics: List[str]) -> List[Metric]:
                """Provider-specific data fetching logic"""
                # Implement provider-specific logic here
                # This is a placeholder implementation
                return []
        
        return ProviderWrapper(name, client)
    
    def fetch_analytics(
        self,
        metrics: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        providers: Optional[List[str]] = None
    ) -> FeatureResponse:
        """
        Fetch analytics data from multiple sources.
        
        Args:
            metrics: List of metric names to fetch
            start_date: Start date for data range (defaults to 7 days ago)
            end_date: End date for data range (defaults to now)
            providers: Specific providers to query (defaults to all enabled)
            
        Returns:
            FeatureResponse with aggregated data and metadata
        """
        start_time = datetime.now()
        
        if not self._initialized:
            return FeatureResponse(
                status=FeatureStatus.FAILURE,
                errors=["Feature not properly initialized"],
                execution_time_ms=0.0
            )
        
        # Set default date range
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=self.config.default_date_range_days)
        
        self.logger.info(
            f"Fetching metrics {metrics} from {start_date} to {end_date}"
        )
        
        try:
            # Use aggregator if available
            if self._aggregator:
                result = self._fetch_with_aggregator(
                    metrics, start_date, end_date, providers
                )
            else:
                result = self._fetch_without_aggregator(
                    metrics, start_date, end_date, providers
                )
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
            
            self.logger.info(
                f"Fetch completed with status {result.status.value} "
                f"in {execution_time:.2f}ms"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching analytics: {str(e)}")
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            return FeatureResponse(
                status=FeatureStatus.FAILURE,
                errors=[f"Fetch failed: {str(e)}"],
                execution_time_ms=execution_time
            )
    
    def _fetch_with_aggregator(
        self,
        metrics: List[str],
        start_date: datetime,
        end_date: datetime,
        providers: Optional[List[str]]
    ) -> FeatureResponse:
        """Fetch data using the aggregator"""
        try:
            # Filter providers if specified
            if providers:
                original_providers = self._aggregator.providers
                self._aggregator.providers = [
                    p for p in original_providers
                    if p.name in providers
                ]
            
            # Fetch aggregated data
            aggregated_result = self._aggregator.aggregate_metrics(
                start_date, end_date, metrics
            )
            
            # Restore original providers
            if providers:
                self._aggregator.providers = original_providers
            
            # Build provider metadata
            provider_metadata = []
            for provider_result in aggregated_result.provider_results:
                metadata = ProviderMetadata(
                    name=provider_result.provider_name,
                    status=provider_result.status,
                    execution_time_ms=provider_result.execution_time_ms or 0.0,
                    error_message=provider_result.error_message,
                    metrics_count=len(provider_result.metrics)
                )
                provider_metadata.append(metadata)
            
            # Determine overall status
            successful_count = sum(
                1 for pm in provider_metadata
                if pm.status == ProviderStatus.SUCCESS
            )
            total_count = len(provider_metadata)
            
            if successful_count == 0:
                status = FeatureStatus.FAILURE
            elif successful_count == total_count:
                status = FeatureStatus.SUCCESS
            else:
                status = FeatureStatus.PARTIAL_SUCCESS
            
            return FeatureResponse(
                status=status,
                aggregated_data=aggregated_result,
                provider_metadata=provider_metadata
            )
            
        except Exception as e:
            self.logger.error(f"Aggregator fetch failed: {str(e)}")
            return FeatureResponse(
                status=FeatureStatus.FAILURE,
                errors=[f"Aggregation failed: {str(e)}"]
            )
    
    def _fetch_without_aggregator(
        self,
        metrics: List[str],
        start_date: datetime,
        end_date: datetime,
        providers: Optional[List[str]]
    ) -> FeatureResponse:
        """Fetch data directly from providers without aggregator"""
        
        target_providers = providers or list(self._providers.keys())
        provider_metadata = []
        raw_data = {}
        errors = []
        
        if self.config.enable_parallel_execution:
            # Parallel execution
            futures = {}
            for provider_name in target_providers:
                if provider_name in self._providers:
                    future = self._executor.submit(
                        self._fetch_from_provider,
                        provider_name,
                        metrics,
                        start_date,
                        end_date
                    )
                    futures[future] = provider_name
            
            # Collect results
            for future in as_completed(futures):
                provider_name = futures[future]
                try:
                    metadata, data = future.result()
                    provider_metadata.append(metadata)
                    raw_data[provider_name] = data
                except Exception as e:
                    error_msg = f"Provider {provider_name} failed: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
        else:
            # Sequential execution
            for provider_name in target_providers:
                if provider_name in self._providers:
                    try:
                        metadata, data = self._fetch_from_provider(
                            provider_name, metrics, start_date, end_date
                        )
                        provider_metadata.append(metadata)
                        raw_data[provider_name] = data
                    except Exception as e:
                        error_msg = f"Provider {provider_name} failed: {str(e)}"
                        errors.append(error_msg)
                        self.logger.error(error_msg)
        
        # Determine status
        successful_count = sum(
            1 for pm in provider_metadata
            if pm.status == ProviderStatus.SUCCESS
        )
        total_count = len(provider_metadata)
        
        if successful_count == 0:
            status = FeatureStatus.FAILURE
        elif successful_count == total_count:
            status = FeatureStatus.SUCCESS
        else:
            status = FeatureStatus.PARTIAL_SUCCESS
        
        return FeatureResponse(
            status=status,
            provider_metadata=provider_metadata,
            raw_provider_data=raw_data,
            errors=errors
        )
    
    def _fetch_from_provider(
        self,
        provider_name: str,
        metrics: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> tuple[ProviderMetadata, Any]:
        """
        Fetch data from a specific provider with error handling.
        
        Args:
            provider_name: Name of the provider
            metrics: Metrics to fetch
            start_date: Start date
            end_date: End date
            
        Returns:
            Tuple of (metadata, data)
        """
        start_time = datetime.now()
        provider = self._providers[provider_name]
        
        try:
            # Fetch data with error handling if enabled
            if self._error_handler:
                data = self._error_handler.execute_with_retry(
                    lambda: self._call_provider_fetch(
                        provider, metrics, start_date, end_date
                    ),
                    provider_name=provider_name
                )
            else:
                data = self._call_provider_fetch(
                    provider, metrics, start_date, end_date
                )
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            metadata = ProviderMetadata(
                name=provider_name,
                status=ProviderStatus.SUCCESS,
                execution_time_ms=execution_time,
                metrics_count=len(data) if isinstance(data, list) else 1
            )
            
            return metadata, data
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            metadata = ProviderMetadata(
                name=provider_name,
                status=ProviderStatus.ERROR,
                execution_time_ms=execution_time,
                error_message=str(e),
                metrics_count=0
            )
            
            return metadata, None
    
    def _call_provider_fetch(
        self,
        provider: Any,
        metrics: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> Any