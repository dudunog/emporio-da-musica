import type { ReactNode } from "react";
import { STORE_NAME, STORE_TAGLINE } from "../chat-copy";
import { SoundholeOrnament } from "./soundhole-ornament";
import { StoreAvatar } from "./store-avatar";

function ChatHeader() {
  return (
    <header className="relative z-10 h-header shrink-0 border-b border-line bg-surface">
      <div className="mx-auto flex h-full max-w-content items-center gap-3 px-page-x">
        <StoreAvatar placement="header" />
        <div className="min-w-0">
          <h1 className="text-title">{STORE_NAME}</h1>
          <p className="text-caption text-muted">{STORE_TAGLINE}</p>
        </div>
      </div>
    </header>
  );
}

export function ChatFrame({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <div className="flex h-dvh flex-col">
      <ChatHeader />
      <main className="relative flex min-h-0 flex-1 flex-col overflow-hidden">
        <SoundholeOrnament />
        {children}
      </main>
    </div>
  );
}

export function StoreNotice({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <ChatFrame>
      <div className="relative flex flex-col items-center px-page-x py-4 *:w-full *:max-w-column">{children}</div>
    </ChatFrame>
  );
}
