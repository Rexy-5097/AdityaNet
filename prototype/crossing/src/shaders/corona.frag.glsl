precision highp float;
uniform float uOpacity;
uniform vec3 uColor;
varying vec3 vNormal;
varying vec3 vView;
void main() {
  float facing = abs(dot(normalize(vNormal), normalize(vView)));
  // Broad, soft: low exponent spreads the glow inward from the silhouette so it fades
  // to nothing well before the mesh edge, reading as a corona rather than a ring.
  float rim = pow(1.0 - facing, 1.7);
  float a = rim * uOpacity;
  gl_FragColor = vec4(uColor * a * 1.15, a);
}
