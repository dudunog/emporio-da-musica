import type { FunctionComponent, Ref } from "react";
import { CONVERSATION_LABEL, CUSTOMER_NAME } from "../chat-copy";
import { retryableEntryId, type Conversation, type EntryKind } from "../conversation";
import { withUnbreakableCurrency } from "../currency-text";
import { AssistantBubble, type EntryBubbleProps } from "./assistant-row";
import { FailureBubble } from "./failure-bubble";
import { TypingIndicator } from "./typing-indicator";

const LOG_CLASSES =
  "relative flex min-h-0 flex-1 flex-col items-center gap-4 overflow-y-auto px-page-x py-4 *:w-full *:max-w-column [scrollbar-color:var(--border)_transparent] [scrollbar-gutter:stable_both-edges] [scrollbar-width:thin] focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-focus";

function CustomerBubble({ text }: EntryBubbleProps) {
  return (
    <article aria-label={CUSTOMER_NAME} className="flex animate-bubble-in justify-end motion-reduce:animate-none">
      <p className="max-w-bubble-user rounded-bubble rounded-br-bubble-inner bg-user px-bubble-x py-bubble-y text-body whitespace-pre-wrap wrap-anywhere text-on-user selection:bg-on-user selection:text-user">
        {withUnbreakableCurrency(text)}
      </p>
    </article>
  );
}

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
  const retryableId = retryableEntryId(conversation);

  return (
    <div ref={logRef} role="log" aria-label={CONVERSATION_LABEL} tabIndex={0} onScroll={onScroll} className={LOG_CLASSES}>
      {conversation.entries.map(({ id, kind, text }) => {
        const Bubble = ENTRY_BUBBLES[kind];
        return <Bubble key={id} text={text} onRetry={id === retryableId ? onRetry : null} />;
      })}
      {conversation.isWaiting && <TypingIndicator />}
    </div>
  );
}
