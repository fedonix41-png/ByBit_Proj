"""Core application modules."""
from .logging_config import setup_logging, get_logger
from .auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_access_token,
    validate_refresh_token,
    generate_secure_token,
    hash_token,
    validate_password_strength,
    get_token_expires_in,
)
from .schemas import (
    TokenPayload,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
    PasswordChangeRequest,
    TokenData,
)
from .deps import (
    get_current_user,
    get_current_active_user,
    get_admin_user,
    get_optional_user,
    get_optional_user_ws,
)
from .security_middleware import SecurityMiddleware
from .rate_limit import RateLimiter, RateLimitMiddleware, rate_limiter
from .security_headers import SecurityHeadersMiddleware, CORSSecurityMiddleware

__all__ = [
    "setup_logging",
    "get_logger",
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "validate_access_token",
    "validate_refresh_token",
    "generate_secure_token",
    "hash_token",
    "validate_password_strength",
    "get_token_expires_in",
    "TokenPayload",
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "UserResponse",
    "RefreshTokenRequest",
    "PasswordChangeRequest",
    "TokenData",
    "get_current_user",
    "get_current_active_user",
    "get_admin_user",
    "get_optional_user",
    "get_optional_user_ws",
    "SecurityMiddleware",
    "RateLimiter",
    "RateLimitMiddleware",
    "rate_limiter",
    "SecurityHeadersMiddleware",
    "CORSSecurityMiddleware",
]
