import { useState, type FormEvent, type KeyboardEvent } from "react";
import { cleanMessage, isSendKey, isSendable } from "../composer-rules";

type ComposerDraftOptions = Readonly<{
  isWaiting: boolean;
  onSend: (message: string) => void;
}>;

export function useComposerDraft({ isWaiting, onSend }: ComposerDraftOptions) {
  const [draft, setDraft] = useState("");
  const message = cleanMessage(draft);
  const canSend = !isWaiting && isSendable(message);

  const submit = () => {
    if (!canSend) return;
    onSend(message);
    setDraft("");
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    submit();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    const { key, shiftKey } = event;
    if (!isSendKey({ key, shiftKey, isComposing: event.nativeEvent.isComposing })) return;
    event.preventDefault();
    submit();
  };

  return { draft, setDraft, canSend, handleSubmit, handleKeyDown };
}
