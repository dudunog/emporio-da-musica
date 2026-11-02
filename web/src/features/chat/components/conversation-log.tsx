import type { FunctionComponent, Ref } from "react";
import { CONVERSATION_LABEL } from "../chat-copy";
import { endsWithFailure, type Conversation, type EntryKind } from "../conversation";
import { AssistantBubble } from "./assistant-bubble";
import { CustomerBubble } from "./customer-bubble";
import { FailureBubble } from "./failure-bubble";
import { TypingIndicator } from "./typing-indicator";

const LOG_CLASSES =
  "relative flex min-h-0 flex-1 flex-col items-center gap-4 overflow-y-auto px-page-x py-4 *:w-full *:max-w-column [scrollbar-color:var(--border)_transparent] [scrollbar-gutter:stable_both-edges] [scrollbar-width:thin] focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-focus";

export type EntryBubbleProps = Readonly<{
  text: string;
  onRetry: (() => void) | null;
}>;

const ENTRY_BUBBLES: Record<EntryKind, FunctionComponent<EntryBubbleProps>> = {
  customer: CustomerBubble,
  assistant: AssistantBubble,
  failure: FailureBubble,
};

type ConversationLogProps = Readonly<{
  conversation: Conversation;
  logRef: Ref<HTMLDivElement>;
  onScroll: () => void;
  onRetry: () => void;
}>;

export function ConversationLog({ conversation, logRef, onScroll, onRetry }: ConversationLogProps) {
  const retryableIndex = endsWithFailure(conversation) ? conversation.entries.length - 1 : -1;

  return (
    <div ref={logRef} role="log" aria-label={CONVERSATION_LABEL} tabIndex={0} onScroll={onScroll} className={LOG_CLASSES}>
      {conversation.entries.map(({ id, kind, text }, index) => {
        const Bubble = ENTRY_BUBBLES[kind];
        return <Bubble key={id} text={text} onRetry={index === retryableIndex ? onRetry : null} />;
      })}
      {conversation.isWaiting && <TypingIndicator />}
    </div>
  );
}
