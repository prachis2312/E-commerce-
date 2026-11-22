PRODUCT = {"name": "Test Mug", "description": "A mug", "price": 9.99, "stock_quantity": 5}


def create_product(client, admin_headers, **overrides):
    r = client.post("/products", json={**PRODUCT, **overrides}, headers=admin_headers)
    assert r.status_code == 201, r.text
    return r.json()


# ---------- authorization ----------

def test_create_product_requires_login(client):
    assert client.post("/products", json=PRODUCT).status_code in (401, 403)


def test_create_product_forbidden_for_normal_user(client, user_headers):
    r = client.post("/products", json=PRODUCT, headers=user_headers)
    assert r.status_code == 403


def test_update_and_delete_forbidden_for_normal_user(client, admin_headers, user_headers):
    p = create_product(client, admin_headers)
    assert client.put(f"/products/{p['id']}", json={"price": 1}, headers=user_headers).status_code == 403
    assert client.delete(f"/products/{p['id']}", headers=user_headers).status_code == 403


def test_create_category_forbidden_for_normal_user(client, user_headers):
    assert client.post("/categories", json={"name": "X"}, headers=user_headers).status_code == 403


# ---------- admin CRUD ----------

def test_admin_can_create_and_read_product(client, admin_headers):
    p = create_product(client, admin_headers)
    r = client.get(f"/products/{p['id']}")  # reading is public
    assert r.status_code == 200
    assert r.json()["name"] == "Test Mug"


def test_admin_can_create_category_and_attach(client, admin_headers):
    cat = client.post("/categories", json={"name": "Kitchen"}, headers=admin_headers).json()
    p = create_product(client, admin_headers, category_id=cat["id"])
    assert p["category"]["name"] == "Kitchen"


def test_duplicate_category_rejected(client, admin_headers):
    client.post("/categories", json={"name": "Kitchen"}, headers=admin_headers)
    assert client.post("/categories", json={"name": "Kitchen"}, headers=admin_headers).status_code == 400


def test_admin_can_update_only_sent_fields(client, admin_headers):
    p = create_product(client, admin_headers)
    r = client.put(f"/products/{p['id']}", json={"price": 19.5}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["price"] == 19.5
    assert r.json()["name"] == "Test Mug"  # untouched


def test_admin_can_delete_product(client, admin_headers):
    p = create_product(client, admin_headers)
    assert client.delete(f"/products/{p['id']}", headers=admin_headers).status_code == 204
    assert client.get(f"/products/{p['id']}").status_code == 404


def test_get_missing_product_404(client):
    assert client.get("/products/9999").status_code == 404


# ---------- listing / filtering ----------

def test_list_filters_and_pagination(client, admin_headers):
    cat = client.post("/categories", json={"name": "A"}, headers=admin_headers).json()
    for i in range(5):
        create_product(client, admin_headers, name=f"P{i}", price=10 + i, category_id=cat["id"])
    create_product(client, admin_headers, name="Other", price=100)

    assert len(client.get("/products").json()) == 6
    assert len(client.get("/products", params={"category_id": cat["id"]}).json()) == 5
    assert len(client.get("/products", params={"min_price": 12, "max_price": 14}).json()) == 3
    assert len(client.get("/products", params={"limit": 2}).json()) == 2
    assert len(client.get("/products", params={"skip": 4, "limit": 10}).json()) == 2


# ---------- stock reservation ----------

def test_reserve_stock_requires_internal_key(client, admin_headers):
    p = create_product(client, admin_headers)
    r = client.post(f"/products/{p['id']}/reserve-stock", json={"quantity": 1},
                    headers={"x-internal-key": "wrong"})
    assert r.status_code == 403
    # even an admin JWT must not work here - this is service-to-service only
    r = client.post(f"/products/{p['id']}/reserve-stock", json={"quantity": 1}, headers=admin_headers)
    assert r.status_code == 422


def test_reserve_decrements_stock(client, admin_headers, internal_headers):
    p = create_product(client, admin_headers, stock_quantity=5)
    r = client.post(f"/products/{p['id']}/reserve-stock", json={"quantity": 2}, headers=internal_headers)
    assert r.status_code == 200
    assert r.json()["remaining_stock"] == 3
    assert client.get(f"/products/{p['id']}").json()["stock_quantity"] == 3


def test_reserve_more_than_available_fails_and_leaves_stock(client, admin_headers, internal_headers):
    p = create_product(client, admin_headers, stock_quantity=2)
    r = client.post(f"/products/{p['id']}/reserve-stock", json={"quantity": 3}, headers=internal_headers)
    assert r.status_code == 400
    assert client.get(f"/products/{p['id']}").json()["stock_quantity"] == 2


def test_last_unit_can_only_be_bought_once(client, admin_headers, internal_headers):
    p = create_product(client, admin_headers, stock_quantity=1)
    url = f"/products/{p['id']}/reserve-stock"
    assert client.post(url, json={"quantity": 1}, headers=internal_headers).status_code == 200
    assert client.post(url, json={"quantity": 1}, headers=internal_headers).status_code == 400
    assert client.get(f"/products/{p['id']}").json()["stock_quantity"] == 0


def test_release_stock_restores_quantity(client, admin_headers, internal_headers):
    p = create_product(client, admin_headers, stock_quantity=5)
    client.post(f"/products/{p['id']}/reserve-stock", json={"quantity": 4}, headers=internal_headers)
    r = client.post(f"/products/{p['id']}/release-stock", json={"quantity": 4}, headers=internal_headers)
    assert r.status_code == 200
    assert client.get(f"/products/{p['id']}").json()["stock_quantity"] == 5


def test_reserve_missing_product_404(client, internal_headers):
    r = client.post("/products/9999/reserve-stock", json={"quantity": 1}, headers=internal_headers)
    assert r.status_code == 404


# ---------- recommendation sync ----------

def test_product_changes_notify_recommendation_service(client, admin_headers, monkeypatch):
    calls = []
    monkeypatch.setattr("app.routes.notify_recommendations", lambda: calls.append(1))

    p = create_product(client, admin_headers)
    assert len(calls) == 1
    client.put(f"/products/{p['id']}", json={"price": 3}, headers=admin_headers)
    assert len(calls) == 2
    client.delete(f"/products/{p['id']}", headers=admin_headers)
    assert len(calls) == 3


def test_recommendation_outage_never_blocks_product_creation(client, admin_headers, monkeypatch):
    import app.notify as notify
    monkeypatch.setattr(notify.requests, "post", lambda *a, **k: (_ for _ in ()).throw(ConnectionError("down")))
    r = client.post("/products", json=PRODUCT, headers=admin_headers)
    assert r.status_code == 201


def test_failed_create_does_not_notify(client, user_headers, monkeypatch):
    calls = []
    monkeypatch.setattr("app.routes.notify_recommendations", lambda: calls.append(1))
    client.post("/products", json=PRODUCT, headers=user_headers)  # 403
    assert calls == []


# ---------- search ----------

def seed_search_data(client, admin_headers):
    kitchen = client.post("/categories", json={"name": "Home & Kitchen"}, headers=admin_headers).json()
    sports = client.post("/categories", json={"name": "Sports"}, headers=admin_headers).json()
    create_product(client, admin_headers, name="Yoga Mat Non-Slip", description="6 mm mat for stretching",
                   category_id=sports["id"])
    create_product(client, admin_headers, name="Door Mat", description="Rubber doormat for the entrance",
                   category_id=kitchen["id"])
    create_product(client, admin_headers, name="Electric Kettle", description="Boils water fast",
                   category_id=kitchen["id"])
    create_product(client, admin_headers, name="100% Cotton Towel", description="Soft towel", category_id=None)
    return kitchen, sports


def names(resp):
    return sorted(p["name"] for p in resp.json())


def test_search_matches_name_case_insensitive(client, admin_headers):
    seed_search_data(client, admin_headers)
    assert names(client.get("/products", params={"q": "KETTLE"})) == ["Electric Kettle"]


def test_search_matches_description(client, admin_headers):
    seed_search_data(client, admin_headers)
    assert names(client.get("/products", params={"q": "boils"})) == ["Electric Kettle"]


def test_search_matches_category_name(client, admin_headers):
    seed_search_data(client, admin_headers)
    assert names(client.get("/products", params={"q": "sports"})) == ["Yoga Mat Non-Slip"]


def test_search_multiple_words_must_all_match(client, admin_headers):
    seed_search_data(client, admin_headers)
    assert names(client.get("/products", params={"q": "yoga mat"})) == ["Yoga Mat Non-Slip"]
    assert len(client.get("/products", params={"q": "mat"}).json()) == 2


def test_search_no_results(client, admin_headers):
    seed_search_data(client, admin_headers)
    assert client.get("/products", params={"q": "zzzz"}).json() == []


def test_blank_search_returns_everything(client, admin_headers):
    seed_search_data(client, admin_headers)
    assert len(client.get("/products", params={"q": "   "}).json()) == 4


def test_search_wildcards_are_treated_literally(client, admin_headers):
    seed_search_data(client, admin_headers)
    assert client.get("/products", params={"q": "%"}).json()[0]["name"] == "100% Cotton Towel"
    assert len(client.get("/products", params={"q": "%"}).json()) == 1
    assert client.get("/products", params={"q": "_"}).json() == []


def test_search_combines_with_category_filter_and_pagination(client, admin_headers):
    kitchen, sports = seed_search_data(client, admin_headers)
    r = client.get("/products", params={"q": "mat", "category_id": kitchen["id"]})
    assert names(r) == ["Door Mat"]
    r = client.get("/products", params={"q": "mat", "limit": 1})
    assert len(r.json()) == 1
    r2 = client.get("/products", params={"q": "mat", "limit": 1, "skip": 1})
    assert r2.json()[0]["id"] != r.json()[0]["id"]


def test_search_does_not_duplicate_products(client, admin_headers):
    seed_search_data(client, admin_headers)
    assert len(client.get("/products", params={"q": "kitchen"}).json()) == 2
