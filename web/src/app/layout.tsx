import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import type { ReactNode } from "react";
import { PAGE_TITLE } from "@/features/chat/chat-copy";

const INTER = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = { title: PAGE_TITLE };

export const viewport: Viewport = {
  colorScheme: "light dark",
  interactiveWidget: "resizes-content",
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="pt-BR" className={`${INTER.variable} antialiased`}>
      <body>{children}</body>
    </html>
  );
}
