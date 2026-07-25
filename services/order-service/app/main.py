from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="Order Service", version="1.0.0")

app.include_router(router, tags=["Orders"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "order-service"}