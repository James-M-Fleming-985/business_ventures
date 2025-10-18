import asyncio
import hashlib
import hmac
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional, Union

import httpx
import redis.asyncio as redis
from jose import jwt
from pydantic import BaseModel, Field, SecretStr

from app.core.exceptions import AuthenticationError
from app.features.api_connector.services.http_client import HTTPClient


class AuthType(str, Enum):
    """Supported authentication types"""
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    HMAC = "hmac"
    CUSTOM = "custom"


class AuthConfig(BaseModel):
    """Base authentication configuration"""
    auth_type: AuthType
    cache_ttl: int = Field(default=3600, ge=0)
    auto_refresh: bool = True
    refresh_threshold: int = Field(default=300, ge=0)  # seconds before expiry


class APIKeyConfig(AuthConfig):
    """API Key authentication configuration"""
    auth_type: AuthType = AuthType.API_KEY
    api_key: SecretStr
    header_name: str = "X-API-Key"
    query_param: Optional[str] = None


class BearerTokenConfig(AuthConfig):
    """Bearer token authentication configuration"""
    auth_type: AuthType = AuthType.BEARER_TOKEN
    token: SecretStr
    header_prefix: str = "Bearer"


class OAuth2Config(AuthConfig):
    """OAuth2 authentication configuration"""
    auth_type: AuthType = AuthType.OAUTH2
    client_id: str
    client_secret: SecretStr
    token_url: str
    scope: Optional[str] = None
    grant_type: str = "client_credentials"
    additional_params: Dict[str, Any] = Field(default_factory=dict)


class BasicAuthConfig(AuthConfig):
    """Basic authentication configuration"""
    auth_type: AuthType = AuthType.BASIC
    username: str
    password: SecretStr


class HMACConfig(AuthConfig):
    """HMAC authentication configuration"""
    auth_type: AuthType = AuthType.HMAC
    secret_key: SecretStr
    algorithm: str = "sha256"
    header_name: str = "X-Signature"
    timestamp_header: str = "X-Timestamp"
    include_timestamp: bool = True


class AuthToken(BaseModel):
    """Authentication token model"""
    token: str
    token_type: str = "bearer"
    expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    additional_data: Dict[str, Any] = Field(default_factory=dict)


class AuthStrategy(ABC):
    """Abstract base class for authentication strategies"""
    
    @abstractmethod
    async def authenticate(
        self, 
        request: httpx.Request
    ) -> httpx.Request:
        """Apply authentication to request"""
        pass
        
    @abstractmethod
    async def refresh(
        self, 
        http_client: HTTPClient
    ) -> Optional[AuthToken]:
        """Refresh authentication token if applicable"""
        pass


class APIKeyStrategy(AuthStrategy):
    """API Key authentication strategy"""
    
    def __init__(self, config: APIKeyConfig):
        self.config = config
        
    async def authenticate(self, request: httpx.Request) -> httpx.Request:
        """Add API key to request"""
        api_key = self.config.api_key.get_secret_value()
        
        if self.config.query_param:
            # Add to query parameters
            params = dict(request.url.params)
            params[self.config.query_param] = api_key
            request.url = request.url.copy_with(params=params)
        else:
            # Add to headers
            request.headers[self.config.header_name] = api_key
            
        return request
        
    async def refresh(self, http_client: HTTPClient) -> Optional[AuthToken]:
        """API keys don't need refresh"""
        return None


class BearerTokenStrategy(AuthStrategy):
    """Bearer token authentication strategy"""
    
    def __init__(self, config: BearerTokenConfig):
        self.config = config
        
    async def authenticate(self, request: httpx.Request) -> httpx.Request:
        """Add bearer token to request"""
        token = self.config.token.get_secret_value()
        request.headers['Authorization'] = f"{self.config.header_prefix} {token}"
        return request
        
    async def refresh(self, http_client: HTTPClient) -> Optional[AuthToken]:
        """Bearer tokens don't auto-refresh"""
        return None


class OAuth2Strategy(AuthStrategy):
    """OAuth2 authentication strategy"""
    
    def __init__(self, config: OAuth2Config):
        self.config = config
        self._token: Optional[AuthToken] = None
        
    async def authenticate(self, request: httpx.Request) -> httpx.Request:
        """Add OAuth2 token to request"""
        if not self._token:
            raise AuthenticationError("OAuth2 token not available")
            
        request.headers['Authorization'] = f"Bearer {self._token.token}"
        return request
        
    async def refresh(self, http_client: HTTPClient) -> Optional[AuthToken]:
        """Refresh OAuth2 token"""
        data = {
            'grant_type': self.config.grant_type,
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret.get_secret_value(),
            **self.config.additional_params
        }
        
        if self.config.scope:
            data['scope'] = self.config.scope
            
        response = await http_client.post(
            self.config.token_url,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if response.status_code != 200:
            raise AuthenticationError(
                f"Failed to obtain OAuth2 token: {response.status_code}"
            )
            
        token_data = response.content
        expires_in = token_data.get('expires_in')
        
        self._token = AuthToken(
            token=token_data['access_token'],
            token_type=token_data.get('token_type', 'bearer'),
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None,
            refresh_token=token_data.get('refresh_token'),
            scope=token_data.get('scope'),
            additional_data={k: v for k, v in token_data.items() 
                           if k not in ['access_token', 'token_type', 'expires_in', 'refresh_token', 'scope']}
        )
        
        return self._token


class BasicAuthStrategy(AuthStrategy):
    """Basic authentication strategy"""
    
    def __init__(self, config: BasicAuthConfig):
        self.config = config
        
    async def authenticate(self, request: httpx.Request) -> httpx.Request:
        """Add basic auth to request"""
        request.headers['Authorization'] = httpx.BasicAuth(
            username=self.config.username,
            password=self.config.password.get_secret_value()
        )._auth_header
        return request
        
    async def refresh(self, http_client: HTTPClient) -> Optional[AuthToken]:
        """Basic auth doesn't need refresh"""
        return None


class HMACStrategy(AuthStrategy):
    """HMAC authentication strategy"""
    
    def __init__(self, config: HMACConfig):
        self.config = config
        
    async def authenticate(self, request: httpx.Request) -> httpx.Request:
        """Add HMAC signature to request"""
        timestamp = str(int(time.time()))
        
        # Build signature payload
        payload_parts = [
            request.method,
            str(request.url.path),
            request.headers.get('Content-Type', ''),
        ]
        
        if self.config.include_timestamp:
            payload_parts.append(timestamp)
            request.headers[self.config.timestamp_header] = timestamp
            
        if request.content:
            payload_parts.append(request.content.decode() if isinstance(request.content, bytes) else str(request.content))
            
        payload = '\n'.join(payload_parts)
        
        # Generate HMAC signature
        secret = self.config.secret_key.get_secret_value().encode()
        signature = hmac.new(
            secret,
            payload.encode(),
            getattr(hashlib, self.config.algorithm)
        ).hexdigest()
        
        request.headers[self.config.header_name] = signature
        return request
        
    async def refresh(self, http_client: HTTPClient) -> Optional[AuthToken]:
        """HMAC doesn't need refresh"""
        return None


class AuthManager:
    """Manages authentication for API connections"""
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        cache_prefix: str = "auth_token:"
    ):
        self.redis_client = redis_client
        self.cache_prefix = cache_prefix
        self._strategies: Dict[str, AuthStrategy] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        
    def register_strategy(
        self,
        name: str,
        config: Union[AuthConfig, Dict[str, Any]]
    ) -> None:
        """Register authentication strategy"""
        if isinstance(config, dict):
            config = self._create_config(config)
            
        strategy = self._create_strategy(config)
        self._strategies[name] = strategy
        self._locks[name] = asyncio.Lock()
        
    def _create_config(self, data: Dict[str, Any]) -> AuthConfig:
        """Create config from dict"""
        auth_type = AuthType(data.get('auth_type'))
        
        config_map = {
            AuthType.API_KEY: APIKeyConfig,
            AuthType.BEARER_TOKEN: BearerTokenConfig,
            AuthType.OAUTH2: OAuth2Config,
            AuthType.BASIC: BasicAuthConfig,
            AuthType.HMAC: HMACConfig,
        }
        
        config_class = config_map.get(auth_type)
        if not config_class:
            raise ValueError(f"Unsupported auth type: {auth_type}")
            
        return config_class(**data)
        
    def _create_strategy(self, config: AuthConfig) -> AuthStrategy:
        """Create strategy from config"""
        strategy_map = {
            AuthType.API_KEY: APIKeyStrategy,
            AuthType.BEARER_TOKEN: BearerTokenStrategy,
            AuthType.OAUTH2: OAuth2Strategy,
            AuthType.BASIC: BasicAuthStrategy,
            AuthType.HMAC: HMACStrategy,
        }
        
        strategy_class = strategy_map.get(config.auth_type)
        if not strategy_class:
            raise ValueError(f"Unsupported auth type: {config.auth_type}")
            
        return strategy_class(config)
        
    async def get_auth_handler(
        self,
        name: str,
        http_client: Optional[HTTPClient] = None
    ) -> httpx.Auth:
        """Get authentication handler for httpx"""
        strategy = self._strategies.get(name)
        if not strategy:
            raise ValueError(f"Authentication strategy '{name}' not found")
            
        return AuthHandler(self, name, strategy, http_client)
        
    async def authenticate_request(
        self,
        name: str,
        request: httpx.Request,
        http_client: Optional[HTTPClient] = None
    ) -> httpx.Request:
        """Apply authentication to request"""
        strategy = self._strategies.get(name)
        if not strategy:
            raise ValueError(f"Authentication strategy '{name}' not found")
            
        # Check if token needs refresh (OAuth2)
        if isinstance(strategy, OAuth2Strategy):
            await self._ensure_valid_token(name, strategy, http_client)
            
        return await strategy.authenticate(request)
        
    async def _ensure_valid_token(
        self,
        name: str,
        strategy: OAuth2Strategy,
        http_client: Optional[HTTPClient]
    ) -> None:
        """Ensure OAuth2 token is valid"""
        async with self._locks[name]:
            # Check cache first
            if self.redis_client:
                cached_token = await self._get_cached_token(name)
                if cached_token:
                    strategy._token = cached_token
                    return
                    
            # Check if current token is valid
            if strategy._token and strategy._token.expires_at:
                if strategy._token.expires_at > datetime.utcnow() + timedelta(seconds=strategy.config.refresh_threshold):
                    return
                    
            # Refresh token
            if not http_client:
                http_client = HTTPClient()
                
            async with http_client:
                token = await strategy.refresh(http_client)
                if token and self.redis_client:
                    await self._cache_token(name, token, strategy.config.cache_ttl)
                    
    async def _get_cached_token(self, name: str) -> Optional[AuthToken]:
        """Get token from cache"""
        key = f"{self.cache_prefix}{name}"
        data = await self.redis_client.get(key)
        if data:
            import json
            token_dict = json.loads(data)
            if 'expires_at' in token_dict and token_dict['expires_at']:
                token_dict['expires_at'] = datetime.fromisoformat(token_dict['expires_at'])
            return AuthToken(**token_dict)
        return None
        
    async def _cache_token(
        self,
        name: str,
        token: AuthToken,
        ttl: int
    ) -> None:
        """Cache token"""
        key = f"{self.cache_prefix}{name}"
        token_dict = token.model_dump()
        if token_dict.get('expires_at'):
            token_dict['expires_at'] = token_dict['expires_at'].isoformat()
        import json
        await self.redis_client.setex(
            key,
            ttl,
            json.dumps(token_dict)
        )


class AuthHandler(httpx.Auth):
    """HTTPX authentication handler"""
    
    def __init__(
        self,
        auth_manager: AuthManager,
        name: str,
        strategy: AuthStrategy,
        http_client: Optional[HTTPClient] = None
    ):
        self.auth_manager = auth_manager
        self.name = name
        self.strategy = strategy
        self.http_client = http_client
        
    def auth_flow(self, request: httpx.Request):
        """Authentication flow for httpx"""
        import asyncio
        loop = asyncio.new_event_loop()
        authenticated_request = loop.run_until_complete(
            self.auth_manager.authenticate_request(
                self.name,
                request,
                self.http_client
            )
        )
        yield authenticated_request
