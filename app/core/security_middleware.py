"""Security middleware for request auditing and logging."""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time

from ..database.session import SessionLocal
from ..database.security_models import SecurityAuditLog


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security auditing and request logging."""
    
    EXCLUDED_PATHS = ["/health", "/health/live", "/health/ready", "/static"]
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        if not any(request.url.path.startswith(p) for p in self.EXCLUDED_PATHS):
            await self._log_request(request, response, start_time)
        
        return response
    
    async def _log_request(self, request: Request, response, start_time: float):
        """Log request to security audit."""
        try:
            user_id = getattr(request.state, "user_id", None)
            
            if response.status_code == 401 or request.url.path.startswith("/api/"):
                db = SessionLocal()
                try:
                    log_entry = SecurityAuditLog(
                        user_id=user_id,
                        event_type="api_access",
                        severity="warning" if response.status_code in [401, 403] else "info",
                        ip_address=self._get_client_ip(request),
                        user_agent=request.headers.get("user-agent", "")[:500],
                        endpoint=str(request.url.path)[:255],
                        method=request.method,
                        status_code=response.status_code,
                        details={"processing_time_ms": int((time.time() - start_time) * 1000)}
                    )
                    db.add(log_entry)
                    db.commit()
                except Exception:
                    db.rollback()
                finally:
                    db.close()
        except Exception:
            pass
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, considering X-Forwarded-For."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
