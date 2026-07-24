import noiseLib from "../shaders/lib/noise.glsl?raw";

/**
 * Shader assembly.
 *
 * GLSL has no module system, so the shared noise library is prepended textually. This
 * is what a `#include` preprocessor would do, without adding a build plugin for a
 * single directive.
 *
 * Compile-time defines produce shader *permutations* per quality tier rather than
 * branching at runtime. A `if (detail > 2)` inside a fragment shader is evaluated per
 * pixel on hardware that executes both sides of a divergent branch — the cost would be
 * paid on the low tier that the tier exists to protect.
 */
export function assembleFragment(source: string, defines: Record<string, number> = {}): string {
  const directives = Object.entries(defines)
    .map(([name, value]) => `#define ${name} ${value}`)
    .join("\n");

  return `${directives}\n${noiseLib}\n${source}`;
}
