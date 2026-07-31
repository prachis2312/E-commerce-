from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
import httpx
from app.config import SERVICE_ROUTES
from fastapi.middleware.cors import CORSMiddleware
import os
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI(title="API Gateway", version="1.0.0")

ALLOWED_ORIGINS=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PrivateNetworkAccessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.headers.get("access-control-request-private-network") == "true":
            response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response

app.add_middleware(PrivateNetworkAccessMiddleware)

# ... rest of your existing routes (health check, proxy route)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "api-gateway"}


@app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(service: str, path: str, request: Request):
    if service not in SERVICE_ROUTES:
        raise HTTPException(status_code=404, detail=f"Unknown service: '{service}'")

    target_base_url = SERVICE_ROUTES[service]
    target_url = f"{target_base_url}/{path}"

    # Forward the original headers (especially Authorization), excluding ones
    # that shouldn't be forwarded as-is (host is specific to this hop)
    forwarded_headers = dict(request.headers)
    forwarded_headers.pop("host", None)

    body = await request.body()

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                params=request.query_params,
                headers=forwarded_headers,
                content=body,
                timeout=10.0
            )
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail=f"Service '{service}' is unavailable")

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("content-type")
    )