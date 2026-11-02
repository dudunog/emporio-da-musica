import { STORE_NAME, STORE_TAGLINE } from "../chat-copy";
import { StoreAvatar } from "./store-avatar";

export function ChatHeader() {
  return (
    <header className="relative z-10 shrink-0 border-b border-line bg-surface">
      <div className="mx-auto flex h-header max-w-content items-center gap-3 px-page-x">
        <StoreAvatar size={36} className="size-avatar-header" />
        <div className="min-w-0">
          <h1 className="text-title">{STORE_NAME}</h1>
          <p className="text-caption text-muted">{STORE_TAGLINE}</p>
        </div>
      </div>
    </header>
  );
}
