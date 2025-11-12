from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from ..models import User, UserRole
from ..database import get_db
from ..utils.security import (
    verify_password, get_password_hash, create_access_token,
    decode_access_token, get_current_user
)
from ..utils.validators import validate_email, validate_phone
from ..schemas.auth import (
    UserCreate, UserResponse, Token, LoginRequest,
    PasswordResetRequest, PasswordResetConfirm
)

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Validate email format
    if not validate_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Validate phone number if provided
    if user_data.phone_number and not validate_phone(user_data.phone_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format"
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | 
        (User.phone_number == user_data.phone_number)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        phone_number=user_data.phone_number,
        password_hash=hashed_password,
        role=UserRole.USER,
        is_email_verified=False,
        is_phone_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse.from_orm(new_user)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login user and return access token"""
    # Find user by email
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 30 * 60,  # 30 minutes in seconds
        "user": UserResponse.from_orm(user)
    }

@router.get("/verify", response_model=UserResponse)
async def verify_token(current_user: User = Depends(get_current_user)):
    """Verify access token and return current user"""
    return UserResponse.from_orm(current_user)

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token"""
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": current_user.id}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 30 * 60,
        "user": UserResponse.from_orm(current_user)
    }

@router.post("/reset-password")
async def reset_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset"""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a reset link will be sent"}
    
    # Generate reset token (in production, this would be sent via email)
    reset_token = create_access_token(
        data={"sub": user.id, "type": "password_reset"},
        expires_delta=timedelta(hours=1)
    )
    
    # TODO: Send reset email with token
    # For now, just return the token for development
    return {
        "message": "Password reset token generated (development only)",
        "reset_token": reset_token  # Remove this in production
    }

@router.post("/reset-password/confirm")
async def confirm_reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Confirm password reset with token"""
    # Decode and verify reset token
    payload = decode_access_token(request.reset_token)
    if not payload or payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.password_hash = get_password_hash(request.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Password reset successful"}

@router.put("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user"""
    # Verify current password
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse.from_orm(current_user)

@router.put("/me", response_model=UserResponse)
async def update_profile(
    name: Optional[str] = None,
    phone_number: Optional[str] = None,
    bio: Optional[str] = None,
    avatar_url: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    # Validate phone number if provided
    if phone_number and not validate_phone(phone_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number format"
        )
    
    # Update fields
    if name is not None:
        current_user.name = name
    if phone_number is not None:
        current_user.phone_number = phone_number
    if bio is not None:
        current_user.bio = bio
    if avatar_url is not None:
        current_user.avatar_url = avatar_url
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.from_orm(current_user)