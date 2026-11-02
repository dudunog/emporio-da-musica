import { RETRY_LABEL } from "../chat-copy";
import { ASSISTANT_BUBBLE_CLASSES, AssistantRow } from "./assistant-row";
import type { EntryBubbleProps } from "./conversation-log";

const RETRY_BUTTON_CLASSES =
  "relative mt-4 min-h-retry cursor-pointer rounded-action border border-line bg-action px-4 text-action font-medium text-failure transition-colors before:absolute before:-inset-retry-outset before:content-[''] hover:border-failure focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus";

function FailureIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" fill="none" className="mt-failure-icon-top size-failure-icon shrink-0 text-failure">
      <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="2" />
      <path d="M8 4.5v4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="8" cy="11.25" r="1.1" fill="currentColor" />
    </svg>
  );
}

export function FailureBubble({ text, onRetry }: EntryBubbleProps) {
  return (
    <AssistantRow>
      <div className={`${ASSISTANT_BUBBLE_CLASSES} border border-failure bg-failure-surface text-ink`}>
        <div role="alert" className="flex items-start gap-2">
          <FailureIcon />
          <p>{text}</p>
        </div>
        {onRetry && (
          <div className="pl-6">
            <button type="button" data-retry-button onClick={onRetry} className={RETRY_BUTTON_CLASSES}>
              {RETRY_LABEL}
            </button>
          </div>
        )}
      </div>
    </AssistantRow>
  );
}
