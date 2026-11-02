import { AssistantMarkdown } from "./assistant-markdown";
import { ASSISTANT_BUBBLE_CLASSES, AssistantRow } from "./assistant-row";
import type { EntryBubbleProps } from "./conversation-log";

export function AssistantBubble({ text }: EntryBubbleProps) {
  return (
    <AssistantRow>
      <div className={`${ASSISTANT_BUBBLE_CLASSES} bg-agent text-ink`}>
        <AssistantMarkdown text={text} />
      </div>
    </AssistantRow>
  );
}
