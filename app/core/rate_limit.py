"""Rate limiting middleware for FastAPI with Redis and in-memory fallback."""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import Dict, Optional, Callable
from datetime import datetime
import time
import os

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from loguru import logger


class RateLimiter:
    """Redis-based sliding window rate limiter."""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_client = None
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._in_memory_store: Dict[str, list] = {}
        self._initialized = False
    
    async def init_redis(self) -> bool:
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using in-memory rate limiting")
            return False
        
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
            )
            await self.redis_client.ping()
            logger.info("Redis connected for rate limiting")
            return True
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using in-memory fallback")
            self.redis_client = None
            return False
    
    async def is_allowed(
        self, 
        key: str, 
        max_requests: int, 
        window_seconds: int
    ) -> tuple[bool, dict]:
        """Check if request is allowed within rate limit."""
        current_time = time.time()
        window_start = current_time - window_seconds
        
        if self.redis_client:
            return await self._check_redis(key, max_requests, window_seconds, current_time, window_start)
        else:
            return self._check_memory(key, max_requests, window_seconds, current_time, window_start)
    
    async def _check_redis(
        self, key: str, max_requests: int, window_seconds: int,
        current_time: float, window_start: float
    ) -> tuple[bool, dict]:
        """Redis sliding window implementation."""
        try:
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, window_seconds)
            
            results = await pipe.execute()
            request_count = results[1]
            
            remaining = max(0, max_requests - request_count - 1)
            retry_after = int(window_seconds - (current_time - window_start)) if request_count >= max_requests else 0
            
            return (
                request_count < max_requests,
                {
                    "limit": max_requests,
                    "remaining": remaining,
                    "reset": int(current_time + window_seconds),
                    "retry_after": retry_after
                }
            )
        except Exception as e:
            logger.warning(f"Redis rate limit error: {e}")
            return True, {"limit": max_requests, "remaining": max_requests, "reset": 0, "retry_after": 0}
    
    def _check_memory(
        self, key: str, max_requests: int, window_seconds: int,
        current_time: float, window_start: float
    ) -> tuple[bool, dict]:
        """In-memory fallback for rate limiting."""
        if key not in self._in_memory_store:
            self._in_memory_store[key] = []
        
        # Clean old entries
        self._in_memory_store[key] = [
            ts for ts in self._in_memory_store[key] if ts > window_start
        ]
        
        request_count = len(self._in_memory_store[key])
        
        if request_count >= max_requests:
            return False, {
                "limit": max_requests,
                "remaining": 0,
                "reset": int(window_start + window_seconds),
                "retry_after": int(window_seconds)
            }
        
        self._in_memory_store[key].append(current_time)
        return True, {
            "limit": max_requests,
            "remaining": max_requests - request_count - 1,
            "reset": int(current_time + window_seconds),
            "retry_after": 0
        }
    
    async def close(self):
        if self.redis_client:
            await self.redis_client.close()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    # Rate limit configurations per endpoint pattern
    RATE_LIMITS = {
        "/auth/login": {"max": 5, "window": 60},      # 5 per minute
        "/auth/register": {"max": 3, "window": 3600},  # 3 per hour
        "/auth/refresh": {"max": 10, "window": 60},    # 10 per minute
        "default": {"max": 100, "window": 60},         # Default: 100 per minute
    }
    
    # Paths to exclude from rate limiting
    EXCLUDED_PATHS = ["/health", "/health/live", "/health/ready", "/static"]
    
    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
    
    async def dispatch(self, request: Request, call_next):
        # Skip excluded paths
        if any(request.url.path.startswith(p) for p in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # Get rate limit config for endpoint
        config = self._get_rate_limit_config(request.url.path)
        
        # Generate key (IP + path, or user_id if authenticated)
        key = self._generate_key(request)
        
        # Check rate limit
        allowed, info = await self.rate_limiter.is_allowed(
            key, config["max"], config["window"]
        )
        
        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": info["retry_after"]
                }
            )
        else:
            response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])
        
        if not allowed:
            response.headers["Retry-After"] = str(info["retry_after"])
        
        return response
    
    def _get_rate_limit_config(self, path: str) -> dict:
        """Get rate limit config for path."""
        for pattern, config in self.RATE_LIMITS.items():
            if pattern != "default" and path.startswith(pattern):
                return config
        return self.RATE_LIMITS["default"]
    
    def _generate_key(self, request: Request) -> str:
        """Generate rate limit key."""
        # Use user_id if authenticated, otherwise IP
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"rate_limit:user:{user_id}:{request.url.path}"
        
        ip = self._get_client_ip(request)
        return f"rate_limit:ip:{ip}:{request.url.path}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


# Global rate limiter instance
rate_limiter = RateLimiter()
