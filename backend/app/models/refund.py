import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from app.database import Base

class RefundStatus(str, enum.Enum):
    REFUND_REQUESTED = "REFUND_REQUESTED"
    REFUND_APPROVED = "REFUND_APPROVED"
    REFUND_REJECTED = "REFUND_REJECTED"
    REFUNDED = "REFUNDED"

class Refund(Base):
    __tablename__ = "refunds"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    buyer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    reason = Column(Text, nullable=True)
    status = Column(String(50), default="REFUND_REQUESTED", index=True)
    processed_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
