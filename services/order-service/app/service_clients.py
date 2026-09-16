import httpx
import os
from dotenv import load_dotenv
import logging


load_dotenv()
logger = logging.getLogger(__name__);

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8002")
CART_SERVICE_URL = os.getenv("CART_SERVICE_URL", "http://cart-service:8003")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")


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


async def reserve_stock(product_id: int, quantity: int) -> dict:
    """
    Atomically reserves (decrements) stock via product-service's
    internal-key-protected endpoint. Returns a dict indicating success
    and, on failure, the reason (so the caller can surface a clean error
    rather than a generic one).
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{PRODUCT_SERVICE_URL}/products/{product_id}/reserve-stock",
                json={"quantity": quantity},
                headers={"x-internal-key": INTERNAL_API_KEY},
                timeout=5.0
            )
            if response.status_code == 200:
                return {"success": True}
            else:
                # product-service returns a 400 with a clear detail message
                # when there isn't enough stock — surface that instead of
                # a generic failure.
                detail = response.json().get("detail", "Could not reserve stock")
                return {"success": False, "detail": detail}
        except httpx.RequestError as e:
            return {"success": False, "detail": f"Could not reach product-service: {e}"}


async def release_stock(product_id: int, quantity: int) -> bool:
    """
    Compensating action: releases previously reserved stock back to
    product-service. Used when a reservation succeeded but a later step
    (payment) failed.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{PRODUCT_SERVICE_URL}/products/{product_id}/release-stock",
                json={"quantity": quantity},
                headers={"x-internal-key": INTERNAL_API_KEY},
                timeout=5.0
            )
            return response.status_code == 200
        except httpx.RequestError as e:
            logger.warning(f"Failed to release stock for product {product_id}: {e}")
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