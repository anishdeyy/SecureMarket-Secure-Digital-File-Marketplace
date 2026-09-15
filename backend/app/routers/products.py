import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc, asc
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate
from app.middleware.auth import get_current_user, require_seller, require_admin
from app.services.audit_service import log_event
from app.services.pricing_service import validate_price_limit

router = APIRouter(prefix="/api/products", tags=["products"])

def _tags(p): 
    try: return json.loads(p.tags) if p.tags else []
    except: return []

def _kw(p):
    try: return json.loads(p.keywords) if p.keywords else []
    except: return []

def _kt(p):
    try: return json.loads(p.key_topics) if p.key_topics else []
    except: return []

@router.get("")
async def list_products(
    page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None, category: Optional[str] = None,
    min_price: Optional[float] = None, max_price: Optional[float] = None,
    min_rating: Optional[float] = None, difficulty: Optional[str] = None,
    language: Optional[str] = None, file_type: Optional[str] = None,
    sort: Optional[str] = "newest", db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.status == "published", Product.is_active == True)
    if search:
        s = f"%{search}%"
        query = query.filter(or_(Product.title.ilike(s), Product.short_description.ilike(s),
                                 Product.summary.ilike(s), Product.category.ilike(s)))
    if category and category.lower() != "all":
        query = query.filter(Product.category.ilike(f"%{category}%"))
    if min_price is not None: query = query.filter(Product.price >= min_price)
    if max_price is not None: query = query.filter(Product.price <= max_price)
    if min_rating is not None: query = query.filter(Product.avg_rating >= min_rating)
    if difficulty: query = query.filter(Product.difficulty.ilike(f"%{difficulty}%"))
    if language: query = query.filter(Product.language.ilike(f"%{language}%"))
    if file_type: query = query.filter(Product.file_extension.ilike(f"%{file_type}%"))

    sort_map = {"newest": desc(Product.created_at), "oldest": asc(Product.created_at),
                "price_low": asc(Product.price), "price_high": desc(Product.price),
                "rating": desc(Product.avg_rating), "popular": desc(Product.total_sales)}
    query = query.order_by(sort_map.get(sort, desc(Product.created_at)))

    total = query.count()
    products = query.offset((page-1)*per_page).limit(per_page).all()
    sellers = {}
    for p in products:
        if p.seller_id not in sellers:
            u = db.query(User).filter(User.id == p.seller_id).first()
            sellers[p.seller_id] = u

    return {
        "items": [_to_list(p, sellers.get(p.seller_id)) for p in products],
        "total": total, "page": page, "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }

def _to_list(p, seller=None):
    q = p.quality_analysis
    return {
        "id": str(p.id), "title": p.title, "short_description": p.short_description,
        "category": p.category, "subcategory": p.subcategory, "price": p.price,
        "currency": p.currency, "preview_image_url": p.preview_image_url,
        "scan_status": p.scan_status,
        "sha256_hash": p.sha256_hash,
        "file_hash_sha256": p.sha256_hash,
        "integrity_id": p.integrity_id,
        "security_status": {
            "malware_scan": "passed" if p.scan_status == "clean" else "pending",
            "integrity_verified": bool(p.sha256_hash),
            "secure_delivery": True,
            "sha256_hash": p.sha256_hash
        },
        "suggested_price": p.suggested_price,
        "maximum_allowed_price": p.maximum_allowed_price,
        "avg_rating": p.avg_rating, "review_count": p.review_count,
        "total_sales": p.total_sales, "file_extension": p.file_extension,
        "difficulty": p.difficulty, "language": p.language, "tags": _tags(p),
        "content_type": p.content_type,
        "quality": {
            "score": q.overall_score,
            "level": q.quality_level
        } if q else None,
        "seller": {"id": str(seller.id), "username": seller.username, "full_name": seller.full_name} if seller else None,
        "created_at": p.created_at.isoformat()
    }

@router.get("/seller/my-products")
async def my_products(
    page: int = Query(1, ge=1), per_page: int = Query(20),
    current_user: User = Depends(require_seller), db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.seller_id == str(current_user.id))
    total = query.count()
    products = query.order_by(desc(Product.created_at)).offset((page-1)*per_page).limit(per_page).all()
    return {"items": [_to_seller(p) for p in products], "total": total, "page": page, "per_page": per_page, "pages": (total+per_page-1)//per_page}

def _to_seller(p):
    q = p.quality_analysis
    return {
        "id": str(p.id), "title": p.title, "short_description": p.short_description,
        "category": p.category, "price": p.price, "currency": p.currency,
        "suggested_price": p.suggested_price,
        "suggested_price_min": p.suggested_price_min,
        "suggested_price_max": p.suggested_price_max,
        "maximum_allowed_price": p.maximum_allowed_price,
        "value_score": p.value_score,
        "price_status": p.price_status or "APPROVED",
        "status": p.status, "scan_status": p.scan_status,
        "sha256_hash": p.sha256_hash,
        "file_hash_sha256": p.sha256_hash,
        "integrity_id": p.integrity_id,
        "security_status": {
            "malware_scan": "passed" if p.scan_status == "clean" else "pending",
            "integrity_verified": bool(p.sha256_hash),
            "duplicate_check": getattr(p, "duplicate_status", "CLEAR") or "CLEAR",
            "secure_delivery": True,
            "sha256_hash": p.sha256_hash
        },
        "duplicate_status": getattr(p, "duplicate_status", "CLEAR") or "CLEAR",
        "quality": {
            "overall_score": q.overall_score,
            "quality_level": q.quality_level,
            "risk_level": q.risk_level
        } if q else None,
        "ai_metadata_generated": p.ai_metadata_generated, "total_sales": p.total_sales,
        "total_downloads": p.total_downloads, "avg_rating": p.avg_rating, "review_count": p.review_count,
        "file_extension": p.file_extension, "file_size_bytes": p.file_size_bytes,
        "original_filename": p.original_filename, "preview_image_url": p.preview_image_url,
        "tags": _tags(p), "keywords": _kw(p), "key_topics": _kt(p),
        "language": p.language, "difficulty": p.difficulty,
        "content_type": p.content_type, "target_audience": p.target_audience,
        "created_at": p.created_at.isoformat(),
        "published_at": p.published_at.isoformat() if p.published_at else None,
    }

@router.get("/{product_id}/quality")
async def get_product_quality(product_id: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    q = p.quality_analysis
    if not q:
        raise HTTPException(status_code=404, detail="Quality assessment not available")
    return {
        "product_id": str(p.id),
        "overall_score": q.overall_score,
        "quality_level": q.quality_level,
        "quality_tier": q.quality_level,
        "detected_content_type": q.detected_content_type,
        "breakdown": {
            "content_usefulness": q.content_usefulness,
            "completeness": q.completeness,
            "structure_organization": q.structure_organization,
            "practical_value": q.practical_value,
            "technical_depth": q.technical_depth,
            "methodology_depth": q.methodology_depth,
            "evidence_results": q.evidence_results
        },
        "confidence_score": q.confidence_score,
        "key_strengths": q.get_strengths(),
        "limitations": q.get_limitations(),
        "target_use_case": q.target_use_case,
        "reasoning": q.reasoning,
        "risk_score": q.risk_score,
        "risk_level": q.risk_level,
        "risk_factors": q.get_risk_factors(),
        "risk_reasons": q.get_risk_reasons(),
        "positive_checks": q.get_positive_checks(),
        "disclaimer": "AI-generated assessment based on file structure and content analysis. Independent verification recommended."
    }

@router.get("/{product_id}")
async def get_product(product_id: str, db: Session = Depends(get_db)):
    pid = product_id.strip()
    p = db.query(Product).filter(Product.id == pid).first()
    if not p:
        p = db.query(Product).filter(Product.id.ilike(pid)).first()
    if not p or (p.status.lower() not in ["published", "approved"]):
        raise HTTPException(status_code=404, detail="Product not found")
    p.view_count += 1
    db.commit()
    seller = db.query(User).filter(User.id == p.seller_id).first()
    q = p.quality_analysis
    return {
        "id": str(p.id), "title": p.title, "short_description": p.short_description,
        "description": p.description, "summary": p.summary,
        "category": p.category, "subcategory": p.subcategory,
        "tags": _tags(p), "keywords": _kw(p), "key_topics": _kt(p),
        "language": p.language, "difficulty": p.difficulty,
        "original_filename": p.original_filename, "file_extension": p.file_extension,
        "mime_type": p.mime_type, "file_size_bytes": p.file_size_bytes,
        "version": p.version, "num_pages": p.num_pages,
        "sha256_hash": p.sha256_hash,
        "file_hash_sha256": p.sha256_hash,
        "integrity_id": p.integrity_id,
        "price": p.price, "currency": p.currency,
        "suggested_price": p.suggested_price,
        "suggested_price_min": p.suggested_price_min,
        "suggested_price_max": p.suggested_price_max,
        "maximum_allowed_price": p.maximum_allowed_price,
        "price_risk_level": p.price_risk_level,
        "value_score": p.value_score,
        "preview_image_url": p.preview_image_url,
        "status": p.status, "scan_status": p.scan_status, "is_featured": p.is_featured,
        "total_sales": p.total_sales, "total_downloads": p.total_downloads,
        "avg_rating": p.avg_rating, "review_count": p.review_count, "view_count": p.view_count,
        "ai_metadata_generated": p.ai_metadata_generated,
        "content_type": p.content_type, "target_audience": p.target_audience,
        "quality_score": q.overall_score if q else None,
        "quality_analysis": {
            "overall_score": q.overall_score,
            "quality_level": q.quality_level,
            "quality_tier": q.quality_level,
            "detected_content_type": q.detected_content_type,
            "content_usefulness": q.content_usefulness,
            "completeness": q.completeness,
            "structure_organization": q.structure_organization,
            "practical_value": q.practical_value,
            "technical_depth": q.technical_depth,
            "methodology_depth": q.methodology_depth,
            "evidence_results": q.evidence_results,
            "confidence_score": q.confidence_score,
            "key_strengths": q.get_strengths(),
            "limitations": q.get_limitations(),
            "target_use_case": q.target_use_case,
            "reasoning": q.reasoning,
            "risk_score": q.risk_score,
            "risk_level": q.risk_level,
            "risk_factors": q.get_risk_factors(),
            "risk_reasons": q.get_risk_reasons(),
            "positive_checks": q.get_positive_checks(),
            "disclaimer": "AI-generated assessment based on file structure and content analysis. Independent verification recommended."
        } if q else None,
        "seller": {"id": str(seller.id), "username": seller.username, "full_name": seller.full_name, "avatar_url": seller.avatar_url} if seller else None,
        "security_status": {
            "malware_scan": "passed" if p.scan_status == "clean" else "pending",
            "integrity_verified": bool(p.sha256_hash),
            "secure_delivery": True,
            "sha256_hash": p.sha256_hash
        },
        "created_at": p.created_at.isoformat(),
        "published_at": p.published_at.isoformat() if p.published_at else None
    }

@router.put("/{product_id}")
async def update_product(product_id: str, update_data: ProductUpdate,
    current_user: User = Depends(require_seller), db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id, Product.seller_id == str(current_user.id)).first()
    if not p: raise HTTPException(status_code=404, detail="Product not found")
    d = update_data.model_dump(exclude_unset=True)

    # Validate price ceiling if seller is modifying price
    if "price" in d and d["price"] is not None:
        proposed_price = float(d["price"])
        is_valid, err_msg, p_calc = validate_price_limit(p, proposed_price)
        if not is_valid:
            raise HTTPException(status_code=400, detail={
                "reason": "PRICE_EXCEEDS_PLATFORM_LIMIT",
                "message": err_msg,
                "maximum_price": p_calc.get("maximum_allowed_price")
            })

    # Protected fields seller cannot override
    disallowed_fields = {"quality_score", "overall_score", "duplicate_status", "sha256_hash", "scan_status", "maximum_allowed_price", "suggested_price"}
    for k, v in d.items():
        if k in disallowed_fields:
            continue
        if k == "tags": p.tags = json.dumps(v)
        elif k == "keywords": p.keywords = json.dumps(v)
        else: setattr(p, k, v)
    db.commit(); db.refresh(p)
    log_event(db, "PRODUCT_UPDATED", str(current_user.id), resource_type="product", resource_id=product_id)
    return _to_seller(p)

@router.post("/{product_id}/publish")
async def publish_product(product_id: str, current_user: User = Depends(require_seller), db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id, Product.seller_id == str(current_user.id)).first()
    if not p: raise HTTPException(status_code=404, detail="Product not found")
    if p.scan_status == "infected": raise HTTPException(status_code=400, detail="Cannot publish: file failed security scan")
    if not p.storage_key: raise HTTPException(status_code=400, detail="Cannot publish: file not uploaded")
    if getattr(p, "duplicate_status", "CLEAR") == "DUPLICATE_DETECTED":
        raise HTTPException(status_code=400, detail="Cannot publish: Duplicate content detected. Only original digital assets can be published.")
    if p.maximum_allowed_price and p.price > p.maximum_allowed_price:
        raise HTTPException(status_code=400, detail=f"Cannot publish: Price ₹{p.price} exceeds platform limit of ₹{p.maximum_allowed_price} for this product.")
    p.status = "published"; p.published_at = datetime.utcnow()
    db.commit()
    log_event(db, "PRODUCT_PUBLISHED", str(current_user.id), resource_type="product", resource_id=product_id)
    return {"success": True, "message": "Product published successfully"}

@router.post("/{product_id}/suspend")
async def suspend_product(product_id: str, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p: raise HTTPException(status_code=404, detail="Product not found")
    p.status = "suspended"; db.commit()
    log_event(db, "ADMIN_ACTION", str(current_user.id), resource_type="product", resource_id=product_id, description="Suspended")
    return {"success": True, "message": "Product suspended"}

@router.delete("/{product_id}")
async def delete_my_product(
    product_id: str,
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db)
):
    """
    Seller endpoint to remove their own product listing.
    Soft-deletes the product (status='removed', is_active=False)
    so existing buyers maintain download access while the product is delisted.
    """
    p = db.query(Product).filter(
        Product.id == product_id,
        Product.seller_id == str(current_user.id)
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found or unauthorized")

    p.status = "removed"
    p.is_active = False
    db.commit()

    log_event(db, "SELLER_PRODUCT_DELETED", str(current_user.id), resource_type="product", resource_id=product_id)
    return {"success": True, "message": f"Product '{p.title}' has been delisted from marketplace."}
