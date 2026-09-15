import hashlib
import hmac
import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.config import settings
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.order import OrderItem

logger = logging.getLogger(__name__)


def create_payment_order(db: Session, order: Order) -> Dict[str, Any]:
    """Create a payment order with the configured gateway."""
    if settings.PAYMENT_MODE == "razorpay":
        return _create_razorpay_order(order)
    else:
        return _create_mock_order(order)


def _create_razorpay_order(order: Order) -> Dict[str, Any]:
    """Create a real Razorpay order."""
    try:
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        amount_paise = int(order.total_amount * 100)  # Convert to paise
        payload = {
            "amount": amount_paise,
            "currency": order.currency or "INR",
            "receipt": str(order.order_number),
            "payment_capture": 1,
            "notes": {"order_id": str(order.id)}
        }

        razorpay_order = client.order.create(payload)
        return {
            "gateway_order_id": razorpay_order["id"],
            "amount": order.total_amount,
            "currency": order.currency,
            "gateway": "razorpay",
            "key_id": settings.RAZORPAY_KEY_ID,
            "is_mock": False
        }
    except Exception as e:
        logger.error(f"Razorpay order creation failed: {e}")
        raise


def _create_mock_order(order: Order) -> Dict[str, Any]:
    """Create a mock payment order for development."""
    mock_order_id = f"mock_order_{uuid.uuid4().hex[:16]}"
    return {
        "gateway_order_id": mock_order_id,
        "amount": order.total_amount,
        "currency": order.currency or "INR",
        "gateway": "mock",
        "is_mock": True,
        "mock_key": "mock_key_id_for_demo"
    }


def verify_payment(
    db: Session,
    order: Order,
    payment_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify payment server-side. Never trust frontend payment success claims.
    """
    if settings.PAYMENT_MODE == "razorpay":
        return _verify_razorpay_payment(db, order, payment_data)
    else:
        return _verify_mock_payment(db, order, payment_data)


def _verify_razorpay_payment(db: Session, order: Order, payment_data: dict) -> dict:
    """Verify Razorpay payment signature and amount."""
    gateway_order_id = payment_data.get("razorpay_order_id")
    gateway_payment_id = payment_data.get("razorpay_payment_id")
    signature = payment_data.get("razorpay_signature")

    if not all([gateway_order_id, gateway_payment_id, signature]):
        return {"success": False, "reason": "Missing payment parameters"}

    # Verify signature
    expected_sig = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        f"{gateway_order_id}|{gateway_payment_id}".encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, signature):
        logger.warning("Razorpay signature verification failed")
        return {"success": False, "reason": "Invalid payment signature"}

    # Verify amount via Razorpay API
    try:
        import razorpay
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        payment_details = client.payment.fetch(gateway_payment_id)

        expected_amount_paise = int(order.total_amount * 100)
        if payment_details["amount"] != expected_amount_paise:
            logger.warning("Amount mismatch in Razorpay payment")
            return {"success": False, "reason": "Payment amount mismatch"}

        if payment_details.get("status") == "authorized":
            try:
                client.payment.capture(gateway_payment_id, expected_amount_paise)
                payment_details = client.payment.fetch(gateway_payment_id)
            except Exception as cap_err:
                logger.warning(f"Could not auto-capture authorized payment: {cap_err}")

        if payment_details["status"] != "captured":
            return {"success": False, "reason": f"Payment not captured: {payment_details['status']}"}

    except Exception as e:
        logger.error(f"Razorpay verification error: {e}")
        return {"success": False, "reason": "Could not verify payment with gateway"}

    return {
        "success": True,
        "gateway_payment_id": gateway_payment_id,
        "gateway_order_id": gateway_order_id,
        "gateway": "razorpay"
    }


def _verify_mock_payment(db: Session, order: Order, payment_data: dict) -> dict:
    """Verify mock payment for development. Simulates real verification logic."""
    mock_scenario = payment_data.get("mock_scenario", "success")

    if mock_scenario == "fail":
        return {"success": False, "reason": "Payment declined (mock simulation)"}

    if mock_scenario == "wrong_amount":
        return {"success": False, "reason": "Amount mismatch detected"}

    # Simulate successful mock payment
    mock_payment_id = f"mock_pay_{uuid.uuid4().hex[:16]}"
    logger.info(f"[MOCK] Payment verified for order {order.order_number}")

    return {
        "success": True,
        "gateway_payment_id": mock_payment_id,
        "gateway_order_id": payment_data.get("gateway_order_id"),
        "gateway": "mock",
        "is_mock": True
    }


def process_successful_payment(db: Session, order: Order, payment_result: dict) -> Payment:
    """Mark order as paid and enable downloads. Uses database transaction."""
    try:
        # Update payment record
        payment = db.query(Payment).filter(Payment.order_id == order.id).first()
        if not payment:
            payment = Payment(order_id=order.id, amount=order.total_amount, currency=order.currency)
            db.add(payment)

        payment.status = PaymentStatus.SUCCESS
        payment.gateway_payment_id = payment_result.get("gateway_payment_id")
        payment.gateway_order_id = payment_result.get("gateway_order_id")
        payment.gateway = payment_result.get("gateway", "mock")
        payment.is_mock = payment_result.get("is_mock", False)
        payment.completed_at = datetime.utcnow()

        # Update order status
        order.status = OrderStatus.PAID
        order.paid_at = datetime.utcnow()

        # Enable downloads for all order items
        for item in order.items:
            item.download_enabled = True

        # Update seller payouts in ledger
        from app.services.fee_service import complete_seller_payout
        complete_seller_payout(db, str(order.id))

        db.commit()
        db.refresh(payment)
        logger.info(f"Payment processed successfully for order {order.order_number}")
        return payment

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to process payment: {e}")
        raise


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify Razorpay webhook signature."""
    if settings.PAYMENT_MODE == "mock":
        return True  # Mock mode always verifies

    if not settings.RAZORPAY_WEBHOOK_SECRET:
        return False

    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)
