from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="Cart Service", version="1.0.0")

app.include_router(router, tags=["Cart"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "cart-service"}