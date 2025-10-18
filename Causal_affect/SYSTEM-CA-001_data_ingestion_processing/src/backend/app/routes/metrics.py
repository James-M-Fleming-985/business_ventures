from typing import Dict, Any
from fastapi import APIRouter, Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    multiprocess,
    ProcessCollector,
    PlatformCollector
)
import time
import psutil
import os

router = APIRouter(prefix="/metrics", tags=["metrics"])

# Initialize collectors
if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
else:
    registry = CollectorRegistry(auto_describe=True)
    ProcessCollector(registry=registry)
    PlatformCollector(registry=registry)

# HTTP Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    registry=registry
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    registry=registry
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    registry=registry
)

# Database metrics
db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
    registry=registry
)

db_connections_idle = Gauge(
    "db_connections_idle",
    "Number of idle database connections",
    registry=registry
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query execution time",
    ["operation", "table"],
    registry=registry
)

# Redis metrics
redis_connections_active = Gauge(
    "redis_connections_active",
    "Number of active Redis connections",
    registry=registry
)

redis_operation_duration_seconds = Histogram(
    "redis_operation_duration_seconds",
    "Redis operation execution time",
    ["operation"],
    registry=registry
)

redis_memory_usage_bytes = Gauge(
    "redis_memory_usage_bytes",
    "Redis memory usage in bytes",
    registry=registry
)

# Application metrics
app_info = Gauge(
    "app_info",
    "Application information",
    ["version", "environment"],
    registry=registry
)

active_users = Gauge(
    "active_users_total",
    "Number of active users",
    registry=registry
)

background_tasks_total = Counter(
    "background_tasks_total",
    "Total number of background tasks",
    ["task_name", "status"],
    registry=registry
)

background_task_duration_seconds = Histogram(
    "background_task_duration_seconds",
    "Background task execution time",
    ["task_name"],
    registry=registry
)

# Business metrics
business_operations_total = Counter(
    "business_operations_total",
    "Total business operations",
    ["operation", "status"],
    registry=registry
)

# System metrics
system_cpu_usage_percent = Gauge(
    "system_cpu_usage_percent",
    "System CPU usage percentage",
    registry=registry
)

system_memory_usage_percent = Gauge(
    "system_memory_usage_percent",
    "System memory usage percentage",
    registry=registry
)

system_disk_usage_percent = Gauge(
    "system_disk_usage_percent",
    "System disk usage percentage",
    registry=registry
)


class MetricsMiddleware:
    """Middleware to collect HTTP metrics."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            method = scope["method"]
            path = scope["path"]
            
            # Skip metrics endpoint to avoid recursion
            if path == "/metrics":
                await self.app(scope, receive, send)
                return
            
            status_code = 500
            response_size = 0
            
            async def send_wrapper(message):
                nonlocal status_code, response_size
                if message["type"] == "http.response.start":
                    status_code = message.get("status", 500)
                elif message["type"] == "http.response.body":
                    body = message.get("body", b"")
                    response_size += len(body)
                await send(message)
            
            try:
                await self.app(scope, receive, send_wrapper)
            finally:
                duration = time.time() - start_time
                
                # Record metrics
                http_requests_total.labels(
                    method=method,
                    endpoint=path,
                    status=str(status_code)
                ).inc()
                
                http_request_duration_seconds.labels(
                    method=method,
                    endpoint=path
                ).observe(duration)
                
                # Request size from Content-Length header
                headers = dict(scope.get("headers", []))
                content_length = headers.get(b"content-length")
                if content_length:
                    http_request_size_bytes.labels(
                        method=method,
                        endpoint=path
                    ).observe(int(content_length))
                
                http_response_size_bytes.labels(
                    method=method,
                    endpoint=path
                ).observe(response_size)
        else:
            await self.app(scope, receive, send)


def update_system_metrics():
    """Update system resource metrics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        system_cpu_usage_percent.set(cpu_percent)
        system_memory_usage_percent.set(memory.percent)
        system_disk_usage_percent.set(disk.percent)
    except Exception:
        pass


@router.get("", response_class=Response)
async def get_metrics() -> Response:
    """Expose metrics in Prometheus format."""
    update_system_metrics()
    
    metrics_data = generate_latest(registry)
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )


# Helper functions for metric updates
def record_db_metrics(active: int, idle: int):
    """Update database connection metrics."""
    db_connections_active.set(active)
    db_connections_idle.set(idle)


def record_db_query(operation: str, table: str, duration: float):
    """Record database query metrics."""
    db_query_duration_seconds.labels(
        operation=operation,
        table=table
    ).observe(duration)


def record_redis_operation(operation: str, duration: float):
    """Record Redis operation metrics."""
    redis_operation_duration_seconds.labels(
        operation=operation
    ).observe(duration)


def record_redis_metrics(connections: int, memory_bytes: int):
    """Update Redis metrics."""
    redis_connections_active.set(connections)
    redis_memory_usage_bytes.set(memory_bytes)


def record_background_task(task_name: str, status: str, duration: float = None):
    """Record background task metrics."""
    background_tasks_total.labels(
        task_name=task_name,
        status=status
    ).inc()
    
    if duration is not None:
        background_task_duration_seconds.labels(
            task_name=task_name
        ).observe(duration)


def record_business_operation(operation: str, status: str):
    """Record business operation metrics."""
    business_operations_total.labels(
        operation=operation,
        status=status
    ).inc()


def set_app_info(version: str, environment: str):
    """Set application information."""
    app_info.labels(
        version=version,
        environment=environment
    ).set(1)


def update_active_users(count: int):
    """Update active users count."""
    active_users.set(count)
