import { describe, expect, it } from "vitest";
import { MAX_MESSAGE_LENGTH, cleanMessage, isSendKey, isSendable } from "./composer-rules";

describe("cleanMessage", () => {
  it("removes only the ends", () => {
    expect(cleanMessage("  oi\n\ntudo bem \n")).toBe("oi\n\ntudo bem");
  });

  it.each([" \n\t\u00a0 ", "\u0085", "\u1680\u2003\u2028\u202f\u205f\u3000", "\u200b", "\u200c\u200d\u2060\ufeff"])("turns the blank draft %j into an empty message", (draft) => {
    expect(cleanMessage(draft)).toBe("");
  });

  it("keeps invisible characters inside the text", () => {
    expect(cleanMessage("\u0085a\u200bb\u0085")).toBe("a\u200bb");
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

  it("rejects a broken character the server refuses and accepts a complete emoji", () => {
    expect(isSendable("oi \ud83d")).toBe(false);
    expect(isSendable("oi \ud83d\ude00")).toBe(true);
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
