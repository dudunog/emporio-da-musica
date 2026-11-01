import base64
import logging
from datetime import date
from pathlib import Path
from typing import Literal, TypedDict

import anthropic
import streamlit as st
from anthropic.types import MessageParam
from streamlit.delta_generator import DeltaGenerator

from emporio_agent.agent import (
    GREETING,
    AgentReply,
    AgentUnavailableError,
    UnavailableReason,
    create_client,
    reply,
)

PAGE_TITLE = "Empório da Música"
STORE_NAME = "Empório da Música"
STORE_TAGLINE = "Sua música começa aqui"
ASSISTANT_NAME = "Lia"
COMPOSER_PLACEHOLDER = "Escreva sua mensagem"
TYPING_INDICATOR_LABEL = "Lia está digitando"
RETRY_BUTTON_LABEL = "Tentar de novo"
ERROR_MESSAGES: dict[UnavailableReason, str] = {
    "authentication": (
        "Nosso atendimento está indisponível neste momento. Tente de novo em alguns minutos."
    ),
    "server": (
        "Nosso atendimento está indisponível neste momento. Tente de novo em alguns minutos."
    ),
    "connection": "Sem conexão agora. Verifique sua internet e tente de novo.",
    "rate_limit": "Estamos com muitas conversas agora. Tente de novo em instantes.",
}
UNAVAILABLE_LOG_HINTS: dict[UnavailableReason, str] = {
    "authentication": "ANTHROPIC_API_KEY is missing or invalid; copy .env.example to .env",
    "server": "the model API returned a server error",
    "connection": "could not reach the model API",
    "rate_limit": "the model API rate limit was hit",
}

APP_DIR = Path(__file__).parent
STYLES_PATH = APP_DIR / "ui" / "styles.css"
AVATAR_PATH = APP_DIR / "ui" / "avatar.svg"
AVATARS: dict[str, str | None] = {"assistant": str(AVATAR_PATH), "user": None}
HISTORY_KEY = "history"
TRANSCRIPT_KEY = "transcript"
RETRY_MESSAGE_KEY = "retry_message"
RUN_COUNTER_KEY = "run_counter"
RETRY_CONTAINER_KEY = "retry"
RETRY_BUTTON_KEY = "retry_button"
HEADER_TEMPLATE = (
    '<header class="store-header">'
    '<img class="store-avatar" src="{avatar}" alt="">'
    '<div><p class="store-name">{name}</p><p class="store-tagline">{tagline}</p></div>'
    "</header>"
)
TYPING_INDICATOR_TEMPLATE = (
    '<div class="typing" role="status">'
    '<span class="typing-dot"></span>'
    '<span class="typing-dot"></span>'
    '<span class="typing-dot"></span>'
    '<span class="typing-label">{label}</span>'
    "</div>"
)
ERROR_BUBBLE_TEMPLATE = (
    '<div class="error-bubble" role="alert"><span class="error-icon"></span><p>{text}</p></div>'
)
FOCUS_SCRIPT_TEMPLATE = """<script>
(() => {{
  document.documentElement.lang = "pt-BR";
  const selector = 'textarea[data-testid="stChatInputTextArea"]';
  let attempts = 0;
  const timer = setInterval(() => {{
    attempts += 1;
    const composer = document.querySelector(selector);
    if (composer && !composer.disabled) {{
      clearInterval(timer);
      if (document.activeElement !== composer) composer.focus({{ preventScroll: true }});
      return;
    }}
    if (attempts >= 600) clearInterval(timer);
  }}, 100);
}})();
</script><!-- {nonce} -->"""
MARKDOWN_DOLLAR = "$"
MARKDOWN_DOLLAR_ESCAPED = "\\$"
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


class Bubble(TypedDict):
    role: Literal["user", "assistant"]
    text: str
    kind: Literal["message", "error"]


@st.cache_resource(show_spinner=False)
def cached_client() -> anthropic.Anthropic:
    return create_client()


def conversation_history() -> list[MessageParam]:
    history: list[MessageParam] = st.session_state[HISTORY_KEY]
    return history


def conversation_transcript() -> list[Bubble]:
    transcript: list[Bubble] = st.session_state[TRANSCRIPT_KEY]
    return transcript


def next_run_nonce() -> int:
    run_count: int = st.session_state.get(RUN_COUNTER_KEY, 0)
    st.session_state[RUN_COUNTER_KEY] = run_count + 1
    return run_count + 1


def ensure_conversation() -> None:
    if HISTORY_KEY in st.session_state:
        return
    opening_history: list[MessageParam] = []
    opening_transcript: list[Bubble] = [{"role": "assistant", "text": GREETING, "kind": "message"}]
    st.session_state[HISTORY_KEY] = opening_history
    st.session_state[TRANSCRIPT_KEY] = opening_transcript


def inject_styles() -> None:
    css = STYLES_PATH.read_text(encoding="utf-8")
    st.html(f"<style>{css}</style>")


def avatar_data_uri() -> str:
    encoded = base64.b64encode(AVATAR_PATH.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def render_header() -> None:
    st.html(
        HEADER_TEMPLATE.format(avatar=avatar_data_uri(), name=STORE_NAME, tagline=STORE_TAGLINE)
    )


def focus_composer() -> None:
    st.html(FOCUS_SCRIPT_TEMPLATE.format(nonce=next_run_nonce()), unsafe_allow_javascript=True)


def as_markdown(text: str) -> str:
    return text.replace(MARKDOWN_DOLLAR, MARKDOWN_DOLLAR_ESCAPED)


def request_retry() -> None:
    transcript = conversation_transcript()
    if not transcript or transcript[-1]["kind"] != "error":
        return
    transcript.pop()
    st.session_state[RETRY_MESSAGE_KEY] = transcript[-1]["text"]


def render_error_bubble(text: str, show_retry: bool) -> None:
    st.html(ERROR_BUBBLE_TEMPLATE.format(text=text))
    if not show_retry:
        return
    with st.container(key=RETRY_CONTAINER_KEY):
        st.button(RETRY_BUTTON_LABEL, key=RETRY_BUTTON_KEY, on_click=request_retry)


def render_bubble(bubble: Bubble, show_retry: bool) -> None:
    with st.chat_message(bubble["role"], avatar=AVATARS[bubble["role"]]):
        if bubble["kind"] == "error":
            render_error_bubble(bubble["text"], show_retry)
            return
        st.markdown(as_markdown(bubble["text"]))


def render_transcript() -> None:
    transcript = conversation_transcript()
    last_index = len(transcript) - 1
    for index, bubble in enumerate(transcript):
        render_bubble(bubble, show_retry=bubble["kind"] == "error" and index == last_index)


def take_pending_message() -> str | None:
    prompt = st.chat_input(placeholder=COMPOSER_PLACEHOLDER, submit_mode="disable")
    if isinstance(prompt, str) and prompt.strip():
        conversation_transcript().append({"role": "user", "text": prompt, "kind": "message"})
        return prompt
    retry_message: str | None = st.session_state.pop(RETRY_MESSAGE_KEY, None)
    return retry_message


def record_reply(agent_reply: AgentReply) -> None:
    st.session_state[HISTORY_KEY] = agent_reply.history
    conversation_transcript().append(
        {"role": "assistant", "text": agent_reply.text, "kind": "message"}
    )
    tool_summary = ", ".join(
        f"{call.name}({'error' if call.is_error else 'ok'})" for call in agent_reply.tool_calls
    )
    LOGGER.info("Agent replied; tools: %s", tool_summary or "none")


def show_unavailable(placeholder: DeltaGenerator, reason: UnavailableReason) -> None:
    LOGGER.error("Agent unavailable (reason=%s): %s", reason, UNAVAILABLE_LOG_HINTS[reason])
    text = ERROR_MESSAGES[reason]
    conversation_transcript().append({"role": "assistant", "text": text, "kind": "error"})
    with placeholder.container():
        render_error_bubble(text, show_retry=True)


def answer(user_message: str) -> None:
    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        placeholder = st.empty()
        placeholder.html(TYPING_INDICATOR_TEMPLATE.format(label=TYPING_INDICATOR_LABEL))
        try:
            client = cached_client()
            agent_reply = reply(client.messages, conversation_history(), user_message, date.today())
        except AgentUnavailableError as unavailable_error:
            show_unavailable(placeholder, unavailable_error.reason)
            return
        placeholder.markdown(as_markdown(agent_reply.text))
    record_reply(agent_reply)


def main() -> None:
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=str(AVATAR_PATH),
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    inject_styles()
    render_header()
    ensure_conversation()
    pending_message = take_pending_message()
    render_transcript()
    if pending_message is not None:
        answer(pending_message)
    focus_composer()


main()
