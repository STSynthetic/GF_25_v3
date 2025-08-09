from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=("method", "path", "status"),
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    labelnames=("method", "path"),
    buckets=(
        0.001,
        0.005,
        0.01,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
    ),
)
IN_PROGRESS = Gauge("http_requests_in_progress", "In-progress HTTP requests")


async def metrics_endpoint() -> Response:
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


async def metrics_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]):
    start = perf_counter()
    IN_PROGRESS.inc()
    try:
        response = await call_next(request)
        return response
    finally:
        duration = perf_counter() - start
        REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)
        status = getattr(request.state, "_status_code", None)
        # If middleware runs before response creation, fallback to response status if available
        if status is None:
            # best effort: status_code may not be set if exception
            status_code = getattr(response, "status_code", 500)
        else:
            status_code = status
        REQUEST_COUNT.labels(request.method, request.url.path, str(status_code)).inc()
        IN_PROGRESS.dec()
