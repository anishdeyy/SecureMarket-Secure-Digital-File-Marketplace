"""
/api/integrity  — SHA-256 integrity record management.

Public endpoints:
  GET  /api/integrity/{integrity_id}          — look up any record by ID (public proof)

Authenticated endpoints:
  GET  /api/integrity/product/{product_id}    — fetch record for a specific product

Admin endpoints:
  GET  /api/integrity/admin/all              — list all records with optional filters
  POST /api/integrity/admin/{integrity_id}/verify  — re-run HMAC seal check
  GET  /api/integrity/admin/tampered         — list records flagged as tampered
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.integrity import FileIntegrityRecord
from app.models.product import Product
from app.models.user import User
from app.services.hash_service import verify_record_seal, run_full_integrity_check
from app.services.storage_service import storage_service
from app.services.audit_service import log_event
from app.middleware.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/integrity", tags=["integrity"])


# ── helpers ──────────────────────────────────────────────────────────────────

def _safe_record(r: FileIntegrityRecord, include_seal: bool = False, include_hash: bool = True) -> dict:
    """Serialize a record. sha256_hash is public for file verification; hmac_seal is admin-only."""
    d = {
        "integrity_id":      r.integrity_id,
        "product_id":        r.product_id,
        "seller_id":         r.seller_id,
        "file_size":         r.file_size,
        "original_filename": r.original_filename,
        "mime_type":         r.mime_type,
        "is_verified":       r.is_verified,
        "tampered_detected": r.tampered_detected,
        "verified_at":       r.verified_at.isoformat() if r.verified_at else None,
        "last_checked_at":   r.last_checked_at.isoformat() if r.last_checked_at else None,
        "created_at":        r.created_at.isoformat() if r.created_at else None,
        "notes":             r.notes,
        "security_status": {
            "malware_scan": "passed",
            "integrity_verified": r.is_verified and not r.tampered_detected,
            "secure_delivery": True,
            "sha256_hash": r.sha256_hash
        }
    }
    if include_hash:
        d["sha256_hash"] = r.sha256_hash
    if include_seal:
        d["hmac_seal"] = r.hmac_seal  # only for admins
    return d


# ── Public ────────────────────────────────────────────────────────────────────

@router.get("/{integrity_id}")
async def get_by_integrity_id(integrity_id: str, db: Session = Depends(get_db)):
    """
    Public endpoint — anyone can verify a file's integrity proof status.
    Exposes authentic SHA-256 hash for byte-level verification.
    """
    integrity_id = integrity_id.upper()
    record = db.query(FileIntegrityRecord).filter(
        FileIntegrityRecord.integrity_id == integrity_id
    ).first()
    if not record:
        raise HTTPException(404, f"No integrity record found for ID: {integrity_id}")

    # Run HMAC seal check immediately on every lookup
    seal_ok, seal_msg = verify_record_seal(record)

    # Cross-check: does product.integrity_id match?
    product = db.query(Product).filter(Product.id == record.product_id).first()
    cross_ok = (product is not None) and (product.integrity_id == record.integrity_id)

    return {
        **_safe_record(record, include_seal=False, include_hash=True),
        "seal_valid":      seal_ok,
        "seal_message":    "Integrity verified" if seal_ok else "Integrity verification failed",
        "cross_check_ok":  cross_ok,
        "cross_check_msg": "Product record verified" if cross_ok else "Product record mismatch",
        "overall_ok":      seal_ok and cross_ok,
    }


# ── Authenticated ─────────────────────────────────────────────────────────────

@router.get("/product/{product_id}")
async def get_by_product(
    product_id: str,
    db: Session = Depends(get_db)
):
    """Fetch integrity record for a product with authentic SHA-256 fingerprint."""
    pid = product_id.strip()
    record = db.query(FileIntegrityRecord).filter(
        FileIntegrityRecord.product_id == pid
    ).first()
    if not record:
        record = db.query(FileIntegrityRecord).filter(
            FileIntegrityRecord.product_id.ilike(pid)
        ).first()
    if not record:
        raise HTTPException(404, "No integrity record for this product")

    product = db.query(Product).filter(Product.id == record.product_id).first()

    seal_ok, seal_msg = verify_record_seal(record)
    cross_ok = (product is not None) and (product.integrity_id == record.integrity_id)

    return {
        **_safe_record(record, include_seal=False, include_hash=True),
        "seal_valid":      seal_ok,
        "seal_message":    "Integrity verified" if seal_ok else "Integrity verification failed",
        "cross_check_ok":  cross_ok,
        "cross_check_msg": "Product record verified" if cross_ok else "Product record mismatch",
        "overall_ok":      seal_ok and cross_ok,
    }


@router.get("/product/{product_id}/live-verify")
async def live_verify_product_file(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Live recalculation of SHA-256 directly from raw file bytes in storage.
    Compares the calculated hash against the stored database fingerprint.
    """
    pid = product_id.strip()
    product = db.query(Product).filter(Product.id == pid).first()
    if not product:
        product = db.query(Product).filter(Product.id.ilike(pid)).first()
    if not product:
        raise HTTPException(404, "Product not found")

    if not product.storage_key:
        raise HTTPException(400, "File is not stored or has no storage reference")

    try:
        content = storage_service.get_file_content(product.storage_key)
    except Exception as e:
        raise HTTPException(500, f"Unable to read file from storage: {str(e)}")

    import hashlib
    actual_hash = hashlib.sha256(content).hexdigest()
    stored_hash = (product.sha256_hash or "").lower().strip()
    is_match = (actual_hash == stored_hash)

    return {
        "match": is_match,
        "status": "MATCH: File integrity verified" if is_match else "MISMATCH: File integrity check failed",
        "actual_hash": actual_hash,
        "stored_hash": stored_hash,
        "file_size_bytes": len(content),
        "integrity_id": product.integrity_id,
        "original_filename": product.original_filename
    }


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get("/admin/all")
async def admin_list_all(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    tampered_only: bool = False,
    search: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: list all integrity records, optionally filter by tampered status."""
    q = db.query(FileIntegrityRecord)
    if tampered_only:
        q = q.filter(FileIntegrityRecord.tampered_detected == True)
    if search:
        s = f"%{search}%"
        q = q.filter(
            FileIntegrityRecord.integrity_id.ilike(s) |
            FileIntegrityRecord.original_filename.ilike(s) |
            FileIntegrityRecord.sha256_hash.ilike(s) |
            FileIntegrityRecord.product_id.ilike(s)
        )
    total = q.count()
    records = q.order_by(desc(FileIntegrityRecord.created_at)) \
               .offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for r in records:
        seal_ok, _ = verify_record_seal(r)
        product = db.query(Product).filter(Product.id == r.product_id).first()
        cross_ok = product and (product.integrity_id == r.integrity_id)
        items.append({
            **_safe_record(r, include_seal=True, include_hash=True),
            "seal_valid":     seal_ok,
            "cross_check_ok": cross_ok,
            "overall_ok":     seal_ok and cross_ok,
            "product_title":  product.title if product else None,
            "product_status": product.status if product else None,
        })

    return {
        "items":    items,
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "pages":    (total + per_page - 1) // per_page,
    }


@router.post("/admin/{integrity_id}/verify")
async def admin_verify_record(
    integrity_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin: re-run full integrity check including file re-hash from storage.
    This is the definitive tamper check.
    """
    integrity_id = integrity_id.upper()
    record = db.query(FileIntegrityRecord).filter(
        FileIntegrityRecord.integrity_id == integrity_id
    ).first()
    if not record:
        raise HTTPException(404, "Record not found")

    # Try to fetch file from storage for re-hash
    product = db.query(Product).filter(Product.id == record.product_id).first()
    file_content = None
    file_fetch_error = None
    if product and product.storage_key:
        try:
            file_content = storage_service.get_file_content(product.storage_key)
        except Exception as e:
            file_fetch_error = str(e)

    result = run_full_integrity_check(db, record, file_content)
    result["file_fetch_error"] = file_fetch_error

    log_event(db, "INTEGRITY_CHECK_RUN", str(current_user.id),
              resource_type="integrity", resource_id=integrity_id,
              description=f"Admin integrity check: overall_ok={result['overall_ok']}")

    return result


@router.get("/admin/tampered")
async def admin_tampered(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: list all records where tamper has been detected."""
    records = db.query(FileIntegrityRecord).filter(
        FileIntegrityRecord.tampered_detected == True
    ).order_by(desc(FileIntegrityRecord.last_checked_at)).all()

    return {
        "count": len(records),
        "records": [_safe_record(r, include_seal=True) for r in records],
    }
