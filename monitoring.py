"""
Monitoring and Metrics
Prometheus metrics, structured logging, health checks
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from typing import Dict
import time
from app_config import get_config
from logger_config import get_logger

logger = get_logger(__name__)
config = get_config()

# Prometheus metrics
analysis_counter = Counter(
    'scanner_analyses_total',
    'Total number of contract analyses',
    ['severity', 'has_llm']
)

analysis_duration = Histogram(
    'scanner_analysis_duration_seconds',
    'Time spent analyzing contracts',
    ['analysis_type']
)

vulnerability_counter = Counter(
    'scanner_vulnerabilities_total',
    'Total vulnerabilities found',
    ['vulnerability_type', 'severity']
)

api_requests = Counter(
    'scanner_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration = Histogram(
    'scanner_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

active_analyses = Gauge(
    'scanner_active_analyses',
    'Number of analyses currently in progress'
)

cache_hits = Counter(
    'scanner_cache_hits_total',
    'Cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'scanner_cache_misses_total',
    'Cache misses',
    ['cache_type']
)


class MetricsMiddleware:
    """Middleware to track API metrics"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        method = scope["method"]
        path = scope["path"]
        
        # Track request
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                api_requests.labels(method=method, endpoint=path, status=status_code).inc()
                duration = time.time() - start_time
                api_request_duration.labels(method=method, endpoint=path).observe(duration)
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


def record_analysis(
    severity: str,
    has_llm: bool,
    duration: float,
    analysis_type: str = "static",
    vulnerability_count: int = 0,
    vulnerabilities: list = None
):
    """Record analysis metrics"""
    analysis_counter.labels(severity=severity, has_llm=str(has_llm)).inc()
    analysis_duration.labels(analysis_type=analysis_type).observe(duration)
    
    if vulnerabilities:
        for vuln in vulnerabilities:
            vulnerability_counter.labels(
                vulnerability_type=vuln.get('type', 'unknown'),
                severity=vuln.get('severity', 'UNKNOWN')
            ).inc()


def record_cache_hit(cache_type: str = "analysis"):
    """Record cache hit"""
    cache_hits.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str = "analysis"):
    """Record cache miss"""
    cache_misses.labels(cache_type=cache_type).inc()


def get_metrics_endpoint():
    """Get Prometheus metrics endpoint handler"""
    async def metrics():
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    return metrics


def get_health_check() -> Dict:
    """Get detailed health check information"""
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "memory": {
                "used_mb": round(process.memory_info().rss / 1024 / 1024, 2),
                "percent": round(process.memory_percent(), 2)
            },
            "cpu": {
                "percent": round(process.cpu_percent(interval=0.1), 2)
            },
            "uptime_seconds": round(time.time() - process.create_time(), 2)
        }
    except ImportError:
        # psutil not available, return basic health
        return {
            "status": "healthy",
            "version": "1.0.0",
            "note": "Detailed metrics require psutil package"
        }
