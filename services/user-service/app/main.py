from fastapi import FastAPI
from app.routes import router
from app.database import Base, engine
from app import models  # noqa: F401  (registers tables on Base)

# Create any missing tables on startup (adds refresh_tokens on first run after upgrade).
Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Service", version="1.0.0")

app.include_router(router, prefix="/auth", tags=["Authentication"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "user-service"}
