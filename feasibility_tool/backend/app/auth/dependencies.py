"""
Authentication Dependencies for Feasibility Platform
Provides get_current_user dependency for protected routes
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from ..models import User
from .utils import decode_token
from ..database import get_db


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode token
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise credentials_exception
    
    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Fetch user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user.
    Alias for get_current_user with explicit active check.
    """
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication - returns User if authenticated, None otherwise.
    Useful for endpoints that work both authenticated and unauthenticated.
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None or payload.get("type") != "access":
        return None
    
    user_id = payload.get("sub")
    if user_id is None:
        return None
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    return user if user and user.is_active else None
