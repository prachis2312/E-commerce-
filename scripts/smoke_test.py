"""
End-to-end smoke test. Runs against the REAL running stack through the API gateway.

    docker compose up -d
    pip install requests
    ADMIN_EMAIL=you@example.com ADMIN_PASSWORD=yourpass python scripts/smoke_test.py

Without ADMIN_EMAIL / ADMIN_PASSWORD the admin and concurrency sections are skipped.
Everything it creates (users, one test product) is unique per run; the test product is deleted at the end.
"""
import os
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import requests

BASE = os.getenv("API_URL", "http://localhost:8000/api")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

passed, failed, skipped = 0, 0, 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


def section(title):
    print(f"\n== {title}")


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def register_and_login(tag):
    suffix = uuid.uuid4().hex[:8]
    email, password = f"smoke_{tag}_{suffix}@example.com", "Smoke-pass-123"
    r = requests.post(f"{BASE}/users/auth/register",
                      json={"username": f"smoke_{tag}_{suffix}", "email": email, "password": password})
    assert r.status_code == 201, r.text
    r = requests.post(f"{BASE}/users/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return email, password, r.json()


def main():
    global skipped

    section("Gateway & services are up")
    for svc in ("users", "products", "cart", "orders", "recommendations"):
        r = requests.get(f"{BASE}/{svc}/health", timeout=10)
        check(f"{svc}-service /health", r.status_code == 200, r.text)

    section("Catalog (public)")
    r = requests.get(f"{BASE}/products/products", params={"limit": 100})
    products = r.json()
    check("product list returns products", r.status_code == 200 and len(products) > 0)
    check("catalog has at least 50 products", len(products) >= 50, f"found {len(products)}")
    check("categories endpoint works", requests.get(f"{BASE}/products/categories").status_code == 200)

    section("Auth: register / login / me")
    email, password, tokens = register_and_login("user")
    check("login returns access + refresh token", "access_token" in tokens and "refresh_token" in tokens)
    me = requests.get(f"{BASE}/users/auth/me", headers=auth(tokens["access_token"]))
    check("/me works with access token", me.status_code == 200 and me.json()["email"] == email)
    check("/me rejects missing token", requests.get(f"{BASE}/users/auth/me").status_code in (401, 403))
    bad = requests.post(f"{BASE}/users/auth/login", json={"email": email, "password": "wrong"})
    check("wrong password -> 401", bad.status_code == 401)

    section("Auth: refresh rotation and logout")
    r = requests.post(f"{BASE}/users/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    check("refresh returns a new pair", r.status_code == 200)
    new = r.json()
    check("refresh token was rotated", new["refresh_token"] != tokens["refresh_token"])
    r = requests.post(f"{BASE}/users/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    check("old refresh token is rejected (reuse)", r.status_code == 401)
    r = requests.post(f"{BASE}/users/auth/refresh", json={"refresh_token": new["refresh_token"]})
    check("reuse detection also killed the newer token", r.status_code == 401)

    _, _, t2 = register_and_login("logout")
    requests.post(f"{BASE}/users/auth/logout", json={"refresh_token": t2["refresh_token"]})
    r = requests.post(f"{BASE}/users/auth/refresh", json={"refresh_token": t2["refresh_token"]})
    check("logout revokes refresh token on the server", r.status_code == 401)

    section("Authorization: normal user cannot use admin routes")
    r = requests.post(f"{BASE}/products/products", headers=auth(tokens["access_token"]),
                      json={"name": "hack", "price": 1, "stock_quantity": 1})
    check("normal user POST /products -> 403", r.status_code == 403, r.text)
    r = requests.post(f"{BASE}/recommendations/recommendations/refresh", headers=auth(tokens["access_token"]))
    check("normal user /recommendations/refresh -> 403", r.status_code == 403, r.text)
    pid = products[0]["id"]
    r = requests.post(f"{BASE}/products/products/{pid}/reserve-stock", json={"quantity": 1},
                      headers=auth(tokens["access_token"]))
    check("normal user cannot call internal reserve-stock", r.status_code in (403, 422), r.text)

    section("Cart")
    _, _, shopper = register_and_login("cart")
    h = auth(shopper["access_token"])
    r = requests.post(f"{BASE}/cart/cart/items", headers=h, json={"product_id": pid, "quantity": 2})
    check("add to cart", r.status_code in (200, 201), r.text)
    r = requests.get(f"{BASE}/cart/cart", headers=h)
    check("cart contains the item", r.status_code == 200 and r.json()["items"][0]["quantity"] == 2, r.text)
    check("cart requires login", requests.get(f"{BASE}/cart/cart").status_code in (401, 403))

    if not (ADMIN_EMAIL and ADMIN_PASSWORD):
        skipped += 1
        print("\n(ADMIN_EMAIL / ADMIN_PASSWORD not set: skipping admin + concurrency sections)")
        return

    section("Admin: login and manage products")
    r = requests.post(f"{BASE}/users/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    check("admin can log in", r.status_code == 200, r.text)
    admin = r.json()
    ah = auth(admin["access_token"])
    r = requests.post(f"{BASE}/products/products", headers=ah, json={
        "name": f"Smoke Test Item {uuid.uuid4().hex[:6]}", "description": "temp",
        "price": 5.0, "stock_quantity": 3})
    check("admin can create a product", r.status_code == 201, r.text)
    product = r.json()
    r = requests.put(f"{BASE}/products/products/{product['id']}", headers=ah, json={"price": 6.5})
    check("admin can edit a product", r.status_code == 200 and r.json()["price"] == 6.5, r.text)

    section("Concurrency: 10 people try to buy the last 3 units at once")
    buyers = [register_and_login(f"buyer{i}")[2] for i in range(10)]

    def buy(tokens_):
        return requests.post(f"{BASE}/orders/orders/buy-now", headers=auth(tokens_["access_token"]),
                             json={"product_id": product["id"], "quantity": 1, "payment_method": "card"},
                             timeout=30)

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(buy, buyers))
    ok = sum(1 for r in results if r.status_code == 201)
    final_stock = requests.get(f"{BASE}/products/products/{product['id']}").json()["stock_quantity"]
    check("never more orders than stock (no overselling)", ok <= 3, f"{ok} orders succeeded")
    check("stock never negative", final_stock >= 0, f"stock={final_stock}")
    check("stock + successful orders == 3 (nothing lost or leaked)", final_stock + ok == 3,
          f"stock={final_stock} orders={ok}")

    section("Cleanup")
    r = requests.delete(f"{BASE}/products/products/{product['id']}", headers=ah)
    check("admin can delete the test product", r.status_code == 204, r.text)

    section("Token refresh keeps admin logged in")
    r = requests.post(f"{BASE}/users/auth/refresh", json={"refresh_token": admin["refresh_token"]})
    check("admin refresh works", r.status_code == 200, r.text)


if __name__ == "__main__":
    try:
        main()
    except requests.ConnectionError:
        print(f"\nCould not reach {BASE}. Is `docker compose up` running?")
        sys.exit(2)
    print(f"\n{passed} passed, {failed} failed" + (" (admin sections skipped)" if skipped else ""))
    sys.exit(1 if failed else 0)
