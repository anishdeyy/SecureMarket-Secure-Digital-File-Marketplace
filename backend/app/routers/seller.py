"""
seller.py — Dedicated Seller Router for SecureMarket
Strictly guarded by require_seller. No buyer or admin cross-over.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderItem, OrderStatus
from app.models.payout import Payout, PayoutStatus
from app.middleware.auth import require_seller

router = APIRouter(prefix="/api/seller", tags=["seller"])

@router.get("/stats")
async def get_seller_stats(
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db)
):
    """Legacy and dashboard stats endpoint for sellers."""
    seller_id = str(current_user.id)
    total_products = db.query(Product).filter(Product.seller_id == seller_id).count()
    published = db.query(Product).filter(Product.seller_id == seller_id, Product.status == "published").count()
    
    payout_stats = db.query(
        func.sum(Payout.gross_amount),
        func.sum(Payout.platform_fee),
        func.sum(Payout.seller_payout)
    ).filter(
        Payout.seller_id == seller_id,
        Payout.status.in_([PayoutStatus.READY, PayoutStatus.COMPLETED])
    ).first()

    gross_revenue = round(float(payout_stats[0] or 0.0), 2)
    net_earnings = round(float(payout_stats[2] or 0.0), 2)

    total_orders = db.query(func.count(OrderItem.id)).filter(OrderItem.seller_id == seller_id).scalar() or 0
    recent_items = db.query(OrderItem).filter(OrderItem.seller_id == seller_id).order_by(desc(OrderItem.created_at)).limit(5).all()

    return {
        "total_products": total_products,
        "published_products": published,
        "total_revenue": gross_revenue,
        "net_revenue": net_earnings,
        "total_orders": int(total_orders),
        "recent_orders": [
            {
                "id": str(it.id),
                "order_id": str(it.order_id),
                "product_id": str(it.product_id),
                "total_amount": it.price_at_purchase,
                "created_at": it.created_at.isoformat() if it.created_at else None
            }
            for it in recent_items
        ]
    }

@router.get("/dashboard")
async def get_seller_dashboard(
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db)
):
    """
    Dedicated dashboard summary for seller accounts.
    Returns authoritative sales, earnings (gross, platform fee, net payout), and product counts.
    """
    seller_id = str(current_user.id)

    # Products count
    total_products = db.query(Product).filter(Product.seller_id == seller_id).count()
    active_products = db.query(Product).filter(
        Product.seller_id == seller_id,
        Product.status == "published",
        Product.is_active == True
    ).count()

    # Total sales & download count
    sales_stats = db.query(
        func.sum(Product.total_sales),
        func.sum(Product.total_downloads)
    ).filter(Product.seller_id == seller_id).first()

    total_sales_count = int(sales_stats[0] or 0)
    total_downloads_count = int(sales_stats[1] or 0)

    # Revenue calculations from Payouts ledger
    payout_stats = db.query(
        func.sum(Payout.gross_amount),
        func.sum(Payout.platform_fee),
        func.sum(Payout.seller_payout)
    ).filter(
        Payout.seller_id == seller_id,
        Payout.status.in_([PayoutStatus.READY, PayoutStatus.COMPLETED])
    ).first()

    gross_revenue = round(float(payout_stats[0] or 0.0), 2)
    platform_fees_deducted = round(float(payout_stats[1] or 0.0), 2)
    net_earnings = round(float(payout_stats[2] or 0.0), 2)

    # Pending payouts
    pending_payouts = db.query(func.sum(Payout.seller_payout)).filter(
        Payout.seller_id == seller_id,
        Payout.status == PayoutStatus.PENDING_PAYOUT
    ).scalar() or 0.0

    # Recent 5 payouts
    recent_payouts = db.query(Payout).filter(
        Payout.seller_id == seller_id
    ).order_by(desc(Payout.created_at)).limit(5).all()

    return {
        "seller": {
            "id": seller_id,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "role": "SELLER"
        },
        "metrics": {
            "gross_revenue": gross_revenue,
            "platform_fees_deducted": platform_fees_deducted,
            "net_earnings": net_earnings,
            "pending_payouts": round(float(pending_payouts), 2),
            "platform_fee_rate": "5.0%",
            "royalty_rate": "95.0%",
            "total_sales_count": total_sales_count,
            "total_downloads_count": total_downloads_count,
            "total_products": total_products,
            "active_products": active_products
        },
        "recent_payouts": [
            {
                "id": str(p.id),
                "order_id": str(p.order_id),
                "gross_amount": p.gross_amount,
                "platform_fee": p.platform_fee,
                "seller_payout": p.seller_payout,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in recent_payouts
        ]
    }

@router.get("/revenue")
async def get_seller_revenue(
    page: int = Query(1, ge=1),
    per_page: int = Query(20),
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db)
):
    """
    Detailed seller revenue ledger with fee deduction transparent itemization.
    """
    seller_id = str(current_user.id)
    query = db.query(Payout).filter(Payout.seller_id == seller_id)
    total = query.count()
    payouts = query.order_by(desc(Payout.created_at)).offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for p in payouts:
        product = db.query(Product).filter(Product.id == p.product_id).first() if p.product_id else None
        items.append({
            "id": str(p.id),
            "order_id": str(p.order_id),
            "product_id": str(p.product_id) if p.product_id else None,
            "product_title": product.title if product else "Digital Product",
            "gross_amount": p.gross_amount,
            "platform_fee": p.platform_fee,
            "other_fee": p.other_fee,
            "net_seller_payout": p.seller_payout,
            "royalty_rate": p.royalty_rate,
            "status": p.status,
            "currency": p.currency,
            "created_at": p.created_at.isoformat() if p.created_at else None
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page
    }

@router.get("/sales")
async def get_seller_sales(
    page: int = Query(1, ge=1),
    per_page: int = Query(20),
    current_user: User = Depends(require_seller),
    db: Session = Depends(get_db)
):
    """
    List individual item sales made by this seller.
    """
    seller_id = str(current_user.id)
    query = db.query(OrderItem).filter(OrderItem.seller_id == seller_id)
    total = query.count()
    items = query.order_by(desc(OrderItem.created_at)).offset((page - 1) * per_page).limit(per_page).all()

    results = []
    for it in items:
        product = db.query(Product).filter(Product.id == it.product_id).first()
        order = db.query(Order).filter(Order.id == it.order_id).first()
        results.append({
            "id": str(it.id),
            "order_number": order.order_number if order else "N/A",
            "product_id": str(it.product_id),
            "product_title": product.title if product else "Product",
            "price": it.price_at_purchase,
            "download_count": it.download_count,
            "order_status": order.status if order else "unknown",
            "created_at": it.created_at.isoformat() if it.created_at else None
        })

    return {
        "items": results,
        "total": total,
        "page": page,
        "per_page": per_page
    }
