import type { ReactNode } from "react";
import { ChatHeader } from "./chat-header";
import { SoundholeOrnament } from "./soundhole-ornament";

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
