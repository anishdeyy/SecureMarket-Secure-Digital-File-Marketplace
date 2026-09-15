import html
import re
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models.review import Review
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewOut
from app.middleware.auth import get_current_user, get_optional_current_user
from app.services.audit_service import log_event

router = APIRouter(tags=["reviews"])

def _sanitize_text(text: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    if not text:
        return ""
    no_html = re.sub(r"<[^>]*>", "", text)
    escaped = html.escape(no_html.strip())
    return escaped

def _update_product_rating(db: Session, product_id: str):
    """Authoritative recalculation of product average rating and review count from active reviews."""
    result = db.query(
        func.avg(Review.rating), func.count(Review.id)
    ).filter(
        Review.product_id == product_id,
        Review.status == "active"
    ).first()

    avg_rating = float(result[0] or 0.0)
    count = int(result[1] or 0)

    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.avg_rating = round(avg_rating, 2)
        product.review_count = count
        db.commit()

@router.get("/api/products/{product_id}/reviews")
async def get_reviews(
    product_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Get all active reviews for a product with total count, average rating,
    and user verification status (can_review and user_review).
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    query = db.query(Review).filter(
        Review.product_id == product_id,
        Review.status == "active"
    )
    total = query.count()
    reviews = query.order_by(desc(Review.created_at)).offset((page-1)*per_page).limit(per_page).all()

    items = []
    for r in reviews:
        user = db.query(User).filter(User.id == r.user_id).first()
        items.append({
            "id": str(r.id),
            "user_id": str(r.user_id),
            "product_id": str(r.product_id),
            "rating": r.rating,
            "title": r.title,
            "body": r.body,
            "comment": r.body,
            "is_verified_purchase": r.is_verified_purchase,
            "username": user.username if user else "Verified Buyer",
            "full_name": user.full_name if user else None,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat() if r.updated_at else None
        })

    avg = db.query(func.avg(Review.rating)).filter(
        Review.product_id == product_id,
        Review.status == "active"
    ).scalar() or 0.0

    # Optional user context
    current_user = get_optional_current_user(request, db) if request else None
    can_review = False
    user_review = None

    if current_user:
        # Check if current user has reviewed
        existing_rev = db.query(Review).filter(
            Review.product_id == product_id,
            Review.user_id == str(current_user.id),
            Review.status == "active"
        ).first()

        if existing_rev:
            user_review = {
                "id": str(existing_rev.id),
                "rating": existing_rev.rating,
                "title": existing_rev.title,
                "body": existing_rev.body,
                "comment": existing_rev.body,
                "is_verified_purchase": existing_rev.is_verified_purchase,
                "created_at": existing_rev.created_at.isoformat()
            }
        else:
            # Check if user purchased and is not the seller
            if str(product.seller_id) != str(current_user.id):
                paid_order = db.query(Order).join(OrderItem).filter(
                    Order.buyer_id == str(current_user.id),
                    OrderItem.product_id == product_id,
                    Order.status == OrderStatus.PAID
                ).first()
                if paid_order:
                    can_review = True

    return {
        "reviews": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "average_rating": round(float(avg), 1),
        "review_count": total,
        "can_review": can_review,
        "user_review": user_review
    }

@router.post("/api/products/{product_id}/reviews")
async def create_review(
    product_id: str,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a verified buyer review:
    1. Product must exist.
    2. Seller cannot review their own product.
    3. User must have a completed (paid) order for this product.
    4. User cannot submit duplicate review (enforced unique user_id + product_id).
    5. Validates 1-5 integer stars and sanitized text.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Sellers cannot review their own products
    if str(product.seller_id) == str(current_user.id):
        raise HTTPException(status_code=403, detail="You cannot review your own product")

    # Verify completed paid order
    order_query = db.query(Order).join(OrderItem).filter(
        Order.buyer_id == str(current_user.id),
        OrderItem.product_id == product_id,
        Order.status == OrderStatus.PAID
    )
    if review_data.order_id:
        order_query = order_query.filter(Order.id == str(review_data.order_id))

    paid_order = order_query.first()
    if not paid_order:
        raise HTTPException(
            status_code=403,
            detail="Purchase this product to leave a verified review."
        )

    # Check for existing review
    existing = db.query(Review).filter(
        Review.user_id == str(current_user.id),
        Review.product_id == product_id
    ).first()

    if existing:
        if existing.status == "active":
            raise HTTPException(
                status_code=400,
                detail="You have already reviewed this product. Please use Edit Review to update your feedback."
            )
        else:
            # Reactivate if previously hidden or soft-deleted
            existing.status = "active"
            existing.rating = review_data.rating
            existing.body = _sanitize_text(review_data.get_comment_text())
            existing.title = _sanitize_text(review_data.title or "")
            existing.updated_at = datetime.utcnow()
            db.commit()
            _update_product_rating(db, product_id)
            log_event(db, "REVIEW_UPDATED", str(current_user.id), resource_type="product", resource_id=product_id)
            return {
                "id": str(existing.id),
                "rating": existing.rating,
                "title": existing.title,
                "body": existing.body,
                "comment": existing.body,
                "is_verified_purchase": True,
                "username": current_user.username,
                "created_at": existing.created_at.isoformat(),
                "updated_at": existing.updated_at.isoformat()
            }

    raw_comment = review_data.get_comment_text()
    if len(raw_comment) < 3:
        raise HTTPException(status_code=400, detail="Review comment must be at least 3 characters long.")
    if len(raw_comment) > 2000:
        raise HTTPException(status_code=400, detail="Review comment cannot exceed 2000 characters.")

    sanitized_comment = _sanitize_text(raw_comment)
    sanitized_title = _sanitize_text(review_data.title or "")

    review = Review(
        user_id=str(current_user.id),
        product_id=product_id,
        order_id=str(paid_order.id),
        rating=review_data.rating,
        title=sanitized_title or None,
        body=sanitized_comment,
        is_verified_purchase=True,
        status="active"
    )
    db.add(review)
    db.commit()

    # Recalculate product rating
    _update_product_rating(db, product_id)

    log_event(db, "REVIEW_CREATED", str(current_user.id),
              resource_type="product", resource_id=product_id,
              description=f"Rating: {review.rating}/5")

    return {
        "id": str(review.id),
        "rating": review.rating,
        "title": review.title,
        "body": review.body,
        "comment": review.body,
        "is_verified_purchase": True,
        "username": current_user.username,
        "created_at": review.created_at.isoformat()
    }

@router.put("/api/reviews/{review_id}")
@router.put("/api/products/{product_id}/reviews/{review_id}")
async def update_review(
    review_id: str,
    update_data: ReviewUpdate,
    product_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing review. Only the original author may edit."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if str(review.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only edit your own review")

    if update_data.rating is not None:
        review.rating = update_data.rating

    new_comment = update_data.get_comment_text()
    if new_comment is not None:
        if len(new_comment) < 3:
            raise HTTPException(status_code=400, detail="Review comment must be at least 3 characters long.")
        if len(new_comment) > 2000:
            raise HTTPException(status_code=400, detail="Review comment cannot exceed 2000 characters.")
        review.body = _sanitize_text(new_comment)

    if update_data.title is not None:
        review.title = _sanitize_text(update_data.title)

    review.updated_at = datetime.utcnow()
    db.commit()

    # Recalculate product rating
    _update_product_rating(db, str(review.product_id))

    log_event(db, "REVIEW_UPDATED", str(current_user.id),
              resource_type="product", resource_id=str(review.product_id),
              description=f"Updated rating: {review.rating}/5")

    return {
        "id": str(review.id),
        "rating": review.rating,
        "title": review.title,
        "body": review.body,
        "comment": review.body,
        "is_verified_purchase": review.is_verified_purchase,
        "username": current_user.username,
        "created_at": review.created_at.isoformat(),
        "updated_at": review.updated_at.isoformat()
    }

@router.delete("/api/reviews/{review_id}")
@router.delete("/api/products/{product_id}/reviews/{review_id}")
async def delete_review(
    review_id: str,
    product_id: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete / hide a review. Only review author or administrator may delete."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    is_author = str(review.user_id) == str(current_user.id)
    is_admin = current_user.has_role("admin")

    if not is_author and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")

    prod_id = str(review.product_id)
    review.status = "deleted"
    db.commit()

    # Recalculate product rating
    _update_product_rating(db, prod_id)

    log_event(db, "REVIEW_DELETED", str(current_user.id),
              resource_type="product", resource_id=prod_id,
              description=f"Review {review_id} deleted by {'admin' if is_admin and not is_author else 'author'}")

    return {"success": True, "message": "Review removed successfully"}
