import functools
import re
from pathlib import Path
from typing import Literal

from pypdf import PdfReader

PolicyTopic = Literal[
    "about_store",
    "opening_hours",
    "payment",
    "exchanges_returns",
    "shipping",
    "promotions",
    "customer_service",
    "warranty",
    "privacy",
    "final_provisions",
]

POLICY_PDF_PATH = Path(__file__).parent.parent / "data" / "políticas_da_loja.pdf"
POLICY_TOPICS: dict[PolicyTopic, str] = {
    "about_store": "1. Sobre a Empório da Música",
    "opening_hours": "2. Horário de Funcionamento",
    "payment": "3. Formas de Pagamento",
    "exchanges_returns": "4. Política de Trocas e Devoluções",
    "shipping": "5. Política de Frete e Entregas",
    "promotions": "6. Promoções e Descontos",
    "customer_service": "7. Atendimento via WhatsApp",
    "warranty": "8. Garantia",
    "privacy": "9. Privacidade e Proteção de Dados",
    "final_provisions": "10. Disposições Finais",
}
PAGE_HEADER = "Empório da Música Manual de Políticas e Procedimentos"
PAGE_FOOTER_PATTERN = re.compile(r"^Página \d+$")
SECTION_START_PATTERN = re.compile(r"^\d{1,2}\. \S", re.MULTILINE)
REPEATED_SPACES_PATTERN = re.compile(r"[ \t]{2,}")
REPEATED_BLANK_LINES_PATTERN = re.compile(r"\n{3,}")
HEADING_PATTERN = re.compile(r"^\d+(\.\d+)*\.?\s[^:]*$")
BLOCK_START_PATTERN = re.compile(r"^(•|\d+(\.\d+)*\.?\s|[A-ZÁÉÍÓÚÂÊÔÃÕÇ][^:]{0,40}:)")


def is_page_decoration(line: str) -> bool:
    stripped = line.strip()
    return stripped == PAGE_HEADER or PAGE_FOOTER_PATTERN.match(stripped) is not None


def extract_policy_text(pdf_path: Path) -> str:
    reader = PdfReader(pdf_path)
    pages = [page.extract_text(extraction_mode="layout") for page in reader.pages]
    lines = "\n".join(pages).splitlines()
    return "\n".join(line for line in lines if not is_page_decoration(line))


def starts_new_block(line: str) -> bool:
    return not line or BLOCK_START_PATTERN.match(line) is not None


def unwrap_lines(lines: list[str]) -> list[str]:
    unwrapped: list[str] = []
    for line in lines:
        previous = unwrapped[-1] if unwrapped else ""
        if not previous or starts_new_block(line) or HEADING_PATTERN.match(previous):
            unwrapped.append(line)
            continue
        unwrapped[-1] = previous + " " + line
    return unwrapped


def clean_section(raw_section: str) -> str:
    lines = [REPEATED_SPACES_PATTERN.sub(" ", line).strip() for line in raw_section.splitlines()]
    joined = "\n".join(unwrap_lines(lines))
    return REPEATED_BLANK_LINES_PATTERN.sub("\n\n", joined).strip()


def split_sections(policy_text: str) -> list[str]:
    starts = [match.start() for match in SECTION_START_PATTERN.finditer(policy_text)]
    ends = [*starts[1:], len(policy_text)]
    return [clean_section(policy_text[start:end]) for start, end in zip(starts, ends, strict=True)]


def load_policy_sections(pdf_path: Path) -> dict[PolicyTopic, str]:
    sections = split_sections(extract_policy_text(pdf_path))
    return dict(zip(POLICY_TOPICS, sections, strict=True))


@functools.cache
def policy_sections() -> dict[PolicyTopic, str]:
    return load_policy_sections(POLICY_PDF_PATH)


def get_policy(topic: PolicyTopic) -> str:
    return policy_sections()[topic]
