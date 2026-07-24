/**
 * WCAG 2.2 contrast math.
 *
 * Extracted from check.ts because it has two real consumers — the budget gate and
 * its test. This is a pure function guarding an accessibility gate: if the maths is
 * wrong, the gate passes silently and every contrast claim in the specification
 * becomes false. That consequence is why it is tested, per §11.5's rule that
 * coverage follows consequence rather than uniformity.
 */

/** Parse `#RRGGBB` into its three 0–255 channels. Throws on any other shape. */
function channels(hex: string): [number, number, number] {
  if (!/^#[0-9a-fA-F]{6}$/.test(hex)) {
    throw new Error(`Expected a #RRGGBB colour, received "${hex}"`);
  }
  return [1, 3, 5].map((offset) => Number.parseInt(hex.slice(offset, offset + 2), 16)) as [
    number,
    number,
    number,
  ];
}

/** Relative luminance. https://www.w3.org/TR/WCAG22/#dfn-relative-luminance */
export function relativeLuminance(hex: string): number {
  const [r, g, b] = channels(hex).map((channel) => {
    const srgb = channel / 255;
    return srgb <= 0.03928 ? srgb / 12.92 : ((srgb + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];

  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/** Contrast ratio between two colours, from 1:1 (identical) to 21:1 (black on white). */
export function contrastRatio(a: string, b: string): number {
  const first = relativeLuminance(a);
  const second = relativeLuminance(b);
  const lighter = Math.max(first, second);
  const darker = Math.min(first, second);
  return (lighter + 0.05) / (darker + 0.05);
}
