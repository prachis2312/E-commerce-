import os, sys

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["ALGORITHM"] = "HS256"
os.environ["INTERNAL_API_KEY"] = "test-internal-key"

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


def make_token(is_admin: bool, user_id: int = 1) -> str:
    return jwt.encode(
        {"sub": "t@example.com", "user_id": user_id, "is_admin": is_admin,
         "exp": datetime.now(timezone.utc) + timedelta(minutes=10)},
        "test-secret", algorithm="HS256",
    )


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_headers():
    return {"Authorization": f"Bearer {make_token(True)}"}


@pytest.fixture()
def user_headers():
    return {"Authorization": f"Bearer {make_token(False)}"}


@pytest.fixture()
def internal_headers():
    return {"x-internal-key": "test-internal-key"}
