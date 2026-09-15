import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import SessionLocal
from app.models.product import Product
from app.services.gemini_service import extract_text_from_file
from app.services.quality_service import evaluate_and_save_product_quality
from app.services.duplicate_detection_service import run_duplicate_check_pipeline
from app.services.storage_service import storage_service

db = SessionLocal()
products = db.query(Product).order_by(Product.created_at.asc()).all()
print(f"Fingerprinting {len(products)} products...")

for p in products:
    print(f"\nProcessing: {p.id[:8]} - {p.title} (Price: {p.price})")
    # Get file content if available
    extracted_text = ""
    if p.storage_key:
        try:
            local_fp = Path(storage_service.local_path) / p.storage_key
            if local_fp.exists():
                content = local_fp.read_bytes()
                extracted_text = extract_text_from_file(content, p.original_filename or local_fp.name, p.mime_type or "application/octet-stream")
        except Exception as e:
            print(f"  Storage read note: {e}")

    if not extracted_text or len(extracted_text.strip()) < 20:
        extracted_text = f"{p.title}\n\n{p.short_description or ''}\n\n{p.summary or ''}\n\n{p.description or ''}"

    # 1. Run Duplicate Check
    exact_hash = p.sha256_hash or "0" * 64
    dup_res = run_duplicate_check_pipeline(
        db,
        product_id=p.id,
        exact_sha256=exact_hash,
        extracted_text=extracted_text,
        title=p.title
    )
    print(f"  Duplicate Status: {dup_res['status']} ({dup_res.get('match_level')})")
    if dup_res['status'] == 'DUPLICATE_DETECTED':
        print(f"  Matched with: {dup_res.get('matched_product_id')} - {dup_res.get('matched_product_title')}")
        p.duplicate_status = "DUPLICATE_DETECTED"
        # If duplicate detected, ensure it's not active/published
        p.status = "rejected"
        db.commit()

    # 2. Evaluate Quality
    quality_analysis = evaluate_and_save_product_quality(db, p, extracted_text)
    print(f"  Quality Score: {quality_analysis.overall_score}/100 ({quality_analysis.quality_level}) | Risk: {quality_analysis.risk_level} ({quality_analysis.risk_score}/100)")

db.close()
print("\nAll products fingerprinted and quality assessed successfully!")
