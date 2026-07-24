// Star with register drain — Artistic (uDrain=0) → Schematic base (uDrain=1).
// Realism pass: sunspots, wider colour range, finer granulation, plage.
precision highp float;

uniform float uTime;
uniform float uDrain;
uniform vec3  uDeepColor;   // cool intergranular / spot penumbra
uniform vec3  uMidColor;    // quiescent surface
uniform vec3  uHotColor;    // active-region cores

varying vec3 vObjectPosition;
varying vec3 vNormal;
varying vec3 vViewDirection;

vec3 emissionRamp(float x) {
  // Deep red → orange → gold → white-hot. The white band is narrow and late, which is
  // what signals extreme temperature; a wide white band reads as a lightbulb.
  vec3 c = mix(uDeepColor, uMidColor, smoothstep(0.0, 0.42, x));
  c = mix(c, uHotColor, smoothstep(0.52, 0.85, x));
  c = mix(c, vec3(1.0, 0.97, 0.90), smoothstep(0.93, 1.0, x));
  return c;
}

void main() {
  vec3 p = normalize(vObjectPosition);
  float phase = uTime * 0.05;

  // Domain warp for non-uniform, non-honeycomb cells.
  vec3 warp = vec3(
    fbm(p * 2.4 + vec3(0.0, phase * 0.05, 0.0), 2),
    fbm(p * 2.4 + vec3(5.2, phase * 0.05, 1.3), 2),
    fbm(p * 2.4 + vec3(9.7, phase * 0.05, 4.8), 2)
  ) - 0.5;
  vec3 pw = p + warp * 0.30;

  // Finer, three-scale granulation so it reads as plasma, not a pattern.
  float superGranule = 1.0 - worley(pw * 5.0, phase * 0.4);
  float granule = 1.0 - worley(pw * 26.0, phase);
  float fine = 1.0 - worley(pw * 64.0, phase * 1.6);
  float network = smoothstep(0.15, 0.85, superGranule);
  float cells = granule * (0.6 + network * 0.4);
  cells = cells * 0.82 + fine * 0.18;
  cells = pow(clamp(cells, 0.0, 1.0), 1.25);

  // ── Sunspots ────────────────────────────────────────────────────────────────
  // Low-frequency dark regions with a darker umbra inside a lighter penumbra — the
  // single strongest cue that separates "a real sun" from "an orange ball".
  float spotField = fbm(pw * 1.7 + vec3(3.1, 0.0, 1.7), 4);
  float spot = smoothstep(0.72, 0.80, spotField);           // umbra
  float penumbra = smoothstep(0.63, 0.72, spotField) - spot; // ring around it

  // ── Active regions / plage ──────────────────────────────────────────────────
  float regionField = fbm(pw * 3.4 + vec3(0.0, phase * 0.08, 0.0), 4);
  float regions = smoothstep(0.60, 0.70, regionField);
  float plage = smoothstep(0.50, 0.60, regionField) - regions;

  float temperature = cells * 0.55 + 0.05;
  temperature += regions * 0.5 + plage * 0.14;
  temperature -= penumbra * 0.35;
  temperature -= spot * 0.75;                                // spots run cool/dark
  temperature = clamp(temperature, 0.0, 1.0);

  vec3 colour = emissionRamp(temperature);

  // Limb darkening (~0.65 measured).
  float facing = clamp(dot(normalize(vNormal), normalize(vViewDirection)), 0.0, 1.0);
  float limb = 0.62 + 0.38 * pow(facing, 0.6);

  float overRange = 1.0 + regions * 1.5;
  vec3 artistic = colour * limb * overRange * 0.82;

  // ── Register drain (unchanged logic) ────────────────────────────────────────
  float lum = dot(artistic, vec3(0.2126, 0.7152, 0.0722));
  vec3 desat = mix(artistic, vec3(lum), uDrain * 0.92);
  float flatten = mix(1.0, 0.5 / max(limb * overRange, 0.001), uDrain);
  vec3 drained = desat * flatten * mix(1.0, 0.16, uDrain);

  gl_FragColor = vec4(drained, 1.0);
}
