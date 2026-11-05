from decimal import ROUND_HALF_UP, Decimal

import pytest

from emporio_agent.catalog import (
    format_brl,
    get_product,
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


def test_product_with_active_promotion_exposes_promotional_price() -> None:
    ohana = get_product(121)
    assert ohana is not None
    assert ohana.list_price_brl == Decimal("549.00")
    assert ohana.promotional_price_brl == Decimal("439.20")
    assert ohana.promotion is not None
    assert ohana.promotion.discount_percent == 20


def test_product_with_inactive_promotion_has_no_promotional_price() -> None:
    takamine = get_product(95)
    assert takamine is not None
    assert takamine.promotional_price_brl is None
    assert takamine.promotion is None
    martin = get_product(93)
    assert martin is not None
    assert martin.promotional_price_brl is None


def test_best_cash_price_is_promotional_when_promotion_is_active() -> None:
    ohana = get_product(121)
    assert ohana is not None
    assert ohana.best_cash_price_brl == Decimal("439.20")
    assert ohana.pix_price_brl is None
    assert "não se aplica a preço promocional" in (ohana.pix_note or "")
    crafter = get_product(90)
    assert crafter is not None
    assert crafter.promotional_price_brl == Decimal("1967.18")
    assert crafter.best_cash_price_brl == Decimal("1967.18")
    quoted_prices = {
        crafter.list_price_brl,
        crafter.promotional_price_brl,
        crafter.pix_price_brl,
        crafter.best_cash_price_brl,
    }
    assert Decimal("1868.82") not in quoted_prices


def test_best_cash_price_is_pix_when_there_is_no_promotion() -> None:
    takamine = get_product(95)
    assert takamine is not None
    assert takamine.pix_price_brl == Decimal("2089.05")
    assert takamine.best_cash_price_brl == Decimal("2089.05")
    assert takamine.pix_note == "Preço à vista no PIX com 5% de desconto."


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


def test_installment_plan_uses_promotional_price_as_base() -> None:
    ohana = get_product(121)
    assert ohana is not None
    assert ohana.max_installments == 5
    assert ohana.installment_value_brl == Decimal("87.84")
    assert ohana.installment_note == "sem juros no cartão de crédito"
    assert ohana.installment_rule_note == (
        "até 12x sem juros no cartão; parcela mínima de R$ 50,00 de 2x a 3x, "
        "de R$ 80,00 de 4x a 6x e de R$ 100,00 de 7x a 12x"
    )
    takamine = get_product(95)
    assert takamine is not None
    assert takamine.max_installments == 12
    assert takamine.installment_value_brl == Decimal("183.25")
