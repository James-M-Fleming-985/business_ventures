from typing import List

from fastapi.middleware.cors import CORSMiddleware


def get_cors_middleware(
    allow_origins: List[str] | None = None,
    allow_credentials: bool = True,
    allow_methods: List[str] | None = None,
    allow_headers: List[str] | None = None,
    expose_headers: List[str] | None = None,
    max_age: int = 600,
) -> type[CORSMiddleware]:
    """Configure and return CORS middleware."""
    if allow_origins is None:
        # Default origins - should be configured per environment
        allow_origins = [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ]

    if allow_methods is None:
        allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

    if allow_headers is None:
        allow_headers = [
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-Request-ID",
            "Accept",
            "Accept-Language",
            "Content-Language",
            "X-API-Key",
        ]

    if expose_headers is None:
        expose_headers = [
            "X-Request-ID",
            "X-Process-Time",
            "X-Total-Count",
            "Link",
            "Content-Disposition",
        ]

    class ConfiguredCORSMiddleware(CORSMiddleware):
        def __init__(self, app):
            super().__init__(
                app,
                allow_origins=allow_origins,
                allow_credentials=allow_credentials,
                allow_methods=allow_methods,
                allow_headers=allow_headers,
                expose_headers=expose_headers,
                max_age=max_age,
            )

    return ConfiguredCORSMiddleware


# Environment-specific CORS configurations
def get_development_cors() -> type[CORSMiddleware]:
    """CORS configuration for development environment."""
    return get_cors_middleware(
        allow_origins=["*"],  # Allow all origins in development
        allow_credentials=True,
    )


def get_production_cors(allowed_domains: List[str]) -> type[CORSMiddleware]:
    """CORS configuration for production environment."""
    return get_cors_middleware(
        allow_origins=allowed_domains,
        allow_credentials=True,
        max_age=3600,  # 1 hour cache for preflight requests
    )


def get_staging_cors() -> type[CORSMiddleware]:
    """CORS configuration for staging environment."""
    return get_cors_middleware(
        allow_origins=[
            "https://staging.example.com",
            "https://staging-api.example.com",
        ],
        allow_credentials=True,
        max_age=1800,  # 30 minutes cache
    )
