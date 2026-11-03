import { TYPING_LABEL } from "../chat-copy";
import { AssistantRow } from "./assistant-row";

const DOT_DELAYS = ["[animation-delay:0ms]", "[animation-delay:200ms]", "[animation-delay:400ms]"];

export function TypingIndicator() {
  return (
    <AssistantRow surfaceClasses="bg-agent">
      <div role="status" className="flex min-h-body-line items-center gap-1 text-muted">
        {DOT_DELAYS.map((delay) => (
          <span
            key={delay}
            className={`size-dot animate-typing rounded-full bg-current opacity-35 motion-reduce:animate-none motion-reduce:opacity-60 ${delay}`}
          />
        ))}
        <span className="sr-only text-caption motion-reduce:not-sr-only motion-reduce:ml-1">{TYPING_LABEL}</span>
      </div>
    </AssistantRow>
  );
}
