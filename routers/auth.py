"""
Authentication Router for Causal Affect Platform
Handles login, registration, logout, and user management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging
import os

from database import get_db
from models import User
from services.auth import (
    get_user_by_email,
    create_user,
    authenticate_user,
    verify_password,
    get_current_user,
    require_auth,
    require_admin,
    set_auth_cookies,
    clear_auth_cookies,
    create_access_token
)
from services import mfa

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _registration_open(db: Session) -> bool:
    """Registration is closed unless ALLOW_REGISTRATION=true or no users exist yet."""
    if os.getenv("ALLOW_REGISTRATION", "false").strip().lower() in ("1", "true", "yes"):
        return True
    return db.query(User).count() == 0


def _client_ip(request: Request) -> str:
    # The right-most X-Forwarded-For entry is the one appended by the nearest proxy.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


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
    if not _registration_open(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is closed"
        )
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
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    remember: bool = Form(False),
    totp_code: str = Form(None),
    db: Session = Depends(get_db)
):
    """Authenticate user and create session (password, plus 2FA code if enrolled)"""
    throttle_key = f"{_client_ip(request)}|{email.lower().strip()}"
    if mfa.login_throttle.is_blocked(throttle_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Try again in 15 minutes."
        )

    user = authenticate_user(db, email, password)

    if not user:
        mfa.login_throttle.record_failure(throttle_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if user.totp_enabled:
        code = (totp_code or "").strip()
        if not code:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Enter your two-factor authentication code", "mfa_required": True},
            )

        step = mfa.verify_totp(user.totp_secret, code, user.totp_last_step or 0)
        if step is not None:
            user.totp_last_step = step
            db.commit()
        else:
            remaining = mfa.consume_recovery_code(user.totp_recovery_hashes, code)
            if remaining is None:
                mfa.login_throttle.record_failure(throttle_key)
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication code", "mfa_required": True},
                )
            user.totp_recovery_hashes = remaining
            db.commit()
            logger.warning(f"Recovery code used for {user.email}")

    mfa.login_throttle.reset(throttle_key)

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


@router.post("/2fa/setup")
async def setup_two_factor(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Start 2FA enrollment: returns a secret to add to an authenticator app."""
    if current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="Two-factor authentication is already enabled")

    current_user.totp_secret = mfa.generate_secret()
    db.commit()
    return {
        "secret": current_user.totp_secret,
        "otpauth_uri": mfa.provisioning_uri(current_user.totp_secret, current_user.email),
        "next": "Add the secret to your authenticator app, then POST a current code to /api/auth/2fa/enable",
    }


@router.post("/2fa/enable")
async def enable_two_factor(
    code: str = Form(...),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Finish enrollment by proving the authenticator works. Returns recovery codes once."""
    if current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="Two-factor authentication is already enabled")
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="Call /api/auth/2fa/setup first")

    step = mfa.verify_totp(current_user.totp_secret, code, 0)
    if step is None:
        raise HTTPException(status_code=400, detail="Invalid code")

    recovery_codes = mfa.generate_recovery_codes()
    current_user.totp_enabled = True
    current_user.totp_last_step = step
    current_user.totp_recovery_hashes = mfa.serialise_recovery_hashes(recovery_codes)
    db.commit()
    return {
        "message": "Two-factor authentication enabled",
        "recovery_codes": recovery_codes,
        "warning": "Store these recovery codes somewhere safe. They are shown only once.",
    }


@router.post("/2fa/disable")
async def disable_two_factor(
    password: str = Form(...),
    code: str = Form(...),
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Turn 2FA off; requires the password and a valid authenticator or recovery code."""
    if not current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="Two-factor authentication is not enabled")
    if not verify_password(password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")

    valid = mfa.verify_totp(current_user.totp_secret, code, current_user.totp_last_step or 0) is not None
    if not valid:
        valid = mfa.consume_recovery_code(current_user.totp_recovery_hashes, code) is not None
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid authentication code")

    current_user.totp_enabled = False
    current_user.totp_secret = None
    current_user.totp_recovery_hashes = None
    current_user.totp_last_step = 0
    db.commit()
    return {"message": "Two-factor authentication disabled"}


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
    """Fix superuser to have enterprise tier"""
    # Any superuser can use this to upgrade themselves
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only superusers can use this endpoint. Your role is: {current_user.role}"
        )
    
    if current_user.subscription_tier == 'enterprise':
        return {"message": "Already on enterprise tier", "tier": "enterprise", "role": current_user.role}
    
    current_user.subscription_tier = 'enterprise'
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"Fixed superuser {current_user.email} to enterprise tier")
    
    return {
        "message": "Upgraded to enterprise tier",
        "tier": current_user.subscription_tier,
        "role": current_user.role,
        "user_id": current_user.id
    }


@router.get("/debug-me")
async def debug_me(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Debug endpoint to see full user info"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "role": current_user.role,
        "subscription_tier": current_user.subscription_tier,
        "is_admin": current_user.is_admin,
        "is_superuser": current_user.is_superuser,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified
    }


@router.post("/promote-owner")
async def promote_owner(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """One-time endpoint to promote jamesmfleming@outlook.com to superuser"""
    # Only allow for the legitimate owner email
    if current_user.email != "jamesmfleming@outlook.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for the platform owner"
        )
    
    # Update role and subscription
    current_user.role = 'superuser'
    current_user.subscription_tier = 'enterprise'
    current_user.is_verified = True
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"Promoted {current_user.email} to superuser with enterprise tier")
    
    return {
        "message": "🎉 You have been promoted to superuser with enterprise access!",
        "role": current_user.role,
        "subscription_tier": current_user.subscription_tier,
        "is_superuser": current_user.is_superuser
    }
