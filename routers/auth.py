"""
Authentication Router for Causal Affect Platform
Handles login, registration, logout, and user management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging

from database import get_db
from models import User
from services.auth import (
    get_user_by_email,
    create_user,
    authenticate_user,
    get_current_user,
    require_auth,
    require_admin,
    set_auth_cookies,
    clear_auth_cookies,
    create_access_token
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/check-first-user")
async def check_first_user(db: Session = Depends(get_db)):
    """Check if this would be the first user (for superuser notice)"""
    user_count = db.query(User).count()
    return {"is_first_user": user_count == 0}


@router.post("/register")
async def register(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    display_name: str = Form(None),
    db: Session = Depends(get_db)
):
    """Register a new user - first user becomes superuser"""
    try:
        # Validate email format
        email = email.lower().strip()
        if not email or '@' not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email address"
            )
        
        # Validate password
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters"
            )
        
        # Check if email already exists
        existing_user = get_user_by_email(db, email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user (first user gets superuser role automatically)
        user = create_user(db, email, password, display_name)
        
        # Set auth cookies
        set_auth_cookies(response, user)
        
        message = "Account created successfully!"
        if user.is_superuser:
            message = "🎉 Welcome! You are the first user and have been granted superuser privileges."
        
        return {
            "message": message,
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "role": user.role
            },
            "redirect": "/dashboard"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login")
async def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    remember: bool = Form(False),
    db: Session = Depends(get_db)
):
    """Authenticate user and create session"""
    user = authenticate_user(db, email, password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Set auth cookies
    set_auth_cookies(response, user)
    
    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role
        },
        "redirect": "/dashboard"
    }


@router.post("/logout")
async def logout(response: Response):
    """Clear session and log out user"""
    clear_auth_cookies(response)
    return {"message": "Logged out successfully", "redirect": "/"}


@router.get("/me")
async def get_me(user: User = Depends(require_auth)):
    """Get current authenticated user"""
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "subscription_tier": user.subscription_tier,
        "is_admin": user.is_admin,
        "is_superuser": user.is_superuser
    }


@router.get("/users")
async def list_users(
    user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "display_name": u.display_name,
            "role": u.role,
            "subscription_tier": u.subscription_tier,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None
        }
        for u in users
    ]


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: str = Form(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user role (admin only)"""
    valid_roles = ['free', 'subscriber', 'admin', 'superuser']
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {valid_roles}"
        )
    
    # Only superuser can grant superuser or admin roles
    if role in ['superuser', 'admin'] and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can grant admin/superuser roles"
        )
    
    # Find user
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent demoting yourself if you're the only superuser
    if target_user.id == current_user.id and target_user.role == 'superuser':
        superuser_count = db.query(User).filter(User.role == 'superuser').count()
        if superuser_count <= 1 and role != 'superuser':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the only superuser"
            )
    
    target_user.role = role
    db.commit()
    
    logger.info(f"User {target_user.email} role changed to {role} by {current_user.email}")
    
    return {"message": f"User role updated to {role}"}


@router.put("/users/{user_id}/subscription")
async def update_user_subscription(
    user_id: int,
    tier: str = Form(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user subscription tier (admin only)"""
    valid_tiers = ['free', 'basic', 'pro', 'enterprise']
    if tier not in valid_tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tier. Must be one of: {valid_tiers}"
        )
    
    # Find user
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    target_user.subscription_tier = tier
    db.commit()
    
    logger.info(f"User {target_user.email} subscription changed to {tier} by {current_user.email}")
    
    return {"message": f"User subscription updated to {tier}"}


@router.post("/fix-superuser")
async def fix_superuser_tier(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Fix first user to have enterprise tier (one-time fix)"""
    # Only the first user (id=1) who is superuser can use this
    if current_user.id != 1 or not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the first superuser can use this endpoint"
        )
    
    if current_user.subscription_tier == 'enterprise':
        return {"message": "Already on enterprise tier", "tier": "enterprise"}
    
    current_user.subscription_tier = 'enterprise'
    db.commit()
    
    logger.info(f"Fixed superuser {current_user.email} to enterprise tier")
    
    return {"message": "Upgraded to enterprise tier", "tier": "enterprise"}
