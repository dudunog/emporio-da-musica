import { CUSTOMER_NAME } from "../chat-copy";
import { withUnbreakableCurrency } from "../currency-text";
import type { EntryBubbleProps } from "./conversation-log";

export function CustomerBubble({ text }: EntryBubbleProps) {
  return (
    <article aria-label={CUSTOMER_NAME} className="flex animate-bubble-in justify-end motion-reduce:animate-none">
      <p className="max-w-bubble-user rounded-bubble rounded-br-bubble-inner bg-user px-bubble-x py-bubble-y text-body whitespace-pre-wrap wrap-anywhere text-on-user selection:bg-on-user/30">
        {withUnbreakableCurrency(text)}
      </p>
    </article>
  );
}
