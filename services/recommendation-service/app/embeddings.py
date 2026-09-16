from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from app.models import ProductEmbedding
from app.service_clients import get_all_products
import hashlib

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


def _hash_text(text: str) -> str:
    """Produces a short, deterministic fingerprint of the product's text,
    so we can detect whether it's changed since the last embedding run
    without comparing the full text every time."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def refresh_embeddings(db: Session) -> int:
    """
    Fetches all products, computes embeddings ONLY for those that are new
    or whose text has changed since the last run (detected via a content
    hash) — skipping the expensive model.encode() call entirely for
    unchanged products. Returns count of embeddings actually processed
    (i.e., newly computed), not the total product count.
    """
    model = get_model()
    products = await get_all_products()

    existing = {pe.product_id: pe for pe in db.query(ProductEmbedding).all()}

    processed = 0
    for product in products:
        text = build_product_text(product)
        new_hash = _hash_text(text)

        existing_record = existing.get(product["id"])

        # Skip re-encoding if this product already has an embedding
        # AND its text hasn't changed since that embedding was computed.
        if existing_record and existing_record.text_hash == new_hash:
            continue

        vector = model.encode(text).tolist()  # only runs for new/changed products now

        if existing_record:
            existing_record.embedding = vector
            existing_record.text_hash = new_hash
        else:
            new_embedding = ProductEmbedding(
                product_id=product["id"],
                embedding=vector,
                text_hash=new_hash
            )
            db.add(new_embedding)

        processed += 1

    db.commit()
    return processed