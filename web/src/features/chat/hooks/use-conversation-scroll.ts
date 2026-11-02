import { useEffect, useLayoutEffect, useRef, type RefObject } from "react";
import type { Conversation } from "../conversation";
import { forcesScrollToEnd, isAtEnd, wasJustCovered } from "../conversation-scroll";

const RETRY_BUTTON_SELECTOR = "[data-retry-button]";

function scrollToEnd(log: HTMLElement) {
  log.scrollTop = log.scrollHeight;
}

function keepEndInViewOnResize(log: HTMLElement, isFollowingRef: RefObject<boolean>): () => void {
  let viewBottom = log.getBoundingClientRect().bottom;
  const handleResize = () => {
    const previousViewBottom = viewBottom;
    viewBottom = log.getBoundingClientRect().bottom;
    const retryBottom = log.querySelector(RETRY_BUTTON_SELECTOR)?.getBoundingClientRect().bottom;
    const retryWasCovered = retryBottom !== undefined && wasJustCovered(retryBottom, previousViewBottom, viewBottom);
    if (isFollowingRef.current || retryWasCovered) scrollToEnd(log);
  };
  const resizeObserver = new ResizeObserver(handleResize);
  resizeObserver.observe(log);
  return () => resizeObserver.disconnect();
}

export function useConversationScroll(conversation: Conversation) {
  const logRef = useRef<HTMLDivElement>(null);
  const isFollowingRef = useRef(true);

  const trackScroll = () => {
    if (logRef.current) isFollowingRef.current = isAtEnd(logRef.current);
  };

  useLayoutEffect(() => {
    if (!logRef.current) return;
    if (forcesScrollToEnd(conversation)) isFollowingRef.current = true;
    if (isFollowingRef.current) scrollToEnd(logRef.current);
  }, [conversation]);

  useEffect(() => {
    if (!logRef.current) return;
    return keepEndInViewOnResize(logRef.current, isFollowingRef);
  }, []);

  return { logRef, trackScroll };
}
