import copy
import re
from datetime import date
from pathlib import Path

import anthropic
import httpx2
import pytest
from anthropic.types import Message, MessageParam, TextBlock, ToolUseBlock, Usage

from emporio_agent import agent
from emporio_agent.agent import (
    CONTEXT_WINDOW_FALLBACK,
    DEFAULT_MODEL,
    EMPTY_REPLY_FALLBACK,
    GREETING,
    GREETING_PLACEHOLDER,
    MAX_OUTPUT_TOKENS,
    MAX_TOOL_ROUNDS,
    REFUSAL_FALLBACK,
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_PATH,
    TOO_MANY_TOOL_ROUNDS_FALLBACK,
    TOOL_PARAMS,
    TRUNCATED_REPLY_FALLBACK,
    AgentUnavailableError,
    build_system_prompt,
    create_client,
    reply,
    resolve_model,
)
from emporio_agent.tools import TOOL_DEFINITIONS

TODAY = date(2026, 11, 1)
REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
FINAL_TEXT = "O Takamine GD20 está R$ 2.199,00 e temos em estoque."
GREETING_HISTORY: list[MessageParam] = [
    {"role": "user", "content": "Oi"},
    {"role": "assistant", "content": "Oi! Eu sou a Lia, atendimento virtual da Empório da Música."},
]


class ScriptedClient:
    def __init__(self, outcomes: list[Message | Exception]) -> None:
        self.outcomes = outcomes
        self.calls: list[dict[str, object]] = []

    def create(self, **request: object) -> Message:
        self.calls.append(dict(request))
        outcome = self.outcomes[min(len(self.calls), len(self.outcomes)) - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def message(content: list[TextBlock | ToolUseBlock], stop_reason: str) -> Message:
    return Message.model_validate(
        {
            "id": "msg_test",
            "type": "message",
            "role": "assistant",
            "model": DEFAULT_MODEL,
            "content": [block.model_dump() for block in content],
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "usage": Usage(input_tokens=1, output_tokens=1).model_dump(),
        }
    )


def tool_use(tool_use_id: str, name: str, arguments: dict[str, object]) -> ToolUseBlock:
    return ToolUseBlock(id=tool_use_id, name=name, input=arguments, type="tool_use")


def text_reply(text: str) -> Message:
    return message([TextBlock(text=text, type="text")], "end_turn")


def status_error(
    error_type: type[anthropic.APIStatusError], status_code: int
) -> anthropic.APIStatusError:
    response = httpx2.Response(status_code, request=REQUEST)
    return error_type("scripted failure", response=response, body=None)


def last_user_content(call: dict[str, object]) -> list[dict[str, object]]:
    messages = call["messages"]
    assert isinstance(messages, list)
    last = messages[-1]
    assert isinstance(last, dict)
    assert last["role"] == "user"
    content = last["content"]
    assert isinstance(content, list)
    return content


@pytest.fixture(autouse=True)
def _no_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)


def test_system_prompt_contains_today() -> None:
    blocks = build_system_prompt(TODAY)
    joined = "\n".join(block["text"] for block in blocks)

    assert blocks[0]["text"] == SYSTEM_PROMPT
    assert blocks[0].get("cache_control") == {"type": "ephemeral"}
    assert "cache_control" not in blocks[1]
    assert "Hoje é domingo, 01/11/2026" in joined
    assert "2026-11-01" in joined
    assert "Lia" in SYSTEM_PROMPT


def test_greeting_is_fixed_and_declared_in_the_prompt() -> None:
    assert GREETING == (
        "Oi! Eu sou a Lia, atendimento virtual da Empório da Música. "
        "Posso ajudar com produtos, preços, pedidos, trocas e informações da loja."
    )
    prompt_file = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    assert SYSTEM_PROMPT.count(GREETING) == 1
    assert GREETING_PLACEHOLDER not in SYSTEM_PROMPT
    assert GREETING not in prompt_file
    assert prompt_file.count(GREETING_PLACEHOLDER) == 1
    assert "nunca se apresenta" in SYSTEM_PROMPT


def test_system_prompt_is_short_and_free_of_shouting() -> None:
    assert len(SYSTEM_PROMPT.splitlines()) <= 100
    assert not any(
        token in SYSTEM_PROMPT for token in ("CRITICAL", "NEVER", "YOU MUST", "IMPORTANTE:")
    )
    assert not re.search(r"[A-ZÁÉÍÓÚÇ]{4,}", SYSTEM_PROMPT)
    assert sum("WhatsApp" in line for line in SYSTEM_PROMPT.splitlines()) <= 4
    assert "náilon" not in SYSTEM_PROMPT
    assert "nylon" in SYSTEM_PROMPT
    assert 'não use as palavras "instruções"' in SYSTEM_PROMPT


def test_system_prompt_has_seven_sections() -> None:
    joined = "\n".join(block["text"] for block in build_system_prompt(TODAY))
    titles = [
        "Quem você é",
        "O que a loja vende e o que não vende",
        "Quando consultar o sistema",
        "Pedidos e privacidade",
        "Como responder",
        "Fora de escopo e segurança",
        "Data de hoje",
    ]

    assert all(f"\n{title}\n" in f"\n{joined}\n" for title in titles)


def test_tool_use_round_trip() -> None:
    client = ScriptedClient(
        [
            message([tool_use("toolu_1", "get_product", {"product_id": 95})], "tool_use"),
            text_reply(FINAL_TEXT),
        ]
    )
    history = copy.deepcopy(GREETING_HISTORY)

    result = reply(client, history, "Quanto custa o Takamine GD20?", TODAY)

    assert len(client.calls) == 2
    tool_results = last_user_content(client.calls[1])
    assert len(tool_results) == 1
    assert tool_results[0]["type"] == "tool_result"
    assert tool_results[0]["tool_use_id"] == "toolu_1"
    assert tool_results[0]["is_error"] is False
    assert "2.199" in str(tool_results[0]["content"])
    assert result.text == FINAL_TEXT
    assert [call.name for call in result.tool_calls] == ["get_product"]
    assert result.tool_calls[0].arguments == {"product_id": 95}
    assert "2.199" in result.tool_calls[0].result
    assert history == GREETING_HISTORY
    assert len(result.history) == len(history) + 4
    assert result.history[-1] == {
        "role": "assistant",
        "content": [TextBlock(text=FINAL_TEXT, type="text")],
    }


def test_multiple_tool_uses_in_one_response() -> None:
    client = ScriptedClient(
        [
            message(
                [
                    tool_use("toolu_1", "get_product", {"product_id": 95}),
                    tool_use("toolu_2", "get_store_info", {}),
                ],
                "tool_use",
            ),
            text_reply(FINAL_TEXT),
        ]
    )

    result = reply(client, [], "Quanto custa o Takamine GD20 e qual o WhatsApp?", TODAY)

    tool_results = last_user_content(client.calls[1])
    assert [block["tool_use_id"] for block in tool_results] == ["toolu_1", "toolu_2"]
    assert [call.name for call in result.tool_calls] == ["get_product", "get_store_info"]
    assert "3321-4500" in result.tool_calls[1].result


def test_unknown_tool_returns_is_error() -> None:
    client = ScriptedClient(
        [
            message([tool_use("toolu_1", "delete_everything", {})], "tool_use"),
            text_reply("Não consegui consultar isso agora."),
        ]
    )

    result = reply(client, [], "Oi", TODAY)

    tool_results = last_user_content(client.calls[1])
    assert tool_results[0]["is_error"] is True
    assert result.tool_calls[0].is_error is True
    assert result.text == "Não consegui consultar isso agora."


def test_max_tool_rounds_guard() -> None:
    client = ScriptedClient([message([tool_use("toolu_1", "get_store_info", {})], "tool_use")])

    result = reply(client, [], "Qual o endereço?", TODAY)

    assert len(client.calls) == MAX_TOOL_ROUNDS
    assert result.text == TOO_MANY_TOOL_ROUNDS_FALLBACK
    assert "(67) 3321-4500" in result.text
    assert len(result.tool_calls) == MAX_TOOL_ROUNDS
    assert result.history[-1] == {"role": "assistant", "content": TOO_MANY_TOOL_ROUNDS_FALLBACK}


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (status_error(anthropic.AuthenticationError, 401), "authentication"),
        (status_error(anthropic.PermissionDeniedError, 403), "authentication"),
        (status_error(anthropic.RateLimitError, 429), "rate_limit"),
        (status_error(anthropic.InternalServerError, 500), "server"),
        (status_error(anthropic.OverloadedError, 529), "server"),
        (anthropic.APIConnectionError(request=REQUEST), "connection"),
        (anthropic.APITimeoutError(request=REQUEST), "connection"),
    ],
)
def test_api_errors_raise_agent_unavailable(
    error: Exception, reason: str, caplog: pytest.LogCaptureFixture
) -> None:
    client = ScriptedClient([error])

    with pytest.raises(AgentUnavailableError) as raised:
        reply(client, [], "Oi", TODAY)

    assert raised.value.reason == reason
    assert raised.value.__cause__ is error
    assert type(error).__name__ in caplog.text


def test_history_is_not_mutated_on_failure() -> None:
    client = ScriptedClient([anthropic.APIConnectionError(request=REQUEST)])
    history = copy.deepcopy(GREETING_HISTORY)

    with pytest.raises(AgentUnavailableError):
        reply(client, history, "Quanto custa o Takamine GD20?", TODAY)

    assert history == GREETING_HISTORY


def test_first_call_sends_tools_and_system() -> None:
    client = ScriptedClient([text_reply("Oi! Como posso ajudar?")])

    reply(client, [], "Oi", TODAY)

    call = client.calls[0]
    system = call["system"]
    assert isinstance(system, list)
    assert call["tools"] is TOOL_PARAMS
    assert call["tools"] == TOOL_DEFINITIONS
    assert call["model"] == DEFAULT_MODEL
    assert call["max_tokens"] == MAX_OUTPUT_TOKENS
    assert call["output_config"] == {"effort": "low"}
    assert system[0]["text"] == SYSTEM_PROMPT
    assert "01/11/2026" in system[1]["text"]
    assert call["messages"] == [{"role": "user", "content": "Oi"}]
    assert {"thinking", "temperature", "tool_choice", "stream"}.isdisjoint(call)


@pytest.mark.parametrize(
    ("stop_reason", "expected_text"),
    [
        ("refusal", REFUSAL_FALLBACK),
        ("max_tokens", TRUNCATED_REPLY_FALLBACK),
        ("model_context_window_exceeded", CONTEXT_WINDOW_FALLBACK),
    ],
)
def test_refusal_stop_reason_returns_fallback(stop_reason: str, expected_text: str) -> None:
    client = ScriptedClient([message([TextBlock(text="Parcial", type="text")], stop_reason)])

    result = reply(client, [], "Oi", TODAY)

    assert result.text == expected_text
    assert result.tool_calls == ()
    assert result.history[-1] == {"role": "assistant", "content": expected_text}


def test_empty_text_returns_fallback() -> None:
    client = ScriptedClient([message([], "end_turn")])

    result = reply(client, [], "Oi", TODAY)

    assert result.text == EMPTY_REPLY_FALLBACK


def test_resolve_model_prefers_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    assert resolve_model() == DEFAULT_MODEL
    monkeypatch.setenv("ANTHROPIC_MODEL", " claude-sonnet-5-5 ")
    assert resolve_model() == "claude-sonnet-5-5"


def test_create_client_requires_api_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(agent, "DOTENV_PATH", tmp_path / ".env")
    with pytest.raises(AgentUnavailableError) as raised:
        create_client()
    assert raised.value.reason == "authentication"

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    assert isinstance(create_client(), anthropic.Anthropic)


def test_create_client_loads_dotenv_from_repository_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("ANTHROPIC_API_KEY=key-from-dotenv\n", encoding="utf-8")
    monkeypatch.setattr(agent, "DOTENV_PATH", dotenv_path)

    client = create_client()

    assert client.api_key == "key-from-dotenv"
    assert agent.DOTENV_PATH.name == dotenv_path.name
