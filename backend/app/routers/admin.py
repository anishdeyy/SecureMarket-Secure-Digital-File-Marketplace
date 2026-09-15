from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.product import Product, ProductStatus
from app.models.order import Order, OrderStatus
from app.models.payment import Payment
from app.models.fraud import FraudAlert, FraudAlertStatus
from app.models.malware import MalwareScan
from app.models.audit import AuditLog
from app.models.payout import Payout
from app.middleware.auth import require_admin
from app.services.audit_service import log_event, send_notification

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/stats")
async def get_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    buyers = db.query(User).filter(User.role == "BUYER").count()
    sellers = db.query(User).filter(User.role == "SELLER").count()
    total_products = db.query(Product).count()
    published = db.query(Product).filter(Product.status == ProductStatus.PUBLISHED).count()
    total_orders = db.query(Order).count()
    paid_orders = db.query(Order).filter(Order.status == OrderStatus.PAID).count()
    total_revenue = db.query(func.sum(Payment.amount)).filter(
        Payment.status == "success"
    ).scalar() or 0
    total_platform_fees = db.query(func.sum(Payout.platform_fee)).filter(
        Payout.status.in_(["ready", "completed"])
    ).scalar() or 0.0
    total_seller_payouts = db.query(func.sum(Payout.seller_payout)).filter(
        Payout.status.in_(["ready", "completed"])
    ).scalar() or 0.0
    total_taxes = db.query(func.sum(Order.tax)).filter(
        Order.status == OrderStatus.PAID
    ).scalar() or 0.0

    fraud_alerts = db.query(FraudAlert).filter(FraudAlert.status == FraudAlertStatus.OPEN).count()
    malware_alerts = db.query(MalwareScan).filter(MalwareScan.result == "infected").count()

    return {
        "total_users": total_users,
        "buyers": buyers,
        "sellers": sellers,
        "total_products": total_products,
        "published_products": published,
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "total_revenue": round(float(total_revenue), 2),
        "total_platform_fees": round(float(total_platform_fees), 2),
        "total_seller_payouts": round(float(total_seller_payouts), 2),
        "total_taxes": round(float(total_taxes), 2),
        "open_fraud_alerts": fraud_alerts,
        "malware_alerts": malware_alerts
    }

@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20),
    search: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if search:
        query = query.filter(
            User.email.ilike(f"%{search}%") | User.username.ilike(f"%{search}%")
        )
    total = query.count()
    users = query.order_by(desc(User.created_at)).offset((page-1)*per_page).limit(per_page).all()
    return {
        "items": [{"id": str(u.id), "email": u.email, "username": u.username,
                   "roles": u.roles, "is_active": u.is_active, "is_suspended": u.is_suspended,
                   "is_email_verified": u.is_email_verified, "created_at": u.created_at.isoformat()} for u in users],
        "total": total, "page": page, "per_page": per_page
    }

@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if str(user.id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot suspend yourself")
    user.is_suspended = True
    db.commit()
    log_event(db, "ADMIN_ACTION", str(current_user.id), resource_type="user", resource_id=user_id,
              description=f"User suspended: {user.email}")
    return {"success": True, "message": f"User {user.username} suspended"}

@router.post("/users/{user_id}/unsuspend")
async def unsuspend_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_suspended = False
    db.commit()
    log_event(db, "ADMIN_ACTION", str(current_user.id), resource_type="user", resource_id=user_id,
              description=f"User unsuspended: {user.email}")
    return {"success": True, "message": f"User {user.username} unsuspended"}

@router.get("/products")
async def admin_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(20),
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if status and status.lower() != "all":
        query = query.filter(Product.status == status.lower())
    if search:
        query = query.filter(Product.title.ilike(f"%{search}%"))

    total = query.count()
    products = query.order_by(desc(Product.created_at)).offset((page-1)*per_page).limit(per_page).all()

    from app.models.order import OrderItem
    items = []
    for p in products:
        seller = db.query(User).filter(User.id == p.seller_id).first()
        orders_count = db.query(OrderItem).filter(OrderItem.product_id == p.id).count()
        items.append({
            "id": str(p.id),
            "title": p.title,
            "status": p.status,
            "scan_status": p.scan_status,
            "price": p.price,
            "category": p.category,
            "total_sales": p.total_sales,
            "total_downloads": p.total_downloads,
            "orders_count": orders_count,
            "seller_id": str(p.seller_id),
            "seller_name": (seller.full_name or seller.username) if seller else "Unknown",
            "seller_email": seller.email if seller else "Unknown",
            "created_at": p.created_at.isoformat()
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page
    }

@router.post("/products/{product_id}/approve")
async def approve_product(
    product_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.status = ProductStatus.PUBLISHED
    from datetime import datetime
    product.published_at = datetime.utcnow()
    product.is_active = True
    db.commit()
    send_notification(db, str(product.seller_id), "Product Approved",
                     f"Your product '{product.title}' has been approved and is now live.", "success")
    log_event(db, "ADMIN_ACTION", str(current_user.id), resource_type="product",
              resource_id=product_id, description="Product approved by admin")
    return {"success": True, "message": "Product approved"}

@router.post("/products/{product_id}/reject")
async def reject_product(
    product_id: str,
    reason: str = "Does not meet marketplace standards",
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.status = ProductStatus.REJECTED
    product.is_active = False
    db.commit()
    send_notification(db, str(product.seller_id), "Product Rejected",
                     f"Your product '{product.title}' was rejected: {reason}", "error")
    log_event(db, "ADMIN_ACTION", str(current_user.id), resource_type="product",
              resource_id=product_id, description=f"Product rejected: {reason}")
    return {"success": True, "message": "Product rejected"}

@router.delete("/products/{product_id}")
async def admin_delete_product(
    product_id: str,
    reason: Optional[str] = "Removed by administrator for compliance or marketplace policy violation",
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Soft-delete product from marketplace by Administrator.
    Sets status to 'REMOVED_BY_ADMIN' and is_active=False.
    Hides from marketplace listings and blocks new purchases,
    while preserving historical buyer downloads and transaction audit trails.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    from app.models.order import OrderItem
    orders_count = db.query(OrderItem).filter(OrderItem.product_id == product.id).count()

    product.status = "REMOVED_BY_ADMIN"
    product.is_active = False
    db.commit()

    log_event(
        db, "ADMIN_PRODUCT_DELETED", str(current_user.id),
        resource_type="product", resource_id=product_id,
        description=f"Product '{product.title}' removed by Admin. Reason: {reason}. Historical orders preserved: {orders_count}"
    )
    send_notification(
        db, str(product.seller_id), "Product Removed by Administrator",
        f"Your product '{product.title}' was removed from the marketplace. Reason: {reason}",
        "error"
    )

    return {
        "success": True,
        "message": f"Product '{product.title}' has been soft-deleted from the marketplace.",
        "product_id": str(product.id),
        "status": product.status,
        "historical_orders_preserved": orders_count
    }

@router.patch("/products/{product_id}/status")
async def admin_update_product_status(
    product_id: str,
    new_status: str = Query(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    valid_statuses = {"published", "suspended", "rejected", "draft", "removed_by_admin"}
    target = new_status.lower().strip()
    if target not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {valid_statuses}")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.status = target
    if target in ("suspended", "rejected", "removed_by_admin"):
        product.is_active = False
    elif target == "published":
        product.is_active = True
        from datetime import datetime
        product.published_at = datetime.utcnow()

    db.commit()
    log_event(db, "ADMIN_STATUS_UPDATE", str(current_user.id), resource_type="product",
              resource_id=product_id, description=f"Admin changed status to {target}")
    return {"success": True, "product_id": product_id, "status": product.status}

@router.get("/orders")
async def admin_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20),
    status: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    total = query.count()
    orders = query.order_by(desc(Order.created_at)).offset((page-1)*per_page).limit(per_page).all()
    return {
        "items": [{"id": str(o.id), "order_number": o.order_number, "status": o.status,
                   "total_amount": o.total_amount, "risk_level": o.risk_level,
                   "buyer_id": str(o.buyer_id), "created_at": o.created_at.isoformat()} for o in orders],
        "total": total, "page": page, "per_page": per_page
    }

@router.get("/fraud")
async def admin_fraud(
    page: int = Query(1, ge=1),
    per_page: int = Query(20),
    status: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    query = db.query(FraudAlert)
    if status:
        query = query.filter(FraudAlert.status == status)
    total = query.count()
    alerts = query.order_by(desc(FraudAlert.created_at)).offset((page-1)*per_page).limit(per_page).all()
    return {
        "items": [{"id": str(a.id), "user_id": str(a.user_id),
                   "order_id": str(a.order_id) if a.order_id else None,
                   "risk_score": a.risk_score, "risk_level": a.risk_level,
                   "reasons": a.reasons, "status": a.status,
                   "created_at": a.created_at.isoformat()} for a in alerts],
        "total": total, "page": page, "per_page": per_page
    }

@router.post("/fraud/{alert_id}/resolve")
async def resolve_fraud(
    alert_id: str,
    action: str = "reviewed",
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    alert = db.query(FraudAlert).filter(FraudAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    valid_actions = ["reviewed", "resolved", "dismissed"]
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Use: {valid_actions}")
    alert.status = action
    alert.reviewed_by = current_user.id
    from datetime import datetime
    alert.reviewed_at = datetime.utcnow()
    alert.action_taken = action
    db.commit()
    log_event(db, "ADMIN_ACTION", str(current_user.id), resource_type="fraud_alert",
              resource_id=alert_id, description=f"Fraud alert {action}")
    return {"success": True, "message": f"Alert {action}"}

@router.get("/malware")
async def admin_malware(
    page: int = Query(1, ge=1),
    per_page: int = Query(20),
    result: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    query = db.query(MalwareScan)
    if result:
        query = query.filter(MalwareScan.result == result)
    total = query.count()
    scans = query.order_by(desc(MalwareScan.created_at)).offset((page-1)*per_page).limit(per_page).all()
    return {
        "items": [{"id": str(s.id), "product_id": str(s.product_id),
                   "result": s.result, "threat_name": s.threat_name,
                   "engine": s.scan_engine, "is_mock": s.is_mock,
                   "created_at": s.created_at.isoformat()} for s in scans],
        "total": total, "page": page, "per_page": per_page
    }

@router.get("/audit-logs")
async def admin_audit(
    page: int = Query(1, ge=1),
    per_page: int = Query(50),
    event: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if event:
        query = query.filter(AuditLog.event == event)
    total = query.count()
    logs = query.order_by(desc(AuditLog.created_at)).offset((page-1)*per_page).limit(per_page).all()
    return {
        "items": [{"id": str(l.id), "event": l.event, "actor_email": l.actor_email,
                   "resource_type": l.resource_type, "resource_id": l.resource_id,
                   "description": l.description, "ip_address": l.ip_address,
                   "created_at": l.created_at.isoformat()} for l in logs],
        "total": total, "page": page, "per_page": per_page
    }

@router.get("/notifications/stats")
async def notification_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return {"message": "ok"}


@router.get("/database-view")
async def admin_database_view(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Direct localhost inspection of all database tables and recent changes.
    Shows table counts, recent file integrity records, and audit events.
    """
    from app.models.integrity import FileIntegrityRecord

    counts = {
        "users": db.query(User).count(),
        "products": db.query(Product).count(),
        "file_integrity_records": db.query(FileIntegrityRecord).count(),
        "audit_logs": db.query(AuditLog).count(),
        "orders": db.query(Order).count(),
        "payments": db.query(Payment).count(),
        "malware_scans": db.query(MalwareScan).count(),
        "fraud_alerts": db.query(FraudAlert).count(),
    }

    recent_integrity = db.query(FileIntegrityRecord).order_by(
        desc(FileIntegrityRecord.created_at)
    ).limit(15).all()

    recent_audits = db.query(AuditLog).order_by(
        desc(AuditLog.created_at)
    ).limit(20).all()

    return {
        "status": "connected",
        "database_type": "sqlite",
        "counts": counts,
        "recent_file_integrity_records": [
            {
                "integrity_id": r.integrity_id,
                "product_id": r.product_id,
                "seller_id": r.seller_id,
                "sha256_hash": r.sha256_hash,
                "file_size": r.file_size,
                "original_filename": r.original_filename,
                "mime_type": r.mime_type,
                "is_verified": r.is_verified,
                "tampered_detected": r.tampered_detected,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in recent_integrity
        ],
        "recent_audit_changes": [
            {
                "id": str(a.id),
                "event": a.event,
                "actor_email": a.actor_email,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "description": a.description,
                "ip_address": a.ip_address,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in recent_audits
        ]
    }


@router.get("/files")
async def admin_files_list(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all digital files in the system with their integrity verification and storage state."""
    from app.models.integrity import FileIntegrityRecord
    from app.services.hash_service import verify_record_seal

    records = db.query(FileIntegrityRecord).order_by(
        desc(FileIntegrityRecord.created_at)
    ).all()

    items = []
    for r in records:
        product = db.query(Product).filter(Product.id == r.product_id).first()
        seller = db.query(User).filter(User.id == r.seller_id).first()
        seal_ok, _ = verify_record_seal(r)
        items.append({
            "integrity_id": r.integrity_id,
            "original_filename": r.original_filename,
            "file_size_bytes": r.file_size,
            "sha256_hash": r.sha256_hash,
            "mime_type": r.mime_type,
            "is_verified": r.is_verified,
            "tampered_detected": r.tampered_detected,
            "seal_valid": seal_ok,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "product_id": r.product_id,
            "product_title": product.title if product else "Unknown",
            "product_status": product.status if product else "Unknown",
            "seller_email": seller.email if seller else "Unknown",
        })

    return {"files": items, "total": len(items)}

@router.get("/products/{product_id}/security-details")
async def get_product_security_details(
    product_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Restricted security diagnostics endpoint for platform administrators.
    Returns low-level cryptographic signatures, storage keys, and integrity records.
    """
    from app.models.integrity import FileIntegrityRecord
    from app.services.hash_service import verify_record_seal

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    integrity_rec = db.query(FileIntegrityRecord).filter(FileIntegrityRecord.product_id == product_id).first()
    seal_valid = False
    seal_message = "No record found"
    if integrity_rec:
        seal_valid, seal_message = verify_record_seal(integrity_rec)

    scans = db.query(MalwareScan).filter(MalwareScan.product_id == product_id).all()
    audits = db.query(AuditLog).filter(AuditLog.resource_id == product_id).order_by(desc(AuditLog.created_at)).limit(10).all()

    return {
        "product_id": str(product.id),
        "title": product.title,
        "original_filename": product.original_filename,
        "storage_key": product.storage_key,
        "sha256_hash": product.sha256_hash,
        "integrity_id": product.integrity_id,
        "integrity_record": {
            "integrity_id": integrity_rec.integrity_id,
            "is_verified": integrity_rec.is_verified,
            "tampered_detected": integrity_rec.tampered_detected,
            "verified_at": integrity_rec.verified_at.isoformat() if integrity_rec.verified_at else None,
        } if integrity_rec else None,
        "seal_valid": seal_valid,
        "seal_message": seal_message,
        "duplicate_status": getattr(product, "duplicate_status", "CLEAR") or "CLEAR",
        "scan_status": product.scan_status,
        "pricing": {
            "suggested_price": product.suggested_price,
            "maximum_allowed_price": product.maximum_allowed_price,
            "value_score": product.value_score,
            "price_status": getattr(product, "price_status", "APPROVED") or "APPROVED"
        },
        "scans": [
            {"engine": s.scan_engine, "result": s.result, "threat": s.threat_name, "scanned_at": s.created_at.isoformat() if s.created_at else None}
            for s in scans
        ],
        "recent_audits": [
            {"event": a.event, "actor": a.actor_email, "desc": a.description, "created_at": a.created_at.isoformat() if a.created_at else None}
            for a in audits
        ]
    }

@router.get("/pricing-rules")
async def get_pricing_rules(
    current_user: User = Depends(require_admin)
):
    from app.pricing_config import (
        GLOBAL_MIN_PRICE_INR,
        GLOBAL_PLATFORM_MAX_PRICE_INR,
        CATEGORY_CEILINGS_INR,
        CONTENT_TYPE_PROFILES,
        PRODUCT_VALUE_SCORE_WEIGHTS,
        PRICING_RULE_VERSION,
    )
    from app.services.fee_service import (
        PLATFORM_FEE_ENABLED,
        DEFAULT_PLATFORM_FEE_PERCENT,
        TAX_ENABLED,
        DEFAULT_TAX_RATE_PERCENT,
        DEFAULT_TAX_LABEL,
        PAYMENT_PROCESSING_FEE_ENABLED,
        DEFAULT_SELLER_FEE_PERCENT,
        FEE_RULE_VERSION,
        TAX_RULE_VERSION
    )
    return {
        "global_platform_max_price": GLOBAL_PLATFORM_MAX_PRICE_INR,
        "global_min_price": GLOBAL_MIN_PRICE_INR,
        "category_ceilings": CATEGORY_CEILINGS_INR,
        "content_type_profiles": CONTENT_TYPE_PROFILES,
        "value_score_weights": PRODUCT_VALUE_SCORE_WEIGHTS,
        "pricing_rule_version": PRICING_RULE_VERSION,
        "fee_settings": {
            "platform_fee_enabled": PLATFORM_FEE_ENABLED,
            "platform_fee_percent": DEFAULT_PLATFORM_FEE_PERCENT,
            "tax_enabled": TAX_ENABLED,
            "tax_rate_percent": DEFAULT_TAX_RATE_PERCENT,
            "tax_label": DEFAULT_TAX_LABEL,
            "payment_processing_fee_enabled": PAYMENT_PROCESSING_FEE_ENABLED,
            "seller_fee_percent": DEFAULT_SELLER_FEE_PERCENT,
            "fee_rule_version": FEE_RULE_VERSION,
            "tax_rule_version": TAX_RULE_VERSION
        }
    }
