import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.consumption_schema import ConsumptionCreate, ConsumptionResponse
from app.services.alert_service import AlertService
from app.services.consumption_service import ConsumptionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consume", tags=["Consumption"])


class ConsumeResponse(ConsumptionResponse):
    alert: str | None = None


@router.post("/", response_model=ConsumeResponse, status_code=status.HTTP_201_CREATED)
def consume_product(data: ConsumptionCreate, db: Session = Depends(get_db)) -> ConsumeResponse:
    try:
        consumption = ConsumptionService(db).register(data)
        alert = AlertService(db).check_low_stock(data.product_name)

        return ConsumeResponse(
            id=consumption.id,
            product_id=consumption.product_id,
            quantity=consumption.quantity,
            unit=consumption.unit,
            created_at=consumption.created_at,
            alert=alert,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
