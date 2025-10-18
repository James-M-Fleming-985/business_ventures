from pathlib import Path
import sys
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import layer implementations
from LAYER_CA_001_01_01_http_client.src.implementation import HTTPClient
from LAYER_CA_001_01_02_auth_manager.src.implementation import AuthManager
from LAYER_CA_001_01_03_rate_limiter.src.implementation import (
    RateLimitConfig, RateLimiter, RateLimitExceeded
)
from LAYER_CA_001_01_04_circuit_breaker.src.implementation import (
    CircuitBreaker, CircuitOpenError, CircuitState
)


# Configure logging
logger = logging.getLogger(__name__)


class ResponseStatus(Enum):
    """Enumeration of possible response statuses."""
    SUCCESS = "success"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    CIRCUIT_OPEN = "circuit_open"
    AUTH_FAILED = "auth_failed"
    TIMEOUT = "timeout"


@dataclass
class FeatureConfig:
    """Configuration for the Multi-Source API Connector feature.
    
    Attributes:
        auth_config: Configuration for authentication manager
        rate_limit_config: Configuration for rate limiting
        circuit_breaker_config: Configuration for circuit breaker
        http_config: Configuration for HTTP client
        enable_async: Whether to enable async operations
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retry attempts in seconds
    """
    auth_config: Dict[str, Any] = field(default_factory=dict)
    rate_limit_config: Optional[RateLimitConfig] = None
    circuit_breaker_config: Dict[str, Any] = field(default_factory=dict)
    http_config: Dict[str, Any] = field(default_factory=dict)
    enable_async: bool = False
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class FeatureResponse:
    """Unified response structure for feature operations.
    
    Attributes:
        status: Response status
        data: Response data if successful
        error: Error message if failed
        metadata: Additional metadata about the response
        timestamp: When the response was generated
    """
    status: ResponseStatus
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class FeatureOrchestrator:
    """Main orchestrator for the Multi-Source API Connector feature.
    
    This class coordinates the interaction between all layers:
    - HTTP Client for making requests
    - Auth Manager for authentication
    - Rate Limiter for request throttling
    - Circuit Breaker for fault tolerance
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """Initialize the feature orchestrator.
        
        Args:
            config: Feature configuration object
            
        Raises:
            ValueError: If layer initialization fails
        """
        self.config = config or FeatureConfig()
        self._executor = ThreadPoolExecutor(max_workers=10) if self.config.enable_async else None
        
        try:
            self._initialize_layers()
        except Exception as e:
            raise ValueError(f"Failed to initialize feature layers: {str(e)}")
    
    def _initialize_layers(self) -> None:
        """Initialize all layer instances with proper configuration.
        
        Raises:
            Exception: If any layer fails to initialize
        """
        # Initialize HTTP Client
        self.http_client = HTTPClient(**self.config.http_config)
        logger.info("HTTP Client initialized successfully")
        
        # Initialize Auth Manager
        self.auth_manager = AuthManager(**self.config.auth_config)
        logger.info("Auth Manager initialized successfully")
        
        # Initialize Rate Limiter
        if self.config.rate_limit_config:
            self.rate_limiter = RateLimiter(self.config.rate_limit_config)
        else:
            # Default rate limit configuration
            default_config = RateLimitConfig(
                requests_per_second=10,
                burst_size=20
            )
            self.rate_limiter = RateLimiter(default_config)
        logger.info("Rate Limiter initialized successfully")
        
        # Initialize Circuit Breaker
        cb_config = self.config.circuit_breaker_config
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=cb_config.get('failure_threshold', 5),
            recovery_timeout=cb_config.get('recovery_timeout', 60),
            expected_exception=cb_config.get('expected_exception', Exception)
        )
        logger.info("Circuit Breaker initialized successfully")
    
    async def make_request_async(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[Dict, str]] = None,
        auth_type: Optional[str] = None,
        **kwargs
    ) -> FeatureResponse:
        """Make an asynchronous API request with all layer protections.
        
        Args:
            url: Target URL
            method: HTTP method
            headers: Request headers
            data: Request body data
            auth_type: Authentication type to use
            **kwargs: Additional arguments for HTTP client
            
        Returns:
            FeatureResponse object with results
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self.make_request,
            url, method, headers, data, auth_type,
            kwargs
        )
    
    def make_request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Union[Dict, str]] = None,
        auth_type: Optional[str] = None,
        **kwargs
    ) -> FeatureResponse:
        """Make an API request with all layer protections.
        
        This method orchestrates:
        1. Authentication header injection
        2. Rate limiting checks
        3. Circuit breaker protection
        4. HTTP request execution
        5. Error handling and retries
        
        Args:
            url: Target URL
            method: HTTP method
            headers: Request headers
            data: Request body data
            auth_type: Authentication type to use
            **kwargs: Additional arguments for HTTP client
            
        Returns:
            FeatureResponse object with results
        """
        headers = headers or {}
        metadata = {
            'url': url,
            'method': method,
            'auth_type': auth_type,
            'attempts': 0
        }
        
        # Apply authentication if specified
        if auth_type:
            try:
                auth_headers = self._get_auth_headers(auth_type)
                headers.update(auth_headers)
            except Exception as e:
                logger.error(f"Authentication failed: {str(e)}")
                return FeatureResponse(
                    status=ResponseStatus.AUTH_FAILED,
                    error=str(e),
                    metadata=metadata
                )
        
        # Attempt request with retries
        for attempt in range(self.config.max_retries):
            metadata['attempts'] = attempt + 1
            
            # Check rate limiting
            try:
                if not self.rate_limiter.check_rate_limit(url):
                    wait_time = self.rate_limiter.get_wait_time(url)
                    return FeatureResponse(
                        status=ResponseStatus.RATE_LIMITED,
                        error=f"Rate limit exceeded. Wait {wait_time:.2f} seconds.",
                        metadata={**metadata, 'wait_time': wait_time}
                    )
            except RateLimitExceeded as e:
                return FeatureResponse(
                    status=ResponseStatus.RATE_LIMITED,
                    error=str(e),
                    metadata=metadata
                )
            
            # Check circuit breaker
            if self.circuit_breaker.state == CircuitState.OPEN:
                return FeatureResponse(
                    status=ResponseStatus.CIRCUIT_OPEN,
                    error="Circuit breaker is open. Service temporarily unavailable.",
                    metadata=metadata
                )
            
            # Make the actual request
            try:
                response = self.circuit_breaker.call(
                    self._execute_request,
                    url, method, headers, data, **kwargs
                )
                
                # Successfully made request
                self.rate_limiter.consume(url)
                
                return FeatureResponse(
                    status=ResponseStatus.SUCCESS,
                    data=response,
                    metadata={
                        **metadata,
                        'response_status': response.get('status_code'),
                        'response_headers': response.get('headers', {})
                    }
                )
                
            except CircuitOpenError:
                return FeatureResponse(
                    status=ResponseStatus.CIRCUIT_OPEN,
                    error="Circuit breaker opened during request.",
                    metadata=metadata
                )
            except Exception as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {str(e)}")
                
                # If this is not the last attempt, wait before retrying
                if attempt < self.config.max_retries - 1:
                    asyncio.create_task(asyncio.sleep(self.config.retry_delay))
                    continue
                
                # Final attempt failed
                return FeatureResponse(
                    status=ResponseStatus.ERROR,
                    error=f"Request failed after {self.config.max_retries} attempts: {str(e)}",
                    metadata=metadata
                )
        
        # Should not reach here
        return FeatureResponse(
            status=ResponseStatus.ERROR,
            error="Unexpected error in request processing",
            metadata=metadata
        )
    
    def _execute_request(
        self,
        url: str,
        method: str,
        headers: Dict[str, str],
        data: Optional[Union[Dict, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Execute the actual HTTP request.
        
        Args:
            url: Target URL
            method: HTTP method
            headers: Request headers
            data: Request body data
            **kwargs: Additional arguments
            
        Returns:
            Response dictionary
            
        Raises:
            Exception: If request fails
        """
        response = self.http_client.request(
            method=method,
            url=url,
            headers=headers,
            json=data if isinstance(data, dict) else None,
            data=data if isinstance(data, str) else None,
            **kwargs
        )
        
        return {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            'elapsed': response.elapsed.total_seconds()
        }
    
    def _get_auth_headers(self, auth_type: str) -> Dict[str, str]:
        """Get authentication headers based on auth type.
        
        Args:
            auth_type: Type of authentication to use
            
        Returns:
            Dictionary of authentication headers
            
        Raises:
            ValueError: If auth type is not supported
        """
        auth_methods = {
            'bearer': self.auth_manager.get_bearer_token,
            'api_key': self.auth_manager.get_api_key,
            'basic': self.auth_manager.get_basic_auth,
            'oauth2': self.auth_manager.get_oauth2_token
        }
        
        if auth_type not in auth_methods:
            raise ValueError(f"Unsupported auth type: {auth_type}")
        
        auth_value = auth_methods[auth_type]()
        
        if auth_type == 'bearer':
            return {'Authorization': f'Bearer {auth_value}'}
        elif auth_type == 'api_key':
            return {'X-API-Key': auth_value}
        elif auth_type == 'basic':
            return {'Authorization': f'Basic {auth_value}'}
        elif auth_type == 'oauth2':
            return {'Authorization': f'Bearer {auth_value}'}
        
        return {}
    
    def batch_requests(
        self,
        requests: List[Dict[str, Any]],
        concurrent_limit: int = 5
    ) -> List[FeatureResponse]:
        """Execute multiple requests with concurrency control.
        
        Args:
            requests: List of request configurations
            concurrent_limit: Maximum concurrent requests
            
        Returns:
            List of FeatureResponse objects
        """
        responses = []
        
        if self.config.enable_async:
            # Use async execution
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def process_batch():
                tasks = []
                for req in requests:
                    task = self.make_request_async(**req)
                    tasks.append(task)
                return await asyncio.gather(*tasks)
            
            responses = loop.run_until_complete(process_batch())
            loop.close()
        else:
            # Sequential execution with rate limiting
            for req in requests:
                response = self.make_request(**req)
                responses.append(response)
        
        return responses
    
    def get_layer_status(self) -> Dict[str, Any]:
        """Get status information from all layers.
        
        Returns:
            Dictionary with status information for each layer
        """
        return {
            'http_client': {
                'initialized': hasattr(self, 'http_client'),
                'session_active': self.http_client.session is not None if hasattr(self, 'http_client') else False
            },
            'auth_manager': {
                'initialized': hasattr(self, 'auth_manager'),
                'auth_types': ['bearer', 'api_key', 'basic', 'oauth2']
            },
            'rate_limiter': {
                'initialized': hasattr(self, 'rate_limiter'),
                'config': self.config.rate_limit_config.__dict__ if self.config.rate_limit_config else None
            },
            'circuit_breaker': {
                'initialized': hasattr(self, 'circuit_breaker'),
                'state': self.circuit_breaker.state.value if hasattr(self, 'circuit_breaker') else None,
                'failure_count': self.circuit_breaker.failure_count if hasattr(self, 'circuit_breaker') else 0
            }
        }
    
    def reset_circuit_breaker(self) -> None:
        """Manually reset the circuit breaker."""
        if hasattr(self, 'circuit_breaker'):
            self.circuit_breaker.reset()
            logger.info("Circuit breaker manually reset")
    
    def update_rate_limits(self, config: RateLimitConfig) -> None:
        """Update rate limiting configuration.
        
        Args:
            config: New rate limit configuration
        """
        self.config.rate_limit_config = config
        self.rate_limiter = RateLimiter(config)
        logger.info(f"Rate limits updated: {config.requests_per_second} req/s, burst: {config.burst_size}")
    
    def close(self) -> None:
        """Clean up resources used by the orchestrator."""
        if hasattr(self, 'http_client') and hasattr(self.http_client, 'close'):
            self.http_client.close()
        
        if self._executor:
            self._executor.shutdown(wait=True)
        
        logger.info("Feature orchestrator closed successfully")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()