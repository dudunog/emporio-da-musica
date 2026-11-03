import { describe, expect, it } from "vitest";
import { INITIAL_CONVERSATION, withCustomerMessage, withFailure, withReply } from "./conversation";
import { followAfterScroll, forcesScrollToEnd, isAtEnd, wasJustCovered } from "./conversation-scroll";

const WAITING = withCustomerMessage(INITIAL_CONVERSATION, "Oi", "message-1");

describe("isAtEnd", () => {
  it("accepts the end within the tolerance", () => {
    expect(isAtEnd({ scrollHeight: 1000, clientHeight: 400, scrollTop: 598 })).toBe(true);
  });

  it("rejects a customer who scrolled up", () => {
    expect(isAtEnd({ scrollHeight: 1000, clientHeight: 400, scrollTop: 500 })).toBe(false);
  });
});

describe("followAfterScroll", () => {
  const FOLLOWING_AT_600 = { isFollowing: true, lastScrollTop: 600 };

  it("keeps following when the view shrinks under an unchanged position", () => {
    const measure = { scrollHeight: 1000, clientHeight: 300, scrollTop: 600 };
    expect(followAfterScroll(FOLLOWING_AT_600, measure)).toEqual({ isFollowing: true, lastScrollTop: 600 });
  });

  it("stops following when the customer moves up", () => {
    const measure = { scrollHeight: 1000, clientHeight: 400, scrollTop: 500 };
    expect(followAfterScroll(FOLLOWING_AT_600, measure)).toEqual({ isFollowing: false, lastScrollTop: 500 });
  });

  it("keeps following when the browser pulls the position back to the new end", () => {
    const measure = { scrollHeight: 1000, clientHeight: 500, scrollTop: 500 };
    expect(followAfterScroll(FOLLOWING_AT_600, measure).isFollowing).toBe(true);
  });

  it("does not resume while the reader moves down short of the end", () => {
    const measure = { scrollHeight: 1000, clientHeight: 400, scrollTop: 300 };
    expect(followAfterScroll({ isFollowing: false, lastScrollTop: 100 }, measure).isFollowing).toBe(false);
  });

  it("resumes when the reader reaches the end", () => {
    const measure = { scrollHeight: 1000, clientHeight: 400, scrollTop: 600 };
    expect(followAfterScroll({ isFollowing: false, lastScrollTop: 100 }, measure).isFollowing).toBe(true);
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
