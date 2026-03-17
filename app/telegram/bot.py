import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.core.config import settings
from app.telegram.handlers import cmd_add, cmd_estoque, handle_consumption

logger = logging.getLogger(__name__)


def build_application() -> Application:
    """Constrói a aplicação do bot com todos os handlers registrados."""
    app = Application.builder().token(settings.telegram_token).build()

    # Comandos
    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("estoque", cmd_estoque))

    # Mensagens de texto (consumo em linguagem natural)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_consumption)
    )

    logger.info("Telegram bot handlers registered")
    return app


def start_bot() -> None:
    """Inicia o bot em modo polling (bloqueante — rodar em thread separada)."""
    if not settings.telegram_token:
        logger.warning("TELEGRAM_TOKEN not set — bot will not start")
        return

    application = build_application()
    logger.info("Starting Telegram bot (polling)...")
    application.run_polling(drop_pending_updates=True)
