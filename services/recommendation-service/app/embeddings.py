from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from app.models import ProductEmbedding
from app.service_clients import get_all_products

# Loaded once at module import time - reused across all requests
_model = None

def get_model():
    global _model
    if _model is None:
        print("Loading sentence-transformer model (first time only)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("Model loaded.")
    return _model


def build_product_text(product: dict) -> str:
    """Combines relevant product fields into one string for embedding."""
    category_name = product.get("category", {}).get("name", "") if product.get("category") else ""
    return f"{product['name']}. {product.get('description', '')}. Category: {category_name}."


async def refresh_embeddings(db: Session) -> int:
    """
    Fetches all products, computes embeddings for any that are new or missing,
    and stores/updates them in the database. Returns count of embeddings processed.
    """
    model = get_model()
    products = await get_all_products()

    existing = {pe.product_id: pe for pe in db.query(ProductEmbedding).all()}

    processed = 0
    for product in products:
        text = build_product_text(product)
        vector = model.encode(text).tolist()  # numpy array -> plain Python list for JSON storage

        if product["id"] in existing:
            existing[product["id"]].embedding = vector
        else:
            new_embedding = ProductEmbedding(product_id=product["id"], embedding=vector)
            db.add(new_embedding)

        processed += 1

    db.commit()
    return processed