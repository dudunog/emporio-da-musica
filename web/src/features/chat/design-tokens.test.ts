import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

type Theme = "light" | "dark";
type ColorPair = Readonly<[foreground: string, background: string, light: number, dark: number]>;

const GLOBALS_CSS = readFileSync("src/app/globals.css", "utf8");
const HEX_COLOR = /#[0-9a-f]{6}\b/gi;
const LIGHT_DARK_VALUE = /^light-dark\((.+),\s*(.+)\)$/;
const VARIABLE_REFERENCE = /^var\((--[\w-]+)\)$/;
const TOKEN_DECLARATION = /^\s*(--[\w-]+):\s*(.+);$/gm;
const THEME_INDEX = { light: 1, dark: 2 };
const LARGE_OR_ICON_MINIMUM = 3;
const TEXT_MINIMUM = 4.5;
const LUMINANCE_THRESHOLD = 0.03928;

const TOKENS = new Map([...GLOBALS_CSS.matchAll(TOKEN_DECLARATION)].map(([, name, value]) => [name, value]));

const TEXT_PAIRS: readonly ColorPair[] = [
  ["--text", "--bg", 16.96, 15.91],
  ["--text", "--surface-agent", 15.3, 13.55],
  ["--text", "--surface", 17.49, 14.87],
  ["--text", "--surface-error", 16.09, 14.34],
  ["--text-on-user", "--surface-user", 5.01, 7.11],
  ["--text-secondary", "--bg", 6.0, 7.03],
  ["--text-secondary", "--surface-agent", 5.41, 5.98],
  ["--text-secondary", "--surface", 6.19, 6.57],
  ["--text-placeholder", "--surface", 4.9, 4.83],
  ["--brand", "--bg", 4.86, 7.83],
  ["--error", "--surface-error", 6.05, 5.99],
  ["--error", "--surface-action", 6.57, 5.09],
  ["--on-brand", "--brand", 5.01, 7.83],
];
const FOCUS_PAIRS: readonly ColorPair[] = [["--focus", "--surface", 5.01, 7.31]];

function resolveToken(name: string, theme: Theme): string {
  const value = TOKENS.get(name);
  if (value === undefined) throw new Error(`Missing token ${name}`);
  return resolveValue(value, theme);
}

function resolveValue(value: string, theme: Theme): string {
  const themed = value.match(LIGHT_DARK_VALUE)?.[THEME_INDEX[theme]] ?? value;
  const reference = themed.match(VARIABLE_REFERENCE)?.[1];
  return reference ? resolveToken(reference, theme) : themed;
}

function channelLuminance(channel: number): number {
  const normalized = channel / 255;
  return normalized <= LUMINANCE_THRESHOLD ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4;
}

function relativeLuminance(hex: string): number {
  const [red, green, blue] = [1, 3, 5].map((start) => channelLuminance(parseInt(hex.slice(start, start + 2), 16)));
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

function contrastRatio(foreground: string, background: string): number {
  const [lighter, darker] = [relativeLuminance(foreground), relativeLuminance(background)].sort((first, second) => second - first);
  return (lighter + 0.05) / (darker + 0.05);
}

function expectPair([foreground, background, light, dark]: ColorPair, minimum: number) {
  const expected = { light, dark };
  for (const theme of ["light", "dark"] as const) {
    const ratio = contrastRatio(resolveToken(foreground, theme), resolveToken(background, theme));
    expect(ratio).toBeGreaterThanOrEqual(minimum);
    expect(ratio).toBeCloseTo(expected[theme], 1);
  }
}

describe("design tokens", () => {
  it.each(TEXT_PAIRS)("%s over %s passes AA", (...pair) => {
    expectPair(pair, TEXT_MINIMUM);
  });

  it.each(FOCUS_PAIRS)("%s over %s is visible", (...pair) => {
    expectPair(pair, LARGE_OR_ICON_MINIMUM);
  });

  it("declares each color once and never pure black", () => {
    const colors = (GLOBALS_CSS.match(HEX_COLOR) ?? []).map((color) => color.toLowerCase());
    expect(new Set(colors).size).toBe(colors.length);
    expect(colors).not.toContain("#000000");
  });

  it("keeps the stylesheet free of comments and overrides", () => {
    expect(GLOBALS_CSS).not.toContain("/*");
    expect(GLOBALS_CSS).not.toContain("!important");
    expect(GLOBALS_CSS.split("\n").length).toBeLessThan(300);
  });
});
