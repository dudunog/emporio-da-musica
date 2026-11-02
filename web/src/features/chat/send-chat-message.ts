import { FAILURE_MESSAGES, type UnavailableReason } from "./chat-copy";
import type { ChatReply } from "./conversation";

const CHAT_ENDPOINT = "/api/chat";
const FALLBACK_REASON: UnavailableReason = "connection";

export type ChatRequest = Readonly<{
  conversationId: string | null;
  message: string;
}>;

export class ChatUnavailableError extends Error {
  readonly reason: UnavailableReason;

  constructor(reason: UnavailableReason) {
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

async function postMessage({ conversationId, message }: ChatRequest): Promise<Response> {
  const request = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversation_id: conversationId, message }),
  };
  return fetch(CHAT_ENDPOINT, request).catch(() => {
    throw new ChatUnavailableError(FALLBACK_REASON);
  });
}

function parseFailureReason(body: unknown): UnavailableReason {
  return isRecord(body) && isUnavailableReason(body.reason) ? body.reason : FALLBACK_REASON;
}

function parseChatReply(body: unknown): ChatReply {
  if (!isRecord(body) || typeof body.conversation_id !== "string" || typeof body.reply !== "string") {
    throw new ChatUnavailableError(FALLBACK_REASON);
  }
  return { conversationId: body.conversation_id, reply: body.reply };
}

export function failureReasonOf(error: unknown): UnavailableReason {
  return error instanceof ChatUnavailableError ? error.reason : FALLBACK_REASON;
}

export async function sendChatMessage(request: ChatRequest): Promise<ChatReply> {
  const response = await postMessage(request);
  const body = await readJson(response);
  if (!response.ok) throw new ChatUnavailableError(parseFailureReason(body));
  return parseChatReply(body);
}
