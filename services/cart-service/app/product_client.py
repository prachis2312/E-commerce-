import httpx
import os
from dotenv import load_dotenv

load_dotenv()

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8002")


async def get_product(product_id: int):
    """
    Calls product-service to fetch a product's details.
    Returns the product dict if found, or None if it doesn't exist.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=5.0)
            if response.status_code == 200:
                return response.json()
            return None
        except httpx.RequestError:
            # product-service is unreachable (down, network issue, etc.)
            return None