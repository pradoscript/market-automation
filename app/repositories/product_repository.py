import logging

from sqlalchemy.orm import Session

from app.models.product_model import Product

logger = logging.getLogger(__name__)


class ProductRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_all(self) -> list[Product]:
        return self._db.query(Product).all()

    def get_by_id(self, product_id: int) -> Product | None:
        return self._db.query(Product).filter(Product.id == product_id).first()

    def get_by_name(self, name: str) -> Product | None:
        return (
            self._db.query(Product)
            .filter(Product.name.ilike(name))
            .first()
        )

    def create(self, product: Product) -> Product:
        self._db.add(product)
        self._db.commit()
        self._db.refresh(product)
        logger.info("Product created: %s", product.name)
        return product

    def update(self, product: Product) -> Product:
        self._db.commit()
        self._db.refresh(product)
        logger.info("Product updated: %s (qty=%.2f %s)", product.name, product.quantity, product.unit)
        return product

    def delete(self, product: Product) -> None:
        self._db.delete(product)
        self._db.commit()
        logger.info("Product deleted: %s", product.name)
