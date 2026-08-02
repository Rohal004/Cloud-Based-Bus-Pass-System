from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, random_token, verify_password
from app.db import get_db
from app.models import User, UserRole
from app.routers.deps import get_current_user
from app.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UpdateProfileRequest,
    VerifyEmailRequest,
)
from app.services.logging_service import log_event

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=MessageResponse)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    verification_token = random_token(12)
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone_number=payload.phone_number,
        password_hash=hash_password(payload.password),
        role=UserRole(payload.role),
        verification_token=verification_token,
    )
    db.add(user)
    db.commit()
    log_event(db, "registration", f"User registered with email {payload.email}", user.id)
    return {"success": True, "message": f"Registered successfully. Verification token: {verification_token}"}


@router.post("/login", response_model=TokenResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id)
    log_event(db, "login", f"User login for email {payload.email}", user.id)
    return {"success": True, "access_token": token, "token_type": "bearer"}


@router.post("/logout", response_model=MessageResponse)
def logout_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_event(db, "logout", "User logged out", current_user.id)
    return {"success": True, "message": "Logout successful"}


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        user.reset_token = random_token(12)
        db.commit()
        log_event(db, "forgot_password", f"Reset token generated for {payload.email}", user.id)
        return {"success": True, "message": f"Password reset token: {user.reset_token}"}
    return {"success": True, "message": "If this account exists, a reset token has been generated."}


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == payload.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    user.password_hash = hash_password(payload.new_password)
    user.reset_token = None
    db.commit()
    log_event(db, "reset_password", "Password reset successful", user.id)
    return {"success": True, "message": "Password reset successful"}


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or user.verification_token != payload.token:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    user.is_verified = True
    user.verification_token = None
    db.commit()
    log_event(db, "verify_email", "Email verified", user.id)
    return {"success": True, "message": "Email verified"}


@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "success": True,
        "data": {
            "user_id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone_number": current_user.phone_number,
            "registration_date": current_user.registration_date,
            "role": current_user.role,
        },
    }


@router.put("/profile", response_model=MessageResponse)
def update_profile(payload: UpdateProfileRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.full_name:
        current_user.full_name = payload.full_name
    if payload.phone_number:
        current_user.phone_number = payload.phone_number
    db.commit()
    log_event(db, "profile_update", "Profile updated", current_user.id)
    return {"success": True, "message": "Profile updated"}
