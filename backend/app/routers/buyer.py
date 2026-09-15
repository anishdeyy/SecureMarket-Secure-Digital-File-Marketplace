"""
buyer.py — Dedicated Buyer Router for SecureMarket
Strictly guarded by require_buyer.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func

from app.database import get_db
from app.models.user import User
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.middleware.auth import require_buyer

router = APIRouter(prefix="/api/buyer", tags=["buyer"])

@router.get("/dashboard")
async def get_buyer_dashboard(
    current_user: User = Depends(require_buyer),
    db: Session = Depends(get_db)
):
    """
    Dedicated buyer dashboard summary: total purchases, total spent, available downloads.
    """
    buyer_id = str(current_user.id)

    # Paid orders count & total spend
    paid_orders = db.query(Order).filter(
        Order.buyer_id == buyer_id,
        Order.status == OrderStatus.PAID
    ).all()

    total_purchases_count = len(paid_orders)
    total_spent = sum(o.total_amount for o in paid_orders)

    # Total downloadable items
    downloads_count = db.query(OrderItem).join(Order).filter(
        Order.buyer_id == buyer_id,
        Order.status == OrderStatus.PAID,
        OrderItem.download_enabled == True
    ).count()

    # Recent orders
    recent = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).filter(
        Order.buyer_id == buyer_id
    ).order_by(desc(Order.created_at)).limit(5).all()

    return {
        "buyer": {
            "id": buyer_id,
            "username": current_user.username,
            "email": current_user.email,
            "role": "BUYER"
        },
        "metrics": {
            "total_purchases_count": total_purchases_count,
            "total_spent": round(float(total_spent), 2),
            "available_downloads_count": downloads_count,
            "currency": "INR"
        },
        "recent_orders": [
            {
                "id": str(o.id),
                "order_number": o.order_number,
                "status": o.status,
                "total_amount": o.total_amount,
                "subtotal": getattr(o, "subtotal", o.total_amount),
                "platform_fee": getattr(o, "platform_fee", 0.0),
                "tax": getattr(o, "tax", 0.0),
                "items_count": len(o.items),
                "created_at": o.created_at.isoformat() if o.created_at else None
            }
            for o in recent
        ]
    }
