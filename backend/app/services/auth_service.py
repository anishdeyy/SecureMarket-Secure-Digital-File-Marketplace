from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import hashlib, hmac, secrets
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

def _hash_pw(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 310000)
    return f"pbkdf2:{salt}:{h.hex()}"

def _verify_pw(plain: str, stored: str) -> bool:
    if stored.startswith("pbkdf2:"):
        _, salt, stored_hash = stored.split(":", 2)
        h = hashlib.pbkdf2_hmac('sha256', plain.encode(), salt.encode(), 310000)
        return hmac.compare_digest(h.hex(), stored_hash)
    return False

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _verify_pw(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return _hash_pw(password)

def create_access_token(data: dict, expires_delta=None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def verify_token(token: str):
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email.lower()).first()

def get_user_by_id(db: Session, user_id: str):
    return db.query(User).filter(User.id == str(user_id)).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def generate_secure_token():
    return secrets.token_urlsafe(32)
