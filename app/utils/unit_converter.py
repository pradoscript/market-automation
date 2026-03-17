# Stub — será expandido na Etapa 10 com todas as conversões

_UNIT_ALIASES: dict[str, str] = {
    "grama": "g",
    "gramas": "g",
    "kg": "kg",
    "quilo": "kg",
    "quilos": "kg",
    "quilograma": "kg",
    "quilogramas": "kg",
    "ml": "ml",
    "mililitro": "ml",
    "mililitros": "ml",
    "litro": "l",
    "litros": "l",
    "l": "l",
    "unidade": "un",
    "unidades": "un",
    "un": "un",
}

# Conversão para unidade base: g→kg, ml→l
_TO_BASE: dict[str, tuple[str, float]] = {
    "g": ("kg", 0.001),
    "ml": ("l", 0.001),
}


def normalize_unit(unit: str) -> str:
    return _UNIT_ALIASES.get(unit.lower(), unit.lower())


def to_base_unit(quantity: float, from_unit: str, product_unit: str) -> float:
    from_unit = normalize_unit(from_unit)
    product_unit = normalize_unit(product_unit)

    if from_unit == product_unit:
        return quantity

    if from_unit in _TO_BASE:
        base_unit, factor = _TO_BASE[from_unit]
        if base_unit == product_unit:
            return quantity * factor

    raise ValueError(
        f"Não é possível converter '{from_unit}' para '{product_unit}'."
    )
