import { useEffect, useRef } from "react";

function focusField(field: HTMLTextAreaElement | null) {
  field?.focus({ preventScroll: true });
}

export function useComposerFocus(isWaiting: boolean) {
  const composerRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!document.getSelection()?.isCollapsed) return;
    focusField(composerRef.current);
  }, [isWaiting]);

  return { composerRef, focusComposer: () => focusField(composerRef.current) };
}
