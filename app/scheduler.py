import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.database.session import SessionLocal
from app.services.alert_service import AlertService
from app.telegram.alert_sender import send_alert

logger = logging.getLogger(__name__)


def _daily_stock_report() -> None:
    if not settings.telegram_chat_id:
        logger.warning("TELEGRAM_CHAT_ID not set — daily report skipped")
        return

    db = SessionLocal()
    try:
        alerts = AlertService(db).get_all_low_stock_alerts()
    finally:
        db.close()

    if alerts:
        items = "\n".join(alerts)
        message = (
            "📋 *Relatório diário de estoque* — 22:15\n\n"
            "Os seguintes itens precisam de atenção:\n\n"
            f"{items}"
        )
    else:
        message = (
            "✅ *Relatório diário de estoque* — 22:15\n\n"
            "Tudo certo por aqui! Nenhum item abaixo do mínimo."
        )

    asyncio.run(send_alert(settings.telegram_chat_id, message))
    logger.info("Daily stock report sent")


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(
        _daily_stock_report,
        trigger=CronTrigger(hour=23, minute=55, timezone="America/Sao_Paulo"),
        id="daily_stock_report",
        name="Daily stock report at 23:55",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — daily report at 22:15 (America/Sao_Paulo)")
    return scheduler
