# Scalable E-Commerce Platform (Microservices Architecture)

A full-stack e-commerce platform built using a microservices architecture, containerized with Docker, with a React frontend and a machine learning-powered recommendation engine integrated as a first-class service. Each core capability (users, products, cart, orders, recommendations) is implemented as an independently deployable service, communicating over REST APIs behind a single API Gateway.

**Live demo (frontend):** https://e-commerce-tau-sepia-91.vercel.app
*(Note: the deployed frontend calls a locally-run backend via `http://localhost:8000`, per this project's deployment approach — see [Deployment](#deployment) below.)*

## Features

- **Shopping:** product catalog with category filter, pagination and **search** (name, description, category), product detail with similar products, cart, checkout (cart or "Buy Now"), order history
- **Accounts:** register / log in with **persistent sessions** (short-lived access token + rotating refresh token, silent refresh, real server-side logout)
- **Admin dashboard:** admins add, edit and delete products, adjust stock and add categories; authorization is enforced by the backend
- **Recommendations:** "Similar products" and "Recommended for you" from sentence embeddings; kept in sync automatically when an admin changes the catalog
- **Correctness under load:** atomic stock reservation with row-level locking, so concurrent buyers can never oversell the last unit
- **Tested:** 60+ automated tests plus an end-to-end smoke test that includes a concurrent-buyers check

## Architecture Overview

- **API Gateway** — single entry point, reverse-proxies requests to backend services, handles CORS
- **User Service** — registration, login, JWT access tokens, rotating refresh tokens, logout
- **Product Service** — product catalog, categories, inventory, search, filtering, pagination, atomic stock reservation
- **Cart Service** — shopping cart management with live stock validation via inter-service calls
- **Order Service** — checkout orchestration (cart-based and "Buy Now"), stock reservation, simulated payment processing, order history
- **Recommendation Service** — content-based product recommendations using sentence embeddings, cosine similarity, and real user interaction history
- **Frontend** — React + Vite single-page app consuming the API Gateway

Each backend service owns its own PostgreSQL database, its own dependencies, and its own Dockerfile, and can be developed, deployed, and scaled independently. Services communicate exclusively over REST APIs — no service directly accesses another service's database.

## Tech Stack

- **Backend:** Python, FastAPI
- **Frontend:** React, Vite, React Router, Axios, plain CSS (design tokens in one stylesheet), Vitest
- **Database:** PostgreSQL (one instance per service, containerized)
- **Auth:** JWT access tokens (HS256) verified independently by every service, opaque refresh tokens stored hashed (SHA-256) in the database, bcrypt password hashing
- **Containerization:** Docker, Docker Compose (11 containers: 5 services + 5 databases + 1 API Gateway)
- **Machine Learning:** Sentence-Transformers (`all-MiniLM-L6-v2`) for text embeddings, NumPy for cosine similarity computation
- **Inter-service communication:** `httpx` / `requests` REST calls, JWT forwarding for user-scoped requests, shared internal API key for trusted service-to-service calls
- **Testing:** pytest (SQLite-backed, no Docker needed), Vitest, end-to-end smoke script
- **Deployment:** Vercel (frontend)

## System Architecture

```
                              ┌──────────────────┐
                              │  Browser / React   │
                              │      Frontend       │
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │     API Gateway       │
                              │        :8000           │
                              │  (CORS, reverse proxy) │
                              └──────────┬──────────┘
                                         │
        ┌──────────────┬────────────────┼────────────────┬──────────────────┐
        │              │                │                │                  │
┌───────▼──────┐ ┌─────▼─────┐   ┌──────▼───────┐ ┌──────▼───────┐ ┌────────▼───────────┐
│ User Service │ │  Product   │   │    Cart      │ │    Order     │ │   Recommendation    │
│   :8001      │ │  Service   │   │   Service    │ │   Service    │ │      Service         │
│              │ │   :8002    │   │    :8003     │ │    :8004     │ │        :8005         │
└───────┬──────┘ └─────┬──────┘   └──────┬───────┘ └──────┬───────┘ └──────────┬───────────┘
        │              │                 │                │                    │
┌───────▼──────┐ ┌─────▼──────┐  ┌───────▼─────┐  ┌───────▼───────┐  ┌─────────▼───────────┐
│  postgres    │ │  product-   │  │   cart-      │  │   order-      │  │   recommendation-     │
│  :5433       │ │  postgres   │  │  postgres    │  │   postgres    │  │      postgres         │
│              │ │   :5434     │  │   :5435      │  │    :5436      │  │       :5437           │
└──────────────┘ └─────────────┘  └──────────────┘  └───────────────┘  └───────────────────────┘

Cross-service calls:
  Cart Service      → Product Service   (validate product, check stock)                 [JWT forwarded]
  Order Service     → Product Service   (reserve / release stock)                       [internal API key]
  Order Service     → Cart Service      (fetch cart, clear cart after checkout)          [JWT forwarded]
  Product Service   → Recommendation    (a product changed: re-embed, best-effort)       [internal API key]
  Recommendation    → Product Service   (fetch catalog for embeddings)                  [no auth — public reads]
  Recommendation    → Order Service     (fetch user purchase history)                   [JWT forwarded]
```

**Why stock changes use a separate internal API key instead of JWT forwarding:** Product Service's admin-only routes (`PUT /products/{id}`) require `is_admin: true`, but a regular customer checking out isn't an admin. Forwarding their JWT would either fail (correctly rejected) or require weakening admin checks (a security regression — any customer could then rewrite prices, not just stock). Instead, Order Service calls narrow, purpose-built `reserve-stock` / `release-stock` routes that only touch `stock_quantity`, authenticated via a shared secret known only to trusted backend services — never exposed to the frontend or any user token.

## Project Structure

```
E-commerce-/
├── api-gateway/
│   └── app/
│       ├── main.py              # CORS, Private Network Access handling, proxy route
│       └── config.py            # SERVICE_ROUTES mapping
├── frontend/
│   ├── vercel.json              # SPA rewrite so deep links (/admin, /login) don't 404
│   └── src/
│       ├── api/                 # one file per backend service; client.js holds the token store + silent refresh
│       │   └── __tests__/       # interceptor tests (Vitest)
│       ├── pages/               # Login, Register, ProductList, ProductDetail, Cart, Checkout, Orders, Admin
│       ├── components/          # Navbar (with search), ProductCard, AdminRoute
│       ├── context/             # AuthContext (tokens + decoded claims), CartContext
│       ├── utils/               # jwt.js (client-side token decoding)
│       └── index.css            # design tokens + shared component styles
├── services/
│   ├── user-service/            # auth.py, models.py (User, RefreshToken), routes.py, tests/
│   ├── product-service/         # routes.py, notify.py (tells recommendations about changes), seed_products.py, tests/
│   ├── cart-service/
│   ├── order-service/           # payment.py, service_clients.py
│   └── recommendation-service/  # embeddings.py, similarity.py, auth.py, tests/
├── scripts/
│   └── smoke_test.py            # end-to-end test against the running stack
├── requirements-dev.txt         # test dependencies
├── docker-compose.yml
└── README.md
```

## Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
- Node.js (LTS) — for the frontend
- Python 3.11+ — only for running tests/scripts outside Docker

### Running the backend

1. Clone the repository
   ```bash
   git clone https://github.com/prachis2312/E-commerce-.git
   cd E-commerce-
   ```

2. Environment variables are set directly in `docker-compose.yml` under each service's `environment:` block (not via per-service `.env` files) — this includes `SECRET_KEY` (shared across services for JWT verification), `INTERNAL_API_KEY` (shared by trusted services) and the token lifetimes (`ACCESS_TOKEN_EXPIRE_MINUTES: 15`, `REFRESH_TOKEN_EXPIRE_DAYS: 7`). Change the secrets before running in any shared/public environment.

3. Start all services and databases
   ```bash
   docker compose up -d --build
   ```
   The first build downloads PyTorch for recommendation-service and can take several minutes; later builds are cached.

4. Create the tables (first run only, fresh databases are empty). user-service also creates its own tables on startup.
   ```bash
   cd services/product-service && python create_tables.py && cd ../..
   cd services/cart-service && python create_tables.py && cd ../..
   cd services/order-service && python create_tables.py && cd ../..
   cd services/recommendation-service && python create_tables.py && cd ../..
   ```

5. Seed the catalog (idempotent, about 80 products in 10 categories)
   ```bash
   docker compose exec product-service python seed_products.py
   ```

6. Make yourself an admin (register on the site first, then):
   ```bash
   docker exec -it ecommerce-postgres psql -U postgres -d user_service_db \
     -c "UPDATE users SET is_admin = true WHERE email = 'you@example.com';"
   ```

7. Generate the product embeddings once (log in again so your token carries the admin claim). After this, embeddings stay in sync automatically.
   ```bash
   TOKEN=$(curl -s -X POST http://localhost:8000/api/users/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"you@example.com","password":"YOUR_PASSWORD"}' | sed 's/.*"access_token":"\([^"]*\)".*/\1/')
   curl -X POST http://localhost:8000/api/recommendations/recommendations/refresh \
     -H "Authorization: Bearer $TOKEN"
   ```
   (The admin page also has a **Refresh recommendations** button.)

### Running the frontend

```bash
cd frontend
echo "VITE_API_URL=http://localhost:8000/api" > .env   # .env is git-ignored
npm install
npm run dev
```

Visit `http://localhost:5173`.

### All entry points

| Component | URL | Docs |
|---|---|---|
| **API Gateway** (use this) | `http://localhost:8000` | — |
| Frontend | `http://localhost:5173` | — |
| User Service (direct) | `http://localhost:8001` | `/docs` |
| Product Service (direct) | `http://localhost:8002` | `/docs` |
| Cart Service (direct) | `http://localhost:8003` | `/docs` |
| Order Service (direct) | `http://localhost:8004` | `/docs` |
| Recommendation Service (direct) | `http://localhost:8005` | `/docs` |

All frontend traffic goes through the gateway (`/api/{service}/...`); direct service ports are available for debugging and Swagger docs.

## Testing

```bash
# backend unit/integration tests (SQLite, no Docker needed)
pip install -r requirements-dev.txt
cd services/user-service && python -m pytest tests -q            # auth, refresh rotation, reuse detection, logout
cd ../product-service && python -m pytest tests -q                # admin authorization, CRUD, search, stock reservation
cd ../recommendation-service && pip install numpy && python -m pytest tests -q   # refresh auth, incremental embeddings, deletion cleanup

# frontend tests (silent token refresh)
cd frontend && npm install && npm test

# end-to-end smoke test against the running stack
# (includes 10 buyers racing for 3 units; skips admin sections if no credentials are given)
ADMIN_EMAIL=you@example.com ADMIN_PASSWORD=... python scripts/smoke_test.py
```

## Deployment

The **frontend** is deployed to Vercel (free tier) from the `frontend/` subdirectory of this repo (`vercel.json` rewrites every path to `index.html` so client-side routes survive a refresh). The **backend** intentionally remains local/Docker-Compose-run rather than deployed to a paid host, given this project's scope and timeline — all 11 containers are demonstrated by running `docker compose up` locally alongside the live frontend URL.

Because of this, the deployed frontend only functions fully when accessed from a machine running the backend locally (`VITE_API_URL` points at `http://localhost:8000`, which resolves to *the visitor's own machine* — a deliberate, documented tradeoff, not an oversight).

**Two notable deployment-specific issues encountered and resolved:**
- **CORS:** the gateway's `ALLOWED_ORIGINS` must include the deployed Vercel URL alongside `http://localhost:5173`, or the browser blocks all API calls from the live site.
- **Chrome's Private Network Access (PNA) policy:** Chrome blocks public HTTPS sites from silently calling `localhost` by default. The gateway answers Chrome's PNA preflight (`Access-Control-Allow-Private-Network: true`) via a small custom middleware, and the browser prompts the user once for permission.

## Example User Flow

1. `POST /auth/register`, then `POST /auth/login` — receive an access token and a refresh token
2. `GET /products?q=yoga` — search the catalog; filter by category; paginate
3. View a product → see **Similar Products** (content-based recommendations)
4. `POST /cart/items` — add to cart (validated live against Product Service's stock)
5. Checkout via `POST /orders` (from cart) or `POST /orders/buy-now` (single product) — reserves stock atomically, simulates payment, creates the order; if payment fails the reserved stock is released
6. Stay logged in: when the 15-minute access token expires, the frontend refreshes it silently
7. `GET /orders` — order history; `GET /recommendations/for-user/{user_id}` — personalized recommendations
8. As admin: manage products and stock at `/admin`; recommendations update automatically

## API Overview

*(all routes below are accessed through the gateway at `http://localhost:8000/api/{service}/...`)*

### User Service
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/auth/register` | Register a new user | No |
| POST | `/auth/login` | Log in, receive access + refresh token | No |
| POST | `/auth/refresh` | Exchange a refresh token for a new pair (rotation) | Refresh token |
| POST | `/auth/logout` | Revoke the refresh token | Refresh token |
| GET | `/auth/me` | Current user's info | Yes |

### Product Service
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/products` | List products (`q` search, `category_id`, `min_price`, `max_price`, `skip`, `limit`) | No |
| GET | `/products/{id}` | Product details | No |
| POST | `/products` | Create product | Yes (admin only) |
| PUT | `/products/{id}` | Update product | Yes (admin only) |
| DELETE | `/products/{id}` | Delete product | Yes (admin only) |
| GET | `/categories` | List categories | No |
| POST | `/categories` | Create category | Yes (admin only) |
| POST | `/products/{id}/reserve-stock` | Atomically check and decrement stock | Internal key |
| POST | `/products/{id}/release-stock` | Return reserved stock (compensating action) | Internal key |
| PATCH | `/products/{id}/stock` | Set stock quantity | Internal key |

### Cart Service
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/cart` | View current user's cart | Yes |
| POST | `/cart/items` | Add item (validates stock via Product Service) | Yes |
| PUT | `/cart/items/{item_id}` | Update item quantity | Yes |
| DELETE | `/cart/items/{item_id}` | Remove item | Yes |
| DELETE | `/cart` | Clear cart | Yes |

### Order Service
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/orders` | Checkout from cart | Yes |
| POST | `/orders/buy-now` | Direct single-product purchase | Yes |
| GET | `/orders` | Order history | Yes |
| GET | `/orders/{id}` | Order details | Yes |
| PUT | `/orders/{id}/status` | Update order status | Yes |

### Recommendation Service
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/recommendations/similar/{product_id}` | Item-to-item similar products | No |
| GET | `/recommendations/for-user/{user_id}` | Personalized recommendations from order history | Yes |
| POST | `/recommendations/refresh` | Embed new/changed products, drop deleted ones | Admin or internal key |

## Sessions & Authentication — Design Notes

- **Two tokens:** a **15-minute access token** (JWT, verified independently by every service with the shared secret — no network call per request) and a **7-day refresh token** (a random opaque string; only its SHA-256 hash is stored in the `refresh_tokens` table, so a database leak does not hand out sessions).
- **Silent refresh:** when any request returns 401, the frontend's axios interceptor calls `/auth/refresh` once (concurrent failures share a single refresh), stores the new pair and retries the original request. The user is only sent to `/login` if the refresh token is expired or revoked. It also notices when another browser tab has already refreshed.
- **Rotation + reuse detection:** every refresh revokes the old refresh token and issues a new one. If an already-used token is presented again (a sign it may have been stolen), every session of that user is revoked.
- **Real logout:** `/auth/logout` revokes the refresh token on the server, not just in the browser.
- **Admin role changes:** `is_admin` is a claim inside the access token, so no extra call is needed to authorize an admin action. The role is re-read from the database on every refresh, so a promotion or demotion takes effect within at most 15 minutes — instead of whenever a long-lived token happens to expire.
- **Storage tradeoff:** tokens live in `localStorage` so the session survives closing the tab. The frontend (Vercel) and backend (localhost) are on different origins, which makes httpOnly cookies unreliable here; the tradeoff is exposure to XSS, which is mitigated by the short access-token lifetime, refresh-token rotation and server-side revocation. A same-origin production deployment would use httpOnly, `SameSite` cookies instead.
- **Not implemented (documented):** an access-token blocklist for instant revocation, rate limiting on `/auth/login`, and email verification / password reset.

## Recommendation Engine — Design Notes

The recommendation system uses **content-based filtering**, chosen over collaborative filtering because it works effectively even with the limited interaction data available in a project of this scale, and doesn't require a large user base to produce meaningful results.

**Embedding model:** `all-MiniLM-L6-v2` (Sentence-Transformers) was chosen over TF-IDF or averaged word vectors because it captures genuine semantic similarity — e.g., recognizing "wireless headphones" and "bluetooth earphones" as related despite minimal word overlap. It runs entirely locally on CPU, avoiding dependency on paid embedding APIs.

**Similarity metric:** Cosine similarity, the standard choice for text embeddings, since it measures semantic direction rather than magnitude (unaffected by description length).

**Two recommendation modes:**
- **Item-to-item** (`/similar/{id}`) — requires no user data; compares a product's embedding against all others in the catalog.
- **Personalized** (`/for-user/{id}`) — builds a user profile vector by averaging the embeddings of products in their real order history (fetched live from Order Service), then finds the closest unpurchased products. Falls back to a cold-start response for users with no order history.

**Similarity threshold with graceful fallback padding:** Recommendations below a minimum cosine similarity score are excluded rather than treated as valid matches — without this, scattered purchase history produced weak suggestions just to fill a quota. Since a *sparse* list is also a poor experience, remaining slots are backfilled with general fallback products, clearly distinguishable via `similarity_score: 0.0` and a `source` field (`user_history` / `user_history_with_fallback` / `cold_start_fallback`), so genuine personalization is never conflated with padding.

**Embedding storage and incremental refresh:** Embeddings are persisted in PostgreSQL (JSON arrays) together with a SHA-256 hash of the product text they were computed from, and loaded into an in-memory cache at startup. A refresh re-embeds only products that are new or whose text changed (hash mismatch), and deletes embeddings of products that no longer exist so they cannot be recommended as dead links. If the product list cannot be fetched completely, the refresh aborts without deleting anything.

**Automatic sync:** when an admin creates, edits or deletes a product, Product Service notifies Recommendation Service in a background task using the internal API key. It is best-effort by design — an outage of the recommendation service never blocks catalog edits, and the next refresh (or the admin button) catches up. Refreshes are serialized with a lock so rapid edits cannot insert duplicate embeddings.

**Scalability tradeoff (documented, not implemented):** At significantly larger catalog sizes, this in-memory linear-scan similarity search would be replaced with `pgvector` (indexed approximate nearest-neighbor search) rather than loading all embeddings into application memory.

## Design Decisions & Tradeoffs

- **Atomic stock reservation (race-condition fix):** checking stock and decrementing it used to be two separate steps, so two buyers could both pass the check for the last unit. `reserve-stock` now does check-and-decrement in a single transaction using `SELECT ... FOR UPDATE`, which locks the product row so concurrent requests queue up and see the updated value. A concurrent-buyers test in the smoke script verifies that stock never goes negative and that orders plus remaining stock always add up.
- **Checkout order: reserve → pay → create order, with compensation:** stock is reserved first, then payment is processed; if payment fails, `release-stock` returns the reserved units (a simplified alternative to the Saga pattern, which a production system would use for full distributed-transaction consistency). The cart does not reserve stock (optimistic); only checkout does.
- **Payment processing is simulated** via a mock function with a ~95% success rate, structured so a real gateway (e.g., Stripe test mode) could be substituted without changing the surrounding checkout logic.
- **Unified checkout for both purchase paths:** "Buy Now" and "Proceed to Checkout" both route through the same Checkout page and payment handling — "Buy Now" skips the cart, not the checkout.
- **Price/name snapshotting:** Cart and Order line items store the price (and, for orders, name) at the time of the transaction, so totals don't silently change when prices update and order history stays accurate if a product is later renamed or removed.
- **JWT forwarding for user-scoped calls:** Order Service and Recommendation Service forward the user's JWT to Cart Service and Order Service respectively, letting downstream services independently verify identity.
- **Internal API key for service-scoped calls:** where the *system* is acting (reserving stock, re-embedding after a catalog change), a narrow endpoint gated by a shared internal key is used instead of JWT forwarding, preserving strict admin-only access to full product mutation. Key comparison uses a constant-time check in recommendation-service.
- **Admin authorization via JWT claims:** Product and Recommendation services verify `is_admin` from the token using the shared secret, avoiding an extra network call on every request (see session notes above for how role changes propagate).
- **Search:** `GET /products?q=` splits the query into words and requires every word to match the name, description or category (case-insensitive). `%` and `_` are escaped so they are treated literally. A production system at larger scale would use Postgres full-text search or a dedicated search engine.
- **Manual table creation vs. migrations:** Tables are created via one-off scripts (`create_tables.py`; user-service also runs `create_all` on startup). A production system would use Alembic for versioned schema migrations.
- **Service discovery:** Not implemented; services use fixed hostnames on Docker Compose's internal network, sufficient at this scale.
- **Secrets in `docker-compose.yml`:** the values committed here are development placeholders; a real deployment would inject secrets from a secrets manager or environment.

## Roadmap

- [x] User Service — auth, JWT, Dockerized
- [x] Product Service — CRUD, categories, filtering, search, seeded data
- [x] Cart Service — cart management, stock validation
- [x] Order Service — checkout orchestration, buy-now, simulated payments
- [x] Recommendation Service — content-based filtering, personalization, fallback handling, automatic sync
- [x] API Gateway — FastAPI reverse proxy, CORS, Private Network Access support
- [x] Admin authorization and admin dashboard
- [x] Internal service-to-service authorization; atomic stock reservation
- [x] Persistent sessions: refresh tokens with rotation, reuse detection and logout
- [x] Frontend (React + Vite) — auth, browsing, search, cart, checkout, orders, recommendations, themed UI
- [x] Automated tests (backend, frontend, end-to-end) and Vercel deployment
- [ ] Next ideas: rate limiting on login, password reset, product images upload, order status updates from the admin page, pgvector for large catalogs

## Author

Prachi Saxena
