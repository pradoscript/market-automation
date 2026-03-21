import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database.session import SessionLocal
from app.repositories.subscriber_repository import SubscriberRepository
from app.services.alert_service import AlertService
from app.telegram.alert_sender import send_to_all

logger = logging.getLogger(__name__)


def _daily_stock_report() -> None:
    db = SessionLocal()
    try:
        alerts = AlertService(db).get_all_low_stock_alerts()
        chat_ids = SubscriberRepository(db).get_all()
    finally:
        db.close()

    if not chat_ids:
        logger.warning("No subscribers — daily report skipped")
        return

    if alerts:
        items = "\n".join(alerts)
        message = (
            "📋 *Relatório diário de estoque* — 23:55\n\n"
            "Os seguintes itens precisam de atenção:\n\n"
            f"{items}"
        )
    else:
        message = (
            "✅ *Relatório diário de estoque* — 23:55\n\n"
            "Tudo certo por aqui! Nenhum item abaixo do mínimo."
        )

    asyncio.run(send_to_all(chat_ids, message))
    logger.info("Daily stock report sent to %d subscribers", len(chat_ids))


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
