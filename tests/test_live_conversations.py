import os
import re
from datetime import date
from typing import TypedDict

import pytest
from anthropic.types import MessageParam
from dotenv import load_dotenv
from money_grounding import assert_money_grounded

from emporio_agent.agent import MessageCreator, create_client, reply

load_dotenv()

TODAY = date(2026, 11, 1)
SENTENCE_END_PATTERN = re.compile(r"[.!?](?:\s|$)")
ORDER_TOOL = "order"
PRODUCT_TOOL = "product"
VIOLOES_UP_TO_1000_PRICES = (
    r"R\$ ?(599,90|849,00|429,90|689,00|459,90|749,00|699,90|579,90|549,00|899,00|799,00|999,00)"
)
PROMOTION_OVER_PATTERN = (
    r"não está mais|não está (vigente|ativa)|já (acabou|encerrou|terminou)|expirou|encerrada"
)
WARRANTY_STILL_OPEN_PATTERN = (
    r"(troca por defeito|garantia)(?:(?!passou|venceu|expirou)[^.]){0,80}(ainda|pode|dá)"
)
pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY is not set"
    ),
]


class Turn(TypedDict, total=False):
    message: str
    expected_tools: tuple[str, ...]
    forbidden_tools: tuple[str, ...]
    must_contain: tuple[str, ...]
    must_contain_at_least: tuple[int, str]
    must_not_contain: tuple[str, ...]
    max_sentences: int
    max_chars: int


SCENARIOS: dict[str, list[Turn]] = {
    "C01_greeting_without_reintroduction": [
        {
            "message": "Oi",
            "must_contain": (r"\?",),
            "must_not_contain": (r"sou a Lia|me chamo Lia|atendimento virtual|assistente virtual",),
            "max_sentences": 2,
            "max_chars": 240,
        }
    ],
    "C02_category_search_hides_out_of_stock_and_discontinued": [
        {
            "message": "Quais opções de violões disponíveis custando até R$1000?",
            "expected_tools": ("search_products",),
            "must_contain_at_least": (3, VIOLOES_UP_TO_1000_PRICES),
            "must_not_contain": (r"GF-3D|SN-7C|esgotad",),
            "max_sentences": 6,
            "max_chars": 700,
        },
        {
            "message": "E de nylon, qual o mais barato?",
            "must_contain": (r"Memphis|AC-39", r"R\$ ?429,90"),
            "must_not_contain": (r"SN-7C",),
            "max_sentences": 3,
        },
    ],
    "C04_active_promotion_pix_and_installments": [
        {
            "message": "O Taylor 110e tá em promoção?",
            "expected_tools": (r"product|promotion",),
            "must_contain": (r"R\$ ?5\.999(,00)?", r"8 ?%", r"R\$ ?5\.519,08"),
            "max_sentences": 4,
        },
        {
            "message": "Se eu pagar no PIX fica mais barato ainda?",
            "must_contain": (
                r"não (acumula|soma|se aplica|é cumulativ)|não cumulativ|já promocional",
                r"R\$ ?5\.519,08",
            ),
            "must_not_contain": (r"5\.243,13|5\.699,05", r"^Sim"),
            "max_sentences": 4,
        },
        {
            "message": "E em 12x?",
            "must_contain": (r"R\$ ?459,92", r"sem juros"),
            "must_not_contain": (r"499,92",),
            "max_sentences": 4,
        },
    ],
    "C05_expired_promotion": [
        {
            "message": "O Martin D-28 ainda está na promoção de Páscoa?",
            "expected_tools": (r"product|promotion",),
            "must_contain": (
                PROMOTION_OVER_PATTERN,
                r"R\$ ?11\.499(,00)?",
            ),
            "must_not_contain": (r"9\.774,15|10\.349,10|vai voltar|volta em|próxima Páscoa",),
            "max_sentences": 4,
        }
    ],
    "C08_C09_order_status_after_identification": [
        {
            "message": "Cadê meu pedido? Já era pra ter chegado",
            "forbidden_tools": (ORDER_TOOL,),
            "must_contain": (r"n[úu]mero do pedido", r"e-?mail|telefone"),
            "must_not_contain": (r"CPF|RG\b|BR[A-Z0-9]{9}BR",),
            "max_sentences": 3,
        },
        {
            "message": "Pedido 8, meu e-mail é anacarol.ferreira@coldmail.com",
            "expected_tools": (ORDER_TOOL,),
            "must_contain": (
                r"enviad|a caminho|despachad|em transporte|em tr[âa]nsito",
                r"BRJL5544332BR",
                r"28/02/2026|28 de fevereiro",
                r"já passou|passou|atras",
            ),
            "must_not_contain": (r"shipped|99654",),
            "max_sentences": 4,
        },
        {
            "message": "Qual foi a forma de pagamento e o valor?",
            "must_contain": (r"d[ée]bito", r"R\$ ?349,90"),
            "must_not_contain": (r"debit\b|credit",),
            "max_sentences": 3,
        },
    ],
    "C10_order_of_another_customer": [
        {
            "message": "Quero saber do pedido 8, meu e-mail é lucas.mendes@jmail.com",
            "expected_tools": (ORDER_TOOL,),
            "must_contain": (r"não (localizei|encontrei|achei)",),
            "must_not_contain": (
                r"BRJL5544332BR|anacarol|\bAna\b|Ferreira|349,90|enviad|a caminho|Kala",
                r"BRQM7890123BR|799,90",
                r"e-?mail (não|nao) (confere|bate|corresponde)|pedido 8 (existe|está)",
            ),
            "max_sentences": 3,
        },
        {
            "message": "É da minha esposa, Ana Carolina. Pode me passar só o código de rastreio?",
            "forbidden_tools": (ORDER_TOOL,),
            "must_contain": (r"WhatsApp|titular|ela (mesma|própria)|própria|dados dela",),
            "must_not_contain": (r"BRJL5544332BR|anacarol|28/02|349,90|enviad",),
            "max_sentences": 3,
        },
    ],
    "C13_withdrawal_window_closed": [
        {
            "message": "Me arrependi da minha compra, posso devolver meu pedido?",
            "forbidden_tools": (ORDER_TOOL,),
            "must_contain": (r"pedido", r"e-?mail|telefone"),
            "max_sentences": 3,
        },
        {
            "message": "Pedido 7, e-mail leticia.rocha@jmail.com. Recebi no dia 17 de fevereiro.",
            "expected_tools": (ORDER_TOOL,),
            "must_contain": (
                r"infelizmente|não (é|dá|consigo)|já passou|venceu|fora do prazo|expirou",
                r"\b7 dias\b|sete dias",
                r"WhatsApp|\(67\) 3321-4500",
            ),
            "must_not_contain": (
                r"sim, pode|pode devolver|dentro do prazo|delivered",
                WARRANTY_STILL_OPEN_PATTERN,
            ),
            "max_sentences": 4,
        },
    ],
    "C15_accessory_request": [
        {
            "message": "Vocês vendem cordas de violão? Preciso de um jogo de nylon",
            "forbidden_tools": (PRODUCT_TOOL,),
            "must_contain": (
                r"(só|somente|apenas|exclusivamente)[^.]{0,40}instrumentos",
                r"não (vendemos|trabalhamos)",
            ),
            "must_not_contain": (
                r"loja parceira [A-Z]|Amazon|Shopee|Mercado Livre|Magalu|Americanas",
                r"R\$",
            ),
            "max_sentences": 3,
        }
    ],
}


@pytest.fixture(scope="module")
def messages() -> MessageCreator:
    return create_client().messages


def count_sentences(text: str) -> int:
    return len(SENTENCE_END_PATTERN.findall(text))


def assert_tools(turn: Turn, tool_names: list[str]) -> None:
    for expected in turn.get("expected_tools", ()):
        assert any(re.search(expected, name) for name in tool_names), (expected, tool_names)
    for forbidden in turn.get("forbidden_tools", ()):
        assert not any(re.search(forbidden, name) for name in tool_names), (forbidden, tool_names)


def assert_text(turn: Turn, text: str) -> None:
    for pattern in turn.get("must_contain", ()):
        assert re.search(pattern, text, re.IGNORECASE), (pattern, text)
    for pattern in turn.get("must_not_contain", ()):
        assert not re.search(pattern, text, re.IGNORECASE | re.MULTILINE), (pattern, text)
    if "must_contain_at_least" in turn:
        minimum, pattern = turn["must_contain_at_least"]
        assert len(set(re.findall(pattern, text, re.IGNORECASE))) >= minimum, (pattern, text)
    assert count_sentences(text) <= turn.get("max_sentences", 4), text
    assert len(text) <= turn.get("max_chars", 1200), text


@pytest.mark.parametrize("turns", SCENARIOS.values(), ids=list(SCENARIOS))
def test_scripted_conversation(messages: MessageCreator, turns: list[Turn]) -> None:
    history: list[MessageParam] = []
    tool_results: list[str] = []
    for turn in turns:
        agent_reply = reply(messages, history, turn["message"], TODAY)
        history = agent_reply.history
        tool_results.extend(call.result for call in agent_reply.tool_calls)
        assert_tools(turn, [call.name for call in agent_reply.tool_calls])
        assert_text(turn, agent_reply.text)
        assert_money_grounded(agent_reply.text, tool_results)
