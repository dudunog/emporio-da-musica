import { describe, expect, it } from "vitest";
import { MAX_MESSAGE_LENGTH, cleanMessage, isSendKey, isSendable } from "./composer-rules";

describe("cleanMessage", () => {
  it("removes only the ends", () => {
    expect(cleanMessage("  oi\n\ntudo bem \n")).toBe("oi\n\ntudo bem");
  });

  it("turns blank drafts into an empty message", () => {
    expect(cleanMessage(" \n\t\u00a0 ")).toBe("");
  });
});

describe("isSendable", () => {
  it("accepts text up to the limit", () => {
    expect(isSendable("a".repeat(MAX_MESSAGE_LENGTH))).toBe(true);
  });

  it("rejects empty text and text above the limit", () => {
    expect(isSendable("")).toBe(false);
    expect(isSendable("a".repeat(MAX_MESSAGE_LENGTH + 1))).toBe(false);
  });
});

describe("isSendKey", () => {
  it("sends on Enter", () => {
    expect(isSendKey({ key: "Enter", shiftKey: false, isComposing: false })).toBe(true);
  });

  it("keeps Shift+Enter as a line break", () => {
    expect(isSendKey({ key: "Enter", shiftKey: true, isComposing: false })).toBe(false);
  });

  it("ignores Enter while composing accents", () => {
    expect(isSendKey({ key: "Enter", shiftKey: false, isComposing: true })).toBe(false);
  });

  it("ignores other keys", () => {
    expect(isSendKey({ key: "a", shiftKey: false, isComposing: false })).toBe(false);
  });
});
