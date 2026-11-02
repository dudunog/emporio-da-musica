import { useComposerFocus } from "../hooks/use-composer-focus";
import { useConversation } from "../hooks/use-conversation";
import { useConversationScroll } from "../hooks/use-conversation-scroll";
import { ChatFrame } from "./chat-frame";
import { Composer } from "./composer";
import { ConversationLog } from "./conversation-log";

export function ChatScreen() {
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
