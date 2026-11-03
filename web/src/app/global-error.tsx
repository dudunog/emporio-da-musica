"use client";

import { Inter } from "next/font/google";
import { PAGE_TITLE, SERVICE_UNAVAILABLE_MESSAGE } from "@/features/chat/chat-copy";
import { StoreNotice } from "@/features/chat/components/chat-frame";
import { FailureBubble } from "@/features/chat/components/failure-bubble";
import "./globals.css";

const INTER = Inter({ subsets: ["latin"], variable: "--font-inter" });

export default function GlobalErrorPage({ retry }: Readonly<{ retry: () => void }>) {
  return (
    <html lang="pt-BR" className={`${INTER.variable} antialiased`}>
      <body>
        <title>{PAGE_TITLE}</title>
        <StoreNotice>
          <FailureBubble text={SERVICE_UNAVAILABLE_MESSAGE} onRetry={retry} />
        </StoreNotice>
      </body>
    </html>
  );
}
