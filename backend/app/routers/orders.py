from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from typing import List
import uuid
from datetime import datetime

from app.database import get_db
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product, ProductStatus
from app.models.user import User
from app.schemas.order import OrderCreate, OrderOut
from app.services.fraud_service import calculate_risk_score, create_fraud_alert
from app.services.audit_service import log_event, send_notification
from app.middleware.auth import get_current_user, require_buyer, get_client_ip
from app.services.fee_service import calculate_order_financials, record_seller_payout

router = APIRouter(prefix="/api/orders", tags=["orders"])

def _generate_order_number() -> str:
    import random
    return f"ORD-{random.randint(100000, 999999)}"

@router.post("")
async def create_order(
    request: Request,
    order_data: OrderCreate,
    current_user: User = Depends(require_buyer),
    db: Session = Depends(get_db)
):
    if not order_data.items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")

    items_data = []
    base_subtotal = 0.0

    for item in order_data.items:
        # Fetch product from DB - never trust client-side price
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.status == ProductStatus.PUBLISHED
        ).first()

        if not product:
            raise HTTPException(status_code=404, detail=f"Product not found or not available")

        # Check product price does not exceed maximum allowed price
        if product.maximum_allowed_price and product.price > product.maximum_allowed_price:
            raise HTTPException(
                status_code=400,
                detail=f"Checkout unavailable: '{product.title}' price exceeds marketplace limits and requires review."
            )

        # Check user hasn't already purchased this
        existing = db.query(OrderItem).join(Order).filter(
            Order.buyer_id == current_user.id,
            OrderItem.product_id == product.id,
            Order.status == OrderStatus.PAID
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"You already own '{product.title}'"
            )

        items_data.append({
            "product": product,
            "price": product.price  # Always use server-side price
        })
        base_subtotal += product.price

    # Compute server-authoritative financials
    fin = calculate_order_financials(price_inr=base_subtotal)

    # Fraud risk assessment
    ip = get_client_ip(request)
    risk = calculate_risk_score(db, str(current_user.id), ip_address=ip,
                                 user_agent=request.headers.get("user-agent"))

    if risk["action"] == "block":
        log_event(db, "FRAUD_ALERT", str(current_user.id),
                 description=f"Order blocked: risk={risk['risk_level']}")
        raise HTTPException(status_code=403, detail="Transaction blocked. Contact support.")

    # Create order with full financial breakdown
    order = Order(
        order_number=_generate_order_number(),
        buyer_id=current_user.id,
        status=OrderStatus.PENDING,
        total_amount=fin["total"],
        subtotal=fin["subtotal"],
        platform_fee=fin["platform_fee"],
        service_fee=fin["service_fee"],
        tax=fin["tax"],
        tax_rate=fin["tax_rate"],
        platform_fee_percent=fin["platform_fee_percent"],
        pricing_rule_version=fin["pricing_rule_version"],
        currency="INR",
        risk_score=risk["risk_score"],
        risk_level=risk["risk_level"],
        risk_reasons=risk["reasons"]
    )
    db.add(order)
    db.flush()  # Get order.id

    # Create order items and payouts
    for item_data in items_data:
        p = item_data["product"]
        item_fin = calculate_order_financials(price_inr=p.price)
        order_item = OrderItem(
            order_id=order.id,
            product_id=p.id,
            seller_id=str(p.seller_id) if p.seller_id else None,
            price_at_purchase=p.price,
            quantity=1,
            subtotal=p.price,
            currency="INR",
            download_limit=5  # Default download limit
        )
        db.add(order_item)
        record_seller_payout(db, order, p, item_fin)

    db.commit()
    db.refresh(order)

    # Create fraud alert for high/critical
    if risk["risk_level"] in ["high", "critical"]:
        create_fraud_alert(db, str(current_user.id), str(order.id),
                          risk["risk_score"], risk["risk_level"], risk["reasons"],
                          ip_address=ip, user_agent=request.headers.get("user-agent"))

    log_event(db, "ORDER_CREATED", str(current_user.id),
              resource_type="order", resource_id=str(order.id),
              description=f"Order created: {order.order_number}")

    return {
        "id": str(order.id),
        "order_number": order.order_number,
        "status": order.status,
        "total_amount": order.total_amount,
        "currency": order.currency,
        "risk_level": order.risk_level,
        "items": [
            {
                "product_id": str(item.product_id),
                "price_at_purchase": item.price_at_purchase,
                "product_title": item_data["product"].title
            }
            for item, item_data in zip(order.items, items_data)
        ]
    }

@router.get("")
async def list_orders(
    current_user: User = Depends(require_buyer),
    db: Session = Depends(get_db)
):
    orders = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).filter(
        Order.buyer_id == current_user.id
    ).order_by(desc(Order.created_at)).all()

    return {"orders": [_order_to_dict(o) for o in orders]}

@router.get("/{order_id}")
async def get_order(
    order_id: str,
    current_user: User = Depends(require_buyer),
    db: Session = Depends(get_db)
):
    order = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    ).filter(
        Order.id == order_id,
        Order.buyer_id == current_user.id  # Prevent IDOR
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return _order_to_dict(order)

def _order_to_dict(order: Order) -> dict:
    return {
        "id": str(order.id),
        "order_number": order.order_number,
        "status": order.status,
        "total_amount": order.total_amount,
        "subtotal": getattr(order, "subtotal", order.total_amount) or order.total_amount,
        "platform_fee": getattr(order, "platform_fee", 0.0) or 0.0,
        "service_fee": getattr(order, "service_fee", 0.0) or 0.0,
        "tax": getattr(order, "tax", 0.0) or 0.0,
        "currency": order.currency,
        "risk_level": order.risk_level,
        "items": [
            {
                "id": str(item.id),
                "product_id": str(item.product_id),
                "price_at_purchase": item.price_at_purchase,
                "download_count": item.download_count,
                "download_limit": item.download_limit,
                "download_enabled": item.download_enabled,
                "product": {
                    "id": str(item.product.id),
                    "title": item.product.title,
                    "file_extension": item.product.file_extension,
                    "preview_image_url": item.product.preview_image_url,
                    "sha256_hash": item.product.sha256_hash,
                    "original_filename": item.product.original_filename,
                    "file_size_bytes": item.product.file_size_bytes,
                    "integrity_id": item.product.integrity_id,
                } if item.product else None
            }
            for item in order.items
        ],
        "created_at": order.created_at.isoformat(),
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
    }
