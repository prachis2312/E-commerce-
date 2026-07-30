from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Order, OrderItem, OrderStatus, PaymentStatus
from app.schemas import BuyNowRequest, CheckoutRequest, OrderResponse, OrderStatusUpdate
from app.auth import get_current_user
from app.payment import process_payment
from app.service_clients import get_product, update_product_stock, get_user_cart, clear_user_cart

router = APIRouter()


async def create_order_from_items(db: Session, user_id: int, items_data: list, payment_method: str) -> Order:
    if not items_data:
        raise HTTPException(status_code=400, detail="No items to order")

    for item in items_data:
        if item["quantity"] > item["current_stock"]:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {item['product_name']}. Only {item['current_stock']} available."
            )

    total_amount = sum(item["price"] * item["quantity"] for item in items_data)
    payment_result = process_payment(total_amount, payment_method)

    if not payment_result["success"]:
        raise HTTPException(status_code=402, detail=payment_result["message"])

    new_order = Order(
        user_id=user_id,
        status=OrderStatus.confirmed,
        payment_status=PaymentStatus.paid,
        payment_method=payment_method,
        total_amount=total_amount
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    for item in items_data:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item["product_id"],
            product_name=item["product_name"],
            quantity=item["quantity"],
            price_at_order=item["price"]
        )
        db.add(order_item)
    db.commit()

    for item in items_data:
        new_stock = item["current_stock"] - item["quantity"]
        success = await update_product_stock(item["product_id"], new_stock)
        if not success:
            # Order and payment already committed at this point — we don't want to
            # roll back the whole order over a stock-sync issue, but we do want
            # this visible in logs rather than silently vanishing.
            print(f"WARNING: failed to update stock for product {item['product_id']}")

    db.refresh(new_order)
    return new_order


@router.post("/orders/buy-now", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def buy_now(
    request: BuyNowRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = await get_product(request.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    items_data = [{
        "product_id": product["id"],
        "product_name": product["name"],
        "quantity": request.quantity,
        "price": product["price"],
        "current_stock": product["stock_quantity"]
    }]

    return await create_order_from_items(db, current_user["user_id"], items_data, request.payment_method)


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def checkout(
    request: CheckoutRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart = await get_user_cart(current_user["token"])
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")

    items_data = []
    for cart_item in cart["items"]:
        product = await get_product(cart_item["product_id"])
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {cart_item['product_id']} no longer exists")
        items_data.append({
            "product_id": product["id"],
            "product_name": product["name"],
            "quantity": cart_item["quantity"],
            "price": product["price"],
            "current_stock": product["stock_quantity"]
        })

    order = await create_order_from_items(db, current_user["user_id"], items_data, request.payment_method)
    await clear_user_cart(current_user["token"])
    return order


@router.get("/orders", response_model=List[OrderResponse])
def list_orders(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Order).filter(Order.user_id == current_user["user_id"]).order_by(Order.created_at.desc()).all()


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user["user_id"]).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    update: OrderStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user["user_id"]).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = update.status
    db.commit()
    db.refresh(order)
    return order