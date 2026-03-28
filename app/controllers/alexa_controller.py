import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from pydantic import BaseModel, Field

from app.core.config import settings
from app.database.session import get_db
from app.repositories.product_repository import ProductRepository
from app.schemas.consumption_schema import ConsumptionCreate
from app.schemas.product_schema import ProductCreate
from app.services.alert_service import AlertService
from app.services.consumption_service import ConsumptionService
from app.services.inventory_service import InventoryService


class AlexaProductAdd(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=20)
    minimum_quantity: float | None = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alexa", tags=["Alexa"])


def verify_api_key(request: Request) -> None:
    api_key = request.headers.get("X-API-Key")
    if api_key != settings.alexa_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


@router.post("/consume")
def alexa_consume(data: ConsumptionCreate, db: Session = Depends(get_db), _: None = Depends(verify_api_key)) -> dict:
    try:
        consumption = ConsumptionService(db).register(data)
        alert = AlertService(db).check_low_stock(data.product_name)
        return {
            "success": True,
            "quantity": consumption.quantity,
            "unit": consumption.unit,
            "alert": alert,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/products")
def alexa_add_product(data: AlexaProductAdd, db: Session = Depends(get_db), _: None = Depends(verify_api_key)) -> dict:
    min_qty = data.minimum_quantity
    if min_qty is None:
        existing = ProductRepository(db).get_by_name(data.name)
        if existing:
            min_qty = existing.minimum_quantity
        else:
            min_qty = round(data.quantity * 0.25, 2)

    product_data = ProductCreate(
        name=data.name,
        quantity=data.quantity,
        unit=data.unit,
        minimum_quantity=min_qty,
    )
    product, created = InventoryService(db).add_product(product_data)
    return {
        "success": True,
        "name": product.name,
        "quantity": product.quantity,
        "unit": product.unit,
        "minimum_quantity": product.minimum_quantity,
        "created": created,
    }


@router.get("/products/{name}")
def alexa_get_product(name: str, db: Session = Depends(get_db), _: None = Depends(verify_api_key)) -> dict:
    try:
        product = InventoryService(db).get_product_by_name(name)
        return {
            "success": True,
            "name": product.name,
            "quantity": product.quantity,
            "unit": product.unit,
            "is_low_stock": product.is_low_stock,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/stock")
def alexa_stock(db: Session = Depends(get_db), _: None = Depends(verify_api_key)) -> dict:
    products = InventoryService(db).get_all_products()
    items = []
    low_stock_items = []
    for p in products:
        item = {
            "name": p.name,
            "quantity": p.quantity,
            "unit": p.unit,
            "minimum_quantity": p.minimum_quantity,
            "is_low_stock": p.is_low_stock,
        }
        items.append(item)
        if p.is_low_stock:
            low_stock_items.append(item)
    return {
        "items": items,
        "low_stock_items": low_stock_items,
        "total": len(items),
        "total_low_stock": len(low_stock_items),
    }


@router.get("/alerts")
def alexa_alerts(db: Session = Depends(get_db), _: None = Depends(verify_api_key)) -> list[str]:
    return AlertService(db).get_all_low_stock_alerts()
