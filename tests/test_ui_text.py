import ast
import re
import unicodedata
from pathlib import Path

import pytest

from emporio_agent.agent import GREETING

APP_PATH = Path(__file__).parent.parent / "app.py"
UI_TEXT_CONSTANT_NAMES = (
    "PAGE_TITLE",
    "STORE_NAME",
    "STORE_TAGLINE",
    "COMPOSER_PLACEHOLDER",
    "TYPING_INDICATOR_LABEL",
    "RETRY_BUTTON_LABEL",
    "SEND_BUTTON_LABEL",
    "SKIP_LINK_LABEL",
    "ERROR_MESSAGES",
)
EXPECTED_TEXTS = {
    "PAGE_TITLE": "Empório da Música",
    "STORE_NAME": "Empório da Música",
    "STORE_TAGLINE": "Sua música começa aqui",
    "COMPOSER_PLACEHOLDER": "Escreva sua mensagem",
    "TYPING_INDICATOR_LABEL": "Lia está digitando",
    "RETRY_BUTTON_LABEL": "Tentar de novo",
    "SEND_BUTTON_LABEL": "Enviar mensagem",
    "SKIP_LINK_LABEL": "Ir para o conteúdo",
    "ERROR_MESSAGES.authentication": (
        "Nosso atendimento está indisponível neste momento. Tente de novo em alguns minutos."
    ),
    "ERROR_MESSAGES.server": (
        "Nosso atendimento está indisponível neste momento. Tente de novo em alguns minutos."
    ),
    "ERROR_MESSAGES.connection": "Sem conexão agora. Verifique sua internet e tente de novo.",
    "ERROR_MESSAGES.rate_limit": "Estamos com muitas conversas agora. Tente de novo em instantes.",
    "GREETING": (
        "Oi! Eu sou a Lia, atendimento virtual da Empório da Música. "
        "Posso ajudar com produtos, preços, pedidos, trocas e informações da loja."
    ),
}
FORBIDDEN_TERMS = (
    "API",
    "LLM",
    "token",
    "sessão",
    "session",
    "rerun",
    "deploy",
    "prompt",
    "modelo",
    "Streamlit",
    "Anthropic",
    "Claude",
    "chat",
    "bot",
    "online",
    "offline",
    "retry",
    "loading",
    "error",
    "erro 4",
    "erro 5",
    "timeout",
    "status code",
    "chave",
    "key",
    ".env",
    "ANTHROPIC_API_KEY",
    "Enter",
    "ok",
    "ops",
)
ACCENTED_WORDS = (
    "Empório",
    "Música",
    "começa",
    "está",
    "não",
    "disponível",
    "informações",
    "preços",
)
FORBIDDEN_TYPOGRAPHY = re.compile(
    r"[\u2014\u2013\u201c\u201d\u2018\u2019\u2026]|[\U0001f300-\U0001faff\U00002600-\U000027bf]"
)
ACCENTED_LETTER = re.compile(r"[áéíóúâêôãõç]", re.IGNORECASE)


def strip_accents(word: str) -> str:
    decomposed = unicodedata.normalize("NFD", word)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def whole_word(term: str) -> re.Pattern[str]:
    return re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", re.IGNORECASE)


def string_values(node: ast.expr) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.Dict):
        return [text for value in node.values if value for text in string_values(value)]
    return []


def assigned_name(node: ast.stmt) -> str | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        return target.id if isinstance(target, ast.Name) else None
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return None


def assigned_value(node: ast.stmt) -> ast.expr | None:
    if isinstance(node, ast.Assign | ast.AnnAssign):
        return node.value
    return None


def dict_entries(node: ast.expr) -> dict[str, str]:
    if not isinstance(node, ast.Dict):
        return {}
    entries: dict[str, str] = {}
    for key, value in zip(node.keys, node.values, strict=True):
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            for text in string_values(value):
                entries[key.value] = text
    return entries


def load_app_module() -> ast.Module:
    return ast.parse(APP_PATH.read_text(encoding="utf-8"))


def ui_texts_from_app() -> dict[str, str]:
    texts: dict[str, str] = {}
    for node in load_app_module().body:
        name = assigned_name(node)
        value = assigned_value(node)
        if name not in UI_TEXT_CONSTANT_NAMES or value is None:
            continue
        texts.update({f"{name}.{key}": text for key, text in dict_entries(value).items()})
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            texts[name] = value.value
    return texts


def all_ui_texts() -> dict[str, str]:
    return {**ui_texts_from_app(), "GREETING": GREETING}


def accented_literals_in_app() -> dict[str, str]:
    literals: dict[str, str] = {}
    for node in ast.walk(load_app_module()):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if ACCENTED_LETTER.search(node.value):
            literals[f"line {node.lineno}"] = node.value
    return literals


def test_ui_texts_match_the_contract() -> None:
    assert all_ui_texts() == EXPECTED_TEXTS


@pytest.mark.parametrize("term", FORBIDDEN_TERMS)
def test_ui_texts_avoid_forbidden_terms(term: str) -> None:
    pattern = whole_word(term)
    offenders = {name: text for name, text in all_ui_texts().items() if pattern.search(text)}
    assert offenders == {}


@pytest.mark.parametrize("word", ACCENTED_WORDS)
def test_ui_texts_keep_accents(word: str) -> None:
    pattern = whole_word(strip_accents(word))
    offenders = {name: text for name, text in all_ui_texts().items() if pattern.search(text)}
    assert offenders == {}


def test_ui_texts_use_plain_typography() -> None:
    offenders = {
        name: text for name, text in all_ui_texts().items() if FORBIDDEN_TYPOGRAPHY.search(text)
    }
    assert offenders == {}


def test_exclamation_only_in_greeting() -> None:
    texts = all_ui_texts()
    assert texts["GREETING"].count("!") == 1
    offenders = {name: text for name, text in texts.items() if "!" in text and name != "GREETING"}
    assert offenders == {}


def test_accented_phrases_in_app_live_in_ui_constants() -> None:
    ui_values = set(ui_texts_from_app().values())
    strays = {
        where: text for where, text in accented_literals_in_app().items() if text not in ui_values
    }
    assert strays == {}
