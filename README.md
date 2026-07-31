# Scalable E-Commerce Platform (Microservices Architecture)

A full-stack e-commerce platform built using a microservices architecture, containerized with Docker, with a React frontend and a machine learning-powered recommendation engine integrated as a first-class service. Each core capability (users, products, cart, orders, recommendations) is implemented as an independently deployable service, communicating over REST APIs behind a single API Gateway.

**Live demo (frontend):** https://e-commerce-tau-sepia-91.vercel.app
*(Note: the deployed frontend calls a locally-run backend via `http://localhost:8000`, per this project's deployment approach — see [Deployment](#deployment) below.)*

## Architecture Overview

- **API Gateway** — single entry point, reverse-proxies requests to backend services, handles CORS
- **User Service** — registration, authentication (JWT), profile management
- **Product Service** — product catalog, categories, inventory, filtering, pagination
- **Cart Service** — shopping cart management with live stock validation via inter-service calls
- **Order Service** — checkout orchestration (cart-based and "Buy Now"), simulated payment processing, stock decrement, order history
- **Recommendation Service** — content-based product recommendations using sentence embeddings, cosine similarity, and real user interaction history
- **Frontend** — React + Vite single-page app consuming the API Gateway

Each backend service owns its own PostgreSQL database, its own dependencies, and its own Dockerfile, and can be developed, deployed, and scaled independently. Services communicate exclusively over REST APIs — no service directly accesses another service's database.

## Tech Stack

- **Backend:** Python, FastAPI
- **Frontend:** React, Vite, React Router, Axios, plain CSS
- **Database:** PostgreSQL (one instance per service, containerized)
- **Auth:** JWT (JSON Web Tokens), bcrypt password hashing, shared secret verification across services
- **Containerization:** Docker, Docker Compose (11 containers: 5 services + 5 databases + 1 API Gateway)
- **Machine Learning:** Sentence-Transformers (`all-MiniLM-L6-v2`) for text embeddings, NumPy for cosine similarity computation
- **Inter-service communication:** `httpx` (async REST calls), JWT token forwarding for user-authenticated cross-service requests, shared internal API key for trusted service-to-service writes
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
  Cart Service      → Product Service   (validate product, check stock)                [JWT forwarded]
  Order Service     → Product Service   (validate stock, decrement inventory)          [internal API key]
  Order Service     → Cart Service      (fetch cart, clear cart after checkout)         [JWT forwarded]
  Recommendation    → Product Service   (fetch catalog for embeddings)                 [no auth — public reads]
  Recommendation    → Order Service     (fetch user purchase history)                  [JWT forwarded]
```

**Why stock decrement uses a separate internal API key instead of JWT forwarding:** Product Service's admin-only routes (`PUT /products/{id}`) require `is_admin: true`, but a regular customer checking out isn't an admin. Forwarding their JWT would either fail (correctly rejected) or require weakening admin checks (a security regression — any customer could then rewrite prices, not just stock). Instead, Order Service calls a narrow, purpose-built `PATCH /products/{id}/stock` route that only touches `stock_quantity`, authenticated via a shared secret key known only to trusted backend services — never exposed to the frontend or any user token.

## Project Structure

```
E-commerce-/
├── api-gateway/
│   └── app/
│       ├── main.py              # CORS, Private Network Access handling, proxy route
│       └── config.py            # SERVICE_ROUTES mapping
├── frontend/
│   └── src/
│       ├── api/                 # one file per backend service (auth, products, cart, orders, recommendations)
│       ├── pages/                # Login, Register, ProductList, ProductDetail, Cart, Checkout, Orders
│       ├── components/           # Navbar, ProductCard
│       ├── context/              # AuthContext (JWT + decoded user claims), CartContext
│       └── utils/                # jwt.js (client-side token decoding)
├── services/
│   ├── user-service/
│   │   └── app/ (main, models, schemas, routes, database, auth)
│   ├── product-service/
│   │   ├── app/ (... + auth.py for admin checks)
│   │   └── seed_products.py     # Fake Store API + manually curated products
│   ├── cart-service/
│   │   └── app/ (... + auth.py, product_client.py)
│   ├── order-service/
│   │   └── app/ (... + auth.py, payment.py, service_clients.py)
│   └── recommendation-service/
│       └── app/
│           ├── embeddings.py    # Sentence-transformer model + embedding generation
│           ├── similarity.py    # Cosine similarity, in-memory vector cache, threshold logic
│           └── service_clients.py
├── docker-compose.yml
└── README.md
```

## Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
- Node.js (LTS) — only needed for running the frontend outside Docker
- Python 3.11+ — only needed for local development/scripts outside Docker

### Running the backend

1. Clone the repository
   ```bash
   git clone https://github.com/prachis2312/E-commerce-.git
   cd E-commerce-
   ```

2. Environment variables are set directly in `docker-compose.yml` under each service's `environment:` block (not via per-service `.env` files) — this includes `SECRET_KEY` (shared across services for JWT verification) and `INTERNAL_API_KEY` (shared between Order Service and Product Service for trusted stock updates). Review and update these values before running in any shared/public environment.

3. Start all services and databases with Docker Compose
   ```bash
   docker-compose up --build
   ```
   Note: the first build downloads the sentence-transformer model's dependencies (PyTorch CPU build) for recommendation-service, which can take several minutes. Subsequent builds are cached and much faster.

4. Create database tables for each service (first run only, since fresh containers start with empty databases)
   ```bash
   cd services/user-service && python create_tables.py && cd ../..
   cd services/product-service && python create_tables.py && cd ../..
   cd services/cart-service && python create_tables.py && cd ../..
   cd services/order-service && python create_tables.py && cd ../..
   cd services/recommendation-service && python create_tables.py && cd ../..
   ```

5. Seed the product catalog
   ```bash
   cd services/product-service
   python seed_products.py
   ```

6. Product embeddings are generated automatically on `recommendation-service` startup. To recompute after adding new products:
   ```
   POST http://localhost:8000/api/recommendations/recommendations/refresh
   ```

### Running the frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. The frontend expects the API Gateway at `http://localhost:8000` (configured via `VITE_API_URL` in `frontend/.env`).

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

## Deployment

The **frontend** is deployed to Vercel (free tier) from the `frontend/` subdirectory of this repo. The **backend** intentionally remains local/Docker-Compose-run rather than deployed to a paid host, given this project's scope and timeline — all 11 containers (5 services + 5 databases + gateway) are demonstrated by running `docker-compose up` locally alongside the live frontend URL.

Because of this, the deployed frontend only functions fully when accessed from a machine running the backend locally (`VITE_API_URL` points at `http://localhost:8000`, which resolves to *the visitor's own machine* — this is a deliberate, documented tradeoff, not an oversight).

**Two notable deployment-specific issues encountered and resolved:**
- **CORS:** the gateway's `ALLOWED_ORIGINS` must include the deployed Vercel URL alongside `http://localhost:5173`, or the browser blocks all API calls from the live site.
- **Chrome's Private Network Access (PNA) policy:** Chrome blocks public HTTPS sites from silently calling `localhost`/private-network addresses by default. The gateway responds to Chrome's PNA preflight check (`Access-Control-Allow-Private-Network: true`) via a small custom middleware layered on top of `CORSMiddleware`, and the browser additionally prompts the user for one-time permission to allow this on first visit.

## Example User Flow

1. `POST /auth/register` — create an account
2. `POST /auth/login` — receive a JWT
3. `GET /products` — browse the catalog, filter by category
4. View a product → see **Similar Products** (content-based recommendations)
5. `POST /cart/items` — add a product to cart (validated live against Product Service's stock)
6. Checkout via `POST /orders` (from cart) or `POST /orders/buy-now` (single-product, skips the cart but not the checkout/payment step) — validates stock, simulates payment, creates the order, decrements inventory via the internal stock-update route, clears the cart (cart checkout only)
7. `GET /orders` — view order history
8. `GET /recommendations/for-user/{user_id}` — personalized "Recommended for you" section based on real order history, with cold-start and low-confidence fallback handling

## API Overview

*(all routes below are accessed through the gateway at `http://localhost:8000/api/{service}/...`)*

### User Service
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/auth/register` | Register a new user | No |
| POST | `/auth/login` | Log in, receive JWT | No |
| GET | `/auth/me` | Current user's info | Yes |

### Product Service
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/products` | List products (filter by category/price, paginated) | No |
| GET | `/products/{id}` | Product details | No |
| POST | `/products` | Create product | Yes (admin only) |
| PUT | `/products/{id}` | Update product (full) | Yes (admin only) |
| PATCH | `/products/{id}/stock` | Update stock only | Internal key (trusted services only) |
| DELETE | `/products/{id}` | Delete product | Yes (admin only) |
| GET | `/categories` | List categories | No |
| POST | `/categories` | Create category | Yes (admin only) |

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
| POST | `/recommendations/refresh` | Recompute and cache product embeddings | No |

## Recommendation Engine — Design Notes

The recommendation system uses **content-based filtering**, chosen over collaborative filtering because it works effectively even with the limited interaction data available in a project of this scale, and doesn't require a large user base to produce meaningful results.

**Embedding model:** `all-MiniLM-L6-v2` (Sentence-Transformers) was chosen over TF-IDF or averaged word vectors because it captures genuine semantic similarity — e.g., recognizing "wireless headphones" and "bluetooth earphones" as related despite minimal word overlap — rather than relying on exact keyword matching. It runs entirely locally on CPU, avoiding dependency on paid embedding APIs.

**Similarity metric:** Cosine similarity, the standard choice for text embeddings, since it measures semantic direction rather than magnitude (unaffected by description length).

**Two recommendation modes:**
- **Item-to-item** (`/similar/{id}`) — requires no user data; compares a product's embedding against all others in the catalog.
- **Personalized** (`/for-user/{id}`) — builds a user profile vector by averaging the embeddings of products in their real order history (fetched live from Order Service), then finds the closest unpurchased products. Falls back to a cold-start response for users with no order history.

**Similarity threshold with graceful fallback padding:** Recommendations below a minimum cosine similarity score are excluded rather than treated as valid matches — testing showed that without this, sparse or scattered purchase history (e.g., a user who bought both jewelry and electronics) produced weak, low-relevance suggestions just to fill a quota. However, a *sparse result list* is also a poor user experience, so when confident matches fall short of the requested count, remaining slots are backfilled with general fallback products — clearly distinguishable in the response via `similarity_score: 0.0` and a distinct `source` field (`user_history` / `user_history_with_fallback` / `cold_start_fallback`), so genuine personalization is never conflated with padding.

**Embedding storage:** Computed embeddings are persisted in PostgreSQL (as JSON arrays) rather than recomputed on every service restart, and loaded into an in-memory cache at startup for fast similarity computation. This was a deliberate choice for scalability: as the catalog grows (e.g., via a larger Kaggle dataset), only new or changed products need re-embedding, not the entire catalog.

**Scalability tradeoff (documented, not implemented):** At significantly larger catalog sizes, this in-memory linear-scan similarity search would be replaced with `pgvector` (Postgres's native vector extension), enabling indexed approximate nearest-neighbor search (HNSW/IVFFlat) directly at the database level, rather than loading all embeddings into application memory.

## Design Decisions & Tradeoffs

- **Checkout ordering (payment before order creation):** Payment is processed *before* the order record is created and *before* stock is decremented. This avoids needing to roll back a created order or restored inventory if payment fails — a simplified alternative to the Saga pattern, which a production system would use for full distributed-transaction consistency across order placement steps.
- **Payment processing is simulated** via a mock function with a ~95% success rate, structured so a real gateway (e.g., Stripe test mode) could be substituted without changing the surrounding checkout logic.
- **Unified checkout for both purchase paths:** "Buy Now" on a product page and "Proceed to Checkout" from the cart both route through the same frontend Checkout page and the same payment-handling logic — "Buy Now" skips the cart, not the checkout/payment step, keeping there be exactly one place in the codebase that handles payment outcomes (including the ~5% simulated failure case).
- **Price/name snapshotting:** Cart and Order line items store the product's price (and, for orders, name) at the time of the transaction, rather than referencing live product data — ensuring cart totals don't silently change if prices update, and order history remains accurate even if a product is later renamed or removed from the catalog.
- **JWT token forwarding for user-scoped calls:** Order Service and Recommendation Service forward the user's original JWT to Cart Service and Order Service respectively, rather than maintaining separate service-to-service credentials — allowing downstream services to independently verify identity using a shared secret key.
- **Internal API key for service-scoped calls:** Where a call represents the *system* acting (e.g., decrementing stock after checkout), rather than a specific user's request, a narrow purpose-built endpoint gated by a shared internal key is used instead of JWT forwarding — preserving strict admin-only access to full product mutation, while still letting trusted internal services perform the one specific write they need.
- **Admin authorization via JWT claims:** Product Service's write routes (`POST`/`PUT`/`DELETE /products`, `POST /categories`) require an `is_admin` claim embedded in the JWT at login, verified independently by Product Service using the same shared secret as User Service — avoiding an extra network call to check permissions on every request. The tradeoff: revoking a user's admin status doesn't take effect until their current token expires, since the claim is baked into the token at issuance. A production system might mitigate this with shorter token lifetimes or a token-revocation list.
- **Manual table creation vs. migrations:** Tables are created via one-off scripts (`create_tables.py`). A production system would use Alembic for versioned schema migrations.
- **Service discovery:** Not implemented; services communicate via fixed hostnames defined in Docker Compose's internal network, sufficient at this scale. Consul/Eureka would be used for dynamic service discovery at larger scale.
- **Frontend auth storage:** JWT is stored in `sessionStorage` (not `localStorage`), balancing persistence across page refreshes against not outliving the browser tab — a reasonable middle ground for a demo application. Claims (`user_id`, `is_admin`) are decoded client-side directly from the JWT payload rather than requiring an extra `/auth/me` call on every page load, since JWT payloads are signed but not encrypted, and the backend independently re-verifies the signature on every real API request regardless of what the frontend reads.

## Roadmap

- [x] User Service — auth, JWT, Dockerized
- [x] Product Service — CRUD, categories, filtering, seeded data
- [x] Cart Service — cart management, stock validation
- [x] Order Service — checkout orchestration, buy-now, simulated payments
- [x] Recommendation Service — content-based filtering, personalization, cold-start and low-confidence fallback handling
- [x] API Gateway — lightweight FastAPI reverse proxy, CORS, Private Network Access support
- [x] Admin authorization on Product Service (JWT `is_admin` claim)
- [x] Internal service-to-service authorization for trusted writes (stock updates)
- [x] Frontend (React + Vite) — auth, product browsing, cart, checkout, order history, recommendations
- [x] Frontend deployment (Vercel)

## Author

Prachi Saxena