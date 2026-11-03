import logging
from dataclasses import dataclass, field
from datetime import date
from functools import cache
from threading import Lock
from typing import Annotated
from uuid import uuid4

from anthropic.types import MessageParam
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import StringConstraints

from emporio_agent.agent import (
    AgentReply,
    AgentUnavailableError,
    MessageCreator,
    ToolCall,
    UnavailableReason,
    create_client,
    reply,
)

MAX_MESSAGE_LENGTH = 4000
MAX_MESSAGE_ID_LENGTH = 64
INVALID_REQUEST_BODY = {"detail": "invalid_request"}
PACKAGE_LOGGER_NAME = "emporio_agent"
LOG_FORMAT = "%(levelname)s %(name)s %(message)s"
TOOL_OUTCOME_LABELS = {False: "ok", True: "error"}
MessageText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_MESSAGE_LENGTH),
]
MessageId = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_MESSAGE_ID_LENGTH),
]
LOGGER = logging.getLogger(__name__)

logging.basicConfig(format=LOG_FORMAT)
logging.getLogger(PACKAGE_LOGGER_NAME).setLevel(logging.INFO)


@dataclass(frozen=True, slots=True)
class ChatRequest:
    message: MessageText
    message_id: MessageId
    conversation_id: str | None = None


@dataclass(frozen=True, slots=True)
class ChatResponse:
    conversation_id: str
    reply: str


@dataclass(slots=True)
class Conversation:
    conversation_id: str = field(default_factory=lambda: str(uuid4()))
    lock: Lock = field(default_factory=Lock)
    history: list[MessageParam] = field(default_factory=list)
    last_message_id: str | None = None
    last_reply: str = ""


CONVERSATIONS: dict[str, Conversation] = {}
CONVERSATIONS_BY_FIRST_MESSAGE: dict[str, Conversation] = {}

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


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


@app.exception_handler(RequestValidationError)
@app.exception_handler(status.HTTP_400_BAD_REQUEST)
def handle_invalid_request(_request: Request, _error: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=INVALID_REQUEST_BODY,
    )


@app.exception_handler(AgentUnavailableError)
def handle_agent_unavailable(_request: Request, error: AgentUnavailableError) -> JSONResponse:
    LOGGER.warning("chat unavailable reason=%s", error.reason)
    return unavailable_response(error.reason)


@app.exception_handler(Exception)
def handle_unexpected_error(_request: Request, error: Exception) -> JSONResponse:
    LOGGER.error("chat failed unexpectedly error=%s", type(error).__name__)
    return unavailable_response("server")


def find_conversation(chat_request: ChatRequest) -> Conversation:
    known_conversation = CONVERSATIONS.get(chat_request.conversation_id or "")
    if known_conversation is not None:
        return known_conversation
    return CONVERSATIONS_BY_FIRST_MESSAGE.setdefault(chat_request.message_id, Conversation())


def run_agent(conversation: Conversation, message: str) -> AgentReply:
    try:
        return reply(messages_client(), conversation.history, message, date.today())
    except AgentUnavailableError:
        raise
    except Exception as error:
        LOGGER.error("chat failed unexpectedly error=%s", type(error).__name__)
        raise AgentUnavailableError("server") from None


def answer_message(conversation: Conversation, chat_request: ChatRequest) -> AgentReply:
    try:
        return run_agent(conversation, chat_request.message)
    except AgentUnavailableError:
        CONVERSATIONS_BY_FIRST_MESSAGE.pop(chat_request.message_id, None)
        raise


def store_turn(conversation: Conversation, message_id: str, agent_reply: AgentReply) -> None:
    CONVERSATIONS_BY_FIRST_MESSAGE.pop(conversation.last_message_id or "", None)
    conversation.history = agent_reply.history
    conversation.last_message_id = message_id
    conversation.last_reply = agent_reply.text
    CONVERSATIONS[conversation.conversation_id] = conversation


@app.post("/api/chat")
def chat(chat_request: ChatRequest) -> ChatResponse:
    conversation = find_conversation(chat_request)
    with conversation.lock:
        if conversation.last_message_id == chat_request.message_id:
            LOGGER.info("chat conversation=%s replayed", conversation.conversation_id)
            return ChatResponse(
                conversation_id=conversation.conversation_id, reply=conversation.last_reply
            )
        agent_reply = answer_message(conversation, chat_request)
        store_turn(conversation, chat_request.message_id, agent_reply)
    LOGGER.info(
        "chat conversation=%s tools=[%s]",
        conversation.conversation_id,
        describe_tool_calls(agent_reply.tool_calls),
    )
    return ChatResponse(conversation_id=conversation.conversation_id, reply=agent_reply.text)
