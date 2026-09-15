from fastapi import FastAPI, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging, os

from app.config import settings
from app.database import engine, Base, get_db
from app.routers import auth, products, uploads, orders, payments, downloads, reviews, wishlist, admin, buyer, seller
from app.routers.integrity import router as integrity_router

# Import ALL models so SQLAlchemy creates every table
import app.models.user, app.models.product, app.models.order
import app.models.payment, app.models.download, app.models.review
import app.models.wishlist, app.models.notification, app.models.fraud
import app.models.malware, app.models.audit, app.models.session
import app.models.integrity, app.models.payout, app.models.refund

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SecureMarket API",
    description="Secure Digital File Marketplace — SHA-256 + HMAC-sealed integrity, Gemini AI, Razorpay",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup():
    logger.info("SecureMarket API — ENV=%s  STORAGE=%s  AI=%s  PAYMENT=%s",
                settings.APP_ENV, settings.STORAGE_MODE, settings.AI_MODE, settings.PAYMENT_MODE)
    Base.metadata.create_all(bind=engine)
    if settings.STORAGE_MODE == "local":
        os.makedirs(settings.LOCAL_STORAGE_PATH, exist_ok=True)
    logger.info("Database tables ready (including file_integrity_records)")

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(uploads.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(downloads.router)
app.include_router(reviews.router)
app.include_router(wishlist.router)
app.include_router(admin.router)
app.include_router(integrity_router)
app.include_router(buyer.router)
app.include_router(seller.router)

# ── Inline: Notifications ────────────────────────────────────────────────────
from app.models.notification import Notification
from app.models.user import User
from app.middleware.auth import get_current_user

notif_router = APIRouter(prefix="/api/notifications", tags=["notifications"])

@notif_router.get("")
async def get_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifs = db.query(Notification).filter(Notification.user_id == user.id)\
               .order_by(desc(Notification.created_at)).limit(50).all()
    unread = sum(1 for n in notifs if not n.is_read)
    return {
        "notifications": [
            {"id": str(n.id), "title": n.title, "message": n.message,
             "type": n.type, "is_read": n.is_read, "action_url": n.action_url,
             "created_at": n.created_at.isoformat()}
            for n in notifs
        ],
        "unread_count": unread
    }

@notif_router.post("/{notif_id}/read")
async def mark_read(notif_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == user.id).first()
    if n: n.is_read = True; db.commit()
    return {"success": True}

@notif_router.post("/read-all")
async def mark_all_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read == False)\
      .update({"is_read": True}); db.commit()
    return {"success": True}

app.include_router(notif_router)

# ── File serve (local dev only) ───────────────────────────────────────────────
files_router = APIRouter(prefix="/api/files", tags=["files"])

@files_router.get("/preview/{key_encoded}")
async def serve_preview(key_encoded: str):
    from fastapi.responses import FileResponse
    from pathlib import Path
    from app.services.storage_service import storage_service as ss
    key = key_encoded.replace("__", "/")
    fp = Path(ss.local_path) / key
    if not fp.exists():
        from fastapi import HTTPException
        raise HTTPException(404, "Preview not found")
    return FileResponse(str(fp))

app.include_router(files_router)

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "SecureMarket", "version": "1.0.0",
            "modes": {"storage": settings.STORAGE_MODE, "payment": settings.PAYMENT_MODE,
                      "ai": settings.AI_MODE, "malware": settings.MALWARE_SCAN_MODE},
            "integrity": "SHA-256 + HMAC-SHA256 sealed records"}

@app.get("/")
async def root():
    return {"message": "SecureMarket API", "docs": "/docs", "health": "/api/health",
            "integrity_api": "/api/integrity/{integrity_id}"}
