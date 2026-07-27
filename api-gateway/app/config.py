import os
from dotenv import load_dotenv

load_dotenv()

SERVICE_ROUTES = {
    "users": os.getenv("USER_SERVICE_URL", "http://user-service:8001"),
    "products": os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8002"),
    "cart": os.getenv("CART_SERVICE_URL", "http://cart-service:8003"),
    "orders": os.getenv("ORDER_SERVICE_URL", "http://order-service:8004"),
    "recommendations": os.getenv("RECOMMENDATION_SERVICE_URL", "http://recommendation-service:8005"),
}