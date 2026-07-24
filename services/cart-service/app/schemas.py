from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemUpdate(BaseModel):
    quantity: int

class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price_at_add: float
    product_name: Optional[str] = None  # enriched at response time, not stored

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse]
    total: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True