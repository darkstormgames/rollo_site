"""Pydantic schemas for authentication and authorization."""

from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserLogin(BaseModel):
    """User login request schema."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class UserRegister(BaseModel):
    """User registration request schema."""
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(
        ..., 
        min_length=8,
        description="Password must be at least 8 characters and contain uppercase, lowercase, digit, and special character"
    )
    confirm_password: str

    def validate_passwords_match(self):
        """Validate that passwords match."""
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class PasswordReset(BaseModel):
    """Password reset request schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    new_password: str = Field(
        ..., 
        min_length=8,
        description="Password must be at least 8 characters and contain uppercase, lowercase, digit, and special character"
    )
    confirm_password: str

    def validate_passwords_match(self):
        """Validate that passwords match."""
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class TokenRefresh(BaseModel):
    """Token refresh request schema."""
    refresh_token: str


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefreshResponse(BaseModel):
    """Token refresh response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserRole(BaseModel):
    """User role schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    permissions: dict


class UserProfile(BaseModel):
    """User profile schema."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    roles: List[UserRole] = []


class AuthResponse(BaseModel):
    """Authentication response schema."""
    user: UserProfile
    tokens: TokenResponse


class MessageResponse(BaseModel):
    """Simple message response schema."""
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None