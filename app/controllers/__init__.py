from app.controllers.inventory_controller import router as inventory_router
from app.controllers.telegram_controller import router as telegram_router

__all__ = ["inventory_router", "telegram_router"]
