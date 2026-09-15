"""
hash_service.py — SHA-256 + HMAC-sealed integrity records with unique integrity_id.
"""
import hashlib, hmac as _hmac, logging
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.config import settings
from app.models.integrity import FileIntegrityRecord, _gen_integrity_id

logger = logging.getLogger(__name__)

def calculate_sha256(file_content: bytes) -> str:
    digest = hashlib.sha256(file_content).hexdigest()
    logger.info("SHA-256: %s…", digest[:16])
    return digest

def _compute_hmac(integrity_id: str, sha256_hash: str) -> str:
    secret  = settings.JWT_SECRET.encode()
    message = f"{integrity_id}:{sha256_hash}".encode()
    return _hmac.new(secret, message, hashlib.sha256).hexdigest()

def generate_integrity_record(
    db, product_id, seller_id, sha256_hash, file_size, original_filename, mime_type
) -> FileIntegrityRecord:
    integrity_id = _gen_integrity_id()
    while db.query(FileIntegrityRecord).filter(FileIntegrityRecord.integrity_id == integrity_id).first():
        integrity_id = _gen_integrity_id()

    seal = _compute_hmac(integrity_id, sha256_hash)
    record = FileIntegrityRecord(
        integrity_id=integrity_id,
        product_id=str(product_id),
        seller_id=str(seller_id),
        sha256_hash=sha256_hash,
        file_size=str(file_size),
        original_filename=original_filename,
        mime_type=mime_type,
        hmac_seal=seal,
        is_verified=True,
        tampered_detected=False,
        verified_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
        notes="Auto-generated on upload",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info("Integrity record: ID=%s  SHA256=%s…  product=%s",
                integrity_id, sha256_hash[:16], str(product_id)[:8])
    return record

def verify_record_seal(record: FileIntegrityRecord) -> Tuple[bool, str]:
    expected = _compute_hmac(record.integrity_id, record.sha256_hash)
    if _hmac.compare_digest(expected, record.hmac_seal):
        return True, "HMAC seal valid — record has not been tampered"
    return False, "⚠ HMAC mismatch — integrity record may have been altered"

def verify_file_against_record(file_content: bytes, record: FileIntegrityRecord) -> Tuple[bool, str]:
    actual = calculate_sha256(file_content)
    if actual == record.sha256_hash:
        return True, f"File hash matches — integrity confirmed"
    return False, f"⚠ Hash mismatch — stored={record.sha256_hash[:20]}…  actual={actual[:20]}…"

def run_full_integrity_check(db, record: FileIntegrityRecord, file_content=None) -> dict:
    seal_ok, seal_msg = verify_record_seal(record)
    file_ok, file_msg = None, "File content not provided"
    if file_content is not None:
        file_ok, file_msg = verify_file_against_record(file_content, record)
    overall_ok = seal_ok and (file_ok is None or file_ok)
    record.last_checked_at = datetime.utcnow()
    record.tampered_detected = not overall_ok
    db.commit()
    return {
        "integrity_id":      record.integrity_id,
        "product_id":        record.product_id,
        "sha256_hash":       record.sha256_hash,
        "file_size":         record.file_size,
        "original_filename": record.original_filename,
        "mime_type":         record.mime_type,
        "verified_at":       record.verified_at.isoformat(),
        "last_checked_at":   record.last_checked_at.isoformat() if record.last_checked_at else None,
        "seal_valid":        seal_ok,
        "seal_message":      seal_msg,
        "file_hash_valid":   file_ok,
        "file_hash_message": file_msg,
        "overall_ok":        overall_ok,
        "tampered_detected": record.tampered_detected,
    }
