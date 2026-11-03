import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AssistantMarkdown } from "./assistant-markdown";

function renderMarkdown(text: string): HTMLElement {
  return render(<AssistantMarkdown text={text} />).container;
}

describe("AssistantMarkdown", () => {
  it("renders paragraphs, lists and bold", () => {
    const container = renderMarkdown("Veja:\n\n- **Kala** por R$ 349,90\n- Ohana\n\nQuer mais?");
    expect(container.querySelectorAll("p")).toHaveLength(2);
    expect(container.querySelectorAll("ul li")).toHaveLength(2);
    expect(container.querySelector("strong")?.textContent).toBe("Kala");
    expect(container.querySelector("li")?.textContent).toContain("R$ 349,90");
  });

  it("does not turn currency into formulas or lose the symbol", () => {
    expect(renderMarkdown("De R$ 10 a R$ 20").textContent).toBe("De R$ 10 a R$ 20");
  });

  it("opens links outside the conversation", () => {
    const link = renderMarkdown("[Loja](https://exemplo.com.br)").querySelector("a");
    expect(link?.getAttribute("href")).toBe("https://exemplo.com.br");
    expect(link?.getAttribute("target")).toBe("_blank");
    expect(link?.getAttribute("rel")).toContain("noopener");
  });

  it("drops unsafe link targets", () => {
    const container = renderMarkdown("[Clique](javascript:alert(1))");
    expect(container.querySelector("a")).toBeNull();
    expect(container.textContent).toBe("Clique");
  });

  it("keeps raw HTML as text", () => {
    const container = renderMarkdown('<img src="imagem" onerror="alert(1)"> <b>oi</b>');
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("b")).toBeNull();
    expect(container.textContent).toContain("<b>oi</b>");
  });

  it("does not render images", () => {
    expect(renderMarkdown("![foto](https://exemplo.com.br/a.png)").querySelector("img")).toBeNull();
  });

  it("renders titles without heading tags and keeps their text", () => {
    const container = renderMarkdown("# Horários\n\nSegunda");
    expect(container.querySelector("h1")).toBeNull();
    expect(container.textContent).toContain("Horários");
  });

  it("keeps single line breaks of a paragraph", () => {
    expect(renderMarkdown("Linha um\nLinha dois").querySelector("p")?.textContent).toBe("Linha um\nLinha dois");
  });
});
