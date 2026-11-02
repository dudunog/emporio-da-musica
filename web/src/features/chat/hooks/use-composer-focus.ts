import { useEffect, useRef } from "react";

export function useComposerFocus(isWaiting: boolean) {
  const composerRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!document.getSelection()?.isCollapsed) return;
    composerRef.current?.focus({ preventScroll: true });
  }, [isWaiting]);

  return composerRef;
}
