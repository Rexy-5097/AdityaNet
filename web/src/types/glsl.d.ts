/**
 * Ambient declarations for Vite's `?raw` imports.
 *
 * Shaders live in real `.glsl` files rather than template literals so they diff
 * readably and get syntax highlighting, and are loaded with Vite's built-in `?raw`
 * suffix rather than a GLSL plugin — one less dependency for the same result.
 *
 * TypeScript has no knowledge of Vite's query suffixes, so without this it reports
 * TS2307. Narrowed to `.glsl?raw` specifically rather than a blanket `*?raw`, so an
 * accidental raw import of some other asset type still fails to compile.
 */
declare module "*.glsl?raw" {
  const source: string;
  export default source;
}
