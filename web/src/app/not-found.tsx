import Link from "next/link";
import { BACK_TO_CHAT_LABEL, NOT_FOUND_MESSAGE } from "@/features/chat/chat-copy";
import { AssistantRow } from "@/features/chat/components/assistant-row";
import { StoreNotice } from "@/features/chat/components/chat-frame";

export default function NotFoundPage() {
  return (
    <StoreNotice>
      <AssistantRow surfaceClasses="bg-agent text-ink">
        <p className="mb-2">{NOT_FOUND_MESSAGE}</p>
        <Link
          href="/"
          className="relative inline-block underline underline-offset-2 before:absolute before:inset-x-0 before:-inset-y-3 before:content-[''] hover:no-underline"
        >
          {BACK_TO_CHAT_LABEL}
        </Link>
      </AssistantRow>
    </StoreNotice>
  );
}
