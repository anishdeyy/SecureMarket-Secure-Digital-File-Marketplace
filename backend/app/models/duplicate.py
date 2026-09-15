import json
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class ProductFileFingerprint(Base):
    __tablename__ = "product_file_fingerprints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), unique=True, nullable=False, index=True)
    exact_sha256 = Column(String(64), nullable=False, index=True)
    normalized_content_hash = Column(String(64), nullable=True, index=True)
    extracted_text_snippet = Column(Text, nullable=True)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="file_fingerprint")

class ProductDuplicateCheck(Base):
    __tablename__ = "product_duplicate_checks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="CLEAR") # CLEAR, DUPLICATE_DETECTED, FLAGGED_FOR_REVIEW
    matched_product_id = Column(String(36), ForeignKey("products.id"), nullable=True)
    match_level = Column(String(50), nullable=True) # LEVEL_1_EXACT_SHA256, LEVEL_2_NORMALIZED_HASH, LEVEL_3_TOKEN_SIMILARITY, LEVEL_4_SEMANTIC_MATCH
    similarity_score = Column(Float, default=0.0)
    details = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", foreign_keys=[product_id], back_populates="duplicate_checks")
    matched_product = relationship("Product", foreign_keys=[matched_product_id])

    def get_details(self):
        try:
            return json.loads(self.details) if self.details else {}
        except Exception:
            return {}
