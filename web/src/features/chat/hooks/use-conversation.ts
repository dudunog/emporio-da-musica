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
import { createMessageId, failureReasonOf, sendChatMessage } from "../send-chat-message";

export function useConversation() {
  const [conversation, setConversation] = useState(INITIAL_CONVERSATION);
  const isRequestOpenRef = useRef(false);
  const { mutate } = useMutation({
    mutationFn: sendChatMessage,
    networkMode: "always",
    onSuccess: (chatReply) => setConversation((current) => withReply(current, chatReply)),
    onError: (error) => setConversation((current) => withFailure(current, failureReasonOf(error))),
    onSettled: () => {
      isRequestOpenRef.current = false;
    },
  });

  const startRequest = (waitingConversation: Conversation) => {
    const customerMessage = lastCustomerMessage(waitingConversation);
    if (isRequestOpenRef.current || customerMessage === null) return;
    isRequestOpenRef.current = true;
    setConversation(waitingConversation);
    mutate({ conversationId: waitingConversation.id, messageId: customerMessage.messageId, message: customerMessage.text });
  };

  const send = (message: string) => startRequest(withCustomerMessage(conversation, message, createMessageId()));

  const retry = () => {
    if (endsWithFailure(conversation)) startRequest(withRetryStarted(conversation));
  };

  return { conversation, send, retry };
}
