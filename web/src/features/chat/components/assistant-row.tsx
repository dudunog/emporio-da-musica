import type { ReactNode } from "react";
import { ASSISTANT_NAME } from "../chat-copy";
import { StoreAvatar } from "./store-avatar";

export const ASSISTANT_BUBBLE_CLASSES =
  "max-w-bubble-agent min-w-0 rounded-bubble rounded-bl-bubble-inner px-bubble-x py-bubble-y text-body wrap-anywhere";

export function AssistantRow({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <article aria-label={ASSISTANT_NAME} className="flex animate-bubble-in items-end gap-2 motion-reduce:animate-none">
      <StoreAvatar size={28} className="size-avatar-bubble" />
      {children}
    </article>
  );
}
