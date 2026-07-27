# Scalable E-Commerce Platform (Microservices Architecture)

A backend-focused e-commerce platform built using a microservices architecture, containerized with Docker. Each core capability (users, products, cart, orders, recommendations) is implemented as an independently deployable service, communicating over REST APIs, with a machine learning-powered recommendation engine integrated as a first-class service.

## Architecture Overview

- **User Service** — registration, authentication (JWT), profile management
- **Product Service** — product catalog, categories, inventory, filtering, pagination
- **Cart Service** — shopping cart management with live stock validation via inter-service calls
- **Order Service** — checkout orchestration (cart-based and "Buy Now"), simulated payment processing, stock decrement, order history
- **Recommendation Service** — content-based product recommendations using sentence embeddings, cosine similarity, and real user interaction history

Each service owns its own PostgreSQL database, its own dependencies, and its own Dockerfile, and can be developed, deployed, and scaled independently. Services communicate exclusively over REST APIs — no service directly accesses another service's database.

## Tech Stack

- **Backend:** Python, FastAPI
- **Database:** PostgreSQL (one instance per service, containerized)
- **Auth:** JWT (JSON Web Tokens), bcrypt password hashing, shared secret verification across services
- **Containerization:** Docker, Docker Compose (10 containers: 5 services + 5 databases)
- **Machine Learning:** Sentence-Transformers (`all-MiniLM-L6-v2`) for text embeddings, NumPy for cosine similarity computation
- **Inter-service communication:** `httpx` (async REST calls), JWT token forwarding for authenticated cross-service requests

## System Architecture

```
                          ┌─────────────────┐
                          │   API clients    │
                          └────────┬─────────┘
                                   │
        ┌──────────────┬──────────┼──────────┬──────────────────┐
        │              │          │          │                  │
┌───────▼──────┐ ┌─────▼─────┐ ┌──▼───────┐ ┌▼─────────────┐ ┌──▼────────────────┐
│ User Service │ │  Product   │ │   Cart   │ │    Order     │ │   Recommendation   │
│   :8001      │ │  Service   │ │ Service  │ │   Service    │ │      Service       │
│              │ │   :8002    │ │  :8003   │ │    :8004     │ │       :8005        │
└───────┬──────┘ └─────┬──────┘ └────┬─────┘ └──────┬───────┘ └──────────┬─────────┘
        │              │             │              │                    │
┌───────▼──────┐ ┌─────▼──────┐┌─────▼─────┐ ┌──────▼───────┐ ┌──────────▼─────────┐
│  postgres    │ │  product-  ││  cart-    │ │   order-     │ │   recommendation-   │
│  :5433       │ │  postgres  ││ postgres  │ │   postgres   │ │      postgres       │
│              │ │   :5434    ││  :5435    │ │    :5436     │ │       :5437         │
└──────────────┘ └────────────┘└───────────┘ └──────────────┘ └─────────────────────┘

Cross-service calls:
  Cart Service      → Product Service   (validate product, check stock)
  Order Service     → Product Service   (validate stock, decrement inventory)
  Order Service     → Cart Service      (fetch cart, clear cart after checkout)
  Recommendation    → Product Service   (fetch catalog for embeddings)
  Recommendation    → Order Service     (fetch user purchase history)
```

## Project Structure

```
ecommerce-microservices/
├── services/
│   ├── user-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── routes.py
│   │   │   ├── database.py
│   │   │   └── auth.py          # JWT creation, password hashing
│   │   ├── create_tables.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── .env.example
│   ├── product-service/
│   │   ├── app/ (main, models, schemas, routes, database)
│   │   ├── seed_products.py     # Fake Store API + manually curated products
│   │   └── ...
│   ├── cart-service/
│   │   ├── app/ (... + auth.py, product_client.py)
│   │   └── ...
│   ├── order-service/
│   │   ├── app/ (... + auth.py, payment.py, service_clients.py)
│   │   └── ...
│   └── recommendation-service/
│       ├── app/
│       │   ├── embeddings.py    # Sentence-transformer model + embedding generation
│       │   ├── similarity.py    # Cosine similarity, in-memory vector cache
│       │   ├── service_clients.py
│       │   └── ...
│       └── ...
├── api-gateway/                 # planned
├── docker-compose.yml
└── README.md
```

## Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
- Python 3.11+ (only needed for local development/scripts outside Docker)

### Running the project

1. Clone the repository
   ```bash
   git clone https://github.com/prachis2312/E-commerce-.git
   cd E-commerce-
   ```

2. Set up environment variables for each service (copy each example file and fill in values — all services must share the same `SECRET_KEY` for JWT verification to work across services)
   ```bash
   cp services/user-service/.env.example services/user-service/.env
   cp services/product-service/.env.example services/product-service/.env
   cp services/cart-service/.env.example services/cart-service/.env
   cp services/order-service/.env.example services/order-service/.env
   cp services/recommendation-service/.env.example services/recommendation-service/.env
   ```

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

6. Generate product embeddings for recommendations
   ```
   POST http://localhost:8005/recommendations/refresh
   ```

7. Services are now available at:

   | Service | URL | Docs |
   |---|---|---|
   | User Service | `http://localhost:8001` | `/docs` |
   | Product Service | `http://localhost:8002` | `/docs` |
   | Cart Service | `http://localhost:8003` | `/docs` |
   | Order Service | `http://localhost:8004` | `/docs` |
   | Recommendation Service | `http://localhost:8005` | `/docs` |

### Notes on local Postgres ports

If PostgreSQL is already installed natively on your machine (default port 5432), this project maps each containerized Postgres instance to a different host port (5433–5437) to avoid conflicts. Internally, all inter-container communication uses the standard port 5432 via Docker's network — only host-facing ports differ.

## Example User Flow

1. `POST /auth/register` (User Service) — create an account
2. `POST /auth/login` (User Service) — receive a JWT
3. `GET /products` (Product Service) — browse the catalog
4. `POST /cart/items` (Cart Service) — add a product to cart (validated live against Product Service's stock)
5. `POST /orders` (Order Service) — checkout: validates stock, simulates payment, creates the order, decrements inventory, clears the cart
   — or `POST /orders/buy-now` to purchase a single product directly, bypassing the cart
6. `GET /recommendations/similar/{product_id}` (Recommendation Service) — see similar products
7. `GET /recommendations/for-user/{user_id}` (Recommendation Service) — personalized recommendations based on order history

## API Overview

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
| PUT | `/products/{id}` | Update product | Yes (admin only) |
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

**Similarity threshold:** Recommendations below a minimum cosine similarity score are excluded rather than padded to a fixed count. This was added after testing revealed that sparse categories (e.g., only 2-3 jewelry items in the catalog) caused the system to return weakly-related items (e.g., clothing) just to fill a quota — excluding low-confidence matches produces more honest, higher-quality results, even if it means returning fewer than the requested number of recommendations.

**Embedding storage:** Computed embeddings are persisted in PostgreSQL (as JSON arrays) rather than recomputed on every service restart, and loaded into an in-memory cache at startup for fast similarity computation. This was a deliberate choice for scalability: as the catalog grows (e.g., via a larger Kaggle dataset), only new or changed products need re-embedding, not the entire catalog.

**Scalability tradeoff (documented, not implemented):** At significantly larger catalog sizes, this in-memory linear-scan similarity search would be replaced with `pgvector` (Postgres's native vector extension), enabling indexed approximate nearest-neighbor search (HNSW/IVFFlat) directly at the database level, rather than loading all embeddings into application memory.

## Design Decisions & Tradeoffs

- **Checkout ordering (payment before order creation):** Payment is processed *before* the order record is created and *before* stock is decremented. This avoids needing to roll back a created order or restored inventory if payment fails — a simplified alternative to the Saga pattern, which a production system would use for full distributed-transaction consistency across order placement steps.
- **Payment processing is simulated** via a mock function with a ~95% success rate, structured so a real gateway (e.g., Stripe test mode) could be substituted without changing the surrounding checkout logic.
- **Price/name snapshotting:** Cart and Order line items store the product's price (and, for orders, name) at the time of the transaction, rather than referencing live product data — ensuring cart totals don't silently change if prices update, and order history remains accurate even if a product is later renamed or removed from the catalog.
- **JWT token forwarding:** Order Service and Recommendation Service forward the user's original JWT to Cart Service and Order Service respectively, rather than maintaining separate service-to-service credentials — allowing downstream services to independently verify identity using a shared secret key.
- **Admin authorization via JWT claims:** Product Service's write routes (`POST`/`PUT`/`DELETE /products`, `POST /categories`) require an `is_admin` claim embedded in the JWT at login, verified independently by Product Service using the same shared secret as User Service — avoiding an extra network call to check permissions on every request. The tradeoff: revoking a user's admin status doesn't take effect until their current token expires, since the claim is baked into the token at issuance. A production system might mitigate this with shorter token lifetimes or a token-revocation list.
- **No API Gateway (yet):** Each service is currently accessed directly on its own port. A gateway (e.g., a lightweight FastAPI router or Kong/Traefik) would consolidate this into a single entry point in a production deployment.
- **Manual table creation vs. migrations:** Tables are created via one-off scripts (`create_tables.py`). A production system would use Alembic for versioned schema migrations.
- **Service discovery:** Not implemented; services communicate via fixed hostnames defined in Docker Compose's internal network, sufficient at this scale. Consul/Eureka would be used for dynamic service discovery at larger scale.

## Roadmap

- [x] User Service — auth, JWT, Dockerized
- [x] Product Service — CRUD, categories, filtering, seeded data
- [x] Cart Service — cart management, stock validation
- [x] Order Service — checkout orchestration, buy-now, simulated payments
- [x] Recommendation Service — content-based filtering, personalization, cold-start handling
- [x] API Gateway — lightweight FastAPI reverse proxy
- [x] Admin authorization on Product Service (JWT `is_admin` claim)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Frontend (React)
- [ ] Deployment (frontend on Vercel; backend demoed locally/via video)
- [ ] Collaborative filtering (stretch goal, via implicit-feedback ALS)

## Author

Prachi Saxena