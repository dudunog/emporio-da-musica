import { endsWithFailure, type Conversation } from "./conversation";

const END_TOLERANCE_PX = 2;

type ScrollMeasure = Readonly<{
  scrollHeight: number;
  clientHeight: number;
  scrollTop: number;
}>;

export function isAtEnd({ scrollHeight, clientHeight, scrollTop }: ScrollMeasure): boolean {
  return scrollHeight - clientHeight - scrollTop <= END_TOLERANCE_PX;
}

export function forcesScrollToEnd(conversation: Conversation): boolean {
  return conversation.isWaiting || endsWithFailure(conversation);
}

export function wasJustCovered(elementBottom: number, previousViewBottom: number, viewBottom: number): boolean {
  return elementBottom <= previousViewBottom && elementBottom > viewBottom;
}
