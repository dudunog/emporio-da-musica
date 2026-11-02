import { useMutation } from "@tanstack/react-query";
import { useRef, useState } from "react";
import {
  INITIAL_CONVERSATION,
  endsWithFailure,
  lastCustomerMessage,
  withCustomerMessage,
  withFailure,
  withReply,
  withRetryStarted,
  type Conversation,
} from "../conversation";
import { failureReasonOf, sendChatMessage } from "../send-chat-message";

export function useConversation() {
  const [conversation, setConversation] = useState(INITIAL_CONVERSATION);
  const isRequestOpenRef = useRef(false);
  const { mutate } = useMutation({
    mutationFn: sendChatMessage,
    onSuccess: (chatReply) => setConversation((current) => withReply(current, chatReply)),
    onError: (error) => setConversation((current) => withFailure(current, failureReasonOf(error))),
    onSettled: () => {
      isRequestOpenRef.current = false;
    },
  });

  const startRequest = (message: string, waitingConversation: Conversation) => {
    if (isRequestOpenRef.current) return;
    isRequestOpenRef.current = true;
    setConversation(waitingConversation);
    mutate({ conversationId: conversation.id, message });
  };

  const send = (message: string) => startRequest(message, withCustomerMessage(conversation, message));

  const retry = () => {
    const message = lastCustomerMessage(conversation);
    if (endsWithFailure(conversation) && message !== null) startRequest(message, withRetryStarted(conversation));
  };

  return { conversation, send, retry };
}
