// Camera-facing radial glow billboard. A perfect circular halo with no aspect artifacts
// and no polygonal edge, because it is a screen-facing quad with a smooth radial falloff.
precision highp float;
uniform float uOpacity;
uniform vec3 uColor;
varying vec2 vUv;
void main() {
  float d = length(vUv - 0.5) * 2.0;          // 0 centre → 1 edge
  float core = smoothstep(1.0, 0.28, d);       // bright near the disc
  float halo = smoothstep(1.0, 0.0, d) * 0.5;  // broad soft falloff
  float a = (core * 0.14 + halo * 0.5) * uOpacity;
  gl_FragColor = vec4(uColor * a, a);
}
