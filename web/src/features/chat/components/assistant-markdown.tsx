import type { ComponentProps } from "react";
import Markdown, { type Components } from "react-markdown";
import { withUnbreakableCurrency } from "../currency-text";

const ALLOWED_ELEMENTS = ["p", "br", "strong", "em", "a", "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5", "h6", "code", "pre"];
const BLOCK_SPACING = "mb-2 last:mb-0";

function Paragraph({ children }: ComponentProps<"p">) {
  return <p className={`${BLOCK_SPACING} whitespace-pre-line`}>{children}</p>;
}

function Heading({ children }: ComponentProps<"h3">) {
  return <p className={`${BLOCK_SPACING} font-semibold`}>{children}</p>;
}

function Strong({ children }: ComponentProps<"strong">) {
  return <strong className="font-semibold">{children}</strong>;
}

function BulletList({ children }: ComponentProps<"ul">) {
  return <ul className={`${BLOCK_SPACING} list-disc pl-list-indent`}>{children}</ul>;
}

function NumberedList({ children }: ComponentProps<"ol">) {
  return <ol className={`${BLOCK_SPACING} list-decimal pl-list-indent`}>{children}</ol>;
}

function ListItem({ children }: ComponentProps<"li">) {
  return <li className="mb-1 last:mb-0 marker:text-muted">{children}</li>;
}

function ExternalLink({ children, href }: ComponentProps<"a">) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className="underline underline-offset-2 hover:no-underline">
      {children}
    </a>
  );
}

function InlineCode({ children }: ComponentProps<"code">) {
  return <code className="rounded-sm bg-surface px-1 font-sans">{children}</code>;
}

function CodeBlock({ children }: ComponentProps<"pre">) {
  return <pre className={`${BLOCK_SPACING} font-sans whitespace-pre-wrap`}>{children}</pre>;
}

const MARKDOWN_COMPONENTS: Components = {
  p: Paragraph,
  h1: Heading,
  h2: Heading,
  h3: Heading,
  h4: Heading,
  h5: Heading,
  h6: Heading,
  strong: Strong,
  ul: BulletList,
  ol: NumberedList,
  li: ListItem,
  a: ExternalLink,
  code: InlineCode,
  pre: CodeBlock,
};

export function AssistantMarkdown({ text }: Readonly<{ text: string }>) {
  return (
    <Markdown allowedElements={ALLOWED_ELEMENTS} unwrapDisallowed components={MARKDOWN_COMPONENTS}>
      {withUnbreakableCurrency(text)}
    </Markdown>
  );
}
