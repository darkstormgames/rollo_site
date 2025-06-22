"""Authentication and authorization API routes."""

import hashlib
import httpx
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.base import DatabaseSession
from models.user import User
from models.role import Role
from models.refresh_token import RefreshToken
from models.password_reset_token import PasswordResetToken
from core.security import SecurityUtils
from core.auth import get_current_user, get_current_active_user
from core.config import settings
from core.logging import get_logger
from schemas.auth import (
    UserLogin, UserRegister, PasswordReset, PasswordResetConfirm,
    TokenRefresh, TokenResponse, TokenRefreshResponse, 
    AuthResponse, MessageResponse, UserProfile
)

logger = get_logger("auth_router")
router = APIRouter()

SSO_BASE_URL = "http://127.0.0.1:3000/api/auth"

async def sso_post(endpoint: str, data: dict, headers: dict = None):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{SSO_BASE_URL}{endpoint}", json=data, headers=headers)
        resp.raise_for_status()
        return resp.json()

async def sso_get(endpoint: str, headers: dict = None):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{SSO_BASE_URL}{endpoint}", headers=headers)
        resp.raise_for_status()
        return resp.json()

def get_db() -> Session:
    """Get database session."""
    db_gen = DatabaseSession.get_session()
    db = next(db_gen)
    try:
        yield db
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


# @router.post("/login", response_model=AuthResponse)
# async def login(
#     credentials: UserLogin,
#     db: Session = Depends(get_db)
# ):
#     """Authenticate user and return JWT tokens."""
#     logger.info(f"Login attempt for username: {credentials.username}")
    
#     # Find user by username
#     user = db.query(User).filter(
#         User.username == credentials.username,
#         User.is_active == True
#     ).first()
    
#     if not user or not SecurityUtils.verify_password(credentials.password, user.password_hash):
#         logger.warning(f"Failed login attempt for username: {credentials.username}")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password"
#         )
    
#     # Create token data
#     token_data = {
#         "sub": user.username,
#         "user_id": user.id,
#         "email": user.email,
#         "roles": [role.name for role in user.roles]
#     }
    
#     # Generate tokens
#     access_token = SecurityUtils.create_access_token(
#         data=token_data,
#         expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
#     )
    
#     refresh_token = SecurityUtils.create_refresh_token(
#         data=token_data,
#         expires_delta=timedelta(days=settings.refresh_token_expire_days)
#     )
    
#     # Store refresh token in database
#     refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
#     db_refresh_token = RefreshToken(
#         token_hash=refresh_token_hash,
#         user_id=user.id,
#         expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
#     )
#     db.add(db_refresh_token)
#     db.commit()
    
#     logger.info(f"Successful login for user: {user.username}")
    
#     return AuthResponse(
#         user=UserProfile.model_validate(user),
#         tokens=TokenResponse(
#             access_token=access_token,
#             refresh_token=refresh_token,
#             token_type="bearer",
#             expires_in=settings.access_token_expire_minutes * 60
#         )
#     )


# @router.post("/register", response_model=AuthResponse)
# async def register(
#     user_data: UserRegister,
#     db: Session = Depends(get_db)
# ):
#     """Register a new user."""
#     logger.info(f"Registration attempt for username: {user_data.username}")
    
#     # Validate passwords match
#     try:
#         user_data.validate_passwords_match()
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )
    
#     # Check if user already exists
#     existing_user = db.query(User).filter(
#         (User.username == user_data.username) | (User.email == user_data.email)
#     ).first()
    
#     if existing_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Username or email already registered"
#         )
    
#     # Create new user
#     password_hash = SecurityUtils.hash_password(user_data.password)
#     user = User(
#         username=user_data.username,
#         email=user_data.email,
#         password_hash=password_hash
#     )
    
#     # Assign default role (user)
#     default_role = db.query(Role).filter(Role.name == "user").first()
#     if default_role:
#         user.roles.append(default_role)
    
#     db.add(user)
#     db.commit()
#     db.refresh(user)
    
#     # Create token data
#     token_data = {
#         "sub": user.username,
#         "user_id": user.id,
#         "email": user.email,
#         "roles": [role.name for role in user.roles]
#     }
    
#     # Generate tokens
#     access_token = SecurityUtils.create_access_token(
#         data=token_data,
#         expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
#     )
    
#     refresh_token = SecurityUtils.create_refresh_token(
#         data=token_data,
#         expires_delta=timedelta(days=settings.refresh_token_expire_days)
#     )
    
#     # Store refresh token
#     refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
#     db_refresh_token = RefreshToken(
#         token_hash=refresh_token_hash,
#         user_id=user.id,
#         expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
#     )
#     db.add(db_refresh_token)
#     db.commit()
    
#     logger.info(f"Successful registration for user: {user.username}")
    
#     return AuthResponse(
#         user=UserProfile.model_validate(user),
#         tokens=TokenResponse(
#             access_token=access_token,
#             refresh_token=refresh_token,
#             token_type="bearer",
#             expires_in=settings.access_token_expire_minutes * 60
#         )
#     )


# @router.post("/refresh", response_model=TokenRefreshResponse)
# async def refresh_token(
#     token_data: TokenRefresh,
#     db: Session = Depends(get_db)
# ):
#     """Refresh access token using refresh token."""
#     # Verify refresh token
#     token_payload = SecurityUtils.verify_token(token_data.refresh_token, "refresh")
#     if not token_payload:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid refresh token"
#         )
    
#     # Check if refresh token exists and is not revoked
#     refresh_token_hash = hashlib.sha256(token_data.refresh_token.encode()).hexdigest()
#     db_refresh_token = db.query(RefreshToken).filter(
#         and_(
#             RefreshToken.token_hash == refresh_token_hash,
#             RefreshToken.user_id == token_payload.user_id,
#             RefreshToken.is_revoked == False,
#             RefreshToken.expires_at > datetime.now(timezone.utc)
#         )
#     ).first()
    
#     if not db_refresh_token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Refresh token not found or expired"
#         )
    
#     # Get user
#     user = db.query(User).filter(
#         User.id == token_payload.user_id,
#         User.is_active == True
#     ).first()
    
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not found or inactive"
#         )
    
#     # Create new access token
#     new_token_data = {
#         "sub": user.username,
#         "user_id": user.id,
#         "email": user.email,
#         "roles": [role.name for role in user.roles]
#     }
    
#     access_token = SecurityUtils.create_access_token(
#         data=new_token_data,
#         expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
#     )
    
#     return TokenRefreshResponse(
#         access_token=access_token,
#         token_type="bearer",
#         expires_in=settings.access_token_expire_minutes * 60
#     )


# @router.post("/logout", response_model=MessageResponse)
# async def logout(
#     token_data: TokenRefresh,
#     current_user: User = Depends(get_current_active_user),
#     db: Session = Depends(get_db)
# ):
#     """Logout user by revoking refresh token."""
#     # Revoke refresh token
#     refresh_token_hash = hashlib.sha256(token_data.refresh_token.encode()).hexdigest()
#     db_refresh_token = db.query(RefreshToken).filter(
#         and_(
#             RefreshToken.token_hash == refresh_token_hash,
#             RefreshToken.user_id == current_user.id,
#             RefreshToken.is_revoked == False
#         )
#     ).first()
    
#     if db_refresh_token:
#         db_refresh_token.is_revoked = True
#         db_refresh_token.revoked_at = datetime.now(timezone.utc)
#         db.commit()
    
#     logger.info(f"User logged out: {current_user.username}")
    
#     return MessageResponse(message="Successfully logged out")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: PasswordReset,
    db: Session = Depends(get_db)
):
    """Request password reset."""
    user = db.query(User).filter(
        User.email == request.email,
        User.is_active == True
    ).first()
    
    if not user:
        # Don't reveal if email exists
        return MessageResponse(
            message="If the email exists, a password reset link has been sent"
        )
    
    # Generate reset token
    reset_token = SecurityUtils.generate_reset_token()
    reset_token_hash = hashlib.sha256(reset_token.encode()).hexdigest()
    
    # Store reset token
    db_reset_token = PasswordResetToken(
        token_hash=reset_token_hash,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour expiry
    )
    db.add(db_reset_token)
    db.commit()
    
    # TODO: Send email with reset token
    logger.info(f"Password reset requested for user: {user.email}")
    logger.debug(f"Reset token (for development): {reset_token}")
    
    return MessageResponse(
        message="If the email exists, a password reset link has been sent"
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using reset token."""
    # Validate passwords match
    try:
        request.validate_passwords_match()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Find and validate reset token
    reset_token_hash = hashlib.sha256(request.token.encode()).hexdigest()
    db_reset_token = db.query(PasswordResetToken).filter(
        and_(
            PasswordResetToken.token_hash == reset_token_hash,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.now(timezone.utc)
        )
    ).first()
    
    if not db_reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get user
    user = db.query(User).filter(User.id == db_reset_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Update password
    user.password_hash = SecurityUtils.hash_password(request.new_password)
    
    # Mark reset token as used
    db_reset_token.is_used = True
    db_reset_token.used_at = datetime.now(timezone.utc)
    
    # Revoke all existing refresh tokens for security
    db.query(RefreshToken).filter(
        and_(
            RefreshToken.user_id == user.id,
            RefreshToken.is_revoked == False
        )
    ).update({
        "is_revoked": True,
        "revoked_at": datetime.now(timezone.utc)
    })
    
    db.commit()
    
    logger.info(f"Password reset completed for user: {user.username}")
    
    return MessageResponse(message="Password reset successfully")


# @router.get("/me", response_model=UserProfile)
# async def get_current_user_profile(
#     current_user: User = Depends(get_current_active_user)
# ):
#     """Get current user profile."""
#     return UserProfile.model_validate(current_user)

@router.post("/login")
async def login(credentials: UserLogin):
    """Proxy login to SSO."""
    try:
        data = credentials.model_dump()
        sso_resp = await sso_post("/login", data)
        return sso_resp
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

@router.post("/register")
async def register(user_data: UserRegister):
    """Proxy register to SSO."""
    try:
        data = user_data.model_dump()
        sso_resp = await sso_post("/register", data)
        return sso_resp
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

@router.post("/refresh")
async def refresh_token(token_data: TokenRefresh):
    """Proxy refresh to SSO."""
    try:
        sso_resp = await sso_post("/refresh", token_data.model_dump())
        return sso_resp
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

@router.post("/logout")
async def logout(token_data: TokenRefresh):
    """Proxy logout to SSO."""
    try:
        sso_resp = await sso_post("/logout", token_data.model_dump())
        return sso_resp
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

@router.get("/me")
async def get_current_user_profile(request: Request):
    """Proxy user profile to SSO."""
    auth_header = request.headers.get("authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    try:
        sso_resp = await sso_get("/me", headers={"Authorization": auth_header})
        return sso_resp
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)