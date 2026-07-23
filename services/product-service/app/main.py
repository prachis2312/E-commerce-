from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="Product Service", version="1.0.0")

app.include_router(router, tags=["Products & Categories"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "product-service"}