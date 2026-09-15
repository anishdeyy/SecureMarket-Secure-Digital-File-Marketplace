import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class PayoutStatus(str, enum.Enum):
    PENDING_PAYOUT = "pending_payout"
    READY = "ready"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Payout(Base):
    __tablename__ = "payouts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    seller_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=True, index=True)
    
    # Financial Breakdown
    gross_amount = Column(Float, nullable=False)     # e.g. ₹699.00 (seller listing price subtotal)
    platform_fee = Column(Float, nullable=False, default=0.0) # e.g. ₹34.95 (5% platform fee)
    other_fee = Column(Float, nullable=False, default=0.0)    # e.g. ₹0.00
    seller_payout = Column(Float, nullable=False)   # e.g. ₹664.05 (net earnings: gross - fees)
    royalty_rate = Column(Float, default=0.95)      # 95% net share
    currency = Column(String(10), default="INR")
    status = Column(String(50), default="pending_payout", index=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
