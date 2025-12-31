"""
Authentication Router for Feasibility Platform
Handles user registration, login, token refresh
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from .schemas import (
    UserRegister,
    UserLogin,
    Token,
    RefreshToken,
    UserResponse,
)
from .utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_password,
)
from .dependencies import get_current_user
from ..models import User, SubscriptionTier
from ..database import get_db


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user with Free tier subscription.
    
    - Creates new user account
    - Hashes password securely
    - Assigns Free tier by default
    - Returns user data (without password)
    """
    # Validate password
    is_valid, error_message = validate_password(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if this is the first user (make them admin)
    user_count = db.query(User).count()
    is_first_user = user_count == 0
    
    # Create new user with Free tier
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        subscription_tier=SubscriptionTier.FREE,
        is_active=True,
        is_superuser=is_first_user,  # First user becomes admin
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    
    - Validates credentials
    - Returns access and refresh tokens
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_data: RefreshToken,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    - Validates refresh token
    - Issues new access and refresh tokens
    """
    # Decode refresh token
    payload = decode_token(refresh_data.refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Verify user exists and is active
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information.
    """
    return current_user
