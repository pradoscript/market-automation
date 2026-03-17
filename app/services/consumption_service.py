import asyncio
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.consumption_model import Consumption
from app.repositories.consumption_repository import ConsumptionRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.consumption_schema import ConsumptionCreate, ConsumptionResponse
from app.utils.unit_converter import normalize_unit, to_base_unit

logger = logging.getLogger(__name__)


class ConsumptionService:
    def __init__(self, db: Session) -> None:
        self._product_repo = ProductRepository(db)
        self._consumption_repo = ConsumptionRepository(db)

    def register(self, data: ConsumptionCreate) -> ConsumptionResponse:
        product = self._product_repo.get_by_name(data.product_name)
        if not product:
            raise ValueError(f"Produto '{data.product_name}' não encontrado no estoque.")

        # Converte a quantidade consumida para a unidade base do produto
        quantity_in_product_unit = to_base_unit(data.quantity, data.unit, product.unit)

        if product.quantity < quantity_in_product_unit:
            raise ValueError(
                f"Estoque insuficiente. Disponível: {product.quantity}{product.unit}, "
                f"tentou consumir: {quantity_in_product_unit}{product.unit}."
            )

        product.quantity = round(product.quantity - quantity_in_product_unit, 4)
        self._product_repo.update(product)

        consumption = Consumption(
            product_id=product.id,
            quantity=data.quantity,
            unit=normalize_unit(data.unit),
        )
        saved = self._consumption_repo.create(consumption)
        logger.info(
            "Consumption registered: %s consumed %.2f%s",
            product.name,
            data.quantity,
            data.unit,
        )

        # Dispara alerta automático se estoque ficou abaixo do mínimo
        if product.quantity <= product.minimum_quantity and settings.telegram_chat_id:
            from app.telegram.alert_sender import send_alert

            alert_message = (
                f"⚠️ {product.name} está acabando. "
                f"Restam apenas {product.quantity}{product.unit} "
                f"(mínimo: {product.minimum_quantity}{product.unit})."
            )
            asyncio.run(send_alert(settings.telegram_chat_id, alert_message))

        return ConsumptionResponse.model_validate(saved)
