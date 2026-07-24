from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cart, CartItem
from app.schemas import CartItemCreate, CartItemUpdate, CartResponse, CartItemResponse
from app.auth import get_current_user
from app.product_client import get_product

router = APIRouter()


def get_or_create_cart(db: Session, user_id: int) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


async def build_cart_response(cart: Cart) -> CartResponse:
    items_response = []
    total = 0.0
    for item in cart.items:
        product = await get_product(item.product_id)
        product_name = product["name"] if product else "Unknown Product"
        items_response.append(CartItemResponse(
            id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_add=item.price_at_add,
            product_name=product_name
        ))
        total += item.price_at_add * item.quantity

    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        items=items_response,
        total=round(total, 2),
        created_at=cart.created_at,
        updated_at=cart.updated_at
    )


@router.get("/cart", response_model=CartResponse)
async def view_cart(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, current_user["user_id"])
    return await build_cart_response(cart)


@router.post("/cart/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def add_item(
    item: CartItemCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    product = await get_product(item.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    cart = get_or_create_cart(db, current_user["user_id"])

    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == item.product_id
    ).first()

    requested_quantity = (existing_item.quantity if existing_item else 0) + item.quantity

    if requested_quantity > product["stock_quantity"]:
        raise HTTPException(
            status_code=400,
            detail=f"Only {product['stock_quantity']} units available in stock"
        )

    if existing_item:
        existing_item.quantity += item.quantity
    else:
        new_item = CartItem(
            cart_id=cart.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_add=product["price"]
        )
        db.add(new_item)

    db.commit()
    db.refresh(cart)
    return await build_cart_response(cart)


@router.put("/cart/items/{item_id}", response_model=CartResponse)
async def update_item(
    item_id: int,
    update: CartItemUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart = get_or_create_cart(db, current_user["user_id"])
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if update.quantity <= 0:
        db.delete(item)
    else:
        product = await get_product(item.product_id)
        if product and update.quantity > product["stock_quantity"]:
            raise HTTPException(
                status_code=400,
                detail=f"Only {product['stock_quantity']} units available in stock"
            )
        item.quantity = update.quantity

    db.commit()
    db.refresh(cart)
    return await build_cart_response(cart)


@router.delete("/cart/items/{item_id}", response_model=CartResponse)
async def remove_item(
    item_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart = get_or_create_cart(db, current_user["user_id"])
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    db.delete(item)
    db.commit()
    db.refresh(cart)
    return await build_cart_response(cart)


@router.delete("/cart", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, current_user["user_id"])
    for item in cart.items:
        db.delete(item)
    db.commit()
    return None