/**
 * Code generation. Spec §11.1 — one of four sanctioned bespoke tooling artifacts.
 *
 * Sprint 0 generates design tokens only. Later sprints add:
 *   S1  openapi.yaml       -> src/generated/api.ts
 *   S1  measurements.json  -> src/generated/measurements.ts
 *
 * `--check` regenerates into memory and diffs against disk without writing.
 * CI runs it so a hand-edited generated file cannot land (spec §10.1 A3).
 *
 * Why generate at all: hand-syncing token values between CSS and Tailwind is a
 * guaranteed drift source. One generator eliminates the class of bug (§5.8).
 */

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const WEB_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const TOKENS_DIR = join(WEB_ROOT, "tokens");
const OUT_FILE = join(WEB_ROOT, "src/generated/tokens.css");

const BANNER = `/*
 * GENERATED FILE — DO NOT EDIT.
 * Source: web/tokens/*.json   Generator: web/scripts/generate.ts
 * Run \`pnpm generate\` after changing a token. CI fails if this file drifts.
 */`;

/** A token file's shape is validated by use, not by a schema: a missing key throws here. */
interface ColorTokens {
  primitive: Record<string, string>;
  semantic: Record<string, Record<string, string>>;
}
interface TypeScale {
  size: string;
  leading: string;
}
interface TypographyTokens {
  family: Record<string, string>;
  interface: Record<string, TypeScale>;
  document: Record<string, TypeScale>;
  weight: Record<string, string>;
  measure: Record<string, string>;
}
interface SpaceTokens {
  space: Record<string, string>;
  layout: Record<string, string>;
  radius: Record<string, string>;
  elevation: Record<string, string>;
}
interface MotionTokens {
  duration: Record<string, string>;
  easing: Record<string, string>;
}

function readTokens<T>(name: string): T {
  return JSON.parse(readFileSync(join(TOKENS_DIR, `${name}.json`), "utf8")) as T;
}

/** `$comment` keys document the source files; they are not tokens. */
function isToken(key: string): boolean {
  return !key.startsWith("$");
}

function entriesOf(obj: Record<string, unknown>): [string, string][] {
  return Object.entries(obj)
    .filter(([k, v]) => isToken(k) && typeof v === "string")
    .map(([k, v]) => [k, v as string]);
}

/**
 * Resolve a semantic theme (role -> primitive name) to concrete values.
 * Throws on an unknown primitive so a typo fails the build rather than
 * emitting an empty custom property that would silently render transparent.
 */
function resolveTheme(
  theme: Record<string, string>,
  primitives: Record<string, string>,
): [string, string][] {
  return entriesOf(theme).map(([role, primitiveName]) => {
    const value = primitives[primitiveName];
    if (value === undefined) {
      throw new Error(
        `Token error: semantic role "${role}" references unknown primitive "${primitiveName}".`,
      );
    }
    return [role, value];
  });
}

function render(): string {
  const color = readTokens<ColorTokens>("color");
  const type = readTokens<TypographyTokens>("typography");
  const space = readTokens<SpaceTokens>("space");
  const motion = readTokens<MotionTokens>("motion");

  const dark = color.semantic["dark"];
  if (dark === undefined) throw new Error("Token error: colour theme 'dark' is missing.");

  const lines: string[] = [BANNER, ""];

  // Tailwind v4 is CSS-first: an `@theme` block IS both the custom-property
  // declarations and the Tailwind scale config. One generated file, not two.
  lines.push("@theme {");

  lines.push("  /* Typography — families */");
  for (const [name, stack] of entriesOf(type.family)) {
    lines.push(`  --font-${name}: ${stack};`);
  }

  lines.push("", "  /* Typography — interface scale (§5.1.3, 13px base) */");
  for (const [name, scale] of Object.entries(type.interface).filter(([k]) => isToken(k))) {
    lines.push(`  --text-${name}: ${scale.size};`);
    lines.push(`  --text-${name}--line-height: ${scale.leading};`);
  }

  lines.push("", "  /* Typography — document scale (§5.1.3, 17px base; DocRenderer only) */");
  for (const [name, scale] of Object.entries(type.document).filter(([k]) => isToken(k))) {
    lines.push(`  --text-doc-${name}: ${scale.size};`);
    lines.push(`  --text-doc-${name}--line-height: ${scale.leading};`);
  }

  lines.push("", "  /* Typography — weights */");
  for (const [name, value] of entriesOf(type.weight)) {
    lines.push(`  --font-weight-${name}: ${value};`);
  }

  lines.push("", "  /* Colour — semantic roles, dark theme (§5.2.2) */");
  for (const [role, value] of resolveTheme(dark, color.primitive)) {
    lines.push(`  --color-${role}: ${value};`);
  }

  lines.push("", "  /* Spacing (§5.3, 4px base) */");
  for (const [name, value] of entriesOf(space.space)) {
    lines.push(`  --spacing-${name}: ${value};`);
  }

  lines.push("", "  /* Radius (§5.4) */");
  for (const [name, value] of entriesOf(space.radius)) {
    lines.push(`  --radius-${name}: ${value};`);
  }

  lines.push("", "  /* Motion (§5.5) */");
  for (const [name, value] of entriesOf(motion.duration)) {
    lines.push(`  --duration-${name}: ${value};`);
  }
  for (const [name, value] of entriesOf(motion.easing)) {
    lines.push(`  --ease-${name}: ${value};`);
  }

  lines.push("}", "");

  // Values Tailwind has no scale for, but which components consume as raw vars.
  lines.push(":root {");
  for (const [name, value] of entriesOf(space.layout)) {
    lines.push(`  --layout-${name}: ${value};`);
  }
  for (const [name, value] of entriesOf(type.measure)) {
    lines.push(`  --measure-${name}: ${value};`);
  }
  for (const [name, value] of entriesOf(space.elevation)) {
    lines.push(`  --elevation-${name}: ${value};`);
  }
  lines.push("}", "");

  return lines.join("\n");
}

// ─── Measurements ────────────────────────────────────────────────────────────

const MEASUREMENTS_IN = join(WEB_ROOT, "src/generated/data/measurements.json");
const MEASUREMENTS_OUT = join(WEB_ROOT, "src/generated/measurements.ts");

/** Mirrors the record emitted by scripts/web/derive.py. */
interface MeasurementRecord {
  value: number;
  precision: number;
  artifact: string;
  pointer: string;
  sha256: string;
  commit: string;
  label: string;
  unit?: string;
  n?: number;
  ci95?: [number, number];
}

/**
 * Emit a frozen, exhaustively-typed measurement map.
 *
 * The point of generating this rather than importing the JSON directly is the union
 * type: `MeasurementKey` makes an unknown or stale key a *compile* error, so a
 * reference that no longer resolves cannot reach a browser. The JSON alone would
 * type every lookup as `MeasurementRecord | undefined` and invite a `!`.
 */
function renderMeasurements(): string {
  const raw = JSON.parse(readFileSync(MEASUREMENTS_IN, "utf8")) as Record<
    string,
    MeasurementRecord
  >;
  const keys = Object.keys(raw).sort();

  if (keys.length === 0) {
    throw new Error("measurements.json is empty. Run scripts/web/derive.py first.");
  }

  return [
    BANNER.replace("web/tokens/*.json", "web/src/generated/data/measurements.json").replace(
      "Run `pnpm generate` after changing a token.",
      "Run scripts/web/derive.py, then `pnpm generate`.",
    ),
    "",
    "/** A quantity measured by the pipeline, bound to the artifact that produced it. */",
    "export interface Measurement {",
    "  readonly value: number;",
    "  /** Decimal places the value is STORED with. Rendering may not exceed it. */",
    "  readonly precision: number;",
    "  readonly artifact: string;",
    "  /** RFC 6901 pointer into `artifact`. */",
    "  readonly pointer: string;",
    "  readonly sha256: string;",
    "  readonly commit: string;",
    "  readonly label: string;",
    "  readonly unit?: string;",
    "  /** Denominator, where one exists. A count without its denominator is a claim. */",
    "  readonly n?: number;",
    "  readonly ci95?: readonly [number, number];",
    "}",
    "",
    "/** Every measurement the platform may display. Anything else is a type error. */",
    "export type MeasurementKey =",
    ...keys.map((key) => `  | ${JSON.stringify(key)}`),
    "  ;",
    "",
    "/**",
    " * The measurement registry.",
    " *",
    " * Typed as Record<MeasurementKey, Measurement> rather than `as const`: literal",
    " * value types buy nothing here, and they make optional fields inaccessible",
    " * through a key union because absent properties do not exist on every member.",
    " * The key union is the part that carries the guarantee.",
    " */",
    "export const M: Readonly<Record<MeasurementKey, Measurement>> = {",
    ...keys.map((key) => `  ${JSON.stringify(key)}: ${JSON.stringify(raw[key])},`),
    "};",
    "",
  ].join("\n");
}

// ─── Entry point ─────────────────────────────────────────────────────────────

interface Target {
  readonly name: string;
  readonly path: string;
  readonly render: () => string;
}

const TARGETS: readonly Target[] = [
  { name: "tokens", path: OUT_FILE, render },
  { name: "measurements", path: MEASUREMENTS_OUT, render: renderMeasurements },
];

function main(): void {
  const check = process.argv.includes("--check");

  for (const target of TARGETS) {
    const next = target.render();

    if (check) {
      let current: string;
      try {
        current = readFileSync(target.path, "utf8");
      } catch {
        console.error(`generate --check: ${target.path} is missing. Run \`pnpm generate\`.`);
        process.exit(1);
      }
      if (current !== next) {
        console.error(
          `generate --check: ${target.name} is stale or hand-edited.\n` +
            "Run `pnpm generate` and commit the result.",
        );
        process.exit(1);
      }
      continue;
    }

    mkdirSync(dirname(target.path), { recursive: true });
    writeFileSync(target.path, next);
    console.log(`generate: wrote ${target.path}`);
  }

  if (check) console.log("generate --check: all generated files are up to date.");
}

main();
