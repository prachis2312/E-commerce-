import os, sys, types

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["ALGORITHM"] = "HS256"
os.environ["INTERNAL_API_KEY"] = "test-internal-key"

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Replace the real (huge) sentence-transformers model with a tiny fake, so tests
# run in milliseconds and need no PyTorch.
import numpy as np

class FakeModel:
    def __init__(self, *a, **k):
        self.encode_calls = 0
    def encode(self, text):
        self.encode_calls += 1
        rng = np.random.default_rng(abs(hash(text)) % (2**32))
        return rng.random(8)

fake_module = types.ModuleType("sentence_transformers")
fake_module.SentenceTransformer = FakeModel
sys.modules["sentence_transformers"] = fake_module

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app import embeddings, routes


def token(is_admin):
    return jwt.encode(
        {"sub": "t@x.com", "user_id": 1, "is_admin": is_admin,
         "exp": datetime.now(timezone.utc) + timedelta(minutes=10)},
        "test-secret", algorithm="HS256")


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    s = sessionmaker(bind=engine, autocommit=False, autoflush=False)()
    yield s
    s.close()


@pytest.fixture()
def catalog(monkeypatch):
    """Mutable fake product list standing in for product-service."""
    products = [
        {"id": 1, "name": "Mug", "description": "A mug", "category": {"name": "Kitchen"}},
        {"id": 2, "name": "Pan", "description": "A pan", "category": {"name": "Kitchen"}},
    ]
    async def fake_fetch():
        return list(products)
    monkeypatch.setattr(embeddings, "get_all_products_strict", fake_fetch)
    return products


@pytest.fixture()
def client(db_session, catalog):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()
