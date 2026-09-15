import os, uuid, time, logging, secrets
from pathlib import Path
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)
_local_download_tokens = {}

class StorageService:
    def __init__(self):
        self.mode = settings.STORAGE_MODE
        if self.mode == "s3":
            import boto3
            self.s3 = boto3.client("s3", aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                   aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                   region_name=settings.AWS_REGION)
            self.bucket = settings.AWS_S3_BUCKET
        else:
            p = Path(settings.LOCAL_STORAGE_PATH)
            if not p.is_absolute():
                backend_dir = Path(__file__).resolve().parent.parent.parent
                if (backend_dir / "storage").exists():
                    p = backend_dir / "storage"
                else:
                    p = Path.cwd() / settings.LOCAL_STORAGE_PATH
            self.local_path = p.resolve()
            self.local_path.mkdir(parents=True, exist_ok=True)

    def _gen_key(self, seller_id, product_id, filename):
        rand = uuid.uuid4().hex
        ext = Path(filename).suffix.lower()
        return f"products/{seller_id}/{product_id}/original/{rand}{ext}"

    def upload_file(self, content, seller_id, product_id, original_filename):
        key = self._gen_key(str(seller_id), str(product_id), original_filename)
        if self.mode == "s3":
            kwargs = {"Bucket": self.bucket, "Key": key, "Body": content, "ServerSideEncryption": "AES256"}
            if settings.AWS_KMS_KEY_ID:
                kwargs["ServerSideEncryption"] = "aws:kms"
                kwargs["SSEKMSKeyId"] = settings.AWS_KMS_KEY_ID
            self.s3.put_object(**kwargs)
        else:
            fp = self.local_path / key
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_bytes(content)
        logger.info(f"File stored: {key[:30]}...")
        return key

    def upload_preview(self, content, seller_id, product_id, filename):
        rand = uuid.uuid4().hex
        ext = Path(filename).suffix.lower()
        key = f"previews/{seller_id}/{product_id}/{rand}{ext}"
        if self.mode == "s3":
            self.s3.put_object(Bucket=self.bucket, Key=key, Body=content)
        else:
            fp = self.local_path / key
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_bytes(content)
        return key

    def generate_download_url(self, storage_key, original_filename=None, mime_type=None, expiration=None):
        exp = expiration or settings.S3_SIGNED_URL_EXPIRATION
        safe_filename = Path(original_filename).name if original_filename else Path(storage_key).name
        if self.mode == "s3":
            params = {"Bucket": self.bucket, "Key": storage_key}
            if safe_filename:
                params["ResponseContentDisposition"] = f'attachment; filename="{safe_filename}"'
            if mime_type:
                params["ResponseContentType"] = mime_type
            return self.s3.generate_presigned_url("get_object", Params=params, ExpiresIn=exp)
        else:
            token = secrets.token_urlsafe(32)
            _local_download_tokens[token] = {
                "key": storage_key,
                "filename": safe_filename,
                "content_type": mime_type or "application/octet-stream",
                "expires_at": time.time() + exp
            }
            base_url = getattr(settings, "BACKEND_URL", "http://localhost:8001").rstrip("/")
            return f"{base_url}/api/downloads/serve/{token}"

    def get_file_content(self, storage_key):
        if self.mode == "s3":
            return self.s3.get_object(Bucket=self.bucket, Key=storage_key)["Body"].read()
        fp = self.local_path / storage_key
        if not fp.exists():
            norm = storage_key.replace("\\", "/")
            if norm.startswith("storage/"):
                alt = self.local_path / norm[8:]
                if alt.exists():
                    return alt.read_bytes()
            backend_fp = Path(__file__).resolve().parent.parent.parent / norm
            if backend_fp.exists():
                return backend_fp.read_bytes()
        return fp.read_bytes()

    def delete_file(self, storage_key):
        try:
            if self.mode == "s3": self.s3.delete_object(Bucket=self.bucket, Key=storage_key)
            else:
                fp = self.local_path / storage_key
                if fp.exists(): fp.unlink()
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}"); return False

    def get_preview_url(self, key):
        if not key: return None
        if self.mode == "s3":
            return self.s3.generate_presigned_url("get_object",
                Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=86400)
        base_url = getattr(settings, "BACKEND_URL", "http://localhost:8001").rstrip("/")
        return f"{base_url}/api/files/preview/{key.replace('/', '__')}"

def get_local_download_entry(token):
    entry = _local_download_tokens.get(token)
    if not entry: return None
    if time.time() > entry["expires_at"]:
        del _local_download_tokens[token]; return None
    return entry

def get_local_file_for_token(token):
    entry = get_local_download_entry(token)
    return entry["key"] if entry else None

storage_service = StorageService()
