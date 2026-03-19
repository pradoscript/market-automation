import asyncio
import logging

from telegram.ext import Application, CommandHandler

from app.core.config import settings
from app.telegram.handlers import cmd_add, cmd_estoque, cmd_use

logger = logging.getLogger(__name__)


def build_application() -> Application:
    """Constrói a aplicação do bot com todos os handlers registrados."""
    app = Application.builder().token(settings.telegram_token).build()

    # Comandos
    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("use", cmd_use))
    app.add_handler(CommandHandler("estoque", cmd_estoque))

    logger.info("Telegram bot handlers registered")
    return app


async def _run_bot() -> None:
    """Executa o bot usando a API async direta, sem signal handlers (seguro em threads)."""
    application = build_application()
    logger.info("Starting Telegram bot (polling)...")

    async with application:
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()  # mantém rodando indefinidamente


def start_bot() -> None:
    """Inicia o bot em modo polling (bloqueante — rodar em thread separada)."""
    if not settings.telegram_token:
        logger.warning("TELEGRAM_TOKEN not set — bot will not start")
        return

    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_bot())
    finally:
        loop.close()
