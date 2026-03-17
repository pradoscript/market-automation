import re
from dataclasses import dataclass

from app.utils.unit_converter import normalize_unit

# Verbos de consumo aceitos
_VERBS = r"(?:consumi|usei|gastei|utilizei|comi|bebi|tomei)"

# Unidades aceitas (com e sem abreviação)
_UNITS = (
    r"(?:kg|quilos?|quilogramas?|g|gramas?|"
    r"l|litros?|ml|mililitros?|"
    r"un|unidades?)"
)

# Padrão principal: verbo + quantidade + unidade + "de" + produto
# Ex: "consumi 500g de frango", "usei 1 litro de leite"
_PATTERN_WITH_UNIT = re.compile(
    rf"{_VERBS}\s+"
    rf"(?P<quantity>\d+(?:[.,]\d+)?)\s*"
    rf"(?P<unit>{_UNITS})\s+"
    rf"(?:de\s+)?"
    rf"(?P<product>.+)",
    re.IGNORECASE,
)

# Padrão sem unidade: verbo + quantidade + produto
# Ex: "consumi 2 ovos", "comi 3 bananas"
_PATTERN_WITHOUT_UNIT = re.compile(
    rf"{_VERBS}\s+"
    rf"(?P<quantity>\d+(?:[.,]\d+)?)\s+"
    rf"(?P<product>.+)",
    re.IGNORECASE,
)


@dataclass
class ParsedConsumption:
    product_name: str
    quantity: float
    unit: str


def parse_consumption_message(text: str) -> ParsedConsumption | None:
    """
    Interpreta uma mensagem de consumo em linguagem natural.

    Exemplos aceitos:
      - "consumi 1kg de frango"
      - "usei 500g de arroz"
      - "bebi 200ml de leite"
      - "consumi 2 ovos"
      - "gastei 1,5 litros de suco"

    Retorna None se a mensagem não for reconhecida.
    """
    text = text.strip()

    match = _PATTERN_WITH_UNIT.fullmatch(text)
    if match:
        quantity = float(match.group("quantity").replace(",", "."))
        unit = normalize_unit(match.group("unit"))
        product_name = match.group("product").strip().lower()
        return ParsedConsumption(product_name=product_name, quantity=quantity, unit=unit)

    match = _PATTERN_WITHOUT_UNIT.fullmatch(text)
    if match:
        quantity = float(match.group("quantity").replace(",", "."))
        product_name = match.group("product").strip().lower()
        return ParsedConsumption(product_name=product_name, quantity=quantity, unit="un")

    return None
