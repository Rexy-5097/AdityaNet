import { describe, expect, it } from "vitest";
import { contrastRatio, relativeLuminance } from "./contrast";

describe("relativeLuminance", () => {
  it("anchors at the WCAG endpoints", () => {
    expect(relativeLuminance("#000000")).toBe(0);
    expect(relativeLuminance("#FFFFFF")).toBe(1);
  });

  it("uses the linear segment below the 0.03928 threshold", () => {
    // #030303 -> 3/255 = 0.01176, which is below the threshold and so must be
    // divided by 12.92 rather than passed through the power curve. Getting this
    // branch wrong shifts every near-black comparison, which is the entire dark theme.
    expect(relativeLuminance("#030303")).toBeCloseTo(0.01176 / 12.92, 6);
  });

  it("is not channel-symmetric: green dominates the coefficients", () => {
    expect(relativeLuminance("#00FF00")).toBeGreaterThan(relativeLuminance("#FF0000"));
    expect(relativeLuminance("#FF0000")).toBeGreaterThan(relativeLuminance("#0000FF"));
  });

  it("rejects malformed input rather than silently returning a number", () => {
    expect(() => relativeLuminance("#FFF")).toThrow();
    expect(() => relativeLuminance("E8EBED")).toThrow();
    expect(() => relativeLuminance("rgb(0,0,0)")).toThrow();
  });
});

describe("contrastRatio", () => {
  it("returns the maximum 21:1 for black against white", () => {
    expect(contrastRatio("#000000", "#FFFFFF")).toBeCloseTo(21, 5);
  });

  it("returns 1:1 for a colour against itself", () => {
    expect(contrastRatio("#4A9EFF", "#4A9EFF")).toBeCloseTo(1, 10);
  });

  it("is order-independent", () => {
    expect(contrastRatio("#E8EBED", "#0A0C0E")).toBeCloseTo(
      contrastRatio("#0A0C0E", "#E8EBED"),
      10,
    );
  });

  it("confirms the specification's AAA claim for body text", () => {
    // §5.2.2 claims --color-fg on --color-base clears the 7:1 AAA floor.
    // If this ever fails, the specification is wrong and must be corrected.
    expect(contrastRatio("#E8EBED", "#0A0C0E")).toBeGreaterThanOrEqual(7);
  });
});
