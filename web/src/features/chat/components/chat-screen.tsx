"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { useComposerFocus } from "../hooks/use-composer-focus";
import { useConversation } from "../hooks/use-conversation";
import { useConversationScroll } from "../hooks/use-conversation-scroll";
import { ChatFrame } from "./chat-frame";
import { Composer } from "./composer";
import { ConversationLog } from "./conversation-log";

function ChatScreen() {
  const { conversation, send, retry } = useConversation();
  const { logRef, trackScroll } = useConversationScroll(conversation);
  const composerRef = useComposerFocus(conversation.isWaiting);

  return (
    <ChatFrame>
      <ConversationLog conversation={conversation} logRef={logRef} onScroll={trackScroll} onRetry={retry} />
      <Composer isWaiting={conversation.isWaiting} onSend={send} textareaRef={composerRef} />
    </ChatFrame>
  );
}

export function ChatApp() {
  const [queryClient] = useState(() => new QueryClient());
  return (
    <QueryClientProvider client={queryClient}>
      <ChatScreen />
    </QueryClientProvider>
  );
}
