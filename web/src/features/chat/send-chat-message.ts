import { FAILURE_MESSAGES, type UnavailableReason } from "./chat-copy";
import type { ChatReply, FailureReason } from "./conversation";

const CHAT_ENDPOINT = "/api/chat";
const FALLBACK_REASON: UnavailableReason = "connection";
const REJECTED_STATUS = 422;
const MESSAGE_ID_BYTES = 16;

type ChatRequest = Readonly<{
  conversationId: string | null;
  messageId: string;
  message: string;
}>;

export class ChatRequestError extends Error {
  readonly reason: FailureReason;

  constructor(reason: FailureReason) {
    super(reason);
    this.reason = reason;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isUnavailableReason(value: unknown): value is UnavailableReason {
  return typeof value === "string" && Object.hasOwn(FAILURE_MESSAGES, value);
}

async function readJson(response: Response): Promise<unknown> {
  return response.json().catch(() => null);
}

async function postChatMessage({ conversationId, messageId, message }: ChatRequest): Promise<Response> {
  return fetch(CHAT_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversation_id: conversationId, message_id: messageId, message }),
  });
}

function parseFailureReason(status: number, body: unknown): FailureReason {
  if (status === REJECTED_STATUS) return "rejected";
  return isRecord(body) && isUnavailableReason(body.reason) ? body.reason : FALLBACK_REASON;
}

function parseChatReply(body: unknown): ChatReply {
  if (!isRecord(body) || typeof body.conversation_id !== "string" || typeof body.reply !== "string" || body.reply === "") {
    throw new ChatRequestError(FALLBACK_REASON);
  }
  return { conversationId: body.conversation_id, reply: body.reply };
}

export function createMessageId(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(MESSAGE_ID_BYTES));
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function failureReasonOf(error: unknown): FailureReason {
  return error instanceof ChatRequestError ? error.reason : FALLBACK_REASON;
}

export async function sendChatMessage(request: ChatRequest): Promise<ChatReply> {
  const response = await postChatMessage(request);
  const body = await readJson(response);
  if (!response.ok) throw new ChatRequestError(parseFailureReason(response.status, body));
  return parseChatReply(body);
}
