import { FAILURE_MESSAGES, GREETING, type UnavailableReason } from "./chat-copy";

export type EntryKind = "customer" | "assistant" | "failure";

export type ConversationEntry = Readonly<{
  id: number;
  kind: EntryKind;
  text: string;
}>;

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

function withEntry(conversation: Conversation, kind: EntryKind, text: string): Conversation {
  const entry = { id: conversation.nextEntryId, kind, text };
  return {
    ...conversation,
    entries: [...conversation.entries, entry],
    nextEntryId: conversation.nextEntryId + 1,
  };
}

export function withCustomerMessage(conversation: Conversation, message: string): Conversation {
  return { ...withEntry(conversation, "customer", message), isWaiting: true };
}

export function withReply(conversation: Conversation, chatReply: ChatReply): Conversation {
  return {
    ...withEntry(conversation, "assistant", chatReply.reply),
    id: chatReply.conversationId,
    isWaiting: false,
  };
}

export function withFailure(conversation: Conversation, reason: UnavailableReason): Conversation {
  return { ...withEntry(conversation, "failure", FAILURE_MESSAGES[reason]), isWaiting: false };
}

export function endsWithFailure(conversation: Conversation): boolean {
  return conversation.entries.at(-1)?.kind === "failure";
}

export function withRetryStarted(conversation: Conversation): Conversation {
  return { ...conversation, entries: conversation.entries.slice(0, -1), isWaiting: true };
}

export function lastCustomerMessage(conversation: Conversation): string | null {
  return conversation.entries.findLast((entry) => entry.kind === "customer")?.text ?? null;
}
