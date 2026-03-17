"""
Conversão e normalização de unidades de medida.

Grandezas suportadas:
  - Massa:   g, kg
  - Volume:  ml, l
  - Contagem: un
"""

# Aliases de texto → símbolo canônico
_UNIT_ALIASES: dict[str, str] = {
    # Massa
    "grama": "g",
    "gramas": "g",
    "g": "g",
    "kg": "kg",
    "quilo": "kg",
    "quilos": "kg",
    "quilograma": "kg",
    "quilogramas": "kg",
    # Volume
    "ml": "ml",
    "mililitro": "ml",
    "mililitros": "ml",
    "l": "l",
    "litro": "l",
    "litros": "l",
    # Contagem
    "un": "un",
    "unidade": "un",
    "unidades": "un",
}

# Fator de conversão entre unidades da mesma grandeza
# (from_unit, to_unit) → factor  |  quantity * factor = resultado
_CONVERSION_TABLE: dict[tuple[str, str], float] = {
    # Massa
    ("g", "kg"): 0.001,
    ("kg", "g"): 1000.0,
    # Volume
    ("ml", "l"): 0.001,
    ("l", "ml"): 1000.0,
}


def normalize_unit(unit: str) -> str:
    """Converte alias textual para símbolo canônico.

    Exemplos:
        "litros" → "l"
        "quilogramas" → "kg"
        "gramas" → "g"
    """
    return _UNIT_ALIASES.get(unit.strip().lower(), unit.strip().lower())


def to_base_unit(quantity: float, from_unit: str, product_unit: str) -> float:
    """Converte *quantity* de *from_unit* para *product_unit*.

    Retorna a quantidade já na unidade do produto, pronta para ser deduzida
    do estoque.

    Exemplos:
        to_base_unit(500, "g",  "kg") → 0.5
        to_base_unit(1,   "kg", "g")  → 1000.0
        to_base_unit(200, "ml", "l")  → 0.2
        to_base_unit(2,   "un", "un") → 2.0

    Raises:
        ValueError: unidades de grandezas diferentes (ex: "g" → "l").
    """
    from_unit = normalize_unit(from_unit)
    product_unit = normalize_unit(product_unit)

    if from_unit == product_unit:
        return quantity

    factor = _CONVERSION_TABLE.get((from_unit, product_unit))
    if factor is None:
        raise ValueError(
            f"Não é possível converter '{from_unit}' para '{product_unit}'. "
            "Verifique se as unidades são da mesma grandeza (massa ou volume)."
        )

    return quantity * factor


def format_quantity(quantity: float, unit: str) -> str:
    """Formata quantidade para exibição amigável.

    Exemplos:
        format_quantity(1.5, "kg")  → "1.5kg"
        format_quantity(2.0, "un")  → "2un"
        format_quantity(0.5, "l")   → "0.5l"
    """
    formatted = f"{quantity:g}"
    return f"{formatted}{unit}"
