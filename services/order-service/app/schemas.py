from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models import OrderStatus, PaymentStatus


class BuyNowRequest(BaseModel):
    product_id: int
    quantity: int = 1
    payment_method: str = "card"


class CheckoutRequest(BaseModel):
    payment_method: str = "card"


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    price_at_order: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: OrderStatus
    payment_status: PaymentStatus
    payment_method: Optional[str]
    total_amount: float
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: OrderStatus