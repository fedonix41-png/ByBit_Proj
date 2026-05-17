"""FastAPI dependencies for authentication and authorization."""
from fastapi import Depends, HTTPException, status, Query, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Union

from ..database.session import SessionLocal, get_db
from ..database.security_models import User
from .auth import validate_access_token

security = HTTPBearer(auto_error=False)


def _extract_token_from_websocket(websocket: WebSocket) -> Optional[str]:
    """Extract JWT token from WebSocket connection.

    Tries to get token from:
    1. Query parameter 'token'
    2. Sec-WebSocket-Protocol header (subprotocol)
    """
    # Try query parameter first
    token = websocket.query_params.get("token")
    if token:
        return token

    # Try Sec-WebSocket-Protocol header (some clients pass token there)
    protocols = websocket.headers.get("sec-websocket-protocol", "")
    for protocol in protocols.split(","):
        protocol = protocol.strip()
        if protocol.startswith("Bearer."):
            return protocol[7:]  # Remove "Bearer." prefix

    return None


async def get_optional_user_ws(
    websocket: WebSocket,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get optional user for WebSocket connections.

    Unlike HTTP endpoints, WebSocket doesn't work with HTTPBearer.
    Token should be passed via query parameter 'token'.
    """
    token = _extract_token_from_websocket(websocket)
    if not token:
        return None

    payload = validate_access_token(token)
    if not payload:
        return None

    return db.query(User).filter(User.id == payload.user_id).first()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = validate_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == payload.user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Optional authentication - returns None if not authenticated."""
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = validate_access_token(token)
    
    if not payload:
        return None
    
    return db.query(User).filter(User.id == payload.user_id).first()
