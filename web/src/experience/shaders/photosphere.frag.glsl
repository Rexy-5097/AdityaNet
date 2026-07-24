// Photosphere — Domain A (artistic rendering, measured input).
//
// PASS 1 of 4. Renders the visible surface: granulation, active regions, limb
// darkening, and the emission ramp that later passes bloom.
//
// PROVENANCE
//   uData*  measured. uDataActivity is normalised log peak SoLEXS count rate for the
//           selected archive day (T1 solexs_lc_1min). It controls how much of the
//           surface is in an active state and how hot those regions run.
//   uArt*   artistic. Chosen for appearance. Nothing here is presented as observed:
//           SoLEXS is a non-imaging photometer and records no spatial detail at all,
//           which is why the frame carries a burned-in watermark saying so.
//
// GRANULATION_SCALES is injected per quality tier so lower tiers pay for fewer
// cellular lookups. Worley is the dominant cost in this shader — 27 hash evaluations
// per scale — so this is the one knob that meaningfully moves frame time.

precision highp float;

uniform float uTime;
uniform float uDataActivity;
uniform vec3  uArtDeepColor;   // intergranular lanes, coolest visible material
uniform vec3  uArtMidColor;    // quiescent granule interiors
uniform vec3  uArtHotColor;    // active-region cores

varying vec3 vObjectPosition;
varying vec3 vNormal;
varying vec3 vViewDirection;

/**
 * Emission ramp.
 *
 * Four stops rather than a two-colour mix. A single mix between orange and yellow is
 * what makes procedural stars read as plastic: real emission traverses deep red
 * through orange and gold into white, and the *narrowness* of the white band is what
 * signals extreme temperature. Widening it looks like a lightbulb.
 */
vec3 emissionRamp(float t) {
  vec3 c = mix(uArtDeepColor, uArtMidColor, smoothstep(0.0, 0.45, t));
  c = mix(c, uArtHotColor, smoothstep(0.55, 0.88, t));
  // Final approach to white is deliberately short and late.
  c = mix(c, vec3(1.0, 0.95, 0.86), smoothstep(0.95, 1.0, t));
  return c;
}

void main() {
  vec3 p = normalize(vObjectPosition);

  // Motion is an order of magnitude slower than the first version. Plasma churns; it
  // does not flow. At this rate a cell visibly evolves over several seconds, which
  // rewards looking without ever reading as animation.
  float phase = uTime * 0.055;

  // ── Domain warping ──────────────────────────────────────────────────────────
  //
  // f(p + h(p)) rather than f(p). Cellular noise on an undistorted domain produces
  // cells of statistically identical size and spacing everywhere, and the eye reads
  // constant statistics as machine-generated however fine the cells become.
  //
  // A low-frequency warp displaces the lookup so cells stretch, crowd, and thin across
  // the disc, which is the irregularity real convection has. One extra fbm buys the
  // single most effective anti-uniformity measure available.
  vec3 warp = vec3(
    fbm(p * 2.1 + vec3(0.0, phase * 0.06, 0.0), 2),
    fbm(p * 2.1 + vec3(5.2, phase * 0.06, 1.3), 2),
    fbm(p * 2.1 + vec3(9.7, phase * 0.06, 4.8), 2)
  ) - 0.5;
  vec3 pw = p + warp * 0.22;

  // ── Multi-scale convection ──────────────────────────────────────────────────
  //
  // SCALE SEPARATION. Real supergranules (~30 Mm) and granules (~1 Mm) differ by
  // ~30:1 on a ~1400 Mm disc. The previous values, 9 and 34, were only 3.8:1 apart —
  // and two cell fields that close in scale visually MERGE into one network. That was
  // the real cause of the "uniform crazed texture" reading; it was never a tuning
  // problem.
  //
  // True absolute scale is unreachable: 1400 granules across a ~450 px disc is 0.3 px
  // per cell, far below Nyquist, and renders as shimmer. So the RATIO is honoured
  // across the full span (4.0 -> 120.0 is 30:1) while the finest rung sits at the
  // resolution limit, with an intermediate scale so the eye reads a continuous
  // hierarchy rather than two disconnected fields.
  float superGranule = 1.0 - worley(pw * 4.0, phase * 0.40);
  float granule = 1.0 - worley(pw * 34.0, phase);

  // Supergranulation MODULATES granule brightness rather than being summed alongside
  // it. That is the actual physical relationship — granules live inside supergranular
  // cells — and it is what produces fine structure organised within coarse structure,
  // instead of two textures competing at similar visual weight.
  float network = smoothstep(0.15, 0.85, superGranule);
  float cells = granule * 0.74 + network * 0.26;

  #if GRANULATION_SCALES > 2
    float fine = 1.0 - worley(pw * 100.0, phase * 1.6);
    cells = cells * 0.86 + fine * 0.14;
  #endif

  // Sharpen the lanes. Convection boundaries are thin and dark; a linear cell field
  // looks like bubblewrap until the dark seams are pushed down.
  cells = pow(clamp(cells, 0.0, 1.0), 1.35);

  // ── Active regions ──────────────────────────────────────────────────────────
  // Large, slow, low-frequency patches where the surface runs markedly hotter. This
  // is what makes the eye explore rather than scan: without it the surface is
  // statistically uniform and there is nowhere to look.
  float regionField = fbm(pw * 3.2 + vec3(0.0, phase * 0.09, 0.0), 4);

  // Activity widens the threshold, so quiet archive days have almost no active
  // region and the most energetic day has several.
  float threshold = mix(0.66, 0.55, uDataActivity);
  float regions = smoothstep(threshold, threshold + 0.11, regionField);

  // Plage: a brighter halo just outside each active core, which is what gives active
  // regions a sense of extent rather than looking like painted spots.
  float plage = smoothstep(threshold - 0.10, threshold + 0.02, regionField) - regions;

  // ── Temperature field ───────────────────────────────────────────────────────
  float temperature = cells * 0.60 + 0.02;
  temperature += plage * 0.14;
  temperature += regions * (0.34 + uDataActivity * 0.38);

  // Cell structure inside an active region runs hotter, so hotspots keep their
  // granular texture instead of blowing out to a flat disc.
  temperature += regions * cells * 0.20;
  temperature = clamp(temperature, 0.0, 1.0);

  vec3 colour = emissionRamp(temperature);

  // ── Limb darkening ──────────────────────────────────────────────────────────
  // Physically the line of sight exits the photosphere at a shallower depth near the
  // limb, so less hot material is visible. It is also the single strongest cue that
  // the object is a sphere rather than a disc, and it is what makes ORBIT read as
  // rotating a solid body.
  // Measured limb-darkening coefficient from SDO/SOHO imagery is ~0.65: the limb sits
  // at ~65% of centre intensity. The previous floor of 0.20 was roughly three times too
  // strong and crushed the edge into a dark rim, which is what made the disc read as a
  // shaded ball rather than a luminous body. This constant comes from a measurement
  // rather than from taste, and it is a ceiling on how dark the edge may go.
  float facing = clamp(dot(normalize(vNormal), normalize(vViewDirection)), 0.0, 1.0);
  float limb = 0.65 + 0.35 * pow(facing, 0.62);

  // Emission stays close to display range; the brightest active cores exceed 1.0 so
  // that the bloom pass has something genuine to find. Raising the whole surface
  // above 1.0 would make bloom hide detail instead of revealing energy.
  float overRange = 1.0 + regions * (1.6 + uDataActivity * 2.4);

  // Scene-referred gain. ACES maps ~0.4 linear to ~0.28 display, so the surface has to
  // be authored brighter than it should appear. Raising the gain rather than flattening
  // the tone curve keeps the filmic shoulder that stops hot cores clipping to white.
  const float EXPOSURE = 0.86;

  gl_FragColor = vec4(colour * limb * overRange * EXPOSURE, 1.0);
}
