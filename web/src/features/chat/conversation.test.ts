import { describe, expect, it } from "vitest";
import { FAILURE_MESSAGES, GREETING } from "./chat-copy";
import {
  INITIAL_CONVERSATION,
  endsWithFailure,
  lastCustomerMessage,
  withCustomerMessage,
  withFailure,
  withReply,
  withRetryStarted,
} from "./conversation";

const FIRST_REPLY = { conversationId: "conversation-1", reply: "Resposta" };

describe("conversation", () => {
  it("starts with only the greeting and no server id", () => {
    expect(INITIAL_CONVERSATION.id).toBeNull();
    expect(INITIAL_CONVERSATION.entries.map(({ kind, text }) => ({ kind, text }))).toEqual([{ kind: "assistant", text: GREETING }]);
    expect(INITIAL_CONVERSATION.isWaiting).toBe(false);
  });

  it("waits after a customer message and stops after the reply", () => {
    const waiting = withCustomerMessage(INITIAL_CONVERSATION, "Oi");
    expect(waiting.isWaiting).toBe(true);
    const answered = withReply(waiting, FIRST_REPLY);
    expect(answered.isWaiting).toBe(false);
    expect(answered.entries.map((entry) => entry.kind)).toEqual(["assistant", "customer", "assistant"]);
  });

  it("always keeps the id of the latest reply", () => {
    const answered = withReply(withCustomerMessage(INITIAL_CONVERSATION, "Oi"), FIRST_REPLY);
    const replaced = withReply(withCustomerMessage(answered, "De novo"), { conversationId: "conversation-2", reply: "Outra" });
    expect(answered.id).toBe("conversation-1");
    expect(replaced.id).toBe("conversation-2");
  });

  it("keeps the id and stores the reason text on failure", () => {
    const answered = withReply(withCustomerMessage(INITIAL_CONVERSATION, "Oi"), FIRST_REPLY);
    const failed = withFailure(withCustomerMessage(answered, "De novo"), "rate_limit");
    expect(failed.id).toBe("conversation-1");
    expect(failed.isWaiting).toBe(false);
    expect(failed.entries.at(-1)?.text).toBe(FAILURE_MESSAGES.rate_limit);
    expect(endsWithFailure(failed)).toBe(true);
  });

  it("retries without duplicating the customer message", () => {
    const failed = withFailure(withCustomerMessage(INITIAL_CONVERSATION, "Oi"), "server");
    const retrying = withRetryStarted(failed);
    expect(retrying.isWaiting).toBe(true);
    expect(retrying.entries.map((entry) => entry.kind)).toEqual(["assistant", "customer"]);
    expect(lastCustomerMessage(retrying)).toBe("Oi");
  });

  it("gives every new entry a new id even after a retry", () => {
    const failed = withFailure(withCustomerMessage(INITIAL_CONVERSATION, "Oi"), "server");
    const answered = withReply(withRetryStarted(failed), FIRST_REPLY);
    const identifiers = answered.entries.map((entry) => entry.id);
    expect(new Set(identifiers).size).toBe(identifiers.length);
    expect(answered.entries.at(-1)?.id).toBeGreaterThan(failed.entries.at(-1)?.id ?? 0);
  });

  it("has no customer message at the start", () => {
    expect(lastCustomerMessage(INITIAL_CONVERSATION)).toBeNull();
  });
});
