"""Authentication service with JWT token management."""
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext
from loguru import logger

from config import settings
from app.core.schemas import TokenPayload


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: int,
    username: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token (15 min default)."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": expire,
        "iat": now,
        "type": "access"
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    logger.debug(f"Created access token for user {user_id}")
    return token


def create_refresh_token(user_id: int) -> str:
    """Create refresh token (7 days default)."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "user_id": user_id,
        "exp": expire,
        "iat": now,
        "type": "refresh"
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    logger.debug(f"Created refresh token for user {user_id}")
    return token


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def validate_access_token(token: str) -> Optional[TokenPayload]:
    """Validate access token, return payload or None."""
    payload = decode_token(token)
    if payload is None:
        return None

    if payload.get("type") != "access":
        logger.warning("Token is not an access token")
        return None

    try:
        return TokenPayload(
            user_id=payload["user_id"],
            username=payload["username"],
            role=payload["role"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        )
    except (KeyError, TypeError) as e:
        logger.error(f"Invalid token payload structure: {e}")
        return None


def validate_refresh_token(token: str) -> Optional[int]:
    """Validate refresh token, return user_id or None."""
    payload = decode_token(token)
    if payload is None:
        return None

    if payload.get("type") != "refresh":
        logger.warning("Token is not a refresh token")
        return None

    user_id = payload.get("user_id")
    if user_id is None:
        logger.error("Refresh token missing user_id")
        return None

    return user_id


def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """SHA-256 hash for token storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """Validate password meets security requirements.
    
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    if len(password) < settings.PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")

    if settings.REQUIRE_PASSWORD_UPPERCASE and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if settings.REQUIRE_PASSWORD_DIGIT and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    return len(errors) == 0, errors


def get_token_expires_in() -> int:
    """Get access token expiration time in seconds."""
    return settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
