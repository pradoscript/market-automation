import asyncio
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.consumption_model import Consumption
from app.repositories.consumption_repository import ConsumptionRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.subscriber_repository import SubscriberRepository
from app.schemas.consumption_schema import ConsumptionCreate, ConsumptionResponse
from app.utils.unit_converter import normalize_unit, to_base_unit

logger = logging.getLogger(__name__)


class ConsumptionService:
    def __init__(self, db: Session) -> None:
        self._product_repo = ProductRepository(db)
        self._consumption_repo = ConsumptionRepository(db)
        self._subscriber_repo = SubscriberRepository(db)

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
        product_name = product.name
        product_unit = product.unit

        consumption = Consumption(
            product_id=product.id,
            quantity=data.quantity,
            unit=normalize_unit(data.unit),
        )
        saved = self._consumption_repo.create(consumption)
        logger.info(
            "Consumption registered: %s consumed %.2f%s",
            product_name,
            data.quantity,
            data.unit,
        )

        # Remove o produto do estoque quando zerar
        if product.quantity == 0:
            self._product_repo.delete(product)
            logger.info("Product removed from stock (quantity reached zero): %s", product_name)

            chat_ids = self._subscriber_repo.get_all()
            if chat_ids:
                from app.telegram.alert_sender import send_to_all
                self._fire_alert(send_to_all(
                    chat_ids,
                    f"🗑️ {product_name} foi removido do estoque (quantidade zerada).",
                ))

            return ConsumptionResponse.model_validate(saved)

        # Salva a quantidade atualizada
        self._product_repo.update(product)

        # Dispara alerta automático se estoque ficou abaixo do mínimo
        if product.quantity <= product.minimum_quantity:
            chat_ids = self._subscriber_repo.get_all()
            if chat_ids:
                from app.telegram.alert_sender import send_to_all
                alert_message = (
                    f"⚠️ {product_name} está acabando. "
                    f"Restam apenas {product.quantity}{product_unit} "
                    f"(mínimo: {product.minimum_quantity}{product_unit})."
                )
                self._fire_alert(send_to_all(chat_ids, alert_message))

        return ConsumptionResponse.model_validate(saved)

    @staticmethod
    def _fire_alert(coro) -> None:
        """Envia alerta async de forma segura, dentro ou fora de event loop."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            asyncio.run(coro)
