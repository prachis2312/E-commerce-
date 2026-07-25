import httpx
import os
from dotenv import load_dotenv

load_dotenv()

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8002")
CART_SERVICE_URL = os.getenv("CART_SERVICE_URL", "http://cart-service:8003")


async def get_product(product_id: int):
    """Fetch a product's details from product-service."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=5.0)
            if response.status_code == 200:
                return response.json()
            return None
        except httpx.RequestError:
            return None


async def update_product_stock(product_id: int, new_stock_quantity: int) -> bool:
    """Decrement (or set) a product's stock via product-service."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{PRODUCT_SERVICE_URL}/products/{product_id}",
                json={"stock_quantity": new_stock_quantity},
                timeout=5.0
            )
            return response.status_code == 200
        except httpx.RequestError:
            return False


async def get_user_cart(token: str):
    """Fetch the current user's cart from cart-service, passing along their JWT."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{CART_SERVICE_URL}/cart",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
            return None
        except httpx.RequestError:
            return None


async def clear_user_cart(token: str) -> bool:
    """Clear the user's cart after successful checkout."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{CART_SERVICE_URL}/cart",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            return response.status_code == 204
        except httpx.RequestError:
            return False