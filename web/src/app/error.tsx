"use client";

import { SERVICE_UNAVAILABLE_MESSAGE } from "@/features/chat/chat-copy";
import { FailureBubble } from "@/features/chat/components/failure-bubble";
import { StoreNotice } from "@/features/chat/components/chat-frame";

export default function ErrorPage({ retry }: Readonly<{ retry: () => void }>) {
  return (
    <StoreNotice>
      <FailureBubble text={SERVICE_UNAVAILABLE_MESSAGE} onRetry={retry} />
    </StoreNotice>
  );
}
