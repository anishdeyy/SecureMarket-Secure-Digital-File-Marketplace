from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    event = Column(String(100), nullable=False, index=True)
    actor_email = Column(String(255))
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    resource_type = Column(String(100))
    resource_id = Column(String(200))
    description = Column(Text)
    extra_metadata = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    user = relationship("User", back_populates="audit_logs")
