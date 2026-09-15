"""
fee_service.py — Authoritative marketplace fee, tax, and seller payout calculation engine.
All financial totals are computed using integer paise arithmetic to prevent floating-point errors.
Zero-value fees are omitted, and seller payouts strictly exclude buyer tax.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.payout import Payout, PayoutStatus
from app.models.order import Order
from app.models.product import Product

# ── Configurable Platform Pricing Defaults ────────────────────────────────────
PLATFORM_FEE_ENABLED = True
DEFAULT_PLATFORM_FEE_PERCENT = 5.0      # 5% platform fee
TAX_ENABLED = True
DEFAULT_TAX_RATE_PERCENT = 18.0         # 18% Applicable Tax / GST
DEFAULT_TAX_LABEL = "Applicable Tax"
PAYMENT_PROCESSING_FEE_ENABLED = False  # Disabled by default
DEFAULT_PROCESSING_FEE_PERCENT = 0.0
DEFAULT_SELLER_FEE_PERCENT = 5.0        # 5% marketplace commission on gross sale

FEE_RULE_VERSION = "FEE_V2"
TAX_RULE_VERSION = "TAX_V1"
PRICING_RULE_VERSION = "PRICING_V3"

def calculate_order_financials(
    price_inr: float,
    quantity: int = 1,
    platform_fee_percent: float = DEFAULT_PLATFORM_FEE_PERCENT,
    tax_rate_percent: float = DEFAULT_TAX_RATE_PERCENT,
    service_fee_percent: float = DEFAULT_PROCESSING_FEE_PERCENT,
    platform_fee_enabled: bool = PLATFORM_FEE_ENABLED,
    tax_enabled: bool = TAX_ENABLED,
    processing_fee_enabled: bool = PAYMENT_PROCESSING_FEE_ENABLED,
    seller_fee_percent: float = DEFAULT_SELLER_FEE_PERCENT,
    discount_inr: float = 0.0,
) -> Dict[str, Any]:
    """
    Authoritative server-side calculation of order financials using integer paise.
    
    Buyer Accounting:
      subtotal = product_price * quantity
      discount = discount_inr
      discounted_subtotal = max(0, subtotal - discount)
      platform_fee = discounted_subtotal * platform_fee_percent (if enabled)
      processing_fee = discounted_subtotal * service_fee_percent (if enabled)
      taxable_base = discounted_subtotal + platform_fee + processing_fee
      tax = taxable_base * tax_rate_percent (if enabled)
      buyer_total = taxable_base + tax

    Seller Accounting:
      seller_gross = subtotal
      seller_fee = seller_gross * seller_fee_percent
      seller_payout = seller_gross - seller_fee (95% net royalty)
      (Buyer tax is strictly excluded from seller revenue)
    """
    qty = max(1, int(quantity))
    price = max(0.0, float(price_inr))
    subtotal_paise = int(round(price * qty * 100))
    discount_paise = int(round(max(0.0, float(discount_inr)) * 100))
    discounted_subtotal_paise = max(0, subtotal_paise - discount_paise)

    # 1. Platform Fee
    if platform_fee_enabled and platform_fee_percent > 0:
        platform_fee_paise = int(round(discounted_subtotal_paise * (platform_fee_percent / 100.0)))
    else:
        platform_fee_paise = 0

    # 2. Payment Processing Fee
    if processing_fee_enabled and service_fee_percent > 0:
        processing_fee_paise = int(round(discounted_subtotal_paise * (service_fee_percent / 100.0)))
    else:
        processing_fee_paise = 0

    # 3. Taxable Base & Tax
    taxable_paise = discounted_subtotal_paise + platform_fee_paise + processing_fee_paise
    if tax_enabled and tax_rate_percent > 0:
        tax_paise = int(round(taxable_paise * (tax_rate_percent / 100.0)))
    else:
        tax_paise = 0

    # 4. Final Buyer Total
    buyer_total_paise = taxable_paise + tax_paise

    # 5. Seller Accounting (strictly separate from buyer tax/fees)
    seller_gross_paise = subtotal_paise
    seller_fee_paise = int(round(seller_gross_paise * (seller_fee_percent / 100.0)))
    seller_payout_paise = max(0, seller_gross_paise - seller_fee_paise)

    # 6. Build clean active fee rows (only display if charged and non-zero)
    fee_lines = [
        {
            "key": "subtotal",
            "label": "Product price",
            "amount": round(subtotal_paise / 100.0, 2),
            "amount_paise": subtotal_paise,
        }
    ]
    if platform_fee_paise > 0:
        fee_lines.append({
            "key": "platform_fee",
            "label": f"Platform fee ({int(platform_fee_percent) if platform_fee_percent.is_integer() else platform_fee_percent}%)",
            "amount": round(platform_fee_paise / 100.0, 2),
            "amount_paise": platform_fee_paise,
        })
    if processing_fee_paise > 0:
        fee_lines.append({
            "key": "processing_fee",
            "label": "Payment processing fee",
            "amount": round(processing_fee_paise / 100.0, 2),
            "amount_paise": processing_fee_paise,
        })
    if tax_paise > 0:
        fee_lines.append({
            "key": "tax",
            "label": f"{DEFAULT_TAX_LABEL} ({int(tax_rate_percent) if tax_rate_percent.is_integer() else tax_rate_percent}%)",
            "amount": round(tax_paise / 100.0, 2),
            "amount_paise": tax_paise,
        })

    return {
        # Integer values in paise (authoritative)
        "subtotal_paise": subtotal_paise,
        "discount_paise": discount_paise,
        "platform_fee_paise": platform_fee_paise,
        "service_fee_paise": processing_fee_paise,
        "tax_paise": tax_paise,
        "buyer_total_paise": buyer_total_paise,
        "seller_gross_paise": seller_gross_paise,
        "seller_fee_paise": seller_fee_paise,
        "seller_payout_paise": seller_payout_paise,

        # Floating point representation in INR for display & database records
        "subtotal": round(subtotal_paise / 100.0, 2),
        "discount": round(discount_paise / 100.0, 2),
        "platform_fee": round(platform_fee_paise / 100.0, 2),
        "service_fee": round(processing_fee_paise / 100.0, 2),
        "tax": round(tax_paise / 100.0, 2),
        "total": round(buyer_total_paise / 100.0, 2),
        "total_amount": round(buyer_total_paise / 100.0, 2),
        "seller_gross": round(seller_gross_paise / 100.0, 2),
        "seller_fee": round(seller_fee_paise / 100.0, 2),
        "seller_payout": round(seller_payout_paise / 100.0, 2),

        # Clean active line items for checkout modal
        "fee_lines": fee_lines,

        # Config versions
        "tax_rate": tax_rate_percent / 100.0,
        "platform_fee_percent": platform_fee_percent / 100.0,
        "service_fee_percent": service_fee_percent / 100.0,
        "royalty_rate": (100.0 - seller_fee_percent) / 100.0,
        "pricing_rule_version": PRICING_RULE_VERSION,
        "fee_rule_version": FEE_RULE_VERSION,
        "tax_rule_version": TAX_RULE_VERSION,
        "currency": "INR",
        "tax_label": DEFAULT_TAX_LABEL,
    }

def record_seller_payout(
    db: Session,
    order: Order,
    product: Product,
    financials: Dict[str, Any],
    status: str = PayoutStatus.PENDING_PAYOUT
) -> Optional[Payout]:
    """Creates an entry in the seller payout ledger for this order."""
    seller_id = str(product.seller_id) if product and product.seller_id else None
    if not seller_id:
        return None

    existing = db.query(Payout).filter(
        Payout.order_id == str(order.id),
        Payout.seller_id == seller_id
    ).first()
    if existing:
        return existing

    payout = Payout(
        order_id=str(order.id),
        seller_id=seller_id,
        product_id=str(product.id) if product else None,
        gross_amount=financials["seller_gross"],
        platform_fee=financials["seller_fee"],
        other_fee=financials["service_fee"],
        seller_payout=financials["seller_payout"],
        royalty_rate=financials["royalty_rate"],
        currency=financials.get("currency", "INR"),
        status=status,
        notes=f"Payout recorded under {financials.get('fee_rule_version', FEE_RULE_VERSION)}"
    )
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return payout

def complete_seller_payout(db: Session, order_id: str):
    """Mark payout status as ready when order is verified and paid."""
    payouts = db.query(Payout).filter(Payout.order_id == str(order_id)).all()
    for p in payouts:
        if p.status == PayoutStatus.PENDING_PAYOUT:
            p.status = PayoutStatus.READY
    db.commit()
