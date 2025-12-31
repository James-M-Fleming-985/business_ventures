"""
Authentication Schemas for Feasibility Platform
Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=255)


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshToken(BaseModel):
    """Refresh token request"""
    refresh_token: str


class UserResponse(BaseModel):
    """User data response (without password)"""
    id: int
    email: str
    full_name: str
    subscription_tier: str
    is_active: bool
    is_superuser: bool
    
    class Config:
        from_attributes = True


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordReset(BaseModel):
    """Password reset with token"""
    token: str
    new_password: str = Field(..., min_length=8)
