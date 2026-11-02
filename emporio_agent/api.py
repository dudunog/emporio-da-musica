import logging
from dataclasses import dataclass, field
from datetime import date
from functools import cache
from threading import Lock
from typing import Annotated
from uuid import uuid4

from anthropic.types import MessageParam
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import StringConstraints

from emporio_agent.agent import (
    AgentUnavailableError,
    MessageCreator,
    ToolCall,
    UnavailableReason,
    create_client,
    reply,
)

MAX_MESSAGE_LENGTH = 4000
PACKAGE_LOGGER_NAME = "emporio_agent"
LOG_FORMAT = "%(levelname)s %(name)s %(message)s"
TOOL_OUTCOME_LABELS = {False: "ok", True: "error"}
MessageText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_MESSAGE_LENGTH),
]
LOGGER = logging.getLogger(__name__)

logging.basicConfig(format=LOG_FORMAT)
logging.getLogger(PACKAGE_LOGGER_NAME).setLevel(logging.INFO)


@dataclass(frozen=True, slots=True)
class ChatRequest:
    message: MessageText
    conversation_id: str | None = None


@dataclass(frozen=True, slots=True)
class ChatResponse:
    conversation_id: str
    reply: str


@dataclass(frozen=True, slots=True)
class UnavailableResponse:
    reason: UnavailableReason


@dataclass(slots=True)
class Conversation:
    conversation_id: str = field(default_factory=lambda: str(uuid4()))
    lock: Lock = field(default_factory=Lock)
    history: list[MessageParam] = field(default_factory=list)


CONVERSATIONS: dict[str, Conversation] = {}

app = FastAPI(title="Empório da Música")


@cache
def messages_client() -> MessageCreator:
    return create_client().messages


def describe_tool_calls(tool_calls: tuple[ToolCall, ...]) -> str:
    return ",".join(f"{call.name}:{TOOL_OUTCOME_LABELS[call.is_error]}" for call in tool_calls)


def unavailable_response(reason: UnavailableReason) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"reason": reason},
    )


@app.exception_handler(AgentUnavailableError)
def handle_agent_unavailable(_request: Request, error: AgentUnavailableError) -> JSONResponse:
    LOGGER.warning("chat unavailable reason=%s", error.reason)
    return unavailable_response(error.reason)


@app.exception_handler(Exception)
def handle_unexpected_error(_request: Request, error: Exception) -> JSONResponse:
    LOGGER.error("chat failed unexpectedly error=%s", type(error).__name__)
    return unavailable_response("server")


@app.post(
    "/api/chat",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": UnavailableResponse}},
)
def chat(chat_request: ChatRequest) -> ChatResponse:
    conversation = CONVERSATIONS.get(chat_request.conversation_id or "") or Conversation()
    with conversation.lock:
        agent_reply = reply(
            messages_client(), conversation.history, chat_request.message, date.today()
        )
        conversation.history = agent_reply.history
    CONVERSATIONS[conversation.conversation_id] = conversation
    LOGGER.info(
        "chat conversation=%s tools=[%s]",
        conversation.conversation_id,
        describe_tool_calls(agent_reply.tool_calls),
    )
    return ChatResponse(conversation_id=conversation.conversation_id, reply=agent_reply.text)
