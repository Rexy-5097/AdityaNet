// Shared noise library — Domain A (artistic).
//
// One implementation of each function, included wherever needed. Duplicated noise is
// how procedural scenes drift out of visual coherence: two slightly different fbms
// look like two different materials.
//
// Everything here is deterministic from position. No seeds, no Math.random, no
// frame-dependent state — two visitors at the same time and orientation see identical
// frames, which the project requires of every rendering.

vec3 hash33(vec3 p) {
  p = vec3(dot(p, vec3(127.1, 311.7, 74.7)),
           dot(p, vec3(269.5, 183.3, 246.1)),
           dot(p, vec3(113.5, 271.9, 124.6)));
  return fract(sin(p) * 43758.5453123);
}

float hash13(vec3 p) {
  p = fract(p * 0.1031);
  p += dot(p, p.yzx + 33.33);
  return fract((p.x + p.y) * p.z);
}

// ── Gradient noise ─────────────────────────────────────────────────────────────
// Used for large-scale structure (active regions, coronal streamers) where smooth
// continuity matters more than cell definition.

float gradientNoise(vec3 p) {
  vec3 i = floor(p);
  vec3 f = fract(p);
  vec3 u = f * f * (3.0 - 2.0 * f);

  #define G(o) dot(hash33(i + o) * 2.0 - 1.0, f - o)
  return mix(
    mix(mix(G(vec3(0,0,0)), G(vec3(1,0,0)), u.x),
        mix(G(vec3(0,1,0)), G(vec3(1,1,0)), u.x), u.y),
    mix(mix(G(vec3(0,0,1)), G(vec3(1,0,1)), u.x),
        mix(G(vec3(0,1,1)), G(vec3(1,1,1)), u.x), u.y),
    u.z) * 0.5 + 0.5;
  #undef G
}

float fbm(vec3 p, int octaves) {
  float sum = 0.0;
  float amplitude = 0.5;
  for (int i = 0; i < 6; i++) {
    if (i >= octaves) break;
    sum += amplitude * gradientNoise(p);
    p *= 2.03;            // non-integer lacunarity avoids axis-aligned banding
    amplitude *= 0.5;
  }
  return sum;
}

// ── Cellular (Worley) noise ────────────────────────────────────────────────────
//
// THE CENTRAL TECHNIQUE OF THE PHOTOSPHERE.
//
// Solar granulation is convection: discrete cells of rising plasma separated by dark
// intergranular lanes. It is *cellular*, not fractal. Rendering it with fbm — as the
// first version of this shader did — produces soft overlapping blobs that read as a
// painted texture, because fbm has no concept of a cell boundary.
//
// Worley returns distance to the nearest feature point, so cell interiors are bright
// and the seams between them are dark. That single change is most of the difference
// between "textured sphere" and "convecting surface".
//
// ANIMATION. The feature points are displaced in place by `phase` rather than the
// domain being translated. Scrolling a noise field reads as water or cloud moving
// past; plasma does not flow in a direction, it churns. Cells therefore breathe and
// shift slightly without the whole field sliding.
float worley(vec3 p, float phase) {
  vec3 i = floor(p);
  vec3 f = fract(p);

  float nearest = 1.0;
  for (int x = -1; x <= 1; x++) {
    for (int y = -1; y <= 1; y++) {
      for (int z = -1; z <= 1; z++) {
        vec3 neighbour = vec3(float(x), float(y), float(z));
        vec3 point = hash33(i + neighbour);
        // Each cell centre orbits its own small path, at its own phase offset.
        point = 0.5 + 0.42 * sin(phase + 6.2831853 * point);
        nearest = min(nearest, length(neighbour + point - f));
      }
    }
  }
  return nearest;
}
