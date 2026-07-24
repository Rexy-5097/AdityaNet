// A prominence arc at the limb — warm plasma looping off the edge. Additive, soft.
precision highp float;
uniform float uOpacity;
uniform vec3 uColor;
uniform float uTime;
varying vec2 vUv;
void main() {
  float across = abs(vUv.y - 0.5) * 2.0;
  float along = vUv.x;
  float body = 1.0 - smoothstep(0.15, 0.85, across);
  float ends = smoothstep(0.0, 0.18, along) * smoothstep(1.0, 0.82, along);
  float flow = 0.7 + 0.3 * sin(along * 8.0 - uTime * 0.6);
  float a = body * ends * flow * uOpacity;
  gl_FragColor = vec4(uColor * a * 1.5, a);
}
