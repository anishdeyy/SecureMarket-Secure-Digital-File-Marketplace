from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base

class FraudAlert(Base):
    __tablename__ = "fraud_alerts"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    order_id = Column(String(36), nullable=True)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)
    reasons = Column(Text, default="[]")
    status = Column(String(50), default="open")
    action_taken = Column(String(200))
    reviewed_by = Column(String(36), nullable=True)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime)

class FraudAlertStatus(str):
    OPEN = "open"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
