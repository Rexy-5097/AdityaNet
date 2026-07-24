/**
 * Post-build hygiene: strip operating-system metadata from the deployable output.
 *
 * WHY THIS EXISTS. The project volume is not HFS+, so macOS writes AppleDouble
 * sidecars (`._name`) beside every file it touches — including files Astro creates
 * during the build. A Sprint 0 build produced 61 of them inside `dist/`, all of
 * which would have been uploaded to the CDN and served publicly.
 *
 * That is not merely untidy. AppleDouble files carry resource forks and extended
 * attributes, which can include the originating path and quarantine provenance. It
 * is a small but genuine information leak, and it is invisible in review because
 * nothing in the source tree mentions them.
 *
 * WHY IT IS A SEPARATE ARTIFACT. The specification budgets four bespoke tooling
 * artifacts. This is a fifth, and the justification is that the alternatives are
 * worse: a shell one-liner in package.json is not cross-platform and not reviewable,
 * and folding removal into check.ts would make a validator mutate the thing it
 * validates. check.ts still asserts the directory is clean afterwards, so this
 * script failing silently cannot result in a leaky deploy.
 */

import { readdirSync, rmSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const DIST = join(dirname(fileURLToPath(import.meta.url)), "..", "dist");

/** Names that are operating-system metadata and never deployable content. */
function isOsMetadata(name: string): boolean {
  return name.startsWith("._") || name === ".DS_Store" || name === "Thumbs.db";
}

function purge(directory: string): number {
  let removed = 0;

  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);

    if (isOsMetadata(entry.name)) {
      rmSync(path, { recursive: true, force: true });
      removed += 1;
      continue;
    }

    if (entry.isDirectory()) removed += purge(path);
  }

  return removed;
}

// ─── Content-Security-Policy script hashes ───────────────────────────────────

/**
 * Compute CSP hashes for Astro's inline hydration scripts and inject them into the
 * deployed header.
 *
 * WHY. Astro bootstraps client islands with inline `<script type="module">`. Under
 * `script-src 'self'` those are blocked, so shipping the experience island would have
 * silently broken it in production — or, worse, forced `'unsafe-inline'` back into the
 * policy and undone the strongest security property this project has.
 *
 * A static site has no request-time nonce, but it does not need one: the scripts are
 * fixed at build time, so their hashes are too. `'sha256-...'` in `script-src` permits
 * exactly those bytes and nothing else. Any tampering with the script changes the hash
 * and the browser refuses to run it.
 *
 * REJECTED ALTERNATIVES.
 *  - `'unsafe-inline'`: permits *any* inline script, which is the injection vector the
 *    policy exists to close. A regression from Sprint 0.
 *  - Astro's `security.csp`: emits a `<meta http-equiv>` tag. Meta CSP cannot express
 *    `frame-ancestors`, applies only after parsing begins, and would sit alongside our
 *    header policy — the browser enforces the intersection, so the header would still
 *    block the scripts. It solves a different problem than the one we have.
 */
function collectInlineScripts(directory: string, found: string[] = []): string[] {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      collectInlineScripts(path, found);
    } else if (entry.name.endsWith(".html")) {
      const markup = readFileSync(path, "utf8");
      for (const match of markup.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)) {
        const body = match[1];
        if (body !== undefined && body.length > 0) found.push(body);
      }
    }
  }
  return found;
}

function injectScriptHashes(): number {
  const headersPath = join(DIST, "_headers");
  if (!existsSync(headersPath)) {
    console.warn("postbuild: dist/_headers not found; skipping CSP hash injection.");
    return 0;
  }

  const bodies = collectInlineScripts(DIST);

  // Hash the exact bytes between the tags — that is what the browser hashes. Set
  // dedupes: Astro emits the same bootstrap on every page carrying an island.
  const hashes = [
    ...new Set(bodies.map((body) => createHash("sha256").update(body, "utf8").digest("base64"))),
  ].map((digest) => `'sha256-${digest}'`);

  const headers = readFileSync(headersPath, "utf8");
  if (!headers.includes("__SCRIPT_HASHES__")) {
    console.warn("postbuild: no __SCRIPT_HASHES__ placeholder in _headers; CSP unchanged.");
    return 0;
  }

  // replaceAll, not replace: the first occurrence of the token in _headers is inside
  // an explanatory comment, and a non-global replace silently patched the comment while
  // leaving the live directive untouched. The gate reported success; the policy was
  // unchanged. Found in Sprint 3.
  writeFileSync(headersPath, headers.replaceAll("__SCRIPT_HASHES__", hashes.join(" ")));
  return hashes.length;
}

// Order matters: hash injection WRITES dist/_headers, and on a non-HFS+ volume every
// write creates a fresh `._` sidecar. Purging first would leave the one created by the
// write. Anything that mutates dist must run before the purge.
const hashCount = injectScriptHashes();
console.log(
  hashCount === 0
    ? "postbuild: no inline scripts; CSP needs no hashes."
    : `postbuild: injected ${hashCount} CSP script hash(es) into dist/_headers.`,
);

const removed = purge(DIST);
console.log(
  removed === 0
    ? "postbuild: dist is clean."
    : `postbuild: removed ${removed} operating-system metadata file(s) from dist.`,
);
