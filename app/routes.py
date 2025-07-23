import os
from typing import List
from datetime import datetime, timezone
from fastapi import HTTPException, Depends, Security, APIRouter, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import Product, ProductUpdate
from app.models import ProductModel
from app.messaging.events import PRODUCT_CREATED, PRODUCT_UPDATED, PRODUCT_DELETED

API_TOKEN = os.getenv("API_TOKEN")
security = HTTPBearer()
router = APIRouter()


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.scheme != "Bearer" or credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=403, detail="Accès interdit")


async def publish_event_safe(request: Request, event_type: str, data: dict):
    """Publier un événement de manière sécurisée"""
    try:
        broker = getattr(request.app.state, "broker", None)
        if broker and broker.is_connected:
            await broker.publish_event(event_type, data)
            print(f"Event published: {event_type}")
        else:
            print(
                f"Warning: Message broker not available, event {event_type} not published"
            )
    except Exception as e:
        print(f"Error publishing event {event_type}: {str(e)}")


@router.post("/products", response_model=Product)
async def create_product(
    product: Product,
    request: Request,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    try:
        db_product = ProductModel(
            **product.model_dump(exclude={"id", "created_at", "updated_at"})
        )
        db.add(db_product)
        db.commit()
        db.refresh(db_product)

        await publish_event_safe(
            request,
            PRODUCT_CREATED,
            {
                "product_id": db_product.id,
                "name": db_product.name,
                "price": float(db_product.price),
                "description": db_product.description,
                "color": db_product.color,
                "stock": db_product.stock,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        return db_product

    except Exception as e:
        db.rollback()
        print(f"Error creating product: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Erreur lors de la création du produit"
        )


@router.get("/products", response_model=List[Product])
def list_products(
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    return db.query(ProductModel).all()


@router.get("/products/{product_id}", response_model=Product)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return product


@router.put("/products/{product_id}", response_model=Product)
async def update_product(
    product_id: int,
    updated_product: ProductUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    try:
        product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Produit non trouvé")

        old_values = {
            "name": product.name,
            "price": float(product.price),
            "description": product.description,
            "color": product.color,
            "stock": product.stock,
        }

        changes = updated_product.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(product, field, value)

        db.commit()
        db.refresh(product)

        await publish_event_safe(
            request,
            PRODUCT_UPDATED,
            {
                "product_id": product.id,
                "name": product.name,
                "price": float(product.price),
                "description": product.description,
                "color": product.color,
                "stock": product.stock,
                "changes": changes,
                "old_values": old_values,
            },
        )

        return product

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error updating product: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Erreur lors de la mise à jour du produit"
        )


@router.delete("/products/{product_id}", response_model=dict)
async def delete_product(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    try:
        product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Produit non trouvé")

        product_data = {
            "product_id": product.id,
            "name": product.name,
            "price": float(product.price),
            "description": product.description,
            "color": product.color,
            "stock": product.stock,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
        }

        db.delete(product)
        db.commit()

        await publish_event_safe(request, PRODUCT_DELETED, product_data)

        return {"message": "Produit supprimé avec succès"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting product: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Erreur lors de la suppression du produit"
        )


@router.get("/health/messaging")
async def check_messaging_health(request: Request):
    """Vérifier l'état de la connexion au message broker"""
    try:
        broker = getattr(request.app.state, "broker", None)
        if broker and broker.is_connected:
            return {
                "status": "healthy",
                "message_broker": "connected",
                "service": broker.service_name,
            }
        else:
            return {
                "status": "warning",
                "message_broker": "disconnected",
                "message": "API fonctionne mais les événements ne sont pas publiés",
            }
    except Exception as e:
        return {"status": "error", "message_broker": "error", "error": str(e)}
