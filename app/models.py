# app/models.py
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime
from datetime import datetime, timezone
from app.db import Base


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Numeric, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String, nullable=True)
    stock = Column(Integer, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
