import pytest

from app.utils.unit_converter import format_quantity, normalize_unit, to_base_unit


class TestNormalizeUnit:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("grama", "g"),
            ("gramas", "g"),
            ("g", "g"),
            ("kg", "kg"),
            ("quilo", "kg"),
            ("quilos", "kg"),
            ("quilograma", "kg"),
            ("quilogramas", "kg"),
            ("ml", "ml"),
            ("mililitro", "ml"),
            ("mililitros", "ml"),
            ("l", "l"),
            ("litro", "l"),
            ("litros", "l"),
            ("un", "un"),
            ("unidade", "un"),
            ("unidades", "un"),
            # Case insensitive
            ("KG", "kg"),
            ("Litros", "l"),
            ("GRAMAS", "g"),
        ],
    )
    def test_normalize(self, raw: str, expected: str) -> None:
        assert normalize_unit(raw) == expected


class TestToBaseUnit:
    @pytest.mark.parametrize(
        "quantity, from_unit, product_unit, expected",
        [
            # Mesma unidade — sem conversão
            (1.0, "kg", "kg", 1.0),
            (500.0, "g", "g", 500.0),
            (1.0, "l", "l", 1.0),
            (2.0, "un", "un", 2.0),
            # g → kg
            (500.0, "g", "kg", 0.5),
            (1000.0, "g", "kg", 1.0),
            (250.0, "g", "kg", 0.25),
            # kg → g
            (1.0, "kg", "g", 1000.0),
            (0.5, "kg", "g", 500.0),
            # ml → l
            (200.0, "ml", "l", 0.2),
            (1000.0, "ml", "l", 1.0),
            # l → ml
            (1.0, "l", "ml", 1000.0),
            (0.5, "l", "ml", 500.0),
            # Aliases por extenso
            (500.0, "gramas", "kg", 0.5),
            (1.0, "litro", "ml", 1000.0),
            (200.0, "mililitros", "l", 0.2),
        ],
    )
    def test_valid_conversions(
        self, quantity: float, from_unit: str, product_unit: str, expected: float
    ) -> None:
        assert to_base_unit(quantity, from_unit, product_unit) == pytest.approx(expected)

    @pytest.mark.parametrize(
        "from_unit, product_unit",
        [
            ("g", "l"),
            ("kg", "ml"),
            ("l", "g"),
            ("ml", "kg"),
            ("un", "kg"),
            ("g", "un"),
        ],
    )
    def test_incompatible_units_raise(self, from_unit: str, product_unit: str) -> None:
        with pytest.raises(ValueError, match="Não é possível converter"):
            to_base_unit(1.0, from_unit, product_unit)


class TestFormatQuantity:
    @pytest.mark.parametrize(
        "quantity, unit, expected",
        [
            (1.5, "kg", "1.5kg"),
            (2.0, "un", "2un"),
            (0.5, "l", "0.5l"),
            (1000.0, "g", "1000g"),
            (0.001, "kg", "0.001kg"),
        ],
    )
    def test_format(self, quantity: float, unit: str, expected: str) -> None:
        assert format_quantity(quantity, unit) == expected
