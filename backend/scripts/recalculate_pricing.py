"""
recalculate_pricing.py — Recalculates quality, value score, suggested price,
and product-specific maximum pricing ceilings for all existing marketplace products.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import json
from app.database import SessionLocal
from app.models.product import Product
from app.models.quality import ProductQualityAnalysis
from app.services.quality_service import (
    evaluate_and_save_product_quality,
    clean_audience_description,
    detect_content_type,
    determine_quality_level,
    compute_listing_risk
)
from app.services.pricing_service import (
    calculate_product_pricing,
    PRICING_RULE_VERSION
)

def recalculate_all():
    db = SessionLocal()
    products = db.query(Product).all()
    print(f"Recalculating quality and pricing for {len(products)} products...")
    
    updated_count = 0
    for p in products:
        text = (p.description or "") + "\n\n" + (p.short_description or "") + "\n\n" + (p.summary or "")
        filename = p.original_filename or f"{p.title}.{p.file_extension or 'pdf'}"
        c_type = detect_content_type(text, filename, p.mime_type or "application/pdf")
        
        # 1. Update or create quality analysis
        qa = p.quality_analysis
        if not qa:
            qa = evaluate_and_save_product_quality(db, p, text, commit=False)
        else:
            # Recompute with evidence-based rubric and tiers
            qa.detected_content_type = c_type
            qa.quality_level = determine_quality_level(qa.overall_score)
            qa.target_use_case = clean_audience_description(qa.target_use_case, filename=filename, title=p.title)
        
        # 2. Recalculate dynamic pricing
        pricing = calculate_product_pricing(p, extracted_text=text, quality_analysis=qa)
        p.suggested_price = pricing["suggested_price"]
        p.suggested_price_min = pricing["suggested_price_min"]
        p.suggested_price_max = pricing["suggested_price_max"]
        p.maximum_allowed_price = pricing["maximum_allowed_price"]
        p.value_score = pricing["value_score"]
        p.pricing_rule_version = PRICING_RULE_VERSION
        
        # 3. Listing Risk (decoupled from quality)
        word_count = len(text.split())
        risk_info = compute_listing_risk(
            price=p.price or 0.0,
            quality_score=qa.overall_score,
            suggested_price=p.suggested_price,
            maximum_allowed_price=p.maximum_allowed_price,
            content_type=c_type,
            is_unique=(p.duplicate_status != "DUPLICATE_DETECTED"),
            malware_clean=(p.scan_status == "clean"),
            word_count=word_count
        )
        qa.risk_score = risk_info["risk_score"]
        qa.risk_level = risk_info["risk_level"]
        qa.risk_reasons = json.dumps(risk_info["risk_reasons"])
        qa.positive_checks = json.dumps(risk_info["positive_checks"])
        
        # 4. Status determination
        if p.price > p.maximum_allowed_price:
            p.price_status = "PRICE_EXCEEDED"
            p.price_risk_level = "high"
        elif p.suggested_price and p.price > p.suggested_price * 3.0:
            p.price_status = "PRICE_REVIEW"
            p.price_risk_level = "medium"
        else:
            p.price_status = "PRICE_VALID"
            p.price_risk_level = "low"
            
        print(f"[{p.title[:35]:35}] Type: {c_type:15} Qual: {qa.overall_score:2} ({qa.quality_level:9}) Price: INR {p.price:6.0f} Sug: INR {p.suggested_price:4.0f} Max: INR {p.maximum_allowed_price:5.0f} Risk: {qa.risk_level:7} Status: {p.price_status}")
        updated_count += 1
        
    db.commit()
    db.close()
    print(f"\nSuccessfully recalculated {updated_count} products.")

if __name__ == "__main__":
    recalculate_all()
