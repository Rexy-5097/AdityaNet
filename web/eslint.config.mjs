import js from "@eslint/js";
import tseslint from "typescript-eslint";
import astro from "eslint-plugin-astro";
import boundaries from "eslint-plugin-boundaries";

/**
 * ESLint configuration.
 *
 * The dependency graph in the specification (§11.2) and the two rendering domains
 * (Amendment 02, P8) are enforced here rather than documented in a README, because a
 * documented rule is applied by a human at 5pm on a Friday eighteen months from now,
 * and a lint rule is applied identically forever.
 *
 * Element types are declared for directories that do not exist yet. That is
 * deliberate: a constraint introduced after the code it governs arrives too late —
 * the violations are already there and now have to be argued about.
 */
export default tseslint.config(
  {
    // `._*` are macOS AppleDouble sidecars. The project volume is not HFS+, so the OS
    // recreates them on every write; they are not source and never will be.
    ignores: ["dist/**", ".astro/**", "node_modules/**", "**/._*"],
  },

  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...astro.configs.recommended,

  // ─── Type safety (§11.4) ───────────────────────────────────────────────────
  {
    rules: {
      // Zero `any`. A third-party gap gets an explicit local .d.ts, not an escape hatch.
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/consistent-type-imports": "error",
      eqeqeq: ["error", "always"],
      "no-console": ["error", { allow: ["warn", "error"] }],
    },
  },

  // ─── Architecture and rendering-domain boundaries ──────────────────────────
  {
    plugins: { boundaries },
    settings: {
      "boundaries/include": ["src/**/*"],
      "boundaries/elements": [
        { type: "pages", pattern: "src/pages/**/*" },
        { type: "layouts", pattern: "src/layouts/**/*" },
        { type: "primitives", pattern: "src/components/primitives/**/*" },
        { type: "evidence", pattern: "src/components/evidence/**/*" },
        { type: "narrative", pattern: "src/components/narrative/**/*" },
        { type: "shell", pattern: "src/components/shell/**/*" },
        // Domain B — measured evidence. Every encoding traceable to an artifact.
        { type: "scientific", pattern: "src/scientific/**/*" },
        // Domain A — artistic. Sealed: nothing outside may reach into it.
        { type: "experience", pattern: "src/experience/**/*" },
        { type: "lib-science", pattern: "src/lib/science/**/*" },
        { type: "lib-format", pattern: "src/lib/format/**/*" },
        { type: "lib-data", pattern: "src/lib/data/**/*" },
        { type: "generated", pattern: "src/generated/**/*" },
      ],
    },
    rules: {
      "boundaries/element-types": [
        "error",
        {
          default: "disallow",
          rules: [
            // Routes compose; they do not implement.
            {
              from: "pages",
              allow: [
                "layouts",
                "primitives",
                "evidence",
                "narrative",
                "shell",
                "scientific",
                "experience",
                "lib-data",
                "lib-format",
                "generated",
              ],
            },
            { from: "layouts", allow: ["primitives", "shell", "lib-format", "generated"] },

            // The two rendering domains may not import each other. This is what
            // guarantees that a total failure of the GPU layer cannot affect a single
            // credibility surface — they cannot even name it.
            {
              from: "experience",
              allow: ["primitives", "lib-science", "lib-format", "generated"],
            },
            {
              from: "scientific",
              allow: ["primitives", "lib-science", "lib-format", "lib-data", "generated"],
            },

            { from: "evidence", allow: ["primitives", "lib-format", "generated"] },
            { from: "narrative", allow: ["primitives", "evidence", "lib-format", "generated"] },
            { from: "shell", allow: ["primitives", "lib-format", "generated"] },

            // Primitives stay data-unaware, or they stop being reusable.
            { from: "primitives", allow: ["lib-format", "generated"] },

            // Pure functions. Keeping scientific logic free of any framework is what
            // makes 100% branch coverage on it both achievable and meaningful (§11.5).
            { from: "lib-science", allow: [] },

            { from: "lib-format", allow: ["generated"] },
            { from: "lib-data", allow: ["lib-format", "generated"] },
            { from: "generated", allow: [] },
          ],
        },
      ],
    },
  },

  // Generated code is verified by `generate --check`, not by lint.
  {
    files: ["src/generated/**/*"],
    rules: { "@typescript-eslint/no-explicit-any": "off" },
  },

  // Build tooling runs in Node and reports to the operator via stdout.
  {
    files: ["scripts/**/*.ts"],
    rules: { "no-console": "off" },
  },
);
