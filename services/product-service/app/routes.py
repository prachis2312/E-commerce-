from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
import os
from app.database import get_db
from app.models import Product, Category
from app.auth import require_admin
from app.notify import notify_recommendations
from app.schemas import (
    ProductCreate, ProductUpdate, ProductResponse,
    CategoryCreate, CategoryResponse, StockUpdate,
    StockReserveRequest, StockReleaseRequest
)

router = APIRouter()

# ---- Category routes ----

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, db: Session = Depends(get_db),admin: dict = Depends(require_admin)):
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    new_category = Category(**category.model_dump())
    db.add(new_category)
    db.commit() 
    db.refresh(new_category)
    return new_category

@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

# ---- Product routes ----

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db),admin: dict = Depends(require_admin)):
    new_product = Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    background_tasks.add_task(notify_recommendations)
    return new_product

@router.get("/products", response_model=List[ProductResponse])
def list_products(
    category_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    return query.offset(skip).limit(limit).all()

@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, updates: ProductUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db),admin: dict = Depends(require_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    background_tasks.add_task(notify_recommendations)
    return product

@router.patch("/products/{product_id}/stock", response_model=ProductResponse)
def adjust_stock(
    product_id: int,
    update: StockUpdate,
    x_internal_key: str = Header(...),
    db: Session = Depends(get_db)
):
    if x_internal_key != os.getenv("INTERNAL_API_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.stock_quantity = update.stock_quantity
    db.commit()
    db.refresh(product)
    return product

@router.post("/products/{product_id}/reserve-stock")
def reserve_stock(
    product_id: int,
    request: StockReserveRequest,
    x_internal_key: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Atomically checks and decrements stock in one database transaction.
    Uses SELECT ... FOR UPDATE to lock the row, so concurrent requests
    for the same product_id are forced to wait and see the updated
    stock value, rather than racing on a stale read.
    """
    if x_internal_key != os.getenv("INTERNAL_API_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")

    product = db.query(Product).filter(Product.id == product_id).with_for_update().first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.stock_quantity < request.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Only {product.stock_quantity} units available in stock"
        )

    product.stock_quantity -= request.quantity
    db.commit()
    db.refresh(product)

    return {"success": True, "remaining_stock": product.stock_quantity}


@router.post("/products/{product_id}/release-stock")
def release_stock(
    product_id: int,
    request: StockReleaseRequest,
    x_internal_key: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Compensating action: adds quantity back to stock.
    Called when a reservation succeeded but a later step (payment)
    failed, so the reserved stock needs to be returned.
    """
    if x_internal_key != os.getenv("INTERNAL_API_KEY"):
        raise HTTPException(status_code=403, detail="Forbidden")

    product = db.query(Product).filter(Product.id == product_id).with_for_update().first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.stock_quantity += request.quantity
    db.commit()
    db.refresh(product)

    return {"success": True, "remaining_stock": product.stock_quantity}

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),admin: dict = Depends(require_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    background_tasks.add_task(notify_recommendations)
    return None