import logging

from sqlalchemy.orm import Session

from app.models.product_model import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product_schema import ProductCreate, ProductResponse

logger = logging.getLogger(__name__)


class InventoryService:
    def __init__(self, db: Session) -> None:
        self._repo = ProductRepository(db)

    def add_product(self, data: ProductCreate) -> tuple[ProductResponse, bool]:
        """Retorna (produto, criado) onde criado=True se novo, False se atualizado."""
        existing = self._repo.get_by_name(data.name)
        if existing:
            existing.quantity = round(existing.quantity + data.quantity, 4)
            existing.minimum_quantity = data.minimum_quantity
            saved = self._repo.update(existing)
            logger.info("Product quantity updated: %s (+%.2f%s)", saved.name, data.quantity, data.unit)
            return self._to_response(saved), False

        product = Product(
            name=data.name,
            quantity=data.quantity,
            unit=data.unit,
            minimum_quantity=data.minimum_quantity,
        )
        saved = self._repo.create(product)
        logger.info("Product added to inventory: %s", saved.name)
        return self._to_response(saved), True

    def get_all_products(self) -> list[ProductResponse]:
        products = self._repo.get_all()
        return [self._to_response(p) for p in products]

    def get_product_by_name(self, name: str) -> ProductResponse:
        product = self._repo.get_by_name(name)
        if not product:
            raise ValueError(f"Produto '{name}' não encontrado no estoque.")
        return self._to_response(product)

    def _to_response(self, product: Product) -> ProductResponse:
        response = ProductResponse.model_validate(product)
        response.is_low_stock = product.quantity <= product.minimum_quantity
        return response
