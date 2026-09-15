"""
FileIntegrityRecord — tamper-evident SHA-256 tracking.

Each uploaded file gets ONE immutable record:
  - integrity_id  : publicly shareable unique identifier (e.g. "FI-XXXXXXXX")
  - sha256_hash   : hex digest of the file content
  - hmac_seal     : HMAC-SHA256(integrity_id + sha256_hash, app secret) — detects backend DB tampering
  - verified_at   : timestamp the hash was first committed
  - product_id    : FK to products
  - seller_id     : FK to users

The integrity_id is stored in the product record AND in this table so any
mismatch between the two is itself an integrity signal.

Verification:
  1. Recompute HMAC from stored integrity_id + sha256_hash.
  2. Compare with stored hmac_seal — if different, the record was tampered.
  3. Re-download the file and recompute SHA-256 — compare with sha256_hash.
"""
import hashlib, hmac, uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


def _gen_integrity_id() -> str:
    """Generate a short, human-readable unique integrity ID like FI-A3F8C2D1."""
    return "FI-" + uuid.uuid4().hex[:8].upper()


class FileIntegrityRecord(Base):
    __tablename__ = "file_integrity_records"

    # Primary key — the integrity_id doubles as PK (it IS the unique ID)
    integrity_id = Column(String(20), primary_key=True, default=_gen_integrity_id)

    # Foreign keys
    product_id   = Column(String(36), ForeignKey("products.id"), nullable=False, unique=True, index=True)
    seller_id    = Column(String(36), ForeignKey("users.id"),    nullable=False, index=True)

    # Core integrity fields
    sha256_hash  = Column(String(64),  nullable=False)          # hex SHA-256 of file bytes
    file_size    = Column(String(20),  nullable=False)           # stored as string to avoid type coercion
    original_filename = Column(String(500), nullable=False)
    mime_type    = Column(String(100), nullable=False)

    # HMAC seal — proves record hasn't been altered in the DB
    hmac_seal    = Column(String(64),  nullable=False)

    # Verification status
    is_verified       = Column(Boolean, default=True)            # True right after upload
    tampered_detected = Column(Boolean, default=False)           # set True if HMAC check fails
    last_checked_at   = Column(DateTime, nullable=True)

    # Immutable timestamps
    verified_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at   = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Human-readable note
    notes        = Column(Text, nullable=True)

    # Relationships (read-only, no back_populates needed here)
    product = relationship("Product", foreign_keys=[product_id])
    seller  = relationship("User",    foreign_keys=[seller_id])
