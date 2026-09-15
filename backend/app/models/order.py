from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base
import enum

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAYMENT_PROCESSING = "payment_processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class Order(Base):
    __tablename__ = "orders"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    buyer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(50), default="pending", index=True)
    total_amount = Column(Float, nullable=False)
    subtotal = Column(Float, default=0.0)
    platform_fee = Column(Float, default=0.0)
    service_fee = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.18)
    platform_fee_percent = Column(Float, default=0.05)
    pricing_rule_version = Column(String(50), default="PRICING_V1")
    currency = Column(String(10), default="INR")
    payment_gateway_order_id = Column(String(200))
    payment_gateway = Column(String(50))
    risk_score = Column(Integer, default=0)
    risk_level = Column(String(20), default="low")
    risk_reasons = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime)

    buyer = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    payment = relationship("Payment", back_populates="order", uselist=False)

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    seller_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    price_at_purchase = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    subtotal = Column(Float, default=0.0)
    currency = Column(String(10), default="INR")
    download_count = Column(Integer, default=0)
    download_limit = Column(Integer, default=5)
    download_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
