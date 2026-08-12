import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("UPLOAD_DIR", tempfile.mkdtemp(prefix="rinko-uploads-"))

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
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def driver_and_headers(client):
    resp = client.post(
        "/auth/signup",
        json={"name": "Alex Silva", "email": "alex@example.com", "password": "s3cret-pass"},
    )
    assert resp.status_code == 200
    body = resp.json()
    return body["driver"], {"Authorization": f"Bearer {body['access_token']}"}


@pytest.fixture
def carrier(client, driver_and_headers):
    _, headers = driver_and_headers
    resp = client.post(
        "/carriers", json={"name": "UniUni", "default_rate_cents": 170}, headers=headers
    )
    assert resp.status_code == 201
    return resp.json()
