import { defineConfig } from "vitest/config";

/**
 * The `pnpm test` gate (§11.5, collapsed to four gates by Part 3 R2).
 *
 * Sprint 0 covers only the WCAG contrast maths. Coverage thresholds are declared
 * per-directory rather than globally, because §11.5 requires coverage to follow
 * consequence: a wrong branch in scientific logic produces a plausible-looking but
 * incorrect chart, which is a silent error. Everywhere else, errors are visible.
 */
export default defineConfig({
  test: {
    include: ["scripts/**/*.test.ts", "src/**/*.test.{ts,tsx}"],
    // macOS writes AppleDouble sidecars (`._name`) onto the non-APFS external volume this
    // repo lives on. They match the globs above but are binary metadata, so Vite fails to
    // transform them and the run reports a phantom failing suite. Excluded, not deleted —
    // the OS recreates them on every write.
    exclude: ["**/node_modules/**", "**/dist/**", "**/._*"],
    environment: "node",
    coverage: {
      provider: "v8",
      include: ["scripts/lib/**", "src/lib/**"],
    },
  },
});
