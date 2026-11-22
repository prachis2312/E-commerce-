from app.models import ProductEmbedding
from app.service_clients import ProductFetchError
from app import embeddings, similarity
from conftest import token

URL = "/recommendations/refresh"


def ids(db):
    return sorted(pe.product_id for pe in db.query(ProductEmbedding).all())


# ---------- who may call refresh ----------

def test_refresh_without_credentials_rejected(client):
    assert client.post(URL).status_code == 401


def test_refresh_rejects_normal_user(client):
    r = client.post(URL, headers={"Authorization": f"Bearer {token(False)}"})
    assert r.status_code == 403


def test_refresh_allows_admin(client):
    r = client.post(URL, headers={"Authorization": f"Bearer {token(True)}"})
    assert r.status_code == 200 and r.json()["embeddings_processed"] == 2


def test_refresh_allows_internal_service_key(client):
    r = client.post(URL, headers={"x-internal-key": "test-internal-key"})
    assert r.status_code == 200


def test_refresh_rejects_wrong_internal_key(client):
    assert client.post(URL, headers={"x-internal-key": "wrong"}).status_code == 401


# ---------- what refresh does ----------

def test_new_product_gets_embedded_and_cached(client, db_session, catalog):
    client.post(URL, headers={"x-internal-key": "test-internal-key"})
    catalog.append({"id": 3, "name": "Kettle", "description": "Boils water", "category": {"name": "Kitchen"}})
    r = client.post(URL, headers={"x-internal-key": "test-internal-key"})
    assert r.json()["embeddings_processed"] == 1  # only the new one
    assert ids(db_session) == [1, 2, 3]
    assert 3 in similarity._embedding_cache


def test_unchanged_products_are_not_re_embedded(client):
    h = {"x-internal-key": "test-internal-key"}
    client.post(URL, headers=h)
    assert client.post(URL, headers=h).json()["embeddings_processed"] == 0


def test_edited_product_is_re_embedded(client, catalog):
    h = {"x-internal-key": "test-internal-key"}
    client.post(URL, headers=h)
    catalog[0]["description"] = "A much bigger mug"
    assert client.post(URL, headers=h).json()["embeddings_processed"] == 1


def test_deleted_product_embedding_is_removed(client, db_session, catalog):
    h = {"x-internal-key": "test-internal-key"}
    client.post(URL, headers=h)
    catalog.pop()  # product 2 deleted by admin
    client.post(URL, headers=h)
    assert ids(db_session) == [1]
    assert 2 not in similarity._embedding_cache  # can't be recommended any more


def test_failed_product_fetch_does_not_wipe_embeddings(client, db_session, monkeypatch):
    h = {"x-internal-key": "test-internal-key"}
    client.post(URL, headers=h)

    async def boom():
        raise ProductFetchError("product-service down")
    monkeypatch.setattr(embeddings, "get_all_products_strict", boom)

    r = client.post(URL, headers=h)
    assert r.status_code == 503
    assert ids(db_session) == [1, 2]  # nothing deleted because of an outage
