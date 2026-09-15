from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models.user import User
from app.models.session import PasswordReset, EmailVerification
from app.schemas.user import UserCreate, UserLogin, UserOut, TokenResponse, UserUpdate, ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth_service import (
    hash_password, authenticate_user, create_access_token,
    create_refresh_token, generate_secure_token, get_user_by_email, verify_password
)
from app.services.audit_service import log_event, send_notification
from app.middleware.auth import get_current_user, get_client_ip
import logging

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    # Check duplicate email
    if get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check duplicate username
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    chosen_role = (user_data.role or "BUYER").upper().strip()
    if chosen_role not in ("BUYER", "SELLER"):
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'BUYER' or 'SELLER'.")

    user = User(
        email=user_data.email.lower(),
        username=user_data.username.lower(),
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=chosen_role,
        roles=chosen_role,
        seller_approved=(chosen_role == "SELLER")
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create email verification token
    token = generate_secure_token()
    ev = EmailVerification(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(ev)
    db.commit()

    log_event(db, "USER_REGISTERED", str(user.id), actor_email=user.email,
              ip_address=get_client_ip(request))
    send_notification(db, str(user.id), "Welcome to SecureMarket!",
                     "Your account has been created. Please verify your email.", "success")

    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=user)

@router.post("/login", response_model=TokenResponse)
async def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.email, credentials.password)

    if not user:
        # Log failed attempt
        log_event(db, "LOGIN_FAILED", actor_email=credentials.email,
                 ip_address=get_client_ip(request))
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if user.is_suspended:
        raise HTTPException(status_code=403, detail="Account is suspended")

    user.last_login = datetime.utcnow()
    db.commit()

    log_event(db, "LOGIN_SUCCESS", str(user.id), actor_email=user.email,
              ip_address=get_client_ip(request))

    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=user)

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # JWT logout is handled client-side by clearing the token
    return {"success": True, "message": "Logged out successfully"}

@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserOut)
async def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name
    if update_data.bio is not None:
        current_user.bio = update_data.bio
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/become-seller")
async def become_seller(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.is_seller():
        return {"success": True, "message": "Already a seller"}

    raise HTTPException(
        status_code=400,
        detail="Dynamic role switching is disabled. SecureMarket enforces strict role separation between Buyers and Sellers. Please register a dedicated Seller account."
    )

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, req.email)
    if user:
        token = generate_secure_token()
        pr = PasswordReset(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(pr)
        db.commit()
        # In production: send email. For demo, return token
        logger.info(f"Password reset token for {user.email}: {token}")

    # Always return success to prevent email enumeration
    return {"success": True, "message": "If that email is registered, you'll receive reset instructions"}

@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    pr = db.query(PasswordReset).filter(
        PasswordReset.token == req.token,
        PasswordReset.is_used == False
    ).first()

    if not pr or pr.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == pr.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(req.new_password)
    pr.is_used = True
    db.commit()

    log_event(db, "PASSWORD_CHANGED", str(user.id), actor_email=user.email)
    return {"success": True, "message": "Password reset successfully"}

@router.post("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    ev = db.query(EmailVerification).filter(
        EmailVerification.token == token,
        EmailVerification.is_used == False
    ).first()

    if not ev or ev.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    user = db.query(User).filter(User.id == ev.user_id).first()
    if user:
        user.is_email_verified = True
        ev.is_used = True
        db.commit()
        log_event(db, "EMAIL_VERIFIED", str(user.id), actor_email=user.email)

    return {"success": True, "message": "Email verified successfully"}
