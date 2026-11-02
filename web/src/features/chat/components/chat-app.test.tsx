import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FAILURE_MESSAGES, GREETING } from "../chat-copy";
import { ChatApp } from "./chat-app";

const DOM_FORBIDDEN_TERMS = [
  "Traceback", "Error", "Exception", "401", "403", "429", "500", "API", "Anthropic", "Claude", "chave", "token", "http", "authentication",
  "invalid", "timeout", "rate limit", "Connection", "127.0.0.1", "ANTHROPIC", ".env", "Loading", "Thinking", "Typing", "Retry", "Bot",
  "Chatbot", "Assistant", "Powered by", "Please wait", "Send message", "Your message", "Press Enter", "Online", "Bem-vindo",
];

type PendingResponse = Readonly<{ resolve: (response: Response) => void; reject: (reason: unknown) => void }>;

const fetchMock = vi.fn<(url: string, options: RequestInit) => Promise<Response>>();
const pendingResponses: PendingResponse[] = [];

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function composer(): HTMLTextAreaElement {
  return screen.getByRole<HTMLTextAreaElement>("textbox", { name: "Sua mensagem" });
}

function typeMessage(text: string) {
  fireEvent.change(composer(), { target: { value: text } });
}

function sendWithEnter(text: string) {
  typeMessage(text);
  fireEvent.keyDown(composer(), { key: "Enter" });
}

async function waitForRequest(): Promise<PendingResponse> {
  await waitFor(() => expect(pendingResponses).not.toHaveLength(0));
  return pendingResponses[0];
}

async function settle(response: Response) {
  const { resolve } = await waitForRequest();
  pendingResponses.shift();
  act(() => resolve(response));
  await waitFor(() => expect(screen.queryByRole("status")).toBeNull());
}

function sentBodies(): unknown[] {
  return fetchMock.mock.calls.map(([, options]) => JSON.parse(String(options.body)));
}

function visibleAndAccessibleText(): string {
  const labels = [...document.querySelectorAll("[aria-label],[placeholder],[title],[alt]")].flatMap((element) =>
    ["aria-label", "placeholder", "title", "alt"].map((attribute) => element.getAttribute(attribute) ?? ""),
  );
  return [document.body.textContent ?? "", ...labels].join(" ");
}

function expectNoForbiddenTerms() {
  const text = visibleAndAccessibleText();
  expect(DOM_FORBIDDEN_TERMS.filter((term) => text.includes(term))).toEqual([]);
}

beforeEach(() => {
  pendingResponses.length = 0;
  fetchMock.mockReset();
  fetchMock.mockImplementation(() => new Promise((resolve, reject) => pendingResponses.push({ resolve, reject })));
  vi.stubGlobal("fetch", fetchMock);
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe() {}
      disconnect() {}
    },
  );
});

afterEach(() => vi.unstubAllGlobals());

describe("ChatApp", () => {
  it("opens with the store identity, the greeting and focus on the composer", () => {
    render(<ChatApp />);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Empório da Música");
    expect(screen.getByText("Sua música começa aqui")).toBeTruthy();
    expect(within(screen.getByRole("log", { name: "Conversa com o atendimento" })).getByText(GREETING)).toBeTruthy();
    expect(composer().placeholder).toBe("Escreva sua mensagem");
    expect(document.activeElement).toBe(composer());
    expect(fetchMock).not.toHaveBeenCalled();
    expectNoForbiddenTerms();
  });

  it.each(["   \n  ", "\t", "\u00a0 \u00a0"])("does not send the blank message %j", (blank) => {
    render(<ChatApp />);
    sendWithEnter(blank);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(screen.getByRole<HTMLButtonElement>("button", { name: "Enviar mensagem" }).disabled).toBe(true);
  });

  it("sends the trimmed message on Enter and clears the draft", async () => {
    render(<ChatApp />);
    sendWithEnter("  Oi  ");
    await waitForRequest();
    expect(sentBodies()).toEqual([{ conversation_id: null, message: "Oi" }]);
    expect(composer().value).toBe("");
    expect(screen.getByText("Oi")).toBeTruthy();
  });

  it("does not send a message above the limit and keeps the field usable", () => {
    render(<ChatApp />);
    sendWithEnter("a".repeat(4001));
    expect(fetchMock).not.toHaveBeenCalled();
    expect(composer().disabled).toBe(false);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("sends with the button", async () => {
    render(<ChatApp />);
    typeMessage("Oi");
    fireEvent.click(screen.getByRole("button", { name: "Enviar mensagem" }));
    await waitForRequest();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("keeps Shift+Enter as a line break", () => {
    render(<ChatApp />);
    typeMessage("linha um");
    const isDefaultKept = fireEvent.keyDown(composer(), { key: "Enter", shiftKey: true });
    expect(isDefaultKept).toBe(true);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("shows the customer text literally, with line breaks and without markup", () => {
    render(<ChatApp />);
    const literal = "**negrito** <b>tag</b>\n- item";
    sendWithEnter(literal);
    const bubble = within(screen.getByRole("article", { name: "Você" })).getByText((_content, element) => element?.tagName === "P");
    expect(bubble.textContent).toBe(literal);
    expect(bubble.querySelector("b, strong, li")).toBeNull();
    expect(bubble.className).toContain("whitespace-pre-wrap");
  });

  it("shows the typing status and blocks sending while keeping the draft editable", async () => {
    render(<ChatApp />);
    sendWithEnter("Primeira");
    expect(screen.getByRole("status").textContent).toContain("Lia está digitando");
    typeMessage("Rascunho");
    expect(composer().disabled).toBe(false);
    expect(screen.getByRole<HTMLButtonElement>("button", { name: "Enviar mensagem" }).disabled).toBe(true);
    fireEvent.keyDown(composer(), { key: "Enter" });
    await waitForRequest();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(composer().value).toBe("Rascunho");
    await settle(jsonResponse(200, { conversation_id: "abc", reply: "Resposta" }));
    expect(screen.queryByRole("status")).toBeNull();
    expect(composer().value).toBe("Rascunho");
    expectNoForbiddenTerms();
  });

  it("renders the reply as Markdown, returns focus and always uses the latest id", async () => {
    render(<ChatApp />);
    sendWithEnter("Primeira");
    await settle(jsonResponse(200, { conversation_id: "first-id", reply: "- **Kala** por R$ 349,90" }));
    expect(screen.getByText("Kala").tagName).toBe("STRONG");
    await waitFor(() => expect(document.activeElement).toBe(composer()));
    sendWithEnter("Segunda");
    await settle(jsonResponse(200, { conversation_id: "second-id", reply: "Ok" }));
    sendWithEnter("Terceira");
    await waitForRequest();
    expect(sentBodies()).toEqual([
      { conversation_id: null, message: "Primeira" },
      { conversation_id: "first-id", message: "Segunda" },
      { conversation_id: "second-id", message: "Terceira" },
    ]);
  });

  it.each([
    ["authentication", FAILURE_MESSAGES.authentication],
    ["server", FAILURE_MESSAGES.server],
    ["connection", FAILURE_MESSAGES.connection],
    ["rate_limit", FAILURE_MESSAGES.rate_limit],
  ])("shows the failure text for %s with one retry button", async (reason, message) => {
    render(<ChatApp />);
    sendWithEnter("Oi");
    await settle(jsonResponse(503, { reason }));
    expect(screen.getByRole("alert").textContent).toBe(message);
    expect(screen.getAllByRole("button", { name: "Tentar de novo" })).toHaveLength(1);
    expect(document.activeElement).toBe(composer());
    expectNoForbiddenTerms();
  });

  it("uses the connection text when the proxy answers without a reason", async () => {
    render(<ChatApp />);
    sendWithEnter("Oi");
    await settle(new Response("Internal Server Error", { status: 500 }));
    expect(screen.getByRole("alert").textContent).toBe(FAILURE_MESSAGES.connection);
    expectNoForbiddenTerms();
  });

  it("uses the connection text when fetch rejects", async () => {
    render(<ChatApp />);
    sendWithEnter("Oi");
    const { reject } = await waitForRequest();
    act(() => reject(new TypeError("Failed to fetch")));
    await waitFor(() => expect(screen.queryByRole("status")).toBeNull());
    expect(screen.getByRole("alert").textContent).toBe(FAILURE_MESSAGES.connection);
    expectNoForbiddenTerms();
  });

  it("retries the same message without a second customer bubble", async () => {
    render(<ChatApp />);
    sendWithEnter("Oi");
    await settle(jsonResponse(503, { reason: "server" }));
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByRole("status")).toBeTruthy();
    expect(document.activeElement).toBe(composer());
    await settle(jsonResponse(200, { conversation_id: "abc", reply: "Voltei" }));
    expect(screen.getAllByRole("article", { name: "Você" })).toHaveLength(1);
    expect(screen.getByText("Voltei")).toBeTruthy();
    expect(sentBodies()).toEqual([
      { conversation_id: null, message: "Oi" },
      { conversation_id: null, message: "Oi" },
    ]);
  });

  it("keeps the retry button only on the last failure", async () => {
    render(<ChatApp />);
    sendWithEnter("Primeira");
    await settle(jsonResponse(503, { reason: "server" }));
    sendWithEnter("Segunda");
    expect(screen.queryByRole("button", { name: "Tentar de novo" })).toBeNull();
    await settle(jsonResponse(503, { reason: "rate_limit" }));
    expect(screen.getAllByRole("alert")).toHaveLength(2);
    expect(screen.getAllByRole("button", { name: "Tentar de novo" })).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    await waitForRequest();
    expect(JSON.parse(String(fetchMock.mock.calls[2][1].body)).message).toBe("Segunda");
  });

  it("keeps every message as a direct child of the log, replacing the indicator", async () => {
    render(<ChatApp />);
    sendWithEnter("Oi");
    const log = screen.getByRole("log");
    expect(log.children).toHaveLength(3);
    await settle(jsonResponse(200, { conversation_id: "abc", reply: "Resposta" }));
    expect(log.children).toHaveLength(3);
  });

  it("sends once when two Enter presses land before a new render", async () => {
    render(<ChatApp />);
    typeMessage("Oi");
    const textarea = composer();
    act(() => {
      textarea.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true }));
      textarea.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true, cancelable: true }));
    });
    await settle(jsonResponse(200, { conversation_id: "abc", reply: "Resposta" }));
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(screen.getAllByRole("article", { name: "Você" })).toHaveLength(1);
  });

  it("does not take focus while the customer has text selected", async () => {
    render(<ChatApp />);
    sendWithEnter("Oi");
    composer().blur();
    const selectedText = screen.getByText(GREETING);
    const selection = document.getSelection();
    selection?.selectAllChildren(selectedText);
    await settle(jsonResponse(200, { conversation_id: "abc", reply: "Resposta" }));
    expect(document.activeElement).not.toBe(composer());
    selection?.removeAllRanges();
  });
});
