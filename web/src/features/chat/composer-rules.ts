export const MAX_MESSAGE_LENGTH = 4000;

const OUTER_BLANKS = /^[\p{White_Space}​-‍⁠﻿]+|[\p{White_Space}​-‍⁠﻿]+$/gu;
const LONE_SURROGATE = /\p{Cs}/u;

type SendKeyEvent = Readonly<{
  key: string;
  shiftKey: boolean;
  isComposing: boolean;
}>;

export function cleanMessage(draft: string): string {
  return draft.replace(OUTER_BLANKS, "");
}

export function isSendable(message: string): boolean {
  return message !== "" && message.length <= MAX_MESSAGE_LENGTH && !LONE_SURROGATE.test(message);
}

export function isSendKey({ key, shiftKey, isComposing }: SendKeyEvent): boolean {
  return key === "Enter" && !shiftKey && !isComposing;
}
