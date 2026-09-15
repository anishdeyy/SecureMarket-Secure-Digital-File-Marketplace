import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.order import Order, OrderStatus
from app.models.payment import Payment
from app.models.download import Download
from app.models.fraud import FraudAlert

logger = logging.getLogger(__name__)

def calculate_risk_score(db, user_id, order_id=None, ip_address=None, user_agent=None):
    score = 0
    reasons = []
    cutoff_24h = datetime.utcnow() - timedelta(hours=24)
    cutoff_1h = datetime.utcnow() - timedelta(hours=1)

    failed_payments = db.query(Payment).join(Order).filter(
        Order.buyer_id == str(user_id),
        Payment.status == "failed",
        Payment.created_at >= cutoff_24h
    ).count()
    if failed_payments >= 5:
        score += 30; reasons.append(f"{failed_payments} failed payment attempts in 24h")
    elif failed_payments >= 3:
        score += 20; reasons.append(f"{failed_payments} failed payment attempts in 24h")
    elif failed_payments >= 1:
        score += 10; reasons.append(f"{failed_payments} failed payment attempt(s) in 24h")

    recent_orders = db.query(Order).filter(
        Order.buyer_id == str(user_id),
        Order.created_at >= cutoff_1h,
        Order.status.in_(["paid", "payment_processing"])
    ).count()
    if recent_orders >= 5:
        score += 20; reasons.append(f"High purchase velocity: {recent_orders} orders in 1h")
    elif recent_orders >= 3:
        score += 10; reasons.append(f"Elevated purchase velocity: {recent_orders} orders in 1h")

    recent_downloads = db.query(Download).filter(
        Download.user_id == str(user_id),
        Download.created_at >= cutoff_1h
    ).count()
    if recent_downloads >= 20:
        score += 15; reasons.append(f"Excessive downloads: {recent_downloads} in 1h")

    prev_critical = db.query(FraudAlert).filter(
        FraudAlert.user_id == str(user_id),
        FraudAlert.risk_level == "critical",
        FraudAlert.status != "dismissed"
    ).count()
    if prev_critical > 0:
        score += 30; reasons.append(f"Previous critical fraud alerts: {prev_critical}")

    risk_level = "low"
    if score >= 80: risk_level = "critical"
    elif score >= 60: risk_level = "high"
    elif score >= 30: risk_level = "medium"

    actions = {"low": "allow", "medium": "allow_monitor", "high": "require_review", "critical": "block"}
    return {"risk_score": min(score, 100), "risk_level": risk_level, "reasons": reasons, "action": actions[risk_level]}

def create_fraud_alert(db, user_id, order_id, risk_score, risk_level, reasons, ip_address=None, user_agent=None):
    alert = FraudAlert(
        user_id=str(user_id), order_id=str(order_id) if order_id else None,
        risk_score=risk_score, risk_level=risk_level,
        reasons=json.dumps(reasons), ip_address=ip_address, user_agent=user_agent
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
