import { FAILURE_MESSAGES, GREETING, type UnavailableReason } from "./chat-copy";

export type EntryKind = "customer" | "assistant" | "failure";

export type FailureReason = UnavailableReason | "rejected";

type CustomerContent = Readonly<{ kind: "customer"; text: string; messageId: string }>;
type ReplyContent = Readonly<{ kind: "assistant" | "failure"; text: string }>;
type ConversationEntry = Readonly<{ id: number }> & (CustomerContent | ReplyContent);

export type Conversation = Readonly<{
  id: string | null;
  entries: readonly ConversationEntry[];
  nextEntryId: number;
  isWaiting: boolean;
}>;

export type ChatReply = Readonly<{
  conversationId: string;
  reply: string;
}>;

export const INITIAL_CONVERSATION: Conversation = {
  id: null,
  entries: [{ id: 0, kind: "assistant", text: GREETING }],
  nextEntryId: 1,
  isWaiting: false,
};

function withEntry(conversation: Conversation, content: CustomerContent | ReplyContent): Conversation {
  return {
    ...conversation,
    entries: [...conversation.entries, { ...content, id: conversation.nextEntryId }],
    nextEntryId: conversation.nextEntryId + 1,
  };
}

export function withCustomerMessage(conversation: Conversation, text: string, messageId: string): Conversation {
  return { ...withEntry(conversation, { kind: "customer", text, messageId }), isWaiting: true };
}

export function withReply(conversation: Conversation, chatReply: ChatReply): Conversation {
  return {
    ...withEntry(conversation, { kind: "assistant", text: chatReply.reply }),
    id: chatReply.conversationId,
    isWaiting: false,
  };
}

export function withFailure(conversation: Conversation, reason: FailureReason): Conversation {
  if (reason === "rejected") return { ...conversation, entries: conversation.entries.slice(0, -1), isWaiting: false };
  return { ...withEntry(conversation, { kind: "failure", text: FAILURE_MESSAGES[reason] }), isWaiting: false };
}

export function endsWithFailure(conversation: Conversation): boolean {
  return conversation.entries.at(-1)?.kind === "failure";
}

export function retryableEntryId(conversation: Conversation): number | null {
  return endsWithFailure(conversation) ? (conversation.entries.at(-1)?.id ?? null) : null;
}

export function withRetryStarted(conversation: Conversation): Conversation {
  return { ...conversation, entries: conversation.entries.slice(0, -1), isWaiting: true };
}

export function lastCustomerMessage(conversation: Conversation): CustomerContent | null {
  return conversation.entries.findLast((entry) => entry.kind === "customer") ?? null;
}
