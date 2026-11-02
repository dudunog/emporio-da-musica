import base64
import html
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
COMPOSER_PLACEHOLDER = "Escreva sua mensagem"
TYPING_INDICATOR_LABEL = "Lia está digitando"
RETRY_BUTTON_LABEL = "Tentar de novo"
SEND_BUTTON_LABEL = "Enviar mensagem"
SKIP_LINK_LABEL = "Ir para o conteúdo"
SERVICE_UNAVAILABLE_MESSAGE = (
    "Nosso atendimento está indisponível neste momento. Tente de novo em alguns minutos."
)
ERROR_MESSAGES: dict[UnavailableReason, str] = {
    "authentication": SERVICE_UNAVAILABLE_MESSAGE,
    "server": SERVICE_UNAVAILABLE_MESSAGE,
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
CHAT_BEHAVIOR_SCRIPT_PATH = APP_DIR / "ui" / "chat-behavior.js"
AVATAR_PATH = APP_DIR / "ui" / "avatar.svg"
AVATARS: dict[str, str | None] = {"assistant": str(AVATAR_PATH), "user": None}
HISTORY_KEY = "history"
TRANSCRIPT_KEY = "transcript"
PENDING_MESSAGE_KEY = "pending_message"
RETRY_CONTAINER_KEY = "resend"
RETRY_BUTTON_KEY = "resend_button"
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
CUSTOMER_TEXT_TEMPLATE = '<p class="customer-text">{text}</p>'
ERROR_BUBBLE_TEMPLATE = (
    '<div class="error-bubble" role="alert"><span class="error-icon"></span><p>{text}</p></div>'
)
SEND_BUTTON_LABEL_MARKER = "__SEND_BUTTON_LABEL__"
SKIP_LINK_LABEL_MARKER = "__SKIP_LINK_LABEL__"
CONNECTION_LOST_LABEL_MARKER = "__CONNECTION_LOST_LABEL__"
MARKDOWN_DOLLAR = "$"
MARKDOWN_DOLLAR_ESCAPED = "\\$"
CURRENCY_PREFIX_WITH_SPACE = "R$ "
CURRENCY_PREFIX_NO_BREAK = "R$\u00a0"
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


def install_chat_behavior() -> None:
    substitutions = {
        SEND_BUTTON_LABEL_MARKER: SEND_BUTTON_LABEL,
        SKIP_LINK_LABEL_MARKER: SKIP_LINK_LABEL,
        CONNECTION_LOST_LABEL_MARKER: ERROR_MESSAGES["connection"],
    }
    script = CHAT_BEHAVIOR_SCRIPT_PATH.read_text(encoding="utf-8")
    for marker, value in substitutions.items():
        script = script.replace(marker, value)
    st.html(f"<script>{script}</script>", unsafe_allow_javascript=True)


def with_unbreakable_currency(text: str) -> str:
    return text.replace(CURRENCY_PREFIX_WITH_SPACE, CURRENCY_PREFIX_NO_BREAK)


def as_markdown(text: str) -> str:
    return with_unbreakable_currency(text).replace(MARKDOWN_DOLLAR, MARKDOWN_DOLLAR_ESCAPED)


def render_customer_text(text: str) -> None:
    st.html(CUSTOMER_TEXT_TEMPLATE.format(text=html.escape(with_unbreakable_currency(text))))


def render_assistant_text(text: str) -> None:
    st.markdown(as_markdown(text))


BUBBLE_RENDERERS = {"user": render_customer_text, "assistant": render_assistant_text}


def request_retry() -> None:
    transcript = conversation_transcript()
    if not transcript or transcript[-1]["kind"] != "error":
        return
    transcript.pop()
    st.session_state[PENDING_MESSAGE_KEY] = transcript[-1]["text"]


def render_error_bubble(text: str, show_retry: bool) -> None:
    with st.container():
        st.html(ERROR_BUBBLE_TEMPLATE.format(text=text))
        if not show_retry:
            st.empty()
            return
        with st.container(key=RETRY_CONTAINER_KEY):
            st.button(RETRY_BUTTON_LABEL, key=RETRY_BUTTON_KEY, on_click=request_retry)


def render_bubble(bubble: Bubble, show_retry: bool) -> None:
    with st.chat_message(bubble["role"], avatar=AVATARS[bubble["role"]]):
        if bubble["kind"] == "error":
            render_error_bubble(bubble["text"], show_retry)
            return
        BUBBLE_RENDERERS[bubble["role"]](bubble["text"])


def render_transcript() -> None:
    transcript = conversation_transcript()
    last_index = len(transcript) - 1
    for index, bubble in enumerate(transcript):
        render_bubble(bubble, show_retry=bubble["kind"] == "error" and index == last_index)


def take_pending_message() -> str | None:
    pending_message: str | None = st.session_state.get(PENDING_MESSAGE_KEY)
    prompt = st.chat_input(
        placeholder=COMPOSER_PLACEHOLDER,
        submit_mode="disable",
        disabled=pending_message is not None,
    )
    if pending_message is not None:
        return pending_message
    message = prompt.strip() if isinstance(prompt, str) else ""
    if not message:
        return None
    conversation_transcript().append({"role": "user", "text": message, "kind": "message"})
    st.session_state[PENDING_MESSAGE_KEY] = message
    return message


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
    with placeholder.container():
        render_error_bubble(text, show_retry=True)
    conversation_transcript().append({"role": "assistant", "text": text, "kind": "error"})


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
        except Exception:
            LOGGER.exception("Unexpected failure while answering")
            show_unavailable(placeholder, "server")
            return
        placeholder.markdown(as_markdown(agent_reply.text))
    record_reply(agent_reply)


def finish_pending_message() -> None:
    del st.session_state[PENDING_MESSAGE_KEY]
    st.rerun()


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
        finish_pending_message()
    install_chat_behavior()


main()
