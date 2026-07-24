// Thin bright warm rim at the limb — the chromosphere edge visible in real solar images.
precision highp float;
uniform float uOpacity;
uniform vec3 uColor;
varying vec3 vNormal;
varying vec3 vView;
void main() {
  float facing = abs(dot(normalize(vNormal), normalize(vView)));
  float a = pow(1.0 - facing, 4.0) * uOpacity;
  gl_FragColor = vec4(uColor * a * 0.7, a);
}
