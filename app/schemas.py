# app/schemas.py
from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ProductBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    price: float
    description: Optional[str] = None
    color: Optional[str] = None
    stock: Optional[str] = None


class ProductUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    color: Optional[str] = None
    stock: Optional[str] = None


class Product(ProductBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
