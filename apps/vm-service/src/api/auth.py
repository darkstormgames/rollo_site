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