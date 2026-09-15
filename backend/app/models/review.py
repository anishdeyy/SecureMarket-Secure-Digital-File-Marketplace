from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base

class Review(Base):
    __tablename__ = "reviews"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    title = Column(String(200))
    body = Column(Text)
    is_verified_purchase = Column(Boolean, default=True)
    status = Column(String(20), default="active", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")
    __table_args__ = (UniqueConstraint('user_id', 'product_id', name='unique_user_product_review'),)
