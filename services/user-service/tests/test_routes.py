from datetime import datetime, timedelta, timezone

from jose import jwt

from app.models import User, RefreshToken
from app.auth import hash_refresh_token

USER = {"username": "alice", "email": "alice@example.com", "password": "pw12345"}


def register(client, **overrides):
    return client.post("/auth/register", json={**USER, **overrides})


def login(client):
    return client.post("/auth/login", json={"email": USER["email"], "password": USER["password"]})


# ---------- register ----------

def test_register_success(client):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == USER["email"]
    assert body["is_admin"] is False
    assert "password" not in body and "hashed_password" not in body


def test_register_duplicate_rejected(client):
    register(client)
    assert register(client).status_code == 400
    assert register(client, email="other@example.com").status_code == 400  # same username


def test_register_cannot_self_promote_to_admin(client, db_session):
    register(client, is_admin=True)  # extra field must be ignored
    assert db_session.query(User).first().is_admin is False


def test_password_is_hashed(client, db_session):
    register(client)
    assert db_session.query(User).first().hashed_password != USER["password"]


# ---------- login ----------

def test_login_returns_both_tokens(client):
    register(client)
    r = login(client)
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client):
    register(client)
    r = client.post("/auth/login", json={"email": USER["email"], "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_user(client):
    assert client.post("/auth/login", json={"email": "no@example.com", "password": "x"}).status_code == 401


def test_access_token_is_short_lived(client):
    register(client)
    token = login(client).json()["access_token"]
    claims = jwt.decode(token, "test-secret", algorithms=["HS256"])
    lifetime = datetime.fromtimestamp(claims["exp"], timezone.utc) - datetime.now(timezone.utc)
    assert timedelta(minutes=14) < lifetime <= timedelta(minutes=15)


def test_refresh_token_stored_hashed_not_raw(client, db_session):
    register(client)
    raw = login(client).json()["refresh_token"]
    stored = db_session.query(RefreshToken).one()
    assert stored.token_hash != raw
    assert stored.token_hash == hash_refresh_token(raw)


# ---------- /me ----------

def test_me_with_valid_token(client):
    register(client)
    token = login(client).json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == USER["email"]


def test_me_without_token(client):
    assert client.get("/auth/me").status_code in (401, 403)


def test_me_with_garbage_token(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer not.a.token"})
    assert r.status_code == 401


def test_me_with_expired_token(client):
    expired = jwt.encode(
        {"sub": "a@b.com", "user_id": 1, "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        "test-secret", algorithm="HS256",
    )
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert r.status_code == 401


def test_me_with_wrong_signature(client):
    forged = jwt.encode({"sub": "a@b.com", "user_id": 1, "is_admin": True,
                         "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
                        "some-other-secret", algorithm="HS256")
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


# ---------- refresh ----------

def test_refresh_issues_new_pair(client):
    register(client)
    first = login(client).json()
    r = client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert r.status_code == 200
    second = r.json()
    assert second["refresh_token"] != first["refresh_token"]  # rotated
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {second['access_token']}"})
    assert me.status_code == 200


def test_old_refresh_token_cannot_be_reused(client):
    register(client)
    first = login(client).json()
    client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
    r = client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert r.status_code == 401


def test_reuse_detection_revokes_whole_family(client):
    register(client)
    first = login(client).json()
    second = client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]}).json()
    # attacker replays the stolen, already-used token...
    client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
    # ...so the legitimate newer token is dead too
    r = client.post("/auth/refresh", json={"refresh_token": second["refresh_token"]})
    assert r.status_code == 401


def test_refresh_with_unknown_token(client):
    assert client.post("/auth/refresh", json={"refresh_token": "nope"}).status_code == 401


def test_refresh_with_expired_token(client, db_session):
    register(client)
    raw = login(client).json()["refresh_token"]
    rec = db_session.query(RefreshToken).one()
    rec.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()
    assert client.post("/auth/refresh", json={"refresh_token": raw}).status_code == 401


def test_refresh_picks_up_new_admin_role(client, db_session):
    register(client)
    raw = login(client).json()["refresh_token"]
    db_session.query(User).first().is_admin = True
    db_session.commit()
    new_access = client.post("/auth/refresh", json={"refresh_token": raw}).json()["access_token"]
    assert jwt.decode(new_access, "test-secret", algorithms=["HS256"])["is_admin"] is True


# ---------- logout ----------

def test_logout_revokes_refresh_token(client):
    register(client)
    raw = login(client).json()["refresh_token"]
    assert client.post("/auth/logout", json={"refresh_token": raw}).status_code == 204
    assert client.post("/auth/refresh", json={"refresh_token": raw}).status_code == 401


def test_logout_unknown_token_is_harmless(client):
    assert client.post("/auth/logout", json={"refresh_token": "nope"}).status_code == 204
