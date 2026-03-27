import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.schemas.consumption_schema import ConsumptionCreate
from app.schemas.product_schema import ProductCreate
from app.services.alert_service import AlertService
from app.services.consumption_service import ConsumptionService
from app.services.inventory_service import InventoryService

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
def alexa_add_product(data: ProductCreate, db: Session = Depends(get_db), _: None = Depends(verify_api_key)) -> dict:
    product, created = InventoryService(db).add_product(data)
    return {
        "success": True,
        "name": product.name,
        "quantity": product.quantity,
        "unit": product.unit,
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


@router.get("/alerts")
def alexa_alerts(db: Session = Depends(get_db), _: None = Depends(verify_api_key)) -> list[str]:
    return AlertService(db).get_all_low_stock_alerts()
