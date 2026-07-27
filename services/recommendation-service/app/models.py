from sqlalchemy import Column, Integer, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class ProductEmbedding(Base):
    __tablename__ = "product_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, unique=True, nullable=False, index=True)  # no FK - different service's DB
    embedding = Column(JSON, nullable=False)  # stored as a list of floats

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())