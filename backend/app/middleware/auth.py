from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.auth_service import verify_token, get_user_by_id
from app.models.user import User

security = HTTPBearer()

def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:].strip()
    payload = verify_token(token)
    if not payload or payload.get("type") != "access":
        return None
    user = get_user_by_id(db, payload.get("sub"))
    if not user or not user.is_active or user.is_suspended:
        return None
    return user

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = verify_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = get_user_by_id(db, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not user.is_active or user.is_suspended:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is suspended")

    return user

def require_buyer(current_user: User = Depends(get_current_user)) -> User:
    """Strict check: Only BUYER accounts can access buyer purchase flows."""
    if not current_user.is_buyer():
        role_label = current_user.normalized_role
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only Buyer accounts can purchase products or access buyer checkouts. Current account role is {role_label}."
        )
    return current_user

def require_seller(current_user: User = Depends(get_current_user)) -> User:
    """Strict check: Only SELLER accounts can upload products, manage listings, and access seller dashboard."""
    if not current_user.is_seller():
        role_label = current_user.normalized_role
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Seller access required. Current account role is {role_label}."
        )
    return current_user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Strict check: Only ADMIN accounts can access management and administrative endpoints."""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def get_client_ip(request) -> str:
    """Extract client IP safely."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
