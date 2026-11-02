import type { KeyboardEventHandler, Ref } from "react";
import { COMPOSER_LABEL, COMPOSER_PLACEHOLDER } from "../chat-copy";
import { MAX_MESSAGE_LENGTH } from "../composer-rules";

const FIELD_TEXT_CLASSES = "col-start-1 row-start-1 py-2 pr-2 text-composer whitespace-pre-wrap wrap-anywhere";

type ComposerFieldProps = Readonly<{
  draft: string;
  onDraftChange: (draft: string) => void;
  onKeyDown: KeyboardEventHandler<HTMLTextAreaElement>;
  textareaRef: Ref<HTMLTextAreaElement>;
}>;

export function ComposerField({ draft, onDraftChange, onKeyDown, textareaRef }: ComposerFieldProps) {
  return (
    <div className="grid max-h-composer min-w-0 flex-1 overflow-hidden">
      <div aria-hidden="true" className={`invisible ${FIELD_TEXT_CLASSES}`}>
        {draft}{" "}
      </div>
      <textarea
        ref={textareaRef}
        rows={1}
        value={draft}
        maxLength={MAX_MESSAGE_LENGTH}
        enterKeyHint="send"
        placeholder={COMPOSER_PLACEHOLDER}
        aria-label={COMPOSER_LABEL}
        onChange={(event) => onDraftChange(event.target.value)}
        onKeyDown={onKeyDown}
        className={`${FIELD_TEXT_CLASSES} h-full max-h-composer resize-none overflow-y-auto bg-transparent text-ink outline-none [scrollbar-width:thin] placeholder:text-placeholder`}
      />
    </div>
  );
}
