export const MAX_MESSAGE_LENGTH = 4000;

type SendKeyEvent = Readonly<{
  key: string;
  shiftKey: boolean;
  isComposing: boolean;
}>;

export function cleanMessage(draft: string): string {
  return draft.trim();
}

export function isSendable(message: string): boolean {
  return message !== "" && message.length <= MAX_MESSAGE_LENGTH;
}

export function isSendKey({ key, shiftKey, isComposing }: SendKeyEvent): boolean {
  return key === "Enter" && !shiftKey && !isComposing;
}
