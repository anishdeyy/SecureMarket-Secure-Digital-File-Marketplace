import json, enum
from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base

class ProductStatus(str, enum.Enum):
    DRAFT = "draft"; SCANNING = "scanning"; READY = "ready"
    PUBLISHED = "published"; REJECTED = "rejected"; SUSPENDED = "suspended"

class ScanStatus(str, enum.Enum):
    PENDING = "pending"; SCANNING = "scanning"; CLEAN = "clean"
    INFECTED = "infected"; FAILED = "failed"

class Category(Base):
    __tablename__ = "categories"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    icon = Column(String(100)); description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Product(Base):
    __tablename__ = "products"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    seller_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    short_description = Column(String(1000)); description = Column(Text); summary = Column(Text)
    category = Column(String(100), index=True); subcategory = Column(String(100))
    tags = Column(Text, default="[]"); keywords = Column(Text, default="[]")
    language = Column(String(50), default="English"); difficulty = Column(String(50))
    original_filename = Column(String(500))
    storage_key = Column(String(1000))          # NEVER exposed to frontend
    file_extension = Column(String(20)); mime_type = Column(String(100))
    file_size_bytes = Column(Integer)
    sha256_hash = Column(String(64), index=True)

    # ── Integrity tracking ──────────────────────────────────────────────────
    # integrity_id mirrors FileIntegrityRecord.integrity_id.
    # If these two ever differ, the product record has been tampered with.
    integrity_id = Column(String(20), nullable=True, unique=True, index=True)

    version = Column(String(50), default="1.0"); num_pages = Column(Integer)
    price = Column(Float, nullable=False, default=0.0); currency = Column(String(10), default="INR")
    # ── Dynamic Pricing & Price Ceiling Engine ──────────────────────────────
    suggested_price = Column(Float, nullable=True)
    suggested_price_min = Column(Float, nullable=True)
    suggested_price_max = Column(Float, nullable=True)
    maximum_allowed_price = Column(Float, nullable=True)
    value_score = Column(Float, nullable=True)
    price_status = Column(String(30), default="APPROVED") # APPROVED, PRICE_REVIEW, REJECTED
    price_risk_level = Column(String(20), default="low")
    pricing_rule_version = Column(String(20), default="PRICING_V3")
    preview_image_url = Column(String(500)); preview_image_key = Column(String(1000))
    status = Column(String(50), default="draft", index=True)
    scan_status = Column(String(50), default="pending")
    is_featured = Column(Boolean, default=False); is_active = Column(Boolean, default=True)
    ai_metadata_generated = Column(Boolean, default=False); ai_metadata_raw = Column(Text)
    content_type = Column(String(100)); target_audience = Column(String(500))
    key_topics = Column(Text, default="[]")
    total_sales = Column(Integer, default=0); total_downloads = Column(Integer, default=0)
    avg_rating = Column(Float, default=0.0); review_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    duplicate_status = Column(String(30), default="CLEAR", index=True) # CLEAR, DUPLICATE_DETECTED, FLAGGED_FOR_REVIEW
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)

    seller     = relationship("User", back_populates="products", foreign_keys=[seller_id])
    order_items = relationship("OrderItem", back_populates="product")
    reviews    = relationship("Review",     back_populates="product")
    downloads  = relationship("Download",   back_populates="product")
    wishlist_items = relationship("Wishlist", back_populates="product")
    malware_scans  = relationship("MalwareScan", back_populates="product")
    quality_analysis = relationship("ProductQualityAnalysis", back_populates="product", uselist=False)
    file_fingerprint = relationship("ProductFileFingerprint", back_populates="product", uselist=False)
    duplicate_checks = relationship("ProductDuplicateCheck", foreign_keys="ProductDuplicateCheck.product_id", back_populates="product")

    def get_tags(self):
        try: return json.loads(self.tags) if self.tags else []
        except: return []
    def get_keywords(self):
        try: return json.loads(self.keywords) if self.keywords else []
        except: return []

class ProductTag(Base):
    __tablename__ = "product_tags"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"))
    tag = Column(String(100), nullable=False)

class ProductMetadata(Base):
    __tablename__ = "product_metadata"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), unique=True)
    metadata_json = Column(Text); generated_by = Column(String(50), default="gemini")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
