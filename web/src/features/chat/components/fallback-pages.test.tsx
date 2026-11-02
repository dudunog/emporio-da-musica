import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ErrorPage from "@/app/error";
import NotFoundPage from "@/app/not-found";
import { BACK_TO_CHAT_LABEL, NOT_FOUND_MESSAGE, RETRY_LABEL, SERVICE_UNAVAILABLE_MESSAGE, STORE_NAME } from "../chat-copy";

describe("fallback pages", () => {
  it("shows the missing page in pt-BR with a way back", () => {
    render(<NotFoundPage />);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(STORE_NAME);
    expect(screen.getByText(NOT_FOUND_MESSAGE)).toBeTruthy();
    expect(screen.getByRole("link", { name: BACK_TO_CHAT_LABEL }).getAttribute("href")).toBe("/");
  });

  it("shows a rendering failure in pt-BR and retries", () => {
    const retry = vi.fn();
    render(<ErrorPage retry={retry} />);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(STORE_NAME);
    expect(screen.getByRole("alert").textContent).toBe(SERVICE_UNAVAILABLE_MESSAGE);
    fireEvent.click(screen.getByRole("button", { name: RETRY_LABEL }));
    expect(retry).toHaveBeenCalledTimes(1);
  });
});
