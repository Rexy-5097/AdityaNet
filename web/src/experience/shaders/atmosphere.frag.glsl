// Atmosphere shell — Domain A (artistic).
//
// PASSES 2 and 3 of 4. One shader, instantiated at several radii:
//   radius ~1.012   chromosphere — thin, red, stops the limb terminating like a decal
//   radius 1.06+    corona       — layered, turbulent, directional
//
// WHY ONE SHADER FOR BOTH. They are the same physical thing at different scales, and
// separate implementations would drift into looking like separate materials. The
// difference is entirely in the uniforms.
//
// WHY SHELLS RATHER THAN A RAYMARCH. A true volumetric corona means marching the view
// ray per pixel — tens of samples where a shell costs one. Several additively blended
// shells at increasing radii reconstruct most of the depth cue for a fraction of the
// budget, and the budget is the constraint this sprint is not allowed to break.

precision highp float;

uniform float uTime;
uniform float uDataActivity;
uniform vec3  uArtColor;
uniform float uArtIntensity;
uniform float uArtRimPower;      // higher = tighter to the limb
uniform float uArtTurbulence;    // spatial frequency of the structure
uniform float uArtStreaks;       // 0 = smooth shell, 1 = strongly directional
uniform float uArtPhaseOffset;   // decorrelates shells so they do not pulse together

varying vec3 vObjectPosition;
varying vec3 vNormal;
varying vec3 vViewDirection;

void main() {
  vec3 p = normalize(vObjectPosition);
  float phase = uTime * 0.04 + uArtPhaseOffset;

  // Viewed from inside (shells render backfaces), the rim is where the shell is seen
  // edge-on and therefore where the most material lies along the line of sight. This
  // is the limb-brightening that makes an atmosphere read as a shell rather than a
  // flat halo sprite.
  float facing = abs(dot(normalize(vNormal), normalize(vViewDirection)));
  float grazing = 1.0 - facing;

  // CRITICAL: fade to zero AT the silhouette, not at maximum.
  //
  // A monotonic `pow(grazing, N)` peaks exactly where the shell's geometry ends, so
  // brightness rises to a maximum and is then cut off by the edge of the sphere. With
  // several nested shells that produces one hard ring per shell — the star reads as
  // onion layers rather than an atmosphere. It is the same "uniform glow" failure
  // wearing a different shape, and it was the dominant artefact after the first pass
  // of this sprint.
  //
  // Multiplying by a term that collapses in the last few percent of grazing angle
  // moves each shell's peak inboard of its own silhouette and lands it at zero, so
  // adjacent shells cross-fade into a continuous gradient instead of stacking edges.
  float rim = pow(grazing, uArtRimPower) * (1.0 - pow(grazing, 9.0));

  // ── Turbulent structure ─────────────────────────────────────────────────────
  float structure = fbm(p * uArtTurbulence + vec3(0.0, phase * 0.5, 0.0), 3);

  // ── Directional streamers ───────────────────────────────────────────────────
  // A uniform glow is the single clearest tell of a procedural star. Real coronal
  // material is organised into radial streamers by the magnetic field. Stretching the
  // sample along the radial axis produces structure that is coherent outward and
  // varied tangentially, which is what "directional" means here.
  vec3 stretched = vec3(p.x * 3.4, p.y * 0.7, p.z * 3.4);
  float streamers = fbm(stretched * uArtTurbulence * 0.55 + vec3(phase * 0.22), 3);
  streamers = pow(clamp(streamers * 1.5, 0.0, 1.0), 2.1);

  float density = mix(structure, streamers, uArtStreaks);

  // Contrast: without this the shell is an even wash and adds no information.
  density = smoothstep(0.18, 0.86, density);

  float alpha = rim * density * uArtIntensity * (0.55 + uDataActivity * 0.75);

  // Hotter cores toward the base of the shell, cooling outward — a subtle shift only,
  // because a strong hue ramp across the corona reads as a cartoon aura.
  vec3 colour = mix(uArtColor, vec3(1.0, 0.93, 0.82), density * 0.28);

  gl_FragColor = vec4(colour * alpha, alpha);
}
