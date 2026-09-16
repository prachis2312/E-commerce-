from sqlalchemy import Column, Integer, JSON, DateTime, String
from sqlalchemy.sql import func
from app.database import Base

class ProductEmbedding(Base):
    __tablename__ = "product_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, unique=True, nullable=False, index=True)
    embedding = Column(JSON, nullable=False)
    text_hash = Column(String, nullable=True)  # NEW — lets us detect unchanged product text

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())