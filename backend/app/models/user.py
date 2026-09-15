from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
import uuid
from datetime import datetime
from app.database import Base
import enum

class RoleEnum(str, enum.Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"
    ADMIN = "ADMIN"

class Role(Base):
    __tablename__ = "roles"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserRole(Base):
    __tablename__ = "user_roles"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    bio = Column(Text)
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    is_suspended = Column(Boolean, default=False)
    seller_approved = Column(Boolean, default=False)
    role = Column(String(20), default="BUYER", nullable=False, index=True)
    roles = Column(String(200), default="BUYER")
    total_sales = Column(String(50), default="0")
    total_purchases = Column(String(50), default="0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    products = relationship("Product", back_populates="seller", foreign_keys="Product.seller_id")
    orders = relationship("Order", back_populates="buyer")
    reviews = relationship("Review", back_populates="user")
    wishlist_items = relationship("Wishlist", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    downloads = relationship("Download", back_populates="user")

    @property
    def normalized_role(self) -> str:
        r = (self.role or self.roles or "BUYER").upper().strip()
        if "ADMIN" in r:
            return "ADMIN"
        if "SELLER" in r:
            return "SELLER"
        return "BUYER"

    def is_buyer(self) -> bool:
        return self.normalized_role == "BUYER"

    def is_seller(self) -> bool:
        return self.normalized_role == "SELLER"

    def is_admin(self) -> bool:
        return self.normalized_role == "ADMIN"

    def has_role(self, role: str) -> bool:
        target = role.upper().strip()
        return self.normalized_role == target

    def set_role(self, new_role: str):
        valid = {"BUYER", "SELLER", "ADMIN"}
        upper = new_role.upper().strip()
        if upper not in valid:
            raise ValueError(f"Invalid role: {new_role}. Allowed: {valid}")
        self.role = upper
        self.roles = upper
