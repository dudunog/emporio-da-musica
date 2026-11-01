import re
from collections.abc import Iterable
from decimal import Decimal

MONEY_PATTERN = re.compile(r"R\$\s?(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{2}))?")
DEFAULT_CENTS = "00"


def extract_money_values(text: str) -> set[Decimal]:
    values: set[Decimal] = set()
    for integer_part, cents in MONEY_PATTERN.findall(text):
        values.add(Decimal(integer_part.replace(".", "") + "." + (cents or DEFAULT_CENTS)))
    return values


def assert_money_grounded(final_text: str, tool_results: Iterable[str]) -> None:
    grounded_values: set[Decimal] = set()
    for tool_result in tool_results:
        grounded_values.update(extract_money_values(tool_result))
    ungrounded_values = extract_money_values(final_text) - grounded_values
    assert not ungrounded_values, (
        f"Money values absent from every tool result: {sorted(ungrounded_values)}"
    )
