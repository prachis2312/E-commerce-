from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ProductEmbedding
from app.schemas import RecommendationResponse, SimilarProduct, RefreshResponse
from app.embeddings import refresh_embeddings
from app import similarity
from app.similarity import (
    load_cache_from_db, get_similar_products, get_recommendations_for_vector,
    build_user_profile_vector
)
from app.service_clients import get_product, get_user_order_history, get_all_products
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
bearer_scheme = HTTPBearer()


@router.post("/recommendations/refresh", response_model=RefreshResponse)
async def refresh(db: Session = Depends(get_db)):
    count = await refresh_embeddings(db)
    load_cache_from_db(db)  # reload the in-memory cache after updating
    return RefreshResponse(embeddings_processed=count, message="Embeddings refreshed successfully")


@router.get("/recommendations/similar/{product_id}", response_model=RecommendationResponse)
async def similar_products(product_id: int, top_n: int = 5):
    if not similarity._embedding_cache:
        raise HTTPException(status_code=503, detail="Embeddings not loaded yet. Call /recommendations/refresh first.")

    results = get_similar_products(product_id, top_n)
    if not results:
        raise HTTPException(status_code=404, detail="Product not found or has no embedding")

    recommendations = []
    for pid, score in results:
        product = await get_product(pid)
        if product:
            recommendations.append(SimilarProduct(
                product_id=pid,
                name=product["name"],
                price=product["price"],
                image_url=product.get("image_url"),
                similarity_score=round(float(score), 4)
            ))

    return RecommendationResponse(recommendations=recommendations, source="content_based_similar")


@router.get("/recommendations/for-user/{user_id}", response_model=RecommendationResponse)
async def recommendations_for_user(
    user_id: int,
    top_n: int = 5,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    if not similarity._embedding_cache:
        raise HTTPException(status_code=503, detail="Embeddings not loaded yet. Call /recommendations/refresh first.")

    token = credentials.credentials
    orders = await get_user_order_history(token)

    purchased_product_ids = []
    for order in orders:
        for item in order.get("items", []):
            purchased_product_ids.append(item["product_id"])

    if not purchased_product_ids:
        # Cold start: no history, fall back to a few generally available products
        all_products = await get_all_products()
        fallback = all_products[:top_n]
        recommendations = [
            SimilarProduct(
                product_id=p["id"], name=p["name"], price=p["price"],
                image_url=p.get("image_url"), similarity_score=0.0
            ) for p in fallback
        ]
        return RecommendationResponse(recommendations=recommendations, source="cold_start_fallback")

    user_vector = build_user_profile_vector(purchased_product_ids)
    if user_vector is None:
        raise HTTPException(status_code=500, detail="Could not build user profile")

    results = get_recommendations_for_vector(user_vector, exclude_ids=set(purchased_product_ids), top_n=top_n)

    recommendations = []
    for pid, score in results:
        product = await get_product(pid)
        if product:
            recommendations.append(SimilarProduct(
                product_id=pid, name=product["name"], price=product["price"],
                image_url=product.get("image_url"), similarity_score=round(float(score), 4)
            ))

    return RecommendationResponse(recommendations=recommendations, source="user_history")