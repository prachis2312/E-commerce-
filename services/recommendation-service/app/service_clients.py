import httpx
import os
from dotenv import load_dotenv

load_dotenv()

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8002")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8004")


async def get_all_products():
    """Fetch all products from product-service, handling pagination."""
    all_products = []
    skip = 0
    limit = 100
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(
                    f"{PRODUCT_SERVICE_URL}/products",
                    params={"skip": skip, "limit": limit},
                    timeout=10.0
                )
                if response.status_code != 200:
                    break
                batch = response.json()
                if not batch:
                    break
                all_products.extend(batch)
                if len(batch) < limit:
                    break
                skip += limit
            except httpx.RequestError:
                break
    return all_products


async def get_product(product_id: int):
    """Fetch a single product's details from product-service."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=5.0)
            if response.status_code == 200:
                return response.json()
            return None
        except httpx.RequestError:
            return None


async def get_user_order_history(token: str):
    """Fetch a user's past orders from order-service, to build their interaction profile."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{ORDER_SERVICE_URL}/orders",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
            return []
        except httpx.RequestError:
            return []