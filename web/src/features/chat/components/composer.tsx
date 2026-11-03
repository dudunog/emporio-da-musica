import type { KeyboardEventHandler, Ref } from "react";
import { COMPOSER_LABEL, COMPOSER_PLACEHOLDER, SEND_LABEL } from "../chat-copy";
import { MAX_MESSAGE_LENGTH } from "../composer-rules";
import { useComposerDraft } from "../hooks/use-composer-draft";

const BOX_CLASSES =
  "flex items-end rounded-composer border border-line bg-surface p-1 pl-4 focus-within:border-focus focus-within:shadow-composer-focus has-[button:focus-visible]:border-line has-[button:focus-visible]:shadow-none";

const FIELD_TEXT_CLASSES = "col-start-1 row-start-1 py-2 pr-2 text-composer whitespace-pre-wrap wrap-anywhere";

const SEND_BUTTON_CLASSES =
  "relative flex size-control shrink-0 cursor-pointer items-center justify-center rounded-full bg-brand text-on-brand transition-[background-color,opacity,scale] before:absolute before:-inset-0.5 before:content-[''] not-disabled:hover:bg-brand-hover not-disabled:active:scale-95 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus disabled:cursor-not-allowed disabled:opacity-50 motion-reduce:transition-none";

type ComposerFieldProps = Readonly<{
  draft: string;
  onDraftChange: (draft: string) => void;
  onKeyDown: KeyboardEventHandler<HTMLTextAreaElement>;
  textareaRef: Ref<HTMLTextAreaElement>;
}>;

type ComposerProps = Readonly<{
  isWaiting: boolean;
  onSend: (message: string) => void;
  textareaRef: Ref<HTMLTextAreaElement>;
}>;

function ComposerField({ draft, onDraftChange, onKeyDown, textareaRef }: ComposerFieldProps) {
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

function SendButton({ isDisabled }: Readonly<{ isDisabled: boolean }>) {
  return (
    <button type="submit" disabled={isDisabled} aria-label={SEND_LABEL} className={SEND_BUTTON_CLASSES}>
      <svg aria-hidden="true" viewBox="0 0 20 20" fill="none" className="size-5">
        <path d="M10 16V4.5M5 9.5l5-5 5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </button>
  );
}

export function Composer({ isWaiting, onSend, textareaRef }: ComposerProps) {
  const { draft, setDraft, canSend, handleSubmit, handleKeyDown } = useComposerDraft({ isWaiting, onSend });

  return (
    <div className="relative shrink-0 bg-page">
      <div className="pointer-events-none absolute inset-x-0 -top-4 h-4 bg-linear-to-t from-page to-transparent" />
      <form onSubmit={handleSubmit} className="mx-auto max-w-content px-page-x pt-2 pb-composer-bottom">
        <div className={BOX_CLASSES}>
          <ComposerField draft={draft} onDraftChange={setDraft} onKeyDown={handleKeyDown} textareaRef={textareaRef} />
          <SendButton isDisabled={!canSend} />
        </div>
      </form>
    </div>
  );
}
