import Link from "next/link";
import { BACK_TO_CHAT_LABEL, NOT_FOUND_MESSAGE } from "@/features/chat/chat-copy";
import { ASSISTANT_BUBBLE_CLASSES, AssistantRow } from "@/features/chat/components/assistant-row";
import { StoreNotice } from "@/features/chat/components/chat-frame";

export default function NotFoundPage() {
  return (
    <StoreNotice>
      <AssistantRow>
        <div className={`${ASSISTANT_BUBBLE_CLASSES} bg-agent text-ink`}>
          <p className="mb-2">{NOT_FOUND_MESSAGE}</p>
          <Link href="/" className="underline underline-offset-2 hover:no-underline">
            {BACK_TO_CHAT_LABEL}
          </Link>
        </div>
      </AssistantRow>
    </StoreNotice>
  );
}
