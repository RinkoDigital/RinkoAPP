from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings

IMAGE_CONTENT_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
EVIDENCE_CONTENT_TYPES = {**IMAGE_CONTENT_TYPES, "application/pdf": ".pdf"}


def _save(subdir: str, file_id: str, file: UploadFile, allowed: dict[str, str]) -> str:
    ext = allowed.get(file.content_type)
    if ext is None:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(allowed))}",
        )

    contents = file.file.read(settings.max_upload_bytes + 1)
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File exceeds maximum allowed size")
    if not contents:
        raise HTTPException(status_code=422, detail="Empty file")

    upload_dir = Path(settings.upload_dir) / subdir
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{file_id}{ext}"
    (upload_dir / filename).write_bytes(contents)
    return f"/uploads/{subdir}/{filename}"


def save_pod_photo(package_id: str, file: UploadFile) -> str:
    return _save("pod", package_id, file, IMAGE_CONTENT_TYPES)


def save_evidence_file(evidence_id: str, file: UploadFile) -> str:
    return _save("evidence", evidence_id, file, EVIDENCE_CONTENT_TYPES)
