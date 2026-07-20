# Scalable E-Commerce Platform (Microservices Architecture)

A backend-focused e-commerce platform built using a microservices architecture, containerized with Docker. Each core capability (users, products, cart, orders, recommendations) is implemented as an independently deployable service, communicating over REST APIs.

## Architecture Overview

- **User Service** — registration, authentication (JWT), profile management
- **Product Service** — product catalog, categories, inventory *(in progress)*
- **Cart Service** — shopping cart management *(planned)*
- **Order Service** — order placement, tracking, history *(planned)*
- **Recommendation Service** — ML-based product recommendations (content-based + collaborative filtering) *(planned)*
- **API Gateway** — single entry point routing requests to appropriate services *(planned)*

Each service has its own database, its own dependencies, and its own Dockerfile, and can be developed, deployed, and scaled independently.

## Tech Stack

- **Backend:** Python, FastAPI
- **Database:** PostgreSQL (per-service, containerized)
- **Auth:** JWT (JSON Web Tokens), bcrypt password hashing
- **Containerization:** Docker, Docker Compose
- **ML (Recommendation Service):** scikit-learn / sentence-transformers, collaborative filtering (SVD/ALS)

## Project Structure

```
ecommerce-microservices/
├── services/
│   ├── user-service/
│   │   ├── app/
│   │   │   ├── main.py          # FastAPI entrypoint
│   │   │   ├── models.py        # SQLAlchemy models
│   │   │   ├── schemas.py       # Pydantic request/response schemas
│   │   │   ├── routes.py        # API routes
│   │   │   ├── database.py      # DB connection setup
│   │   │   └── auth.py          # JWT + password hashing logic
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── .env.example
│   ├── product-service/
│   ├── cart-service/
│   ├── order-service/
│   └── recommendation-service/
├── api-gateway/
├── docker-compose.yml
└── README.md
```

## Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
- Python 3.11+ (only needed for local development outside Docker)

### Running the project

1. Clone the repository
   ```bash
   git clone https://github.com/prachis2312/E-commerce-.git
   cd E-commerce-
   ```

2. Set up environment variables for each service (copy the example file and fill in values)
   ```bash
   cp services/user-service/.env.example services/user-service/.env
   ```

3. Start all services with Docker Compose
   ```bash
   docker-compose up --build
   ```

4. Once running, User Service is available at:
   - API: `http://localhost:8001`
   - Interactive docs (Swagger UI): `http://localhost:8001/docs`

5. Create database tables (first run only)
   ```bash
   cd services/user-service
   python -m venv venv
   source venv/Scripts/activate   # on Windows Git Bash
   pip install -r requirements.txt
   python create_tables.py
   ```

### Notes on local Postgres port

If you already run PostgreSQL natively on your machine (default port 5432), this project maps its containerized Postgres to host port **5433** instead, to avoid conflicts. Internally, containers still communicate over port 5432 via Docker's network — only the host-facing port differs.

## API Overview (User Service)

| Method | Endpoint       | Description                    | Auth Required |
|--------|----------------|---------------------------------|----------------|
| POST   | `/auth/register` | Register a new user           | No             |
| POST   | `/auth/login`     | Log in, receive JWT token     | No             |
| GET    | `/auth/me`        | Get current user's info       | Yes (Bearer token) |
| GET    | `/health`         | Health check                  | No             |

## Design Decisions & Tradeoffs

- **Manual table creation vs. migrations:** Tables are currently created via a one-off script (`create_tables.py`). In a production system, a migration tool like Alembic would be used instead, to track schema changes over time.
- **Service discovery:** Not implemented (would use Consul/Eureka at larger scale); services communicate via fixed hostnames defined in Docker Compose's internal network, which is sufficient at this scale.
- **Per-service databases:** Each microservice owns its own database/schema, following the microservices principle of loose coupling — no service directly queries another's database.

## Roadmap

- [x] User Service — auth, JWT, Dockerized
- [ ] Product Service
- [ ] Cart Service
- [ ] Order Service
- [ ] Recommendation Service (content-based + collaborative filtering)
- [ ] API Gateway
- [ ] CI/CD pipeline (GitHub Actions)

## Author

Prachi Saxena