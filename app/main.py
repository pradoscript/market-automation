import logging

from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, debug=settings.debug)


@app.on_event("startup")
def on_startup() -> None:
    from sqlalchemy import create_engine

    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Database connection established")


@app.get("/health")
def health_check() -> dict:
    logger.info("Health check called")
    return {"status": "ok", "app": settings.app_name}
