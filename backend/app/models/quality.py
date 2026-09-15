import json
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class ProductQualityAnalysis(Base):
    __tablename__ = "product_quality_analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), unique=True, nullable=False, index=True)
    
    # 0 to 100 overall weighted score
    overall_score = Column(Integer, nullable=False, default=0)
    quality_level = Column(String(20), nullable=False, default="Good")  # Excellent, Good, Fair, Low, Very Low
    detected_content_type = Column(String(50), default="Document")
    
    # Dimension sub-scores (0-100)
    content_usefulness = Column(Integer, nullable=False, default=0)
    completeness = Column(Integer, nullable=False, default=0)
    structure_organization = Column(Integer, nullable=False, default=0)
    practical_value = Column(Integer, nullable=False, default=0)
    technical_depth = Column(Integer, nullable=False, default=0)
    methodology_depth = Column(Integer, nullable=False, default=70)
    evidence_results = Column(Integer, nullable=False, default=70)
    
    # AI Qualitative feedback
    confidence_score = Column(Float, default=0.85)
    key_strengths = Column(Text, default="[]")
    limitations = Column(Text, default="[]")
    target_use_case = Column(String(500), nullable=True)
    reasoning = Column(Text, nullable=True)
    
    # Listing Risk Score (separate from quality score: 0-24 Low, 25-49 Medium, 50-74 High, 75-100 Critical)
    risk_score = Column(Integer, default=10)
    risk_level = Column(String(20), default="low")  # low, medium, high, critical
    risk_factors = Column(Text, default="[]")
    risk_reasons = Column(Text, default="[]")
    positive_checks = Column(Text, default="[]")
    
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="quality_analysis")

    def get_strengths(self):
        try:
            return json.loads(self.key_strengths) if self.key_strengths else []
        except Exception:
            return []

    def get_limitations(self):
        try:
            return json.loads(self.limitations) if self.limitations else []
        except Exception:
            return []

    def get_risk_factors(self):
        try:
            return json.loads(self.risk_factors) if self.risk_factors else []
        except Exception:
            return []

    def get_risk_reasons(self):
        try:
            return json.loads(self.risk_reasons) if self.risk_reasons else []
        except Exception:
            return []

    def get_positive_checks(self):
        try:
            return json.loads(self.positive_checks) if self.positive_checks else []
        except Exception:
            return []
