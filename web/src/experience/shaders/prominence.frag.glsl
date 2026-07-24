// Prominence — Domain A (artistic).
//
// PASS 4 of 4. A handful of magnetic loops anchored on the limb.
//
// Prominences are the element most likely to tip from "rewarding" into "demanding
// attention", so the brief is deliberately restrained: a small number, slow, and
// dimmer than the active regions they rise from. They should be noticed on the second
// look, not the first.
//
// Geometry is a partial torus tangent to the surface, so orbiting genuinely reveals
// their three-dimensionality — a billboard would collapse the moment the user drags,
// which is precisely when the illusion most needs to hold.

precision highp float;

uniform float uTime;
uniform float uDataActivity;
uniform vec3  uArtColor;
uniform float uArtSeed;

varying vec2 vUv;

void main() {
  // vUv.x runs along the loop, vUv.y around its cross-section.
  float along = vUv.x;
  float across = vUv.y;

  // Soft round cross-section: opaque core fading to nothing at the edge, so the loop
  // reads as a filament of gas rather than a modelled tube.
  float radial = 1.0 - smoothstep(0.15, 0.5, abs(across - 0.5));

  // Fade at both footpoints. A loop that ends abruptly looks like geometry; plasma
  // fades into the surface it emerges from.
  float ends = smoothstep(0.0, 0.22, along) * smoothstep(1.0, 0.78, along);

  // Material drains along the loop, slowly. The flow is the only motion, and it is
  // slow enough to be ambiguous at a glance.
  float flow = 0.62 + 0.38 * sin(along * 9.0 - uTime * 0.42 + uArtSeed * 6.283);

  // Amplitude raised now that prominences composite OVER the corona rather than
  // under it. Previously they were both dim and buried, which is why they never read.
  float alpha = radial * ends * flow * (0.55 + uDataActivity * 0.85);

  // Cooler and redder than the photosphere: prominences are chromospheric material
  // suspended above a hotter surface, and rendering them hotter than their source
  // reverses the depth cue.
  gl_FragColor = vec4(uArtColor * alpha * 1.9, alpha);
}
