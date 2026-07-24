/**
 * Invariant and budget enforcement. Spec §11.1 — one of four bespoke tooling artifacts.
 *
 * This is the `pnpm budget` gate. It converts specification principles into build
 * failures rather than relying on developer discipline, which has a half-life of
 * about six months.
 *
 * Sprint 0 enforces:
 *   1. Contrast floors  (§12.2 — AAA body text; a token change cannot silently
 *                        drop text below 7:1)
 *   2. Initial JS budget (§11.6 — measured from the built HTML, gzipped)
 *
 * Later sprints add: L2 evidence consistency (S1), banned lexicon (S2),
 * per-artifact data-tier budgets (S6).
 */

import { readFileSync, existsSync, statSync, readdirSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { join, dirname, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { contrastRatio } from "./lib/contrast";

const WEB_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const OUT_DIR = join(WEB_ROOT, "dist");
const REPO_ROOT = join(WEB_ROOT, "..");

/**
 * Per-route budgets. Spec §11.6 as revised by Amendment 02 §18.11 (measured, not
 * estimated). Routes are added to this table as they ship; a route absent from it
 * is a route whose cost nobody has agreed to.
 */
const JS_BUDGETS_BYTES: ReadonlyArray<{ route: string; html: string; budget: number }> = [
  // Amendment 02 §18.0 budgets. `/` rises to 450 KB when the experience island lands
  // in Sprint 3; until then it is a static page and is held to the evidence budget.
  { route: "/", html: "index.html", budget: 450 * 1024 },
  { route: "/validation", html: "validation/index.html", budget: 15 * 1024 },
  { route: "/validation/001", html: "validation/contradiction-001/index.html", budget: 15 * 1024 },
  { route: "/validation/003", html: "validation/contradiction-003/index.html", budget: 15 * 1024 },
  { route: "/findings", html: "findings/index.html", budget: 120 * 1024 },
  { route: "/pipeline", html: "pipeline/index.html", budget: 200 * 1024 },
  { route: "/data", html: "data/index.html", budget: 260 * 1024 },
  { route: "/build", html: "build/index.html", budget: 20 * 1024 },
];

const failures: string[] = [];
const notes: string[] = [];

function fail(message: string): void {
  failures.push(message);
}

// ─── 1. Contrast floors ──────────────────────────────────────────────────────

interface ColorTokens {
  primitive: Record<string, string>;
  semantic: Record<string, Record<string, string>>;
  contrastFloors: Record<string, number>;
}

function checkContrast(): void {
  const tokens = JSON.parse(
    readFileSync(join(WEB_ROOT, "tokens/color.json"), "utf8"),
  ) as ColorTokens;

  const dark = tokens.semantic["dark"];
  if (dark === undefined) {
    fail("colour tokens: theme 'dark' is missing");
    return;
  }

  const resolve = (role: string): string | undefined => {
    const primitiveName = dark[role];
    return primitiveName === undefined ? undefined : tokens.primitive[primitiveName];
  };

  const background = resolve("canvas");
  if (background === undefined) {
    fail("colour tokens: semantic role 'canvas' does not resolve");
    return;
  }

  for (const [role, floor] of Object.entries(tokens.contrastFloors)) {
    if (role.startsWith("$")) continue;

    const foreground = resolve(role);
    if (foreground === undefined) {
      fail(`contrast: role "${role}" has a floor but does not resolve to a colour`);
      continue;
    }

    const ratio = contrastRatio(foreground, background);
    if (ratio < floor) {
      fail(
        `contrast: --color-${role} (${foreground}) on --color-canvas (${background}) ` +
          `is ${ratio.toFixed(2)}:1, below the required ${floor}:1`,
      );
    } else {
      notes.push(`  --color-${role.padEnd(12)} ${ratio.toFixed(2)}:1  (floor ${floor}:1)`);
    }
  }
}

// ─── 1b. Token namespace collisions ──────────────────────────────────────────

/**
 * Reject a colour token whose name collides with a font-size utility.
 *
 * Tailwind v4 derives utilities from token names, and `--color-x` and `--text-x` both
 * generate `text-x`. The colour wins. Naming a colour role `base` therefore turned
 * every `text-base` in the codebase into `color: var(--color-base)` — painting body
 * copy in the background colour, invisible on the background.
 *
 * It produced no error, no warning, and no failing test. The page simply had missing
 * paragraphs, and it survived a visual pass because the surrounding layout looked
 * correct. Found in Sprint 3 by reading computed styles in a browser.
 *
 * Checked against both our own type scale and Tailwind's built-in font-size names,
 * since either side of the collision is enough to cause it.
 */
const TAILWIND_FONT_SIZES: readonly string[] = [
  "xs", "sm", "base", "lg", "xl", "2xl", "3xl", "4xl", "5xl", "6xl", "7xl", "8xl", "9xl",
];

function checkTokenCollisions(): void {
  const colours = JSON.parse(
    readFileSync(join(WEB_ROOT, "tokens/color.json"), "utf8"),
  ) as { semantic: Record<string, Record<string, string>> };
  const typography = JSON.parse(
    readFileSync(join(WEB_ROOT, "tokens/typography.json"), "utf8"),
  ) as { interface: Record<string, unknown> };

  const theme = colours.semantic["dark"] ?? {};
  const colourNames = Object.keys(theme).filter((name) => !name.startsWith("$"));
  const sizeNames = new Set([
    ...Object.keys(typography.interface).filter((name) => !name.startsWith("$")),
    ...TAILWIND_FONT_SIZES,
  ]);

  const collisions = colourNames.filter((name) => sizeNames.has(name));

  if (collisions.length > 0) {
    fail(
      `token collision: colour role(s) ${collisions.map((n) => `"${n}"`).join(", ")} ` +
        `share a name with a font-size utility. Tailwind generates text-<name> for both ` +
        `and the colour wins, silently recolouring text. Rename the colour role.`,
    );
  } else {
    notes.push(`  token collisions: none across ${colourNames.length} colour role(s)`);
  }
}

// ─── 2. Initial JS budget ────────────────────────────────────────────────────

/**
 * Measure what a browser actually downloads for a route: parse the built HTML for
 * script sources and sum their gzipped sizes.
 *
 * Two rejected alternatives, for the record. Summing dist/_astro/** over-counts
 * chunks that no single route loads. Trusting the bundler's own reported total
 * would trust the thing being measured — and the framework migration that produced
 * this file happened precisely because a reported number was taken on faith.
 */
function measureRouteJs(htmlPath: string): { bytes: number; scripts: number } | null {
  const absolute = join(OUT_DIR, htmlPath);
  if (!existsSync(absolute)) return null;

  const markup = readFileSync(absolute, "utf8");

  /**
   * Collect every JavaScript module a browser would fetch for this route.
   *
   * Sprint 3 found that counting `<script src>` alone under-reported the experience
   * island by roughly 150x — it measured 2.0 KB against a true ~300 KB. Astro
   * references island code through `<astro-island component-url renderer-url>`
   * attributes, and those chunks then import further chunks. None of it appears as a
   * classic script tag.
   *
   * So: seed from every `/_astro/*.js` path mentioned anywhere in the markup, then walk
   * the import graph transitively. A budget that measures around the payload it exists
   * to constrain is worse than no budget, because it reports a reassuring number.
   */
  const queue = [
    ...new Set(
      [...markup.matchAll(/["'(]([/][^"'()\s]*\.js)["')]/g)]
        .map((match) => match[1])
        .filter((path): path is string => path !== undefined),
    ),
  ];

  const seen = new Set<string>();
  let bytes = 0;

  while (queue.length > 0) {
    const modulePath = queue.pop()!;
    if (seen.has(modulePath)) continue;
    seen.add(modulePath);

    const asset = join(OUT_DIR, modulePath);
    if (!existsSync(asset) || !statSync(asset).isFile()) continue;

    const code = readFileSync(asset);
    bytes += gzipSync(code).length;

    // Static and dynamic imports both appear as absolute /_astro/ paths after bundling.
    for (const match of code.toString("utf8").matchAll(/["'(]([/]_astro[/][^"'()\s]*\.js)["')]/g)) {
      const dependency = match[1];
      if (dependency !== undefined && !seen.has(dependency)) queue.push(dependency);
    }
  }

  const sources = seen;

  // Inline scripts are real payload and must be counted. Sprint 3 found this the hard
  // way: the experience island reported "0.0 KB, 0 scripts" because Astro's island
  // bootstrap is inline, so the budget gate was measuring around the very thing it
  // existed to measure. Their CSP hashes are injected by scripts/postbuild.ts.
  let inlineCount = 0;
  for (const match of markup.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)) {
    if (/\btype="application\/ld\+json"/.test(match[0])) continue;
    const body = match[1];
    if (body === undefined || body.length === 0) continue;
    inlineCount += 1;
    bytes += gzipSync(Buffer.from(body, "utf8")).length;
  }

  return { bytes, scripts: sources.size + inlineCount };
}

function checkRouteBudgets(): void {
  if (!existsSync(OUT_DIR)) {
    notes.push("  route budgets: skipped (no build output — run `pnpm build` first)");
    return;
  }

  for (const { route, html, budget } of JS_BUDGETS_BYTES) {
    const measured = measureRouteJs(html);
    if (measured === null) {
      fail(`route budget: ${route} has a budget but emitted no ${html}`);
      continue;
    }

    const kib = (measured.bytes / 1024).toFixed(1);
    const budgetKib = (budget / 1024).toFixed(0);

    if (measured.bytes > budget) {
      fail(
        `route ${route}: ${kib} KB gz JS exceeds the ${budgetKib} KB budget ` +
          `(${measured.scripts} scripts)`,
      );
    } else {
      notes.push(
        `  route ${route.padEnd(12)} ${kib.padStart(6)} KB gz JS  ` +
          `(budget ${budgetKib} KB, ${measured.scripts} scripts)`,
      );
    }
  }
}

// ─── 3. Deployable-output hygiene ────────────────────────────────────────────

/**
 * Assert that nothing in dist/ is operating-system metadata.
 *
 * scripts/postbuild.ts removes these; this is the safety net that ensures a failure
 * there cannot silently ship resource forks and extended attributes to a public CDN.
 * Belt and braces, because the failure is invisible in code review.
 */
function checkDistHygiene(): void {
  if (!existsSync(OUT_DIR)) return;

  const strays: string[] = [];

  const walk = (directory: string): void => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const path = join(directory, entry.name);
      if (entry.name.startsWith("._") || entry.name === ".DS_Store") {
        strays.push(relative(OUT_DIR, path));
      } else if (entry.isDirectory()) {
        walk(path);
      }
    }
  };
  walk(OUT_DIR);

  if (strays.length > 0) {
    fail(
      `dist hygiene: ${strays.length} operating-system metadata file(s) would be ` +
        `deployed (e.g. ${strays.slice(0, 3).join(", ")}). Run \`pnpm build\`.`,
    );
  } else {
    notes.push("  dist hygiene: no operating-system metadata");
  }
}

// ─── 4. Evidence consistency ─────────────────────────────────────────────────

/**
 * The gate this platform exists for.
 *
 * Every other check verifies that the code is well-built. This one verifies that the
 * website is not lying. It extracts each rendered measurement from the built HTML,
 * re-reads the ORIGINAL scientific artifact from disk, resolves the recorded JSON
 * pointer, formats it, and asserts the strings match.
 *
 * Critically, it trusts nothing in between. It does not read measurements.json and it
 * does not read the generated TypeScript — both are outputs of the same generator
 * that produced the page, so agreeing with them would prove only self-consistency.
 * Going back to the artifact closes the loop from rendered pixels to committed
 * science.
 *
 * Error budget: zero, permanently. This check is not waivable.
 */

/**
 * Parse a scientific artifact that may contain Python's non-standard JSON output.
 *
 * `json.dump` emits bare `NaN`, `Infinity`, and `-Infinity` unless `allow_nan=False`.
 * Python reads them back happily, so the defect is invisible from the pipeline side —
 * but they are not JSON (RFC 8259 has no such literals), and `JSON.parse` rejects the
 * whole document. `benchmark_results.json` contains `"brier": NaN` for the models that
 * emit hard classifications rather than probabilities.
 *
 * The substitution is deliberately narrow: only bare literals in numeric positions
 * become `null`. It cannot mask a value mismatch, because a field that was NaN was
 * never a number this platform could have displayed. Strings containing "NaN" are
 * unaffected — the surrounding punctuation is required to match.
 *
 * This is tolerance at the boundary, not endorsement. Recorded as a defect against the
 * artifact: any standards-compliant API consumer would fail on these files.
 */
function parseScientificJson(text: string): unknown {
  const sanitised = text
    .replace(/(:\s*)(NaN|-?Infinity)(\s*[,}\]])/g, "$1null$3")
    .replace(/([[,]\s*)(NaN|-?Infinity)(\s*[,\]])/g, "$1null$3");
  return JSON.parse(sanitised);
}

/** Resolve an RFC-6901 pointer. Mirrors resolve_pointer() in scripts/web/derive.py. */
function resolvePointer(document: unknown, pointer: string): unknown {
  if (pointer === "") return document;

  let current: unknown = document;
  for (const rawToken of pointer.slice(1).split("/")) {
    // '~1' before '~0': decoding in the wrong order turns a literal '~1' into '/'.
    const token = rawToken.replace(/~1/g, "/").replace(/~0/g, "~");
    if (Array.isArray(current)) {
      current = current[Number(token)];
    } else if (typeof current === "object" && current !== null && token in current) {
      current = (current as Record<string, unknown>)[token];
    } else {
      throw new Error(`pointer ${pointer} failed at ${token}`);
    }
  }
  return current;
}

/** Mirrors formatValue() in src/lib/format/quantity.ts. */
function formatFromArtifact(value: number, precision: number, unit?: string): string {
  if (unit === "bytes") {
    const units = ["B", "KiB", "MiB", "GiB", "TiB"];
    let scaled = value;
    let index = 0;
    while (scaled >= 1024 && index < units.length - 1) {
      scaled /= 1024;
      index += 1;
    }
    return `${scaled.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
  }

  const formatted = value.toLocaleString("en-US", {
    minimumFractionDigits: precision,
    maximumFractionDigits: precision,
  });
  return unit === undefined ? formatted : `${formatted} ${unit}`;
}

interface MeasurementRecord {
  value: number;
  precision: number;
  artifact: string;
  pointer: string;
  unit?: string;
}

function checkEvidenceConsistency(): void {
  if (!existsSync(OUT_DIR)) {
    notes.push("  evidence consistency: skipped (no build output)");
    return;
  }

  const measurementsPath = join(WEB_ROOT, "src/generated/data/measurements.json");
  if (!existsSync(measurementsPath)) {
    fail("evidence consistency: measurements.json is missing. Run scripts/web/derive.py.");
    return;
  }
  // measurements.json supplies only WHERE to look (artifact + pointer + precision).
  // The VALUE always comes from the artifact itself, never from here.
  const registry = JSON.parse(readFileSync(measurementsPath, "utf8")) as Record<
    string,
    MeasurementRecord
  >;

  const artifactCache = new Map<string, unknown>();
  const loadArtifact = (relative: string): unknown => {
    const cached = artifactCache.get(relative);
    if (cached !== undefined) return cached;
    const parsed = parseScientificJson(readFileSync(join(REPO_ROOT, relative), "utf8"));
    artifactCache.set(relative, parsed);
    return parsed;
  };

  let verified = 0;

  const htmlFiles: string[] = [];
  const collect = (directory: string): void => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const path = join(directory, entry.name);
      if (entry.isDirectory()) collect(path);
      else if (entry.name.endsWith(".html")) htmlFiles.push(path);
    }
  };
  collect(OUT_DIR);

  for (const file of htmlFiles) {
    const markup = readFileSync(file, "utf8");
    const route = relative(OUT_DIR, file);

    // Each card carries its key; the value it rendered sits in data-measurement-value.
    const cards = markup.matchAll(
      /data-measurement-key="([^"]+)"[\s\S]*?data-measurement-value[^>]*>([^<]*)</g,
    );

    for (const card of cards) {
      const key = card[1];
      const rendered = card[2];
      if (key === undefined || rendered === undefined) continue;

      // The HTML attribute is entity-encoded; the registry key is not.
      const decodedKey = key.replace(/&quot;/g, '"').replace(/&amp;/g, "&");
      const record = registry[decodedKey];
      if (record === undefined) {
        fail(`evidence: ${route} renders unknown measurement key "${decodedKey}"`);
        continue;
      }

      let truth: string;
      try {
        const raw = resolvePointer(loadArtifact(record.artifact), record.pointer);
        if (typeof raw !== "number") {
          fail(`evidence: ${record.artifact}${record.pointer} is not a number`);
          continue;
        }
        truth = formatFromArtifact(raw, record.precision, record.unit);
      } catch (error) {
        fail(`evidence: ${record.artifact}${record.pointer} — ${(error as Error).message}`);
        continue;
      }

      const shown = rendered.trim().replace(/&nbsp;/g, " ");
      if (shown !== truth) {
        fail(
          `evidence: ${route} renders "${shown}" for ${record.artifact}${record.pointer}, ` +
            `but the artifact says "${truth}"`,
        );
      } else {
        verified += 1;
      }
    }
  }

  if (verified === 0) {
    notes.push("  evidence consistency: no measurements rendered yet");
  } else {
    notes.push(`  evidence consistency: ${verified} rendered value(s) match their artifacts`);
  }
}

// ─── 5. Banned lexicon ───────────────────────────────────────────────────────

/**
 * Reject vocabulary that would imply live operations or overstate the platform.
 *
 * This exists as a gate rather than a style guide because marketing language
 * re-enters a codebase through copy edits months later, when nobody remembers the
 * rule. A failing build remembers.
 *
 * Only high-signal multi-word terms are blocked. Single words like "live" appear
 * legitimately (`live_time_s` is a real column) and a rule everyone disables is worse
 * than no rule at all.
 */
const BANNED_TERMS: readonly RegExp[] = [
  /\breal[-\s]?time\b/i,
  /\blive (telemetry|data|feed)\b/i,
  /\bmission control\b/i,
  /\bAI[-\s]powered\b/i,
  /\bstate[-\s]of[-\s]the[-\s]art\b/i,
  /\bcutting[-\s]edge\b/i,
  /\brevolutionary\b/i,
  /\bseamless(ly)?\b/i,
  /\bofficial (platform|tool|software)\b/i,
];

/** Visible text only: attribute values and markup are not user-facing prose. */
function visibleText(markup: string): string {
  return markup
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ");
}

function checkBannedLexicon(htmlFiles: readonly string[]): void {
  let flagged = 0;

  for (const file of htmlFiles) {
    const text = visibleText(readFileSync(file, "utf8"));
    for (const pattern of BANNED_TERMS) {
      const match = pattern.exec(text);
      if (match !== null) {
        fail(`lexicon: ${relative(OUT_DIR, file)} contains "${match[0]}" (implies live operation)`);
        flagged += 1;
      }
    }
  }

  if (flagged === 0) notes.push(`  banned lexicon: clean across ${htmlFiles.length} page(s)`);
}

// ─── 6. Measurement literals in source ───────────────────────────────────────

/**
 * Reject hand-typed numbers in page templates.
 *
 * The evidence-consistency gate proves that every *rendered* measurement matches its
 * artifact, but it can only check values that went through MetricCard. A number typed
 * directly into prose — "340 channels", "581 events" — would sail past it while being
 * exactly the kind of unsourced claim principle P1 exists to prevent.
 *
 * IMPLEMENTATION CHOICE. The specification calls for a custom ESLint rule. This is a
 * source scan instead. An AST rule would be more precise, but Astro template text
 * nodes are awkward to reach through the parser, and a half-working plugin that
 * silently stops matching is worse than a blunt check that visibly does. Recorded as
 * technical debt: revisit if false positives become frequent enough to matter.
 *
 * Threshold: any decimal, or any integer of three or more digits. Small integers
 * ("Sprint 4", "six times") read as prose; a three-digit number reads as a datum.
 */
function checkMeasurementLiterals(): void {
  const sourceFiles: string[] = [];
  const collectSources = (directory: string): void => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const path = join(directory, entry.name);
      if (entry.name.startsWith("._")) continue;
      if (entry.isDirectory()) {
        if (entry.name !== "generated") collectSources(path);
      } else if (entry.name.endsWith(".astro")) {
        sourceFiles.push(path);
      }
    }
  };
  collectSources(join(WEB_ROOT, "src"));

  const NUMERIC = /(\d+\.\d+|\b\d{3,}\b)/;

  /**
   * Standards identifiers are named constants, not measurements. "SHA-256" is the
   * name of an algorithm in the same way "viridis" is the name of a colormap — it
   * has no uncertainty, no denominator, and no artifact to cite.
   *
   * Found by this gate on its first run, which flagged the SHA-256 label in
   * SourceRef. Stripping these is narrower and safer than raising the digit
   * threshold, which would have let genuine three-digit measurements through.
   */
  const STANDARDS = /\b(?:SHA|RFC|ISO|WCAG|UTF|ES|HTTP|AES|CSP)[-\s]?\d[\d.]*\b/gi;

  let flagged = 0;

  for (const file of sourceFiles) {
    const source = readFileSync(file, "utf8");

    // Everything after the frontmatter fence is template. The frontmatter itself is
    // TypeScript, already governed by tsc and ESLint.
    const fenceEnd = source.indexOf("---", 3);
    const template = fenceEnd === -1 ? source : source.slice(fenceEnd + 3);

    const prose = template
      // Script and style blocks are code, governed by tsc and ESLint, and their
      // comments are not user-facing prose.
      .replace(/<script[\s\S]*?<\/script>/g, " ")
      .replace(/<style[\s\S]*?<\/style>/g, " ")
      // Class attributes next. Tailwind utilities carry numbers (`opacity-100`,
      // `max-w-2xl`, `grid-cols-3`) and are never prose. Stripping them before the
      // expression pass matters because a multi-line JSX map breaks the non-greedy
      // `{...}` match, leaving tags — and their class names — in the text.
      .replace(/\bclass(Name)?(:list)?\s*=\s*("[^"]*"|'[^']*'|\{[\s\S]*?\})/g, " ")
      .replace(/\{[\s\S]*?\}/g, " ") // expressions are code, checked elsewhere
      .replace(/<!--[\s\S]*?-->/g, " ")
      .replace(/<[^>]+>/g, " ") // tags carry class names, not prose
      .replace(STANDARDS, " ");

    const match = NUMERIC.exec(prose);
    if (match !== null) {
      fail(
        `measurement literal: ${relative(WEB_ROOT, file)} has "${match[0]}" in template text. ` +
          `Use <MetricCard metric="..."> so the value resolves to an artifact.`,
      );
      flagged += 1;
    }
  }

  if (flagged === 0) {
    notes.push(`  measurement literals: none in ${sourceFiles.length} template(s)`);
  }
}

// ─── Run ─────────────────────────────────────────────────────────────────────

function builtHtmlFiles(): string[] {
  if (!existsSync(OUT_DIR)) return [];
  const files: string[] = [];
  const walk = (directory: string): void => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const path = join(directory, entry.name);
      if (entry.isDirectory()) walk(path);
      else if (entry.name.endsWith(".html")) files.push(path);
    }
  };
  walk(OUT_DIR);
  return files;
}

checkContrast();
checkTokenCollisions();
checkRouteBudgets();
checkDistHygiene();
checkEvidenceConsistency();
checkBannedLexicon(builtHtmlFiles());
checkMeasurementLiterals();

if (notes.length > 0) {
  console.log("check: measurements\n" + notes.join("\n"));
}

if (failures.length > 0) {
  console.error(`\ncheck: ${failures.length} failure(s)\n` + failures.map((f) => `  ${f}`).join("\n"));
  process.exit(1);
}

console.log("\ncheck: all invariants and budgets satisfied.");
