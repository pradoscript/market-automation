import pytest

from app.utils.message_parser import ParsedConsumption, parse_consumption_message


@pytest.mark.parametrize(
    "message, expected",
    [
        # Com unidade abreviada
        ("consumi 1kg de frango", ParsedConsumption("frango", 1.0, "kg")),
        ("usei 500g de arroz", ParsedConsumption("arroz", 500.0, "g")),
        ("bebi 200ml de leite", ParsedConsumption("leite", 200.0, "ml")),
        ("gastei 2l de suco", ParsedConsumption("suco", 2.0, "l")),
        # Com unidade por extenso
        ("consumi 1 quilo de carne", ParsedConsumption("carne", 1.0, "kg")),
        ("usei 500 gramas de farinha", ParsedConsumption("farinha", 500.0, "g")),
        ("bebi 1 litro de água", ParsedConsumption("água", 1.0, "l")),
        ("usei 100 mililitros de azeite", ParsedConsumption("azeite", 100.0, "ml")),
        # Com vírgula como separador decimal
        ("consumi 1,5kg de frango", ParsedConsumption("frango", 1.5, "kg")),
        ("usei 0,5 litros de leite", ParsedConsumption("leite", 0.5, "l")),
        # Sem unidade (contagem)
        ("consumi 2 ovos", ParsedConsumption("ovos", 2.0, "un")),
        ("comi 3 bananas", ParsedConsumption("bananas", 3.0, "un")),
        # Sem "de" antes do produto
        ("consumi 1kg frango", ParsedConsumption("frango", 1.0, "kg")),
        # Outros verbos
        ("utilizei 300g de manteiga", ParsedConsumption("manteiga", 300.0, "g")),
        ("tomei 1 litro de leite", ParsedConsumption("leite", 1.0, "l")),
    ],
)
def test_parse_valid_messages(message: str, expected: ParsedConsumption) -> None:
    result = parse_consumption_message(message)
    assert result == expected


@pytest.mark.parametrize(
    "message",
    [
        "olá, tudo bem?",
        "comprei frango",
        "frango 1kg",
        "",
        "consumi",
        "consumi frango",
    ],
)
def test_parse_invalid_messages(message: str) -> None:
    assert parse_consumption_message(message) is None
