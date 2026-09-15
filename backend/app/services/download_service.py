import logging
from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.download import Download
from app.models.fraud import FraudAlert
from app.services.storage_service import storage_service
from app.services.audit_service import log_event

logger = logging.getLogger(__name__)

def authorize_download(db, user_id, product_id, ip_address=None, user_agent=None):
    product = db.query(Product).filter(Product.id == str(product_id)).first()
    if not product:
        _log_blocked(db, user_id, product_id, None, "Product not found", ip_address, user_agent)
        return False, "Product not found", None, None, None
    if product.status != "published":
        _log_blocked(db, user_id, product_id, None, "Product not available", ip_address, user_agent)
        return False, "Product not available for download", None, None, None
    if product.scan_status == "infected":
        _log_blocked(db, user_id, product_id, None, "File failed security scan", ip_address, user_agent)
        return False, "File failed security scan and cannot be downloaded", None, None, None

    order_item = db.query(OrderItem).join(Order).filter(
        Order.buyer_id == str(user_id),
        OrderItem.product_id == str(product_id),
        Order.status == "paid",
        OrderItem.download_enabled == True
    ).first()

    if not order_item:
        _log_blocked(db, user_id, product_id, None, "No authorized purchase found", ip_address, user_agent)
        return False, "You must purchase this product before downloading", None, None, None

    if order_item.download_count >= order_item.download_limit:
        _log_blocked(db, user_id, product_id, order_item.id, f"Download limit reached", ip_address, user_agent)
        return False, f"Download limit reached ({order_item.download_limit} downloads). Contact support.", None, None, None

    critical_alert = db.query(FraudAlert).filter(
        FraudAlert.user_id == str(user_id),
        FraudAlert.risk_level == "critical",
        FraudAlert.status.in_(["open", "reviewed"])
    ).first()
    if critical_alert:
        _log_blocked(db, user_id, product_id, order_item.id, "Account under fraud review", ip_address, user_agent)
        return False, "Your account is under security review. Contact support.", None, None, None

    if not product.storage_key:
        _log_blocked(db, user_id, product_id, order_item.id, "File not found in storage", ip_address, user_agent)
        return False, "File is temporarily unavailable", None, None, None

    filename = product.original_filename or f"product-{product.id}.{product.file_extension or 'file'}"
    mime_type = product.mime_type or "application/octet-stream"

    try:
        download_url = storage_service.generate_download_url(
            product.storage_key,
            original_filename=filename,
            mime_type=mime_type
        )
    except Exception as e:
        logger.error(f"Download URL generation failed: {e}")
        return False, "Download temporarily unavailable", None, None, None

    order_item.download_count += 1
    product.total_downloads += 1

    dl = Download(user_id=str(user_id), product_id=str(product_id),
                  order_item_id=str(order_item.id), status="success",
                  ip_address=ip_address, user_agent=user_agent)
    db.add(dl)
    db.commit()

    log_event(db, "DOWNLOAD_SUCCESS", str(user_id), resource_type="product",
              resource_id=str(product_id), description=f"Downloaded: {product.title}", ip_address=ip_address)
    return True, "Download authorized", download_url, filename, mime_type

def _log_blocked(db, user_id, product_id, order_item_id, reason, ip_address, user_agent):
    try:
        dl = Download(user_id=str(user_id), product_id=str(product_id),
                      order_item_id=str(order_item_id) if order_item_id else None,
                      status="blocked", block_reason=reason,
                      ip_address=ip_address, user_agent=user_agent)
        db.add(dl)
        log_event(db, "DOWNLOAD_BLOCKED", str(user_id), resource_type="product",
                  resource_id=str(product_id), description=f"Blocked: {reason}", ip_address=ip_address)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log blocked download: {e}")
        try: db.rollback()
        except: pass
