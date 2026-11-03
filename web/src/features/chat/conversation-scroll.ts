import { endsWithFailure, type Conversation } from "./conversation";

const END_TOLERANCE_PX = 2;

type ScrollMeasure = Readonly<{
  scrollHeight: number;
  clientHeight: number;
  scrollTop: number;
}>;

export type ScrollFollow = Readonly<{
  isFollowing: boolean;
  lastScrollTop: number;
}>;

export function isAtEnd({ scrollHeight, clientHeight, scrollTop }: ScrollMeasure): boolean {
  return scrollHeight - clientHeight - scrollTop <= END_TOLERANCE_PX;
}

export function followAfterScroll({ isFollowing, lastScrollTop }: ScrollFollow, measure: ScrollMeasure): ScrollFollow {
  const hasMovedUp = measure.scrollTop < lastScrollTop;
  return {
    isFollowing: isAtEnd(measure) || (isFollowing && !hasMovedUp),
    lastScrollTop: measure.scrollTop,
  };
}

export function forcesScrollToEnd(conversation: Conversation): boolean {
  return conversation.isWaiting || endsWithFailure(conversation);
}

export function wasJustCovered(elementBottom: number, previousViewBottom: number, viewBottom: number): boolean {
  return elementBottom <= previousViewBottom && elementBottom > viewBottom;
}
