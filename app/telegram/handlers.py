import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.database.session import SessionLocal
from app.services.alert_service import AlertService
from app.services.consumption_service import ConsumptionService
from app.services.inventory_service import InventoryService
from app.schemas.consumption_schema import ConsumptionCreate
from app.schemas.product_schema import ProductCreate
from app.utils.message_parser import parse_consumption_message

logger = logging.getLogger(__name__)


async def handle_consumption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa mensagens naturais de consumo.

    Exemplos:
        "consumi 1kg de frango"
        "usei 500ml de leite"
        "comi 2 ovos"
    """
    text = update.message.text.strip()
    parsed = parse_consumption_message(text)

    if not parsed:
        await update.message.reply_text(
            "Não entendi. Tente algo como:\n"
            "• consumi 1kg de frango\n"
            "• usei 500ml de leite\n"
            "• comi 2 ovos"
        )
        return

    db = SessionLocal()
    try:
        consumption = ConsumptionService(db).register(
            ConsumptionCreate(
                product_name=parsed.product_name,
                quantity=parsed.quantity,
                unit=parsed.unit,
            )
        )
        alert = AlertService(db).check_low_stock(parsed.product_name)

        reply = (
            f"✅ Registrado: {parsed.quantity}{parsed.unit} de {parsed.product_name}."
        )
        if alert:
            reply += f"\n\n{alert}"

        await update.message.reply_text(reply)
        logger.info("Consumption via Telegram: %s", text)

    except ValueError as e:
        await update.message.reply_text(f"❌ Erro: {e}")
        logger.warning("Consumption error via Telegram: %s | input: %s", e, text)
    finally:
        db.close()


async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/add <nome> <quantidade> <unidade> <minimo>

    Exemplo:
        /add frango 2 kg 0.5
    """
    args = context.args
    if not args or len(args) < 4:
        await update.message.reply_text(
            "Uso: /add <nome> <quantidade> <unidade> <minimo>\n"
            "Exemplo: /add frango 2 kg 0.5"
        )
        return

    name = args[0]
    try:
        quantity = float(args[1].replace(",", "."))
        unit = args[2]
        minimum_quantity = float(args[3].replace(",", "."))
    except ValueError:
        await update.message.reply_text(
            "Quantidade e mínimo devem ser números. Ex: /add frango 2 kg 0.5"
        )
        return

    db = SessionLocal()
    try:
        product = InventoryService(db).add_product(
            ProductCreate(
                name=name,
                quantity=quantity,
                unit=unit,
                minimum_quantity=minimum_quantity,
            )
        )
        await update.message.reply_text(
            f"✅ Produto adicionado!\n"
            f"📦 {product.name}: {product.quantity}{product.unit} "
            f"(mínimo: {product.minimum_quantity}{product.unit})"
        )
    except ValueError as e:
        await update.message.reply_text(f"❌ Erro: {e}")
    finally:
        db.close()


async def cmd_estoque(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/estoque — lista todos os produtos com status de estoque."""
    db = SessionLocal()
    try:
        products = InventoryService(db).get_all_products()

        if not products:
            await update.message.reply_text("Estoque vazio. Use /add para cadastrar produtos.")
            return

        lines = ["📦 *Estoque atual:*\n"]
        for p in products:
            status = "⚠️" if p.is_low_stock else "✅"
            lines.append(f"{status} *{p.name}*: {p.quantity}{p.unit} (mín: {p.minimum_quantity}{p.unit})")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    finally:
        db.close()
