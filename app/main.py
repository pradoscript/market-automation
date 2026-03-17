import logging

from fastapi import FastAPI

from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, debug=settings.debug)


@app.get("/health")
def health_check() -> dict:
    logger.info("Health check called")
    return {"status": "ok", "app": settings.app_name}
