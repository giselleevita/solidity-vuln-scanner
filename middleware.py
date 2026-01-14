"""
Middleware for FastAPI: Rate limiting, caching, and security
"""

import time
import hashlib
from collections import defaultdict
from functools import wraps
from typing import Callable, Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app_config import get_config
from logger_config import get_logger

logger = get_logger(__name__)
config = get_config()


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: Optional[int] = None, window_seconds: Optional[int] = None):
        self.max_requests = max_requests or config.rate_limit_max_requests
        self.window_seconds = window_seconds or config.rate_limit_window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests in current window"""
        now = time.time()
        window_start = now - self.window_seconds
        
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]
        
        return max(0, self.max_requests - len(self.requests[key]))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        if not self.rate_limiter.is_allowed(client_ip):
            remaining = self.rate_limiter.get_remaining(client_ip)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again later. ({remaining} requests remaining)"
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.rate_limiter.get_remaining(client_ip)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.max_requests)
        
        return response


# Simple cache for analysis results
class AnalysisCache:
    """In-memory cache for analysis results"""
    
    def __init__(self, max_size: Optional[int] = None, ttl_seconds: Optional[int] = None):
        self.cache = {}
        self.max_size = max_size or config.cache_max_size
        self.ttl_seconds = ttl_seconds or config.cache_ttl_seconds
    
    def _generate_key(self, contract_code: str, contract_name: str) -> str:
        """Generate cache key using SHA-256 (secure hash)"""
        content = f"{contract_code}:{contract_name}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, contract_code: str, contract_name: str):
        """Get cached result"""
        key = self._generate_key(contract_code, contract_name)
        
        if key in self.cache:
            cached_time, result = self.cache[key]
            if time.time() - cached_time < self.ttl_seconds:
                return result
            else:
                del self.cache[key]
        
        return None
    
    def set(self, contract_code: str, contract_name: str, result):
        """Cache result"""
        key = self._generate_key(contract_code, contract_name)
        
        # Evict oldest if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][0])
            del self.cache[oldest_key]
        
        self.cache[key] = (time.time(), result)
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()


# Global instances (use config values)
rate_limiter = RateLimiter(
    max_requests=config.rate_limit_max_requests,
    window_seconds=config.rate_limit_window_seconds
)
analysis_cache = AnalysisCache(
    max_size=config.cache_max_size,
    ttl_seconds=config.cache_ttl_seconds
)

