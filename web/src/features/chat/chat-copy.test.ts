import { readFileSync, readdirSync } from "node:fs";
import { describe, expect, it } from "vitest";
import * as chatCopy from "./chat-copy";

const SERVICE_UNAVAILABLE = "Nosso atendimento está indisponível neste momento. Tente de novo em alguns minutos.";
const NO_CONNECTION = "Sem conexão agora. Verifique sua internet e tente de novo.";
const TOO_MANY_CONVERSATIONS = "Estamos com muitas conversas agora. Tente de novo em instantes.";
const CONTRACT_COPY = {
  PAGE_TITLE: "Empório da Música",
  STORE_NAME: "Empório da Música",
  STORE_TAGLINE: "Sua música começa aqui",
  ASSISTANT_NAME: "Lia",
  CUSTOMER_NAME: "Você",
  GREETING: "Oi! Eu sou a Lia, atendimento virtual da Empório da Música. Posso ajudar com produtos, preços, pedidos, trocas e informações da loja.",
  CONVERSATION_LABEL: "Conversa com o atendimento",
  COMPOSER_PLACEHOLDER: "Escreva sua mensagem",
  COMPOSER_LABEL: "Sua mensagem",
  SEND_LABEL: "Enviar mensagem",
  TYPING_LABEL: "Lia está digitando",
  RETRY_LABEL: "Tentar de novo",
  AVATAR_ALT: "",
  NOT_FOUND_MESSAGE: "Esta página não existe.",
  BACK_TO_CHAT_LABEL: "Voltar para o atendimento",
  SERVICE_UNAVAILABLE_MESSAGE: SERVICE_UNAVAILABLE,
  NO_CONNECTION_MESSAGE: NO_CONNECTION,
  TOO_MANY_CONVERSATIONS_MESSAGE: TOO_MANY_CONVERSATIONS,
  FAILURE_MESSAGES: {
    authentication: SERVICE_UNAVAILABLE,
    server: SERVICE_UNAVAILABLE,
    connection: NO_CONNECTION,
    rate_limit: TOO_MANY_CONVERSATIONS,
  },
};

const FORBIDDEN_TERMS = [
  "API", "LLM", "token", "sessão", "session", "rerun", "deploy", "prompt", "modelo", "Next", "Vercel", "React", "Anthropic", "Claude", "chat", "bot",
  "online", "offline", "retry", "loading", "error", "erro 4", "erro 5", "timeout", "status code", "chave", "key", ".env", "ANTHROPIC_API_KEY", "Enter", "ok", "ops",
];
const REQUIRED_ACCENTS = ["Empório", "Música", "começa", "está", "não", "indisponível", "conexão", "informações", "preços"];
const FORBIDDEN_TYPOGRAPHY = /[—–“”‘’…]|[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u;
const COPY_STRINGS = Object.values(chatCopy).filter((value) => typeof value === "string");
const SOURCE_PATHS = readdirSync("src", { recursive: true, encoding: "utf8" }).filter((path) => /\.tsx?$/.test(path) && !path.includes(".test."));

describe("chat copy", () => {
  it("has zero diff with the contract", () => {
    expect({ ...chatCopy }).toEqual(CONTRACT_COPY);
  });

  it("has the closed list of 32 forbidden terms", () => {
    expect(FORBIDDEN_TERMS).toHaveLength(32);
  });

  it.each(FORBIDDEN_TERMS)("does not contain %s", (term) => {
    expect(COPY_STRINGS.filter((text) => text.toLowerCase().includes(term.toLowerCase()))).toEqual([]);
  });

  it.each(REQUIRED_ACCENTS)("has the accent of %s", (word) => {
    expect(COPY_STRINGS.some((text) => text.includes(word))).toBe(true);
    expect(COPY_STRINGS.some((text) => text.includes(word.normalize("NFD").replace(/\p{M}/gu, "")) && text !== word)).toBe(false);
  });

  it("uses only plain typography", () => {
    expect(COPY_STRINGS.filter((text) => FORBIDDEN_TYPOGRAPHY.test(text))).toEqual([]);
  });

  it("keeps one exclamation, in the greeting opening", () => {
    expect(COPY_STRINGS.join(" ").match(/!/g)).toHaveLength(1);
    expect(chatCopy.GREETING.startsWith("Oi!")).toBe(true);
  });

  it.each(["src/app/layout.tsx", "src/app/global-error.tsx"])("declares the page language in %s", (path) => {
    expect(readFileSync(path, "utf8")).toContain('lang="pt-BR"');
  });

  it("uses the avatar as the icon", () => {
    expect(readFileSync("src/app/icon.svg", "utf8")).toBe(readFileSync("public/avatar.svg", "utf8"));
  });

  it("has no literal pt-BR text outside the copy module", () => {
    const offenders = SOURCE_PATHS.filter((path) => !path.endsWith("chat-copy.ts")).filter((path) =>
      COPY_STRINGS.some((text) => text !== "" && text.length > 3 && readFileSync(`src/${path}`, "utf8").includes(text)),
    );
    expect(offenders).toEqual([]);
  });
});
