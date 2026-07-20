from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="User Service", version="1.0.0")

app.include_router(router, prefix="/auth", tags=["Authentication"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "user-service"}