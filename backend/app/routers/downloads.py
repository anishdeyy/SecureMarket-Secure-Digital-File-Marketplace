from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.download import Download
from app.models.user import User
from app.services.download_service import authorize_download
from app.middleware.auth import get_current_user, get_client_ip

router = APIRouter(prefix="/api/downloads", tags=["downloads"])

@router.get("/product/{product_id}")
async def download_product(
    product_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Secure download endpoint. Performs all authorization checks before
    returning a temporary signed URL. Never exposes storage paths.
    """
    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    authorized, reason, download_url, filename, mime_type = authorize_download(
        db, str(current_user.id), product_id, ip, user_agent
    )

    if not authorized:
        raise HTTPException(status_code=403, detail=reason)

    return {
        "download_url": download_url,
        "filename": filename,
        "content_type": mime_type,
        "expires_in_seconds": 300,
        "message": "Download link generated. Link expires in 5 minutes."
    }

@router.get("/history")
async def download_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    downloads = db.query(Download).filter(
        Download.user_id == current_user.id
    ).order_by(desc(Download.created_at)).limit(50).all()

    return {
        "downloads": [
            {
                "id": str(d.id),
                "product_id": str(d.product_id),
                "status": d.status,
                "created_at": d.created_at.isoformat()
            }
            for d in downloads
        ]
    }

@router.get("/serve/{token}")
async def serve_local_file(token: str):
    """
    Serve a file using a temporary token (local dev only).
    In production, S3 signed URLs are used instead.
    """
    from app.services.storage_service import get_local_download_entry, storage_service
    from fastapi.responses import FileResponse
    from pathlib import Path

    entry = get_local_download_entry(token)
    if not entry:
        raise HTTPException(status_code=404, detail="Download link expired or invalid")

    file_path = Path(storage_service.local_path) / entry["key"]
    if not file_path.exists():
        norm = entry["key"].replace("\\", "/")
        if norm.startswith("storage/"):
            alt = Path(storage_service.local_path) / norm[8:]
            if alt.exists():
                file_path = alt
        backend_fp = Path(__file__).resolve().parent.parent.parent / norm
        if not file_path.exists() and backend_fp.exists():
            file_path = backend_fp
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=entry.get("filename") or file_path.name,
        media_type=entry.get("content_type") or "application/octet-stream"
    )
