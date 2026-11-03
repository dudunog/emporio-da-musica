import type { ReactNode } from "react";
import { ASSISTANT_NAME } from "../chat-copy";
import { AssistantMarkdown } from "./assistant-markdown";
import { StoreAvatar } from "./store-avatar";

const BUBBLE_CLASSES = "max-w-bubble-agent min-w-0 rounded-bubble rounded-bl-bubble-inner px-bubble-x py-bubble-y text-body wrap-anywhere";

export type EntryBubbleProps = Readonly<{
  text: string;
  onRetry: (() => void) | null;
}>;

type AssistantRowProps = Readonly<{
  surfaceClasses: string;
  children: ReactNode;
}>;

export function AssistantRow({ surfaceClasses, children }: AssistantRowProps) {
  return (
    <article aria-label={ASSISTANT_NAME} className="flex animate-bubble-in items-end gap-2 motion-reduce:animate-none">
      <StoreAvatar placement="bubble" />
      <div className={`${BUBBLE_CLASSES} ${surfaceClasses}`}>{children}</div>
    </article>
  );
}

export function AssistantBubble({ text }: EntryBubbleProps) {
  return (
    <AssistantRow surfaceClasses="bg-agent text-ink">
      <AssistantMarkdown text={text} />
    </AssistantRow>
  );
}
