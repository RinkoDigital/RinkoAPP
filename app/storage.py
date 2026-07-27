from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def save_pod_photo(package_id: str, file: UploadFile) -> str:
    ext = ALLOWED_CONTENT_TYPES.get(file.content_type)
    if ext is None:
        raise HTTPException(status_code=422, detail="Photo must be JPEG, PNG, or WebP")

    contents = file.file.read(settings.max_pod_photo_bytes + 1)
    if len(contents) > settings.max_pod_photo_bytes:
        raise HTTPException(status_code=413, detail="Photo exceeds maximum allowed size")
    if not contents:
        raise HTTPException(status_code=422, detail="Empty file")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{package_id}{ext}"
    (upload_dir / filename).write_bytes(contents)
    return f"/uploads/{filename}"
