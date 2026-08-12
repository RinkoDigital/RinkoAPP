import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile

from app import storage
from app.config import settings


def _fake_upload(content_type="image/png", data=b"\x89PNG" + b"0" * 20):
    return UploadFile(filename="f.png", file=io.BytesIO(data), headers={"content-type": content_type})


def test_local_backend_writes_to_disk(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "storage_backend", "local")
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))

    url = storage.save_evidence_file("evidence-1", _fake_upload())

    assert url == "/uploads/evidence/evidence-1.png"
    assert (tmp_path / "evidence" / "evidence-1.png").exists()


def test_s3_backend_uploads_and_returns_public_url(monkeypatch):
    monkeypatch.setattr(settings, "storage_backend", "s3")
    monkeypatch.setattr(settings, "s3_bucket", "rinko-evidence")
    monkeypatch.setattr(settings, "s3_region", "auto")
    monkeypatch.setattr(settings, "s3_public_base_url", "https://cdn.rinkodigital.com")
    storage._s3_client = None

    mock_client = MagicMock()
    with patch("app.storage.boto3.client", return_value=mock_client) as mock_boto:
        url = storage.save_evidence_file("evidence-2", _fake_upload())

    mock_boto.assert_called_once()
    mock_client.put_object.assert_called_once()
    kwargs = mock_client.put_object.call_args.kwargs
    assert kwargs["Bucket"] == "rinko-evidence"
    assert kwargs["Key"] == "evidence/evidence-2.png"
    assert kwargs["ContentType"] == "image/png"
    assert url == "https://cdn.rinkodigital.com/evidence/evidence-2.png"

    storage._s3_client = None


def test_s3_backend_falls_back_to_aws_url_without_public_base(monkeypatch):
    monkeypatch.setattr(settings, "storage_backend", "s3")
    monkeypatch.setattr(settings, "s3_bucket", "rinko-evidence")
    monkeypatch.setattr(settings, "s3_region", "us-east-1")
    monkeypatch.setattr(settings, "s3_public_base_url", "")
    storage._s3_client = None

    with patch("app.storage.boto3.client", return_value=MagicMock()):
        url = storage.save_evidence_file("evidence-3", _fake_upload())

    assert url == "https://rinko-evidence.s3.us-east-1.amazonaws.com/evidence/evidence-3.png"
    storage._s3_client = None


def test_rejects_unsupported_content_type_before_touching_storage(monkeypatch):
    monkeypatch.setattr(settings, "storage_backend", "s3")
    with patch("app.storage.boto3.client") as mock_boto:
        with pytest.raises(HTTPException) as exc_info:
            storage.save_evidence_file("evidence-4", _fake_upload(content_type="application/zip"))
        assert exc_info.value.status_code == 422
    mock_boto.assert_not_called()
