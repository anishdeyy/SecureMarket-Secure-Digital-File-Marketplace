import enum
from sqlalchemy import Column, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, unique=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    status = Column(String(50), default="pending")
    gateway = Column(String(50), default="mock")
    gateway_payment_id = Column(String(200))
    gateway_order_id = Column(String(200))
    gateway_signature = Column(String(500))
    is_mock = Column(Boolean, default=False)
    webhook_received = Column(Boolean, default=False)
    webhook_verified = Column(Boolean, default=False)
    failure_reason = Column(String(500))
    extra_data = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    order = relationship("Order", back_populates="payment")
