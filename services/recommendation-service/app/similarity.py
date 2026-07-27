import numpy as np
from sqlalchemy.orm import Session
from app.models import ProductEmbedding

# In-memory cache, loaded from DB at startup and refreshed on demand
_embedding_cache = {}  # product_id -> numpy array


def load_cache_from_db(db: Session):
    """Loads all stored embeddings from Postgres into memory for fast similarity computation."""
    global _embedding_cache
    all_embeddings = db.query(ProductEmbedding).all()
    _embedding_cache = {
        pe.product_id: np.array(pe.embedding) for pe in all_embeddings
    }
    print(f"Loaded {len(_embedding_cache)} product embeddings into memory.")


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Standard cosine similarity between two vectors."""
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def get_similar_products(product_id: int, top_n: int = 5) -> list:
    """Returns top_n product_ids most similar to the given product, excluding itself."""
    if product_id not in _embedding_cache:
        return []

    target_vector = _embedding_cache[product_id]
    scores = []

    for other_id, other_vector in _embedding_cache.items():
        if other_id == product_id:
            continue
        score = cosine_similarity(target_vector, other_vector)
        scores.append((other_id, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]


MIN_SIMILARITY_THRESHOLD = 0.3

def get_recommendations_for_vector(query_vector, exclude_ids, top_n=5, min_score=MIN_SIMILARITY_THRESHOLD):
    scores = []
    for product_id, vector in _embedding_cache.items():
        if product_id in exclude_ids:
            continue
        score = cosine_similarity(query_vector, vector)
        if score >= min_score:
            scores.append((product_id, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_n]

def build_user_profile_vector(product_ids: list) -> np.ndarray:
    """Averages the embeddings of a list of products to build a single 'user preference' vector."""
    vectors = [_embedding_cache[pid] for pid in product_ids if pid in _embedding_cache]
    if not vectors:
        return None
    return np.mean(vectors, axis=0)