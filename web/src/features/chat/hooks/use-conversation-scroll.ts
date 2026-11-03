import { useEffect, useLayoutEffect, useRef, type RefObject } from "react";
import type { Conversation } from "../conversation";
import { followAfterScroll, forcesScrollToEnd, wasJustCovered, type ScrollFollow } from "../conversation-scroll";

const RETRY_BUTTON_SELECTOR = "[data-retry-button]";
const INITIAL_FOLLOW: ScrollFollow = { isFollowing: true, lastScrollTop: 0 };

function scrollToEnd(log: HTMLElement, followRef: RefObject<ScrollFollow>) {
  log.scrollTop = log.scrollHeight;
  followRef.current = { ...followRef.current, lastScrollTop: log.scrollTop };
}

function keepEndInViewOnResize(log: HTMLElement, followRef: RefObject<ScrollFollow>): () => void {
  let viewBottom = log.getBoundingClientRect().bottom;
  const handleResize = () => {
    const previousViewBottom = viewBottom;
    viewBottom = log.getBoundingClientRect().bottom;
    const retryBottom = log.querySelector(RETRY_BUTTON_SELECTOR)?.getBoundingClientRect().bottom;
    const retryWasCovered = retryBottom !== undefined && wasJustCovered(retryBottom, previousViewBottom, viewBottom);
    if (followRef.current.isFollowing || retryWasCovered) scrollToEnd(log, followRef);
  };
  const resizeObserver = new ResizeObserver(handleResize);
  resizeObserver.observe(log);
  return () => resizeObserver.disconnect();
}

export function useConversationScroll(conversation: Conversation) {
  const logRef = useRef<HTMLDivElement>(null);
  const followRef = useRef(INITIAL_FOLLOW);

  const trackScroll = () => {
    if (logRef.current) followRef.current = followAfterScroll(followRef.current, logRef.current);
  };

  useLayoutEffect(() => {
    if (!logRef.current) return;
    if (forcesScrollToEnd(conversation)) followRef.current = { ...followRef.current, isFollowing: true };
    if (followRef.current.isFollowing) scrollToEnd(logRef.current, followRef);
  }, [conversation]);

  useEffect(() => {
    if (!logRef.current) return;
    return keepEndInViewOnResize(logRef.current, followRef);
  }, []);

  return { logRef, trackScroll };
}
