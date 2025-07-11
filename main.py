from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from db import SessionLocal, Base, engine
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime
from dotenv import load_dotenv
import os
import uvicorn

load_dotenv()

# Authentification par token
security = HTTPBearer()
API_TOKEN = os.getenv("API_TOKEN")


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.scheme != "Bearer" or credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=403, detail="Accès interdit")


app = FastAPI(title="API Produits")


# SQLAlchemy Model
class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Numeric, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String, nullable=True)
    stock = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True)


# Création des tables si elles n'existent pas déjà
Base.metadata.create_all(bind=engine)


# Pydantic Models
class Product(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    name: str
    price: float
    description: Optional[str] = None
    color: Optional[str] = None
    stock: Optional[int] = None
    created_at: Optional[datetime] = None


class ProductUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    color: Optional[str] = None
    stock: Optional[int] = None
    created_at: Optional[datetime] = None


# Dépendance pour la base
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Routes
@app.post("/products", response_model=Product)
def create_product(
    product: Product,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    db_product = ProductModel(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/products", response_model=List[Product])
def list_products(
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    return db.query(ProductModel).all()


@app.get("/products/{product_id}", response_model=Product)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product


@app.put("/products/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    updated_product: ProductUpdate,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    for field, value in updated_product.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@app.delete("/products/{product_id}", response_model=dict)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token)
):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    db.delete(product)
    db.commit()
    return {"message": "Produit supprimé avec succès"}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
