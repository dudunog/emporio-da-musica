import logging
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal, Protocol, Unpack

import anthropic
from anthropic.types import (
    Message,
    MessageParam,
    OutputConfigParam,
    TextBlock,
    TextBlockParam,
    ToolParam,
    ToolResultBlockParam,
    ToolUseBlock,
)
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from dotenv import load_dotenv

from emporio_agent.tools import TOOL_DEFINITIONS, dispatch_tool

DEFAULT_MODEL = "claude-opus-5-5"
MODEL_ENVIRONMENT_VARIABLE = "ANTHROPIC_MODEL"
API_KEY_ENVIRONMENT_VARIABLE = "ANTHROPIC_API_KEY"
MAX_TOOL_ROUNDS = 8
MAX_OUTPUT_TOKENS = 1024
OUTPUT_CONFIG: OutputConfigParam = {"effort": "low"}
SYSTEM_PROMPT_PATH = Path(__file__).parent / "system-prompt.md"
DOTENV_PATH = Path(__file__).parent.parent / ".env"
SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
GREETING = (
    "Oi! Eu sou a Lia, atendimento virtual da Empório da Música. "
    "Posso ajudar com produtos, preços, pedidos, trocas e informações da loja."
)
TODAY_SECTION_TITLE = "Data de hoje"
TODAY_TEMPLATE = (
    "Hoje é {weekday}, {label} ({iso}). Prazos de devolução, troca e entrega já chegam "
    "calculados nas consultas; use as datas prontas em vez de contar dias."
)
WEEKDAY_NAMES_PT_BR = {
    0: "segunda-feira",
    1: "terça-feira",
    2: "quarta-feira",
    3: "quinta-feira",
    4: "sexta-feira",
    5: "sábado",
    6: "domingo",
}
TOO_MANY_TOOL_ROUNDS_FALLBACK = (
    "Não consegui concluir essa consulta agora. Pode tentar de novo em instantes "
    "ou falar com a loja pelo WhatsApp."
)
REFUSAL_FALLBACK = (
    "Isso eu não consigo ajudar por aqui. Posso ajudar com instrumentos, pedidos "
    "e dúvidas sobre a loja."
)
TRUNCATED_REPLY_FALLBACK = (
    "Minha resposta ficou longa demais e foi cortada. Pode perguntar de novo, "
    "de um jeito mais específico?"
)
EMPTY_REPLY_FALLBACK = "Não entendi bem. Pode repetir de outro jeito?"
STOP_REASON_FALLBACKS: dict[str, str] = {
    "refusal": REFUSAL_FALLBACK,
    "max_tokens": TRUNCATED_REPLY_FALLBACK,
    "model_context_window_exceeded": TRUNCATED_REPLY_FALLBACK,
}
UnavailableReason = Literal["authentication", "connection", "rate_limit", "server"]
SDK_ERROR_REASONS: tuple[tuple[type[anthropic.APIError], UnavailableReason], ...] = (
    (anthropic.AuthenticationError, "authentication"),
    (anthropic.PermissionDeniedError, "authentication"),
    (anthropic.RateLimitError, "rate_limit"),
    (anthropic.APIStatusError, "server"),
    (anthropic.APIConnectionError, "connection"),
)
LOGGER = logging.getLogger(__name__)


class MessageCreator(Protocol):
    def create(self, **request: Unpack[MessageCreateParamsNonStreaming]) -> Message: ...


@dataclass(frozen=True, slots=True)
class ToolCall:
    name: str
    arguments: dict[str, object]
    result: str
    is_error: bool


@dataclass(frozen=True, slots=True)
class AgentReply:
    text: str
    tool_calls: tuple[ToolCall, ...]
    history: list[MessageParam]


class AgentUnavailableError(Exception):
    def __init__(self, reason: UnavailableReason) -> None:
        super().__init__(reason)
        self.reason: UnavailableReason = reason


def resolve_model() -> str:
    return os.environ.get(MODEL_ENVIRONMENT_VARIABLE, "").strip() or DEFAULT_MODEL


def create_client() -> anthropic.Anthropic:
    load_dotenv(DOTENV_PATH)
    api_key = os.environ.get(API_KEY_ENVIRONMENT_VARIABLE, "").strip()
    if not api_key:
        LOGGER.error("%s is not set", API_KEY_ENVIRONMENT_VARIABLE)
        raise AgentUnavailableError("authentication")
    return anthropic.Anthropic(api_key=api_key)


def today_section(today: date) -> str:
    sentence = TODAY_TEMPLATE.format(
        weekday=WEEKDAY_NAMES_PT_BR[today.weekday()],
        label=today.strftime("%d/%m/%Y"),
        iso=today.isoformat(),
    )
    return f"{TODAY_SECTION_TITLE}\n\n{sentence}"


def build_system_prompt(today: date) -> list[TextBlockParam]:
    return [
        {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": today_section(today)},
    ]


def as_tool_param(definition: dict[str, object]) -> ToolParam:
    name = definition.get("name")
    description = definition.get("description")
    input_schema = definition.get("input_schema")
    if not (isinstance(name, str) and isinstance(description, str)):
        raise TypeError(f"Tool definition needs string name and description: {definition!r}")
    if not isinstance(input_schema, dict):
        raise TypeError(f"Tool definition needs an input_schema object: {definition!r}")
    return {"name": name, "description": description, "input_schema": input_schema, "strict": True}


TOOL_PARAMS: list[ToolParam] = [as_tool_param(definition) for definition in TOOL_DEFINITIONS]


def unavailable_reason(api_error: anthropic.APIError) -> UnavailableReason:
    for error_type, reason in SDK_ERROR_REASONS:
        if isinstance(api_error, error_type):
            return reason
    return "server"


def create_message(
    client: MessageCreator, system: list[TextBlockParam], messages: list[MessageParam]
) -> Message:
    try:
        return client.create(
            model=resolve_model(),
            max_tokens=MAX_OUTPUT_TOKENS,
            system=system,
            messages=messages,
            tools=TOOL_PARAMS,
            output_config=OUTPUT_CONFIG,
        )
    except anthropic.APIError as api_error:
        reason = unavailable_reason(api_error)
        LOGGER.exception("Claude API request failed (reason=%s)", reason)
        raise AgentUnavailableError(reason) from api_error


def run_tool_use(block: ToolUseBlock, today: date) -> tuple[ToolCall, ToolResultBlockParam]:
    outcome = dispatch_tool(block.name, block.input, today)
    call = ToolCall(
        name=block.name,
        arguments=block.input,
        result=outcome.content,
        is_error=outcome.is_error,
    )
    result_block: ToolResultBlockParam = {
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": outcome.content,
        "is_error": outcome.is_error,
    }
    return call, result_block


def fallback_reply(text: str, messages: list[MessageParam], calls: list[ToolCall]) -> AgentReply:
    history: list[MessageParam] = [*messages, {"role": "assistant", "content": text}]
    return AgentReply(text=text, tool_calls=tuple(calls), history=history)


def finish_reply(
    response: Message, messages: list[MessageParam], calls: list[ToolCall]
) -> AgentReply:
    fallback = STOP_REASON_FALLBACKS.get(response.stop_reason or "")
    if fallback is not None:
        return fallback_reply(fallback, messages, calls)
    text = "".join(block.text for block in response.content if isinstance(block, TextBlock))
    if not text.strip():
        return fallback_reply(EMPTY_REPLY_FALLBACK, messages, calls)
    history: list[MessageParam] = [*messages, response.to_param()]
    return AgentReply(text=text, tool_calls=tuple(calls), history=history)


def reply(
    client: MessageCreator, history: list[MessageParam], user_message: str, today: date
) -> AgentReply:
    messages: list[MessageParam] = [*history, {"role": "user", "content": user_message}]
    system = build_system_prompt(today)
    calls: list[ToolCall] = []
    for _ in range(MAX_TOOL_ROUNDS):
        response = create_message(client, system, messages)
        if response.stop_reason != "tool_use":
            return finish_reply(response, messages, calls)
        messages.append(response.to_param())
        outcomes = [
            run_tool_use(block, today)
            for block in response.content
            if isinstance(block, ToolUseBlock)
        ]
        calls.extend(call for call, _ in outcomes)
        messages.append({"role": "user", "content": [block for _, block in outcomes]})
    return fallback_reply(TOO_MANY_TOOL_ROUNDS_FALLBACK, messages, calls)
