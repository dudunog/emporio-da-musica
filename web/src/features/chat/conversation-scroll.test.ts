import { describe, expect, it } from "vitest";
import { INITIAL_CONVERSATION, withCustomerMessage, withFailure, withReply } from "./conversation";
import { forcesScrollToEnd, isAtEnd, wasJustCovered } from "./conversation-scroll";

const WAITING = withCustomerMessage(INITIAL_CONVERSATION, "Oi");

describe("isAtEnd", () => {
  it("accepts the end within the tolerance", () => {
    expect(isAtEnd({ scrollHeight: 1000, clientHeight: 400, scrollTop: 598 })).toBe(true);
  });

  it("rejects a customer who scrolled up", () => {
    expect(isAtEnd({ scrollHeight: 1000, clientHeight: 400, scrollTop: 500 })).toBe(false);
  });
});

describe("forcesScrollToEnd", () => {
  it("forces on send and on a new failure", () => {
    expect(forcesScrollToEnd(WAITING)).toBe(true);
    expect(forcesScrollToEnd(withFailure(WAITING, "server"))).toBe(true);
  });

  it("does not force on a reply", () => {
    expect(forcesScrollToEnd(withReply(WAITING, { conversationId: "abc", reply: "Oi" }))).toBe(false);
  });
});

describe("wasJustCovered", () => {
  it("detects an element that the composer growth just hid", () => {
    expect(wasJustCovered(700, 720, 690)).toBe(true);
  });

  it("ignores what was already out of view or is still visible", () => {
    expect(wasJustCovered(900, 720, 690)).toBe(false);
    expect(wasJustCovered(600, 720, 690)).toBe(false);
  });
});
