from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..database.session import get_db
from ..database.security_models import User, UserSession, SecurityAuditLog
from ..core.auth import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    hash_token, validate_password_strength, validate_refresh_token
)
from ..core.schemas import (
    LoginRequest, RegisterRequest, TokenResponse, UserResponse,
    RefreshTokenRequest
)
from ..core.deps import get_current_user
from config import (
    MAX_FAILED_LOGIN_ATTEMPTS, ACCOUNT_LOCKOUT_MINUTES, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register new user."""
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    is_valid, errors = validate_password_strength(data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail={"message": "Weak password", "errors": errors})
    
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role="user",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    _log_security_event(db, None, "user_registered", request, {"username": data.username})
    
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login and get tokens."""
    user = db.query(User).filter(User.username == data.username).first()
    
    if not user:
        _log_security_event(db, None, "login_failed", request, {"reason": "user_not_found", "username": data.username})
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user.locked_until and user.locked_until > datetime.utcnow():
        _log_security_event(db, user.id, "login_blocked", request, {"reason": "account_locked"})
        raise HTTPException(status_code=403, detail="Account temporarily locked")
    
    if not verify_password(data.password, user.password_hash):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        
        if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=ACCOUNT_LOCKOUT_MINUTES)
            _log_security_event(db, user.id, "account_locked", request, {"attempts": user.failed_login_attempts})
        
        db.commit()
        _log_security_event(db, user.id, "login_failed", request, {"reason": "invalid_password"})
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        _log_security_event(db, user.id, "login_failed", request, {"reason": "account_disabled"})
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    access_token = create_access_token(user.id, user.username, user.role)
    refresh_token = create_refresh_token(user.id)
    
    session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        ip_address=_get_client_ip(request),
        user_agent=request.headers.get("user-agent", "")[:500]
    )
    db.add(session)
    
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    db.commit()
    
    _log_security_event(db, user.id, "login_success", request)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    user_id = validate_refresh_token(data.refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    token_hash = hash_token(data.refresh_token)
    session = db.query(UserSession).filter(
        UserSession.refresh_token_hash == token_hash,
        UserSession.revoked_at == None,
        UserSession.expires_at > datetime.utcnow()
    ).first()
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    access_token = create_access_token(user.id, user.username, user.role)
    new_refresh_token = create_refresh_token(user.id)
    
    session.revoked_at = datetime.utcnow()
    
    new_session = UserSession(
        user_id=user.id,
        refresh_token_hash=hash_token(new_refresh_token),
        ip_address=_get_client_ip(request),
        user_agent=request.headers.get("user-agent", "")[:500]
    )
    db.add(new_session)
    db.commit()
    
    _log_security_event(db, user.id, "token_refresh", request)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    request: Request,
    data: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout and revoke refresh token."""
    token_hash = hash_token(data.refresh_token)
    
    session = db.query(UserSession).filter(
        UserSession.refresh_token_hash == token_hash,
        UserSession.user_id == current_user.id
    ).first()
    
    if session:
        session.revoked_at = datetime.utcnow()
        db.commit()
    
    _log_security_event(db, current_user.id, "logout", request)
    
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return UserResponse.model_validate(current_user)


def _log_security_event(db: Session, user_id: int, event_type: str, request: Request, details: dict = None):
    """Log security event to audit log."""
    try:
        log = SecurityAuditLog(
            user_id=user_id,
            event_type=event_type,
            ip_address=_get_client_ip(request),
            user_agent=request.headers.get("user-agent", "")[:500],
            details=details
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()


def _get_client_ip(request: Request) -> str:
    """Get client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
