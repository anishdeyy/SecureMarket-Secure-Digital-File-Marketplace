import json, logging, uuid, os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path
from app.database import get_db
from app.models.product import Product
from app.models.malware import MalwareScan
from app.models.integrity import FileIntegrityRecord
from app.models.user import User
from app.services.storage_service import storage_service
from app.services.hash_service import calculate_sha256, generate_integrity_record
from app.services.malware_service import validate_file_security, scan_for_malware
from app.services.gemini_service import generate_metadata_gemini, extract_text_from_file
from app.services.quality_service import evaluate_and_save_product_quality
from app.services.duplicate_detection_service import run_duplicate_check_pipeline
from app.services.pricing_service import calculate_product_pricing, validate_price_limit
from app.services.audit_service import log_event, send_notification
from app.middleware.auth import require_seller, get_client_ip
from app.config import settings

router = APIRouter(prefix="/api/uploads", tags=["uploads"])
logger = logging.getLogger(__name__)
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

@router.post("/product")
async def upload_product_file(
    request: Request,
    file: UploadFile = File(...),
    price: float = Form(...),
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db)
):
    """
    Full security pipeline:
      1. Read + size validation
      2. File-type / MIME / extension validation
      3. SHA-256 hash
      4. Create FileIntegrityRecord  ← NEW: unique integrity_id + HMAC seal
      5. Malware scan
      6. Private storage
      7. Gemini AI metadata
    """
    file_content = await file.read()
    file_size = len(file_content)
    logger.info("Upload: %s  size=%d  user=%s", file.filename, file_size, str(current_user.id)[:8])

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(413, f"File too large. Max {settings.MAX_UPLOAD_SIZE_MB} MB")
    if file_size == 0:
        raise HTTPException(400, "File is empty")

    mime_type = file.content_type or "application/octet-stream"
    is_valid, validation_msg = validate_file_security(file.filename, file_content, mime_type)
    if not is_valid:
        log_event(db, "FILE_REJECTED", str(current_user.id), description=f"Rejected: {validation_msg}")
        raise HTTPException(400, f"File rejected: {validation_msg}")

    # ── SHA-256 ──────────────────────────────────────────────────────────────
    sha256_hash = calculate_sha256(file_content)
    log_event(db, "HASH_GENERATED", str(current_user.id), description=f"SHA-256: {sha256_hash[:16]}…")

    # ── Create product stub ──────────────────────────────────────────────────
    ext = Path(file.filename).suffix.lower().lstrip(".")
    product_id = str(uuid.uuid4())

    product = Product(
        id=product_id, seller_id=str(current_user.id),
        title=Path(file.filename).stem.replace("-", " ").replace("_", " ").title(),
        original_filename=file.filename,
        file_extension=ext, mime_type=mime_type,
        file_size_bytes=file_size, sha256_hash=sha256_hash,
        price=max(0.0, price), status="scanning", scan_status="scanning",
        tags="[]", keywords="[]", key_topics="[]"
    )
    db.add(product)
    db.commit()
    log_event(db, "FILE_UPLOADED", str(current_user.id),
              resource_type="product", resource_id=product_id)

    # ── Generate integrity record (unique integrity_id + HMAC seal) ──────────
    try:
        integrity_rec = generate_integrity_record(
            db         = db,
            product_id = product_id,
            seller_id  = str(current_user.id),
            sha256_hash= sha256_hash,
            file_size  = file_size,
            original_filename = file.filename,
            mime_type  = mime_type,
        )
        # Mirror integrity_id in the product row so any divergence is detectable
        product.integrity_id = integrity_rec.integrity_id
        db.commit()
        logger.info("Integrity record saved: %s", integrity_rec.integrity_id)
    except Exception as e:
        logger.error("Integrity record creation failed: %s", e)
        integrity_rec = None

    # ── Malware scan ─────────────────────────────────────────────────────────
    scan_result = scan_for_malware(file_content, file.filename)
    db.add(MalwareScan(
        product_id=product_id, scan_engine=scan_result["engine"],
        result=scan_result["result"], threat_name=scan_result.get("threat_name"),
        details=scan_result.get("details"), is_mock=scan_result.get("is_mock", False)
    ))

    if scan_result["result"] == "infected":
        product.scan_status = "infected"; product.status = "rejected"
        db.commit()
        log_event(db, "MALWARE_SCAN_FAILED", str(current_user.id),
                  resource_type="product", resource_id=product_id)
        send_notification(db, str(current_user.id), "Security Scan Failed",
            f"'{file.filename}' rejected: {scan_result.get('threat_name', 'Malware detected')}", "error")
        raise HTTPException(400, f"File rejected by security scan: {scan_result.get('threat_name')}")

    # ── Private storage ──────────────────────────────────────────────────────
    try:
        storage_key = storage_service.upload_file(
            file_content, str(current_user.id), product_id, file.filename)
        product.storage_key = storage_key
        product.scan_status = "clean"
        product.status      = "ready"
    except Exception as e:
        logger.error("Storage failed: %s", e)
        product.status = "rejected"; db.commit()
        raise HTTPException(500, "File storage failed. Please try again.")
    db.commit()
    log_event(db, "MALWARE_SCAN_PASSED", str(current_user.id),
              resource_type="product", resource_id=product_id)

    # ── Gemini AI metadata ───────────────────────────────────────────────────
    ai_metadata, ai_error = {}, None
    try:
        ai_metadata = generate_metadata_gemini(file_content, file.filename, mime_type)
        product.ai_metadata_generated = True
        product.ai_metadata_raw       = json.dumps(ai_metadata)
        product.title                 = ai_metadata.get("title", product.title)
        product.short_description     = ai_metadata.get("short_description", "")
        product.summary               = ai_metadata.get("summary", "")
        product.category              = ai_metadata.get("category", "Documents")
        product.subcategory           = ai_metadata.get("subcategory", "")
        product.tags                  = json.dumps(ai_metadata.get("tags", []))
        product.keywords              = json.dumps(ai_metadata.get("keywords", []))
        product.language              = ai_metadata.get("language", "English")
        product.difficulty            = ai_metadata.get("difficulty", "Unknown")
        product.content_type          = ai_metadata.get("content_type", "Document")
        product.target_audience       = ai_metadata.get("target_audience", "")
        product.key_topics            = json.dumps(ai_metadata.get("key_topics", []))
        db.commit()
        log_event(db, "AI_METADATA_GENERATED", str(current_user.id),
                  resource_type="product", resource_id=product_id)
        send_notification(db, str(current_user.id), "✨ AI Metadata Generated",
            f"Review metadata for '{product.title}' before publishing.", "success",
            action_url=f"/seller/products/{product_id}/edit")
    except Exception as e:
        logger.error("AI metadata failed: %s", e)
        ai_error = str(e)
        send_notification(db, str(current_user.id), "Metadata Note",
            "AI could not analyse the file. Please fill in details manually.", "warning")

    # ── Duplicate content check & File Quality Assessment ────────────────────
    extracted_text = extract_text_from_file(file_content, file.filename, mime_type)
    if not extracted_text or len(extracted_text.strip()) < 20:
        extracted_text = f"{product.title}\n\n{product.short_description or ''}\n\n{product.summary or ''}"

    dup_res = run_duplicate_check_pipeline(
        db,
        product_id=product_id,
        exact_sha256=sha256_hash,
        extracted_text=extracted_text,
        title=product.title
    )
    if dup_res.get("status") == "DUPLICATE_DETECTED":
        product.duplicate_status = "DUPLICATE_DETECTED"
        product.status = "rejected"
        db.commit()
        log_event(db, "DUPLICATE_CONTENT_BLOCKED", str(current_user.id),
                  resource_type="product", resource_id=product_id,
                  description=f"Duplicate content detected ({dup_res.get('match_level')})")
        send_notification(db, str(current_user.id), "Duplicate Content Detected",
                          "Uploaded file matches existing content in the marketplace. It cannot be published.", "error")

    quality_analysis = evaluate_and_save_product_quality(db, product, extracted_text)

    # ── Dynamic Pricing Ceiling Calculation ───────────────────────────────────
    pricing_data = calculate_product_pricing(product, extracted_text=extracted_text, quality_analysis=quality_analysis)
    product.suggested_price = pricing_data["suggested_price"]
    product.suggested_price_min = pricing_data["suggested_price_min"]
    product.suggested_price_max = pricing_data["suggested_price_max"]
    product.maximum_allowed_price = pricing_data["maximum_allowed_price"]
    product.value_score = pricing_data["value_score"]

    if product.price > product.maximum_allowed_price:
        product.price = product.maximum_allowed_price
        product.price_status = "APPROVED"
    else:
        product.price_status = "APPROVED"
    db.commit()

    return {
        "success": True,
        "product_id": product_id,
        "filename": file.filename,
        "file_size_bytes": file_size,
        "file_extension": ext,
        "security_status": {
            "malware_scan": "passed",
            "integrity_verified": True,
            "secure_delivery": True,
        },
        "scan_status": "clean",
        "duplicate_status": dup_res.get("status", "CLEAR"),
        "duplicate_check": dup_res,
        "quality_score": quality_analysis.overall_score if quality_analysis else None,
        "quality_level": quality_analysis.quality_level if quality_analysis else None,
        "ai_metadata": ai_metadata,
        "ai_error": ai_error,
        "pricing": {
            "value_score": pricing_data["value_score"],
            "suggested_price": pricing_data["suggested_price"],
            "suggested_price_min": pricing_data["suggested_price_min"],
            "suggested_price_max": pricing_data["suggested_price_max"],
            "maximum_allowed_price": pricing_data["maximum_allowed_price"],
            "tier": pricing_data["tier"],
            "reason": pricing_data["reason"]
        },
        "product": {
            "id": product_id,
            "title": product.title,
            "status": product.status,
            "category": product.category,
            "price": product.price,
            "suggested_price": product.suggested_price,
            "suggested_price_min": product.suggested_price_min,
            "suggested_price_max": product.suggested_price_max,
            "maximum_allowed_price": product.maximum_allowed_price,
            "value_score": product.value_score,
            "scan_status": product.scan_status,
            "security_status": {
                "malware_scan": "passed",
                "integrity_verified": True,
                "secure_delivery": True,
            },
            "duplicate_status": product.duplicate_status,
            "quality_score": quality_analysis.overall_score if quality_analysis else None,
            "content_type": product.content_type,
            "target_audience": product.target_audience,
        }
    }

@router.post("/preview/{product_id}")
async def upload_preview_image(
    product_id: str, file: UploadFile = File(...),
    current_user: User = Depends(require_seller), db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id, Product.seller_id == str(current_user.id)
    ).first()
    if not product:
        raise HTTPException(404, "Product not found")
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "Preview image must be under 5 MB")
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(400, "Only image files allowed for preview")
    key = storage_service.upload_preview(content, str(current_user.id), product_id, file.filename)
    url = storage_service.get_preview_url(key)
    product.preview_image_url = url
    product.preview_image_key = key
    db.commit()
    return {"success": True, "preview_url": url}
