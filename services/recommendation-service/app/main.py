from fastapi import FastAPI
from app.routes import router
from app.database import SessionLocal
from app.similarity import load_cache_from_db

app = FastAPI(title="Recommendation Service", version="1.0.0")

app.include_router(router, tags=["Recommendations"])

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        load_cache_from_db(db)
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "recommendation-service"}