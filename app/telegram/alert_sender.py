import logging

from telegram import Bot
from telegram.error import TelegramError

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_alert(chat_id: int | str, message: str) -> None:
    """Envia uma mensagem de alerta para um chat específico."""
    if not settings.telegram_token:
        logger.warning("TELEGRAM_TOKEN not set — alert not sent: %s", message)
        return

    try:
        bot = Bot(token=settings.telegram_token)
        await bot.send_message(chat_id=chat_id, text=message)
        logger.info("Alert sent to chat_id=%s: %s", chat_id, message)
    except TelegramError as e:
        logger.error("Failed to send alert to chat_id=%s: %s", chat_id, e)


async def send_to_all(chat_ids: list[int], message: str) -> None:
    """Envia uma mensagem para todos os subscribers cadastrados."""
    if not settings.telegram_token or not chat_ids:
        return

    bot = Bot(token=settings.telegram_token)
    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id=chat_id, text=message)
            logger.info("Alert sent to chat_id=%s", chat_id)
        except TelegramError as e:
            logger.error("Failed to send alert to chat_id=%s: %s", chat_id, e)
