import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("UPLOAD_DIR", tempfile.mkdtemp(prefix="rinko-uploads-"))

from app.config import settings
from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_headers():
    return {"x-admin-key": settings.admin_api_key}


@pytest.fixture
def company_and_key(client, admin_headers):
    resp = client.post(
        "/companies",
        json={"name": "Acme Logistics", "default_rate_cents": 4},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    return body, {"x-api-key": body["api_key"]}
