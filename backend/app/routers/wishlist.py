from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.wishlist import Wishlist
from app.models.product import Product, ProductStatus
from app.models.user import User
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])

@router.post("/{product_id}")
async def add_to_wishlist(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.status == ProductStatus.PUBLISHED
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.product_id == product_id
    ).first()

    if existing:
        return {"success": True, "message": "Already in wishlist"}

    item = Wishlist(user_id=current_user.id, product_id=product_id)
    db.add(item)
    db.commit()
    return {"success": True, "message": "Added to wishlist"}

@router.delete("/{product_id}")
async def remove_from_wishlist(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.product_id == product_id
    ).first()
    if item:
        db.delete(item)
        db.commit()
    return {"success": True, "message": "Removed from wishlist"}

@router.get("")
async def get_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items = db.query(Wishlist).filter(Wishlist.user_id == current_user.id).all()
    result = []
    for item in items:
        p = db.query(Product).filter(Product.id == item.product_id).first()
        if p and p.status == ProductStatus.PUBLISHED:
            result.append({
                "id": str(item.id),
                "product_id": str(p.id),
                "title": p.title,
                "price": p.price,
                "currency": p.currency,
                "preview_image_url": p.preview_image_url,
                "avg_rating": p.avg_rating,
                "category": p.category,
                "file_extension": p.file_extension,
                "added_at": item.created_at.isoformat()
            })
    return {"items": result, "total": len(result)}
