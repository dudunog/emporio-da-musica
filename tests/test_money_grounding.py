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


def test_policy_values_pass_only_when_policy_was_consulted() -> None:
    shipping_policy = dispatch_tool("get_policy", {"topic": "shipping"}, TODAY).content
    final_text = "Frete grátis acima de R$ 500,00; abaixo disso a taxa é R$ 35,00."
    assert_money_grounded(final_text, [shipping_policy])
    with pytest.raises(AssertionError):
        assert_money_grounded(final_text, [])


def test_text_without_money_passes_with_no_tool_results() -> None:
    assert_money_grounded("A loja abre de segunda a sexta.", [])
