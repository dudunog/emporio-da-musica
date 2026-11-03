import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ChatApp } from "./chat-screen";

const SCROLL_HEIGHT = 1000;
const CLIENT_HEIGHT = 400;
const READER_POSITION = 100;

type PendingResponse = (response: Response) => void;

const pendingResponses: PendingResponse[] = [];
const fetchMock = vi.fn(() => new Promise<Response>((resolve) => pendingResponses.push(resolve)));
let resizeCallback: () => void = () => {};
let logBottom = 720;

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function composer(): HTMLTextAreaElement {
  return screen.getByRole<HTMLTextAreaElement>("textbox", { name: "Sua mensagem" });
}

function sendWithEnter(text: string) {
  fireEvent.change(composer(), { target: { value: text } });
  return fireEvent.keyDown(composer(), { key: "Enter" });
}

function renderMeasuredLog(): HTMLElement {
  render(<ChatApp />);
  const log = screen.getByRole("log");
  Object.defineProperty(log, "scrollHeight", { value: SCROLL_HEIGHT });
  Object.defineProperty(log, "clientHeight", { value: CLIENT_HEIGHT, configurable: true });
  return log;
}

function scrollReaderUp(log: HTMLElement) {
  log.scrollTop = READER_POSITION;
  fireEvent.scroll(log);
}

async function settle(response: Response) {
  await waitFor(() => expect(pendingResponses).not.toHaveLength(0));
  const resolve = pendingResponses.shift();
  act(() => resolve?.(response));
  await waitFor(() => expect(screen.queryByRole("status")).toBeNull());
}

beforeEach(() => {
  pendingResponses.length = 0;
  fetchMock.mockClear();
  logBottom = 720;
  vi.stubGlobal("fetch", fetchMock);
  vi.stubGlobal(
    "ResizeObserver",
    class {
      constructor(callback: () => void) {
        resizeCallback = callback;
      }
      observe() {}
      disconnect() {}
    },
  );
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
    return new DOMRect(0, 0, 0, this.tagName === "BUTTON" ? 700 : logBottom);
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("conversation scroll", () => {
  it("takes a reader who scrolled up to the end when sending", () => {
    const log = renderMeasuredLog();
    scrollReaderUp(log);
    sendWithEnter("Oi");
    expect(log.scrollTop).toBe(SCROLL_HEIGHT);
  });

  it("does not pull a reader who scrolled up while waiting", async () => {
    const log = renderMeasuredLog();
    sendWithEnter("Oi");
    scrollReaderUp(log);
    await settle(jsonResponse(200, { conversation_id: "abc", reply: "Resposta" }));
    expect(log.scrollTop).toBe(READER_POSITION);
  });

  it("shows a new failure to a reader who scrolled up", async () => {
    const log = renderMeasuredLog();
    sendWithEnter("Oi");
    scrollReaderUp(log);
    await settle(jsonResponse(503, { reason: "server" }));
    expect(log.scrollTop).toBe(SCROLL_HEIGHT);
  });

  it("keeps following when the composer grows before the scroll event arrives", async () => {
    const log = renderMeasuredLog();
    sendWithEnter("Oi");
    Object.defineProperty(log, "clientHeight", { value: CLIENT_HEIGHT - 100, configurable: true });
    fireEvent.scroll(log);
    log.scrollTop = 0;
    await settle(jsonResponse(200, { conversation_id: "abc", reply: "Resposta" }));
    expect(log.scrollTop).toBe(SCROLL_HEIGHT);
  });

  it("keeps the end in view when the composer grows", () => {
    const log = renderMeasuredLog();
    log.scrollTop = SCROLL_HEIGHT - CLIENT_HEIGHT;
    resizeCallback();
    expect(log.scrollTop).toBe(SCROLL_HEIGHT);
  });

  it("uncovers the retry button when the composer grows over it", async () => {
    const log = renderMeasuredLog();
    sendWithEnter("Oi");
    await settle(jsonResponse(503, { reason: "server" }));
    scrollReaderUp(log);
    logBottom = 690;
    resizeCallback();
    expect(log.scrollTop).toBe(SCROLL_HEIGHT);
  });
});

describe("composer focus and keys", () => {
  it("focuses without scrolling", () => {
    const focus = vi.spyOn(HTMLTextAreaElement.prototype, "focus");
    render(<ChatApp />);
    expect(focus).toHaveBeenCalledWith({ preventScroll: true });
  });

  it("returns focus after a reply", async () => {
    render(<ChatApp />);
    sendWithEnter("Oi");
    composer().blur();
    await settle(jsonResponse(200, { conversation_id: "abc", reply: "Resposta" }));
    expect(document.activeElement).toBe(composer());
  });

  it("does not insert a line break when Enter sends", () => {
    render(<ChatApp />);
    expect(sendWithEnter("Oi")).toBe(false);
  });

  it("does not post a message above the limit and keeps the field usable", async () => {
    render(<ChatApp />);
    sendWithEnter("a".repeat(4001));
    await act(async () => {});
    expect(fetchMock).not.toHaveBeenCalled();
    expect(composer().disabled).toBe(false);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("keeps the customer currency on one line", () => {
    render(<ChatApp />);
    sendWithEnter("Paguei R$ 10");
    expect(screen.getByRole("article", { name: "Você" }).textContent).toBe("Paguei R$ 10");
  });
});
