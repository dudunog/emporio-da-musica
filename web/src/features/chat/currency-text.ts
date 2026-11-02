const CURRENCY_PREFIX_WITH_SPACE = /R\$ /g;
const CURRENCY_PREFIX_NO_BREAK = "R$ ";

export function withUnbreakableCurrency(text: string): string {
  return text.replace(CURRENCY_PREFIX_WITH_SPACE, CURRENCY_PREFIX_NO_BREAK);
}
