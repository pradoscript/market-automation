import logging

from sqlalchemy.orm import Session

from app.models.consumption_model import Consumption

logger = logging.getLogger(__name__)


class ConsumptionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, consumption: Consumption) -> Consumption:
        self._db.add(consumption)
        self._db.commit()
        self._db.refresh(consumption)
        logger.info(
            "Consumption recorded: product_id=%d qty=%.2f %s",
            consumption.product_id,
            consumption.quantity,
            consumption.unit,
        )
        return consumption

    def get_by_product(self, product_id: int) -> list[Consumption]:
        return (
            self._db.query(Consumption)
            .filter(Consumption.product_id == product_id)
            .order_by(Consumption.created_at.desc())
            .all()
        )
