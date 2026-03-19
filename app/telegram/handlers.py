import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from app.database.session import SessionLocal
from app.schemas.consumption_schema import ConsumptionCreate
from app.schemas.product_schema import ProductCreate
from app.services.alert_service import AlertService
from app.services.consumption_service import ConsumptionService
from app.services.inventory_service import InventoryService
from app.utils.unit_converter import normalize_unit

logger = logging.getLogger(__name__)

# Regex para extrair quantidade e unidade juntos, ex: "2kg", "500g", "1.5l", "0,5kg"
_QTY_UNIT_RE = re.compile(r"^(\d+(?:[.,]\d+)?)\s*([a-zA-Z]+)$")


def _parse_qty_unit(token: str) -> tuple[float, str]:
    """Extrai quantidade e unidade de um token como '2kg' ou '500g'.

    Raises:
        ValueError: formato inválido.
    """
    match = _QTY_UNIT_RE.match(token.strip())
    if not match:
        raise ValueError(
            f"'{token}' não é um formato válido. Use número+unidade, ex: 2kg, 500g, 1.5l"
        )
    quantity = float(match.group(1).replace(",", "."))
    unit = normalize_unit(match.group(2))
    return quantity, unit


async def cmd_use(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/use <produto> <quantidade><unidade>

    O nome do produto pode ter espaços. O último argumento é sempre qty+unit.

    Exemplos:
        /use frango 500g
        /use frango frito 1kg
        /use leite integral 200ml
    """
    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            "Uso: /use <produto> <quantidade><unidade>\n\n"
            "Exemplos:\n"
            "• /use frango 500g\n"
            "• /use frango frito 1kg\n"
            "• /use leite integral 200ml\n"
            "• /use ovos 2un"
        )
        return

    # Último arg é qty+unit, tudo antes é o nome do produto
    qty_unit_token = args[-1]
    product_name = " ".join(args[:-1]).lower()

    try:
        quantity, unit = _parse_qty_unit(qty_unit_token)
    except ValueError as e:
        await update.message.reply_text(f"❌ {e}")
        return

    db = SessionLocal()
    try:
        ConsumptionService(db).register(
            ConsumptionCreate(
                product_name=product_name,
                quantity=quantity,
                unit=unit,
            )
        )
        alert = AlertService(db).check_low_stock(product_name)

        reply = f"✅ Registrado: {quantity}{unit} de {product_name}."
        if alert:
            reply += f"\n\n{alert}"

        await update.message.reply_text(reply)
        logger.info("Consumption via /use: %s %s%s", product_name, quantity, unit)

    except ValueError as e:
        await update.message.reply_text(f"❌ Erro: {e}")
        logger.warning("Consumption error via /use: %s | product: %s", e, product_name)
    finally:
        db.close()


async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/add <produto> <quantidade><unidade> <minimo><unidade>

    O nome do produto pode ter espaços. Os dois últimos argumentos são qty+unit.

    Exemplos:
        /add frango 2kg 0.5kg
        /add frango frito 1.5kg 0.3kg
        /add leite integral 2l 0.5l
        /add ovos 12un 2un
    """
    args = context.args
    if not args or len(args) < 3:
        await update.message.reply_text(
            "Uso: /add <produto> <quantidade><unidade> <minimo><unidade>\n\n"
            "Exemplos:\n"
            "• /add frango 2kg 0.5kg\n"
            "• /add frango frito 1.5kg 0.3kg\n"
            "• /add leite integral 2l 0.5l\n"
            "• /add ovos 12un 2un"
        )
        return

    # Últimos 2 args são qty+unit e minimum+unit, tudo antes é nome
    minimum_token = args[-1]
    qty_unit_token = args[-2]
    product_name = " ".join(args[:-2]).strip()

    if not product_name:
        await update.message.reply_text("❌ Nome do produto não pode ser vazio.")
        return

    try:
        quantity, unit = _parse_qty_unit(qty_unit_token)
        minimum_quantity, minimum_unit = _parse_qty_unit(minimum_token)
    except ValueError as e:
        await update.message.reply_text(f"❌ {e}")
        return

    if unit != minimum_unit:
        await update.message.reply_text(
            f"❌ A unidade da quantidade ({unit}) e do mínimo ({minimum_unit}) devem ser iguais."
        )
        return

    db = SessionLocal()
    try:
        product = InventoryService(db).add_product(
            ProductCreate(
                name=product_name,
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
            lines.append(
                f"{status} *{p.name}*: {p.quantity}{p.unit} (mín: {p.minimum_quantity}{p.unit})"
            )

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    finally:
        db.close()
