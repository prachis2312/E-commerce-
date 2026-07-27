from pydantic import BaseModel
from typing import List


class SimilarProduct(BaseModel):
    product_id: int
    name: str
    price: float
    image_url: str | None = None
    similarity_score: float


class RecommendationResponse(BaseModel):
    recommendations: List[SimilarProduct]
    source: str  # "content_based_similar" | "user_history" | "cold_start_fallback"


class RefreshResponse(BaseModel):
    embeddings_processed: int
    message: str