from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, validator, ConfigDict


class AuthType(str, Enum):
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    CUSTOM_HEADER = "custom_header"


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class WebhookEvent(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    RATE_LIMIT = "rate_limit"
    AUTH_ERROR = "auth_error"
    TIMEOUT = "timeout"
    RETRY_EXHAUSTED = "retry_exhausted"


class AuthConfig(BaseModel):
    """Authentication configuration for API"""
    model_config = ConfigDict(from_attributes=True)
    
    auth_type: AuthType
    api_key: Optional[str] = None
    api_key_header: Optional[str] = "X-API-Key"
    bearer_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = None
    oauth2_token_url: Optional[HttpUrl] = None
    oauth2_scopes: Optional[List[str]] = Field(default_factory=list)
    custom_headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    
    @validator("api_key", "bearer_token", "password", "oauth2_client_secret")
    def validate_secrets(cls, v):
        if v and len(v) < 8:
            raise ValueError("Secret values must be at least 8 characters")
        return v


class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""
    model_config = ConfigDict(from_attributes=True)
    
    requests_per_second: Optional[float] = Field(None, ge=0.1, le=1000)
    requests_per_minute: Optional[int] = Field(None, ge=1, le=60000)
    requests_per_hour: Optional[int] = Field(None, ge=1, le=3600000)
    requests_per_day: Optional[int] = Field(None, ge=1, le=86400000)
    burst_size: Optional[int] = Field(10, ge=1, le=1000)
    retry_after_header: Optional[str] = "Retry-After"
    rate_limit_header: Optional[str] = "X-RateLimit-Limit"
    rate_limit_remaining_header: Optional[str] = "X-RateLimit-Remaining"


class RetryConfig(BaseModel):
    """Retry configuration for failed requests"""
    model_config = ConfigDict(from_attributes=True)
    
    max_retries: int = Field(3, ge=0, le=10)
    initial_delay_ms: int = Field(1000, ge=100, le=60000)
    max_delay_ms: int = Field(60000, ge=1000, le=300000)
    exponential_base: float = Field(2.0, ge=1.1, le=10.0)
    jitter: bool = True
    retry_on_status_codes: List[int] = Field(
        default_factory=lambda: [429, 500, 502, 503, 504]
    )
    retry_on_timeout: bool = True
    
    @validator("retry_on_status_codes")
    def validate_status_codes(cls, v):
        for code in v:
            if code < 400 or code > 599:
                raise ValueError(f"Status code {code} must be 4xx or 5xx")
        return v


class WebhookConfig(BaseModel):
    """Webhook configuration for event notifications"""
    model_config = ConfigDict(from_attributes=True)
    
    enabled: bool = False
    url: Optional[HttpUrl] = None
    events: List[WebhookEvent] = Field(default_factory=list)
    secret_key: Optional[str] = None
    timeout_seconds: int = Field(30, ge=1, le=300)
    max_retries: int = Field(3, ge=0, le=10)
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)


class APIEndpointBase(BaseModel):
    """Base API endpoint configuration"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=255)
    path: str = Field(..., min_length=1, max_length=2048)
    method: HTTPMethod = HTTPMethod.GET
    description: Optional[str] = Field(None, max_length=1000)
    timeout_seconds: int = Field(30, ge=1, le=300)
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    query_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    body_template: Optional[Dict[str, Any]] = Field(default_factory=dict)
    response_mapping: Optional[Dict[str, str]] = Field(default_factory=dict)
    is_paginated: bool = False
    pagination_type: Optional[str] = Field(None, pattern="^(offset|cursor|page)$")
    max_pages: Optional[int] = Field(None, ge=1, le=1000)


class APIEndpoint(APIEndpointBase):
    """API endpoint with metadata"""
    id: UUID = Field(default_factory=uuid4)
    api_config_id: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


class APIEndpointCreate(APIEndpointBase):
    """Schema for creating API endpoint"""
    pass


class APIEndpointUpdate(BaseModel):
    """Schema for updating API endpoint"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    path: Optional[str] = Field(None, min_length=1, max_length=2048)
    method: Optional[HTTPMethod] = None
    description: Optional[str] = Field(None, max_length=1000)
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300)
    headers: Optional[Dict[str, str]] = None
    query_params: Optional[Dict[str, Any]] = None
    body_template: Optional[Dict[str, Any]] = None
    response_mapping: Optional[Dict[str, str]] = None
    is_paginated: Optional[bool] = None
    pagination_type: Optional[str] = Field(None, pattern="^(offset|cursor|page)$")
    max_pages: Optional[int] = Field(None, ge=1, le=1000)
    is_active: Optional[bool] = None


class APIConfigBase(BaseModel):
    """Base API configuration"""
    model_config = ConfigDict(from_attributes=True)
    
    name: str = Field(..., min_length=1, max_length=255)
    base_url: HttpUrl
    description: Optional[str] = Field(None, max_length=1000)
    version: Optional[str] = Field(None, max_length=50)
    auth_config: Optional[AuthConfig] = None
    rate_limit_config: Optional[RateLimitConfig] = None
    retry_config: Optional[RetryConfig] = None
    webhook_config: Optional[WebhookConfig] = None
    default_headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    default_timeout_seconds: int = Field(30, ge=1, le=300)
    ssl_verify: bool = True
    follow_redirects: bool = True
    max_redirects: int = Field(5, ge=0, le=20)


class APIConfig(APIConfigBase):
    """API configuration with metadata"""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    last_health_check: Optional[datetime] = None
    health_status: Optional[str] = None
    endpoints: List[APIEndpoint] = Field(default_factory=list)


class APIConfigCreate(APIConfigBase):
    """Schema for creating API configuration"""
    pass


class APIConfigUpdate(BaseModel):
    """Schema for updating API configuration"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    base_url: Optional[HttpUrl] = None
    description: Optional[str] = Field(None, max_length=1000)
    version: Optional[str] = Field(None, max_length=50)
    auth_config: Optional[AuthConfig] = None
    rate_limit_config: Optional[RateLimitConfig] = None
    retry_config: Optional[RetryConfig] = None
    webhook_config: Optional[WebhookConfig] = None
    default_headers: Optional[Dict[str, str]] = None
    default_timeout_seconds: Optional[int] = Field(None, ge=1, le=300)
    ssl_verify: Optional[bool] = None
    follow_redirects: Optional[bool] = None
    max_redirects: Optional[int] = Field(None, ge=0, le=20)
    is_active: Optional[bool] = None