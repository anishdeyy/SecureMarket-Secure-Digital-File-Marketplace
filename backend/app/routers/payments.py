from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel, field_validator
import logging
import random
import uuid
import json
from datetime import datetime

from app.database import get_db
from app.models.order import Order, OrderItem, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.product import Product, ProductStatus
from app.models.user import User
from app.services.payment_service import (
    create_payment_order, verify_payment,
    process_successful_payment, verify_webhook_signature
)
from app.services.audit_service import log_event, send_notification
from app.services.fraud_service import calculate_risk_score
from app.middleware.auth import get_current_user, get_optional_current_user, require_buyer, get_client_ip
from app.config import settings
from app.services.fee_service import calculate_order_financials, record_seller_payout, complete_seller_payout

router = APIRouter(prefix="/api/payments", tags=["payments"])
logger = logging.getLogger(__name__)

def _generate_order_number() -> str:
    return f"ORD-{random.randint(100000, 999999)}"

class CreatePaymentOrderRequest(BaseModel):
    product_id: str

    @field_validator("product_id", mode="before")
    @classmethod
    def convert_id(cls, v):
        return str(v)

@router.get("/calculate-checkout")
async def calculate_checkout(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Authoritative server-side pre-purchase calculation of order breakdown.
    Displays subtotal, platform fee, and applicable tax itemization.
    Omits zero-value fees and validates pricing limits.
    """
    clean_id = str(product_id).strip()
    product = db.query(Product).filter(
        Product.id == clean_id,
        Product.status == "published",
        Product.is_active == True
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not available for purchase")

    # Authoritative check against product ceiling
    if product.maximum_allowed_price and product.price > product.maximum_allowed_price:
        raise HTTPException(
            status_code=400,
            detail="Checkout unavailable: This product's price exceeds marketplace limits and requires review."
        )

    fin = calculate_order_financials(price_inr=product.price)
    return {
        "product_id": str(product.id),
        "product_title": product.title,
        "base_price": fin["subtotal"],
        "subtotal": fin["subtotal"],
        "platform_fee": fin["platform_fee"],
        "platform_fee_percent": fin["platform_fee_percent"] * 100.0,
        "service_fee": fin["service_fee"],
        "tax": fin["tax"],
        "tax_rate_percent": fin["tax_rate"] * 100.0,
        "tax_label": fin.get("tax_label", "Applicable Tax"),
        "total_amount": fin["total"],
        "total_paise": fin["buyer_total_paise"],
        "fee_lines": fin["fee_lines"],
        "currency": fin["currency"],
        "pricing_rule_version": fin["pricing_rule_version"],
        "fee_rule_version": fin.get("fee_rule_version", "FEE_V2"),
        "tax_rule_version": fin.get("tax_rule_version", "TAX_V1")
    }

@router.post("/create-order")
async def create_payment_order_direct(
    data: CreatePaymentOrderRequest,
    request: Request,
    current_user: User = Depends(require_buyer),
    db: Session = Depends(get_db)
):
    """
    Server-authoritative payment order creation:
    1. Authenticate user as strictly BUYER.
    2. Load product from DB by ID.
    3. Confirm product exists & is published/active.
    4. Validate price <= product.maximum_allowed_price.
    5. Calculate authoritative financials using integer paise arithmetic.
    6. Check if user already owns product (prevent double purchase).
    7. If price is 0: mark PAID immediately, enable download.
    8. If price > 0: create Razorpay order for exact buyer_total_paise.
    9. Record pending seller payout ledger entry.
    """
    product_id = str(data.product_id).strip()
    logger.info(f"[Payment] Initiating order for product_id='{product_id}', user='{current_user.email}'")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.status == "published",
        Product.is_active == True
    ).first()

    if not product:
        unpub = db.query(Product).filter(Product.id == product_id).first()
        if unpub:
            logger.warning(f"[Payment] Product '{product_id}' exists but status is '{unpub.status}', is_active={unpub.is_active}")
            raise HTTPException(status_code=400, detail="This product is currently not available for purchase")
        logger.warning(f"[Payment] Product '{product_id}' not found in database")
        raise HTTPException(status_code=404, detail="Product not found or not available")

    # Authoritative check against product ceiling
    if product.maximum_allowed_price and product.price > product.maximum_allowed_price:
        raise HTTPException(
            status_code=400,
            detail="Checkout unavailable: This product's price exceeds marketplace limits and requires review."
        )

    # Prevent purchasing one's own product
    if str(product.seller_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="You cannot purchase your own product")

    # Check if user already has an active paid order for this product
    existing_paid = db.query(OrderItem).join(Order).filter(
        Order.buyer_id == str(current_user.id),
        OrderItem.product_id == str(product.id),
        Order.status == OrderStatus.PAID
    ).first()

    if existing_paid:
        logger.info(f"[Payment] User '{current_user.email}' already owns product '{product.title}'")
        raise HTTPException(status_code=400, detail=f"You already own '{product.title}'. Check 'My Purchases' to download.")

    # Calculate fraud risk
    ip = get_client_ip(request)
    risk = calculate_risk_score(db, str(current_user.id), ip_address=ip,
                                user_agent=request.headers.get("user-agent"))

    if risk.get("action") == "block":
        log_event(db, "FRAUD_ALERT", str(current_user.id),
                  description=f"Order blocked: risk={risk.get('risk_level')}")
        raise HTTPException(status_code=403, detail="Transaction blocked by risk security filters. Contact support.")

    # Server-authoritative financials calculated from DB price
    fin = calculate_order_financials(price_inr=product.price)
    price_inr = fin["subtotal"]
    total_inr = fin["total"]
    amount_paise = fin["buyer_total_paise"]

    # Create internal Order record
    order_number = _generate_order_number()
    order = Order(
        order_number=order_number,
        buyer_id=str(current_user.id),
        status=OrderStatus.PENDING,
        total_amount=total_inr,
        subtotal=fin["subtotal"],
        platform_fee=fin["platform_fee"],
        service_fee=fin["service_fee"],
        tax=fin["tax"],
        tax_rate=fin["tax_rate"],
        platform_fee_percent=fin["platform_fee_percent"],
        pricing_rule_version=fin["pricing_rule_version"],
        currency="INR",
        risk_score=risk.get("risk_score", 0),
        risk_level=risk.get("risk_level", "low"),
        risk_reasons=json.dumps(risk.get("reasons", [])) if isinstance(risk.get("reasons"), (list, dict)) else str(risk.get("reasons", "[]"))
    )
    db.add(order)
    db.flush()

    # Create OrderItem
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        seller_id=str(product.seller_id) if product.seller_id else None,
        price_at_purchase=price_inr,
        quantity=1,
        subtotal=price_inr,
        currency="INR",
        download_limit=5,
        download_count=0,
        download_enabled=(price_inr == 0)
    )
    db.add(order_item)

    # Record initial pending payout in seller payouts ledger
    record_seller_payout(db, order, product, fin)

    db.commit()
    db.refresh(order)

    # ── If Free Asset (₹0) ──────────────────────────────────────────────────
    if price_inr == 0:
        order.status = OrderStatus.PAID
        order.paid_at = datetime.utcnow()
        product.total_sales += 1
        complete_seller_payout(db, str(order.id))
        db.commit()

        log_event(db, "PAYMENT_SUCCESS", str(current_user.id),
                  resource_type="order", resource_id=str(order.id),
                  description=f"Free order completed: {order.order_number}")

        send_notification(db, str(current_user.id),
                          "Free Download Ready! 🎉",
                          f"Your download for '{product.title}' is ready in My Purchases.",
                          "success", action_url="/purchases")

        return {
            "success": True,
            "order_id": str(order.id),
            "order_number": order.order_number,
            "is_free": True,
            "paid": True,
            "message": "Product claimed successfully!"
        }

    # ── Paid Asset: Create Razorpay Order ────────────────────────────────────
    if settings.PAYMENT_MODE == "razorpay":
        try:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            payload = {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": order.order_number,
                "payment_capture": 1,
                "notes": {
                    "order_id": str(order.id),
                    "product_id": str(product.id),
                    "product_title": product.title[:40],
                    "buyer_id": str(current_user.id),
                    "subtotal": str(fin["subtotal"]),
                    "platform_fee": str(fin["platform_fee"]),
                    "tax": str(fin["tax"])
                }
            }
            logger.info(f"[Payment] Creating Razorpay order for {amount_paise} paise (₹{total_inr})")
            razorpay_order = client.order.create(payload)
            rzp_order_id = razorpay_order["id"]

            order.payment_gateway_order_id = rzp_order_id
            order.payment_gateway = "razorpay"
            order.status = OrderStatus.PAYMENT_PROCESSING
            db.commit()

            # Record pending payment
            payment = Payment(
                order_id=order.id,
                amount=total_inr,
                currency="INR",
                status=PaymentStatus.PENDING,
                gateway="razorpay",
                gateway_order_id=rzp_order_id,
                is_mock=False
            )
            db.add(payment)
            db.commit()

            log_event(db, "PAYMENT_CREATED", str(current_user.id),
                      resource_type="order", resource_id=str(order.id),
                      description=f"Razorpay order created: {rzp_order_id}")

            return {
                "success": True,
                "is_free": False,
                "paid": False,
                "gateway": "razorpay",
                "order_id": str(order.id),
                "order_number": order.order_number,
                "razorpay_order_id": rzp_order_id,
                "amount_paise": amount_paise,
                "amount_inr": total_inr,
                "subtotal_inr": fin["subtotal"],
                "platform_fee": fin["platform_fee"],
                "tax": fin["tax"],
                "currency": "INR",
                "key_id": settings.RAZORPAY_KEY_ID,
                "product_title": product.title
            }
        except Exception as e:
            order.status = OrderStatus.FAILED
            db.commit()
            logger.error(f"[Payment] Failed to create Razorpay order: {e}")
            raise HTTPException(status_code=500, detail=f"Unable to initialize Razorpay payment: {str(e)}")

    else:
        # Mock mode
        mock_id = f"mock_order_{uuid.uuid4().hex[:16]}"
        order.payment_gateway_order_id = mock_id
        order.payment_gateway = "mock"
        order.status = OrderStatus.PAYMENT_PROCESSING
        db.commit()

        return {
            "success": True,
            "is_free": False,
            "paid": False,
            "is_mock": True,
            "gateway": "mock",
            "order_id": str(order.id),
            "order_number": order.order_number,
            "gateway_order_id": mock_id,
            "amount_inr": total_inr,
            "subtotal_inr": fin["subtotal"],
            "platform_fee": fin["platform_fee"],
            "tax": fin["tax"],
            "currency": "INR",
            "product_title": product.title
        }


@router.post("/create")
async def create_payment(
    order_id: str,
    current_user: User = Depends(require_buyer),
    db: Session = Depends(get_db)
):
    """Legacy order-based payment creation (maintained for backward compatibility)."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.buyer_id == str(current_user.id)
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == OrderStatus.PAID:
        raise HTTPException(status_code=400, detail="Order already paid")

    order.status = OrderStatus.PAYMENT_PROCESSING
    db.commit()

    payment = db.query(Payment).filter(Payment.order_id == order.id).first()
    if not payment:
        payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            currency=order.currency,
            status=PaymentStatus.PENDING
        )
        db.add(payment)
        db.commit()

    try:
        gateway_data = create_payment_order(db, order)
        order.payment_gateway_order_id = gateway_data["gateway_order_id"]
        order.payment_gateway = gateway_data["gateway"]
        db.commit()

        return {
            "gateway_order_id": gateway_data["gateway_order_id"],
            "amount": gateway_data["amount"],
            "currency": gateway_data["currency"],
            "gateway": gateway_data["gateway"],
            "is_mock": gateway_data.get("is_mock", False),
            "order_number": order.order_number,
            **({} if not gateway_data.get("key_id") else {"key_id": gateway_data["key_id"]})
        }
    except Exception as e:
        order.status = OrderStatus.PENDING
        db.commit()
        logger.error(f"Payment creation failed: {e}")
        raise HTTPException(status_code=500, detail="Payment initialization failed")


@router.post("/verify")
async def verify_payment_endpoint(
    data: Dict[str, Any],
    current_user: User = Depends(require_buyer),
    db: Session = Depends(get_db)
):
    """
    Verify payment server-side. NEVER trust frontend payment claims.
    Backend cryptographically verifies HMAC-SHA256 signature, amount, and order status.
    """
    order_id = data.get("order_id")
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id is required")

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.buyer_id == str(current_user.id)
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == OrderStatus.PAID:
        return {"success": True, "message": "Order already verified and paid", "order_id": str(order.id)}

    logger.info(f"[Payment] Verifying payment for order {order.order_number}")
    result = verify_payment(db, order, data.get("payment_data") or data)

    if result.get("success"):
        process_successful_payment(db, order, result)

        log_event(db, "PAYMENT_SUCCESS", str(current_user.id),
                  resource_type="order", resource_id=str(order.id),
                  description=f"Payment verified: {order.order_number}",
                  metadata={"gateway": result.get("gateway"), "is_mock": result.get("is_mock")})

        send_notification(db, str(current_user.id),
                          "Purchase Successful! 🎉",
                          f"Your order {order.order_number} has been confirmed. You can now download your files.",
                          "success", action_url=f"/purchases")

        # Update seller stats and download entitlement
        for item in order.items:
            if item.product:
                item.product.total_sales += 1
            item.download_enabled = True
        db.commit()

        return {
            "success": True,
            "order_id": str(order.id),
            "order_number": order.order_number,
            "status": "paid"
        }
    else:
        payment = db.query(Payment).filter(Payment.order_id == order.id).first()
        if payment:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = result.get("reason")
        order.status = OrderStatus.FAILED
        db.commit()

        log_event(db, "PAYMENT_FAILED", str(current_user.id),
                  resource_type="order", resource_id=str(order.id),
                  description=f"Payment failed: {result.get('reason')}")

        raise HTTPException(status_code=400, detail=result.get("reason", "Payment verification failed"))


@router.post("/webhook")
async def payment_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Handle Razorpay webhook with HMAC verification and idempotent entitlement delivery."""
    body = await request.body()

    if not verify_webhook_signature(body, x_razorpay_signature or ""):
        logger.warning("Invalid webhook signature received")
        log_event(db, "WEBHOOK_INVALID_SIGNATURE")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    import json
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    event = payload.get("event")
    logger.info(f"[Payment Webhook] Received event: {event}")
    log_event(db, "WEBHOOK_RECEIVED", metadata={"event": event})

    if event == "payment.captured":
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        notes = payment_entity.get("notes", {})
        order_id = notes.get("order_id")

        if order_id:
            order = db.query(Order).filter(Order.id == order_id).first()
            if order and order.status != OrderStatus.PAID:
                result = {
                    "success": True,
                    "gateway_payment_id": payment_entity.get("id"),
                    "gateway_order_id": payment_entity.get("order_id"),
                    "gateway": "razorpay"
                }
                process_successful_payment(db, order, result)
                log_event(db, "PAYMENT_SUCCESS_WEBHOOK", resource_id=order_id)

    return {"status": "ok"}
