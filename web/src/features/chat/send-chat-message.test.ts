import { afterEach, describe, expect, it, vi } from "vitest";
import { ChatRequestError, failureReasonOf, sendChatMessage } from "./send-chat-message";

const REQUEST = { conversationId: null, message: "Oi" };

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

async function reasonOfFailure(): Promise<unknown> {
  return sendChatMessage(REQUEST).then(
    () => "no failure",
    (error: unknown) => failureReasonOf(error),
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("sendChatMessage", () => {
  it("posts the wire format to the same origin", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { conversation_id: "abc", reply: "Oi" }));
    vi.stubGlobal("fetch", fetchMock);
    await sendChatMessage({ conversationId: "abc", message: "Tudo bem?" });
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/chat");
    expect(options.method).toBe("POST");
    expect(JSON.parse(options.body)).toEqual({ conversation_id: "abc", message: "Tudo bem?" });
  });

  it("sends a null conversation id on the first message", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { conversation_id: "abc", reply: "Oi" }));
    vi.stubGlobal("fetch", fetchMock);
    await sendChatMessage(REQUEST);
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ conversation_id: null, message: "Oi" });
  });

  it("maps a successful answer", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, { conversation_id: "abc", reply: "Oi" })));
    await expect(sendChatMessage(REQUEST)).resolves.toEqual({ conversationId: "abc", reply: "Oi" });
  });

  it.each(["authentication", "connection", "rate_limit", "server"])("keeps the reason %s from a 503", async (reason) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(503, { reason })));
    await expect(reasonOfFailure()).resolves.toBe(reason);
  });

  it("uses the connection reason when fetch rejects", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(reasonOfFailure()).resolves.toBe("connection");
  });

  it.each([
    ["plain text from the proxy", new Response("Internal Server Error", { status: 500 })],
    ["an empty gateway answer", new Response(null, { status: 504 })],
    ["an unknown reason", jsonResponse(503, { reason: "constructor" })],
    ["a successful answer without reply", jsonResponse(200, { conversation_id: "abc" })],
    ["a successful answer with an empty reply", jsonResponse(200, { conversation_id: "abc", reply: "" })],
    ["a successful answer that is not JSON", new Response("<html></html>", { status: 200 })],
  ])("uses the connection reason for %s", async (_description, response) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
    await expect(reasonOfFailure()).resolves.toBe("connection");
  });

  it("reports a validation answer as a rejected message", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(422, { detail: [] })));
    await expect(reasonOfFailure()).resolves.toBe("rejected");
  });

  it("carries the reason on the error type", () => {
    expect(failureReasonOf(new ChatRequestError("rate_limit"))).toBe("rate_limit");
    expect(failureReasonOf(new Error("unexpected"))).toBe("connection");
  });
});
