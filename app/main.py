import logging
import threading

from fastapi import FastAPI
from sqlalchemy import text

from app.controllers import alerts_router, inventory_router, telegram_router
from app.core.config import settings
from app.database.session import engine
from app.scheduler import start_scheduler
from app.telegram.bot import start_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, debug=settings.debug)


@app.on_event("startup")
def on_startup() -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Database connection established")

    bot_thread = threading.Thread(target=start_bot, daemon=True, name="telegram-bot")
    bot_thread.start()
    logger.info("Telegram bot thread started")

    start_scheduler()


app.include_router(inventory_router)
app.include_router(telegram_router)
app.include_router(alerts_router)


@app.get("/health")
def health_check() -> dict:
    logger.info("Health check called")
    return {"status": "ok", "app": settings.app_name}
