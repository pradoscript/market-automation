import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.product_schema import ProductCreate, ProductResponse
from app.services.alert_service import AlertService
from app.services.inventory_service import InventoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["Inventory"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: Session = Depends(get_db)) -> ProductResponse:
    product, _ = InventoryService(db).add_product(data)
    return product


@router.get("/", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)) -> list[ProductResponse]:
    return InventoryService(db).get_all_products()


@router.get("/{name}", response_model=ProductResponse)
def get_product(name: str, db: Session = Depends(get_db)) -> ProductResponse:
    try:
        return InventoryService(db).get_product_by_name(name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


alerts_router = APIRouter(prefix="/alerts", tags=["Alerts"])


@alerts_router.get("/", response_model=list[str])
def list_low_stock_alerts(db: Session = Depends(get_db)) -> list[str]:
    return AlertService(db).get_all_low_stock_alerts()
