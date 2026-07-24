import { defineConfig } from "astro/config";
import tailwind from "@tailwindcss/vite";
import react from "@astrojs/react";

/**
 * Astro configuration.
 *
 * Astro was chosen over Next.js on measured evidence, not preference: a page with
 * zero interactive components shipped 184 KB gz of JavaScript under the Next App
 * Router (React always hydrates) versus 0 bytes under Astro. Every route budget in
 * the specification sat below the Next floor, which made them unachievable rather
 * than merely ambitious. See docs/adr/0002-astro-over-nextjs.md.
 *
 * The consequence that matters architecturally: evidence surfaces cost nothing, and
 * that is what pays for a 450 KB immersive island on /explore.
 *
 * @see docs/web/SPEC_AMENDMENT_02_EXPERIENCE.md §18.11 for measured budgets.
 */
export default defineConfig({
  // React powers the experience island only. Every evidence surface remains a
  // zero-JavaScript Astro page; the integration adds nothing to routes without an island.
  integrations: [react()],

  // Static output. There is no runtime server: every response is enumerable at build
  // time, so the build emits a plain directory hostable anywhere, indefinitely.
  output: "static",

  // Static hosts serve /path/ as /path/index.html. Emitting directory-style URLs
  // makes deployed paths match the file layout exactly, so a deep link behaves
  // identically on a CDN and on `python -m http.server`.
  build: {
    format: "directory",
    // Emit one stylesheet rather than inlining per-page <style> blocks. Inline styles
    // would force `style-src 'unsafe-inline'`, and keeping the CSP strict is worth
    // more than saving one cached request.
    inlineStylesheets: "never",
  },

  vite: {
    plugins: [tailwind()],
    build: {
      // Surface real transfer sizes in build output so budget regressions are visible
      // at the moment they are introduced, not at the next audit.
      reportCompressedSize: true,
    },
  },
});
