from pathlib import Path

import boto3
from botocore.client import Config as BotoConfig
from fastapi import HTTPException, UploadFile

from app.config import settings

IMAGE_CONTENT_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
EVIDENCE_CONTENT_TYPES = {**IMAGE_CONTENT_TYPES, "application/pdf": ".pdf"}

_s3_client = None


def _validate(file: UploadFile, allowed: dict[str, str]) -> tuple[str, bytes]:
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

    return ext, contents


def _save_local(subdir: str, file_id: str, ext: str, contents: bytes) -> str:
    upload_dir = Path(settings.upload_dir) / subdir
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{file_id}{ext}"
    (upload_dir / filename).write_bytes(contents)
    return f"/uploads/{subdir}/{filename}"


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            region_name=settings.s3_region,
            endpoint_url=settings.s3_endpoint_url or None,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            config=BotoConfig(signature_version="s3v4"),
        )
    return _s3_client


def _save_s3(subdir: str, file_id: str, ext: str, contents: bytes, content_type: str) -> str:
    key = f"{subdir}/{file_id}{ext}"
    _get_s3_client().put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=contents,
        ContentType=content_type,
    )
    base = settings.s3_public_base_url or (
        f"https://{settings.s3_bucket}.s3.{settings.s3_region}.amazonaws.com"
    )
    return f"{base.rstrip('/')}/{key}"


def _save(subdir: str, file_id: str, file: UploadFile, allowed: dict[str, str]) -> str:
    ext, contents = _validate(file, allowed)
    if settings.storage_backend == "s3":
        return _save_s3(subdir, file_id, ext, contents, file.content_type)
    return _save_local(subdir, file_id, ext, contents)


def save_pod_photo(package_id: str, file: UploadFile) -> str:
    return _save("pod", package_id, file, IMAGE_CONTENT_TYPES)


def save_evidence_file(evidence_id: str, file: UploadFile) -> str:
    return _save("evidence", evidence_id, file, EVIDENCE_CONTENT_TYPES)
