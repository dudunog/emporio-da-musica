import { describe, expect, it } from "vitest";
import { withUnbreakableCurrency } from "./currency-text";

describe("withUnbreakableCurrency", () => {
  it("joins the symbol and every value", () => {
    expect(withUnbreakableCurrency("De R$ 549,00 por R$ 439,20")).toBe("De R$ 549,00 por R$ 439,20");
  });

  it("keeps other text intact", () => {
    expect(withUnbreakableCurrency("Sem valor, R$549 e 5 reais")).toBe("Sem valor, R$549 e 5 reais");
  });
});
