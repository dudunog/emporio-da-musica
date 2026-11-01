from decimal import ROUND_HALF_UP, Decimal

import pytest

from emporio_agent.catalog import (
    format_brl,
    installment_plan,
    pix_price,
    promotional_price,
)


def test_pix_price_is_five_percent_off_rounded_half_up() -> None:
    assert pix_price(Decimal("2199")) == Decimal("2089.05")
    assert pix_price(Decimal("799.90")) == Decimal("759.91")
    assert pix_price(Decimal("2399")) == Decimal("2279.05")


def test_promotional_price_rounds_to_cents() -> None:
    assert promotional_price(Decimal("2399"), 18) == Decimal("1967.18")
    assert promotional_price(Decimal("5999"), 8) == Decimal("5519.08")
    assert promotional_price(Decimal("549"), 20) == Decimal("439.20")
    assert promotional_price(Decimal("359"), 10) == Decimal("323.10")


def test_format_brl_uses_brazilian_separators() -> None:
    assert format_brl(Decimal("2089.05")) == "R$ 2.089,05"
    assert format_brl(Decimal("159.9")) == "R$ 159,90"
    assert format_brl(Decimal("19567")) == "R$ 19.567,00"
    assert format_brl(Decimal("1400")) == "R$ 1.400,00"


@pytest.mark.parametrize(
    ("price", "expected_plan"),
    [
        (Decimal("2199"), (12, Decimal("183.25"))),
        (Decimal("999"), (9, Decimal("111.00"))),
        (Decimal("599.90"), (6, Decimal("99.98"))),
        (Decimal("199.90"), (3, Decimal("66.63"))),
        (Decimal("120"), (2, Decimal("60.00"))),
        (Decimal("439.20"), (5, Decimal("87.84"))),
        (Decimal("159.90"), (3, Decimal("53.30"))),
        (Decimal("429.90"), (5, Decimal("85.98"))),
    ],
)
def test_installment_plan_values(price: Decimal, expected_plan: tuple[int, Decimal]) -> None:
    assert installment_plan(price) == expected_plan


@pytest.mark.parametrize(
    ("price", "expected_max_installments"),
    [
        (Decimal("100"), 2),
        (Decimal("149.99"), 2),
        (Decimal("150"), 3),
        (Decimal("319.99"), 3),
        (Decimal("320"), 4),
        (Decimal("323.10"), 4),
        (Decimal("359"), 4),
        (Decimal("549"), 6),
        (Decimal("699.99"), 6),
        (Decimal("700"), 7),
        (Decimal("1199.99"), 11),
        (Decimal("1200"), 12),
        (Decimal("2199"), 12),
        (Decimal("19567"), 12),
    ],
)
def test_installment_plan_boundaries(price: Decimal, expected_max_installments: int) -> None:
    max_installments, installment_value = installment_plan(price)
    assert max_installments == expected_max_installments
    expected_value = (price / max_installments).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    assert installment_value == expected_value
