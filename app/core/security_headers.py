from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List
import os

from loguru import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    def __init__(self, app, allowed_origins: List[str] = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or self._get_allowed_origins()
    
    def _get_allowed_origins(self) -> List[str]:
        """Get allowed CORS origins from config."""
        origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000")
        return [o.strip() for o in origins_str.split(",") if o.strip()]
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )
        
        if not request.url.path.startswith("/api/"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none'"
            )
        
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        if "Server" in response.headers:
            del response.headers["Server"]
        
        return response


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """Secure CORS middleware with origin validation."""
    
    def __init__(self, app, allowed_origins: List[str] = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or []
    
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            origin = request.headers.get("Origin", "")
            
            if self._is_origin_allowed(origin):
                response = await call_next(request)
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                response.headers["Access-Control-Allow-Headers"] = (
                    "Authorization, Content-Type, Accept, X-Requested-With, "
                    "X-CSRF-Token, X-Request-ID"
                )
                response.headers["Access-Control-Max-Age"] = "86400"
                return response
            else:
                from starlette.responses import Response
                return Response(status_code=403)
        
        response = await call_next(request)
        
        origin = request.headers.get("Origin", "")
        if self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = (
                "X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset"
            )
        
        return response
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed."""
        if not origin:
            return False
        
        if os.getenv("DEBUG", "false").lower() == "true":
            if "localhost" in origin or "127.0.0.1" in origin:
                return True
        
        return origin in self.allowed_origins
