from datetime import date
from decimal import Decimal

import pytest
from money_grounding import assert_money_grounded, extract_money_values

from emporio_agent.tools import dispatch_tool

TODAY = date(2026, 11, 1)
TAKAMINE_RESULT = '{"list_price_brl": "R$ 2.199,00", "pix_price_brl": "R$ 2.089,05"}'


def test_extract_money_values_normalizes_formats() -> None:
    extracted = extract_money_values("custa R$ 2.199,00 ou R$2199 no PIX R$ 2.089,05")
    assert extracted == {Decimal("2199.00"), Decimal("2089.05")}


def test_extract_money_values_reads_line_break_after_currency_sign() -> None:
    assert extract_money_values("exceto abaixo de R$\n50,00") == {Decimal("50.00")}


def test_grounded_values_pass() -> None:
    assert_money_grounded("Custa R$ 2.199,00 e no PIX sai por R$ 2.089,05.", [TAKAMINE_RESULT])


def test_value_with_different_cents_fails() -> None:
    with pytest.raises(AssertionError, match=r"2089\.00"):
        assert_money_grounded("No PIX sai por R$ 2.089,00.", [TAKAMINE_RESULT])


def test_policy_constants_pass_without_tool_results() -> None:
    final_text = (
        "Frete grátis acima de R$ 500,00; abaixo disso a taxa é R$ 35,00. "
        "A parcela mínima é R$ 80,00 de 4x a 6x e R$ 100,00 de 7x a 12x."
    )
    assert_money_grounded(final_text, [])
    with pytest.raises(AssertionError, match=r"45\.00"):
        assert_money_grounded("A taxa é R$ 45,00.", [])


def test_difference_between_two_grounded_values_passes() -> None:
    shipping_policy = dispatch_tool("get_policy", {"topic": "shipping"}, TODAY).content
    assert_money_grounded("No PIX você economiza R$ 109,95.", [TAKAMINE_RESULT])
    with pytest.raises(AssertionError, match=r"109\.00"):
        assert_money_grounded("No PIX você economiza R$ 109,00.", [TAKAMINE_RESULT])
    assert_money_grounded("Frete grátis acima de R$ 500,00.", [shipping_policy])


def test_text_without_money_passes_with_no_tool_results() -> None:
    assert_money_grounded("A loja abre de segunda a sexta.", [])
