import logging

from sqlalchemy.orm import Session

from app.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


class AlertService:
    def __init__(self, db: Session) -> None:
        self._repo = ProductRepository(db)

    def check_low_stock(self, product_name: str) -> str | None:
        product = self._repo.get_by_name(product_name)
        if not product:
            return None

        if product.quantity <= product.minimum_quantity:
            message = (
                f"⚠️ {product.name} está acabando. "
                f"Restam apenas {product.quantity}{product.unit} "
                f"(mínimo: {product.minimum_quantity}{product.unit})."
            )
            logger.warning("Low stock alert: %s", message)
            return message

        return None

    def get_all_low_stock_alerts(self) -> list[str]:
        products = self._repo.get_all()
        alerts = []
        for product in products:
            if product.quantity <= product.minimum_quantity:
                alerts.append(
                    f"⚠️ {product.name}: {product.quantity}{product.unit} "
                    f"(mínimo: {product.minimum_quantity}{product.unit})"
                )
        return alerts
