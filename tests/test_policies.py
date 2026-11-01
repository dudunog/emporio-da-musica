import re
from typing import get_args

from pypdf import PdfReader

from emporio_agent.policies import (
    PAGE_HEADER,
    POLICY_PDF_PATH,
    POLICY_TOPICS,
    PolicyTopic,
    get_policy,
    load_policy_sections,
    policy_sections,
)

WHITESPACE_PATTERN = re.compile(r"\s+")
PAGE_FOOTER_PATTERN = re.compile(r"Página \d+")
FIRST_SECTION_TITLE = "1. Sobre a Empório da Música"


def without_whitespace(text: str) -> str:
    return WHITESPACE_PATTERN.sub("", text)


def test_policy_topics_cover_the_ten_manual_sections() -> None:
    assert len(POLICY_TOPICS) == 10
    assert set(POLICY_TOPICS) == set(get_args(PolicyTopic))
    assert list(POLICY_TOPICS.values()) == [
        "1. Sobre a Empório da Música",
        "2. Horário de Funcionamento",
        "3. Formas de Pagamento",
        "4. Política de Trocas e Devoluções",
        "5. Política de Frete e Entregas",
        "6. Promoções e Descontos",
        "7. Atendimento via WhatsApp",
        "8. Garantia",
        "9. Privacidade e Proteção de Dados",
        "10. Disposições Finais",
    ]


def test_every_section_starts_with_its_title_and_is_not_empty() -> None:
    sections = policy_sections()
    assert set(sections) == set(POLICY_TOPICS)
    for topic, title in POLICY_TOPICS.items():
        assert sections[topic].startswith(title), topic
        assert len(sections[topic]) > len(title) + 20, topic


def test_sections_keep_the_manual_numbers() -> None:
    returns = get_policy("exchanges_returns")
    assert "7 (sete) dias corridos" in returns
    assert "30 (trinta) dias corridos" in returns
    assert "10 dias úteis" in returns
    assert "não se aplica sobre preços já promocionais" in get_policy("promotions")
    assert "rain check" in get_policy("promotions")
    opening_hours = get_policy("opening_hours")
    assert "Sábado" in opening_hours
    assert "09:00 às 13:00" in opening_hours
    payment = get_policy("payment")
    assert "parcela mínima de R$ 80,00" in payment
    assert "R$ 2.000,00" in payment
    shipping = get_policy("shipping")
    assert "R$ 500,00" in shipping
    assert "R$ 35,00" in shipping
    assert "5 a 12 dias úteis" in shipping
    warranty = get_policy("warranty")
    assert "(noventa) dias" in warranty
    assert "trastes, cordas, feltros" in warranty
    assert "LGPD" in get_policy("privacy")
    assert "24 horas úteis" in get_policy("customer_service")


def test_indented_numbered_items_do_not_split_sections() -> None:
    customer_service = get_policy("customer_service")
    assert "3. Consulta:" in customer_service
    assert "5. Fechamento:" in customer_service
    assert "7.3 Situações Especiais" in customer_service


def test_page_headers_and_footers_are_removed() -> None:
    for section in policy_sections().values():
        assert PAGE_HEADER not in section
        assert PAGE_FOOTER_PATTERN.search(section) is None
        assert "  " not in section
        assert "\n\n\n" not in section


def test_no_paragraph_is_lost_when_splitting() -> None:
    reader = PdfReader(POLICY_PDF_PATH)
    raw_pages = [page.extract_text(extraction_mode="layout") for page in reader.pages]
    raw_lines = "\n".join(raw_pages).splitlines()
    body_lines = [
        line
        for line in raw_lines
        if line.strip() != PAGE_HEADER and PAGE_FOOTER_PATTERN.search(line) is None
    ]
    body = "\n".join(body_lines)
    body = body[body.index(FIRST_SECTION_TITLE) :]
    joined_sections = "".join(policy_sections().values())
    assert without_whitespace(joined_sections) == without_whitespace(body)


def test_load_policy_sections_is_pure_and_cached_accessor_is_stable() -> None:
    assert load_policy_sections(POLICY_PDF_PATH) == policy_sections()
    assert policy_sections() is policy_sections()
