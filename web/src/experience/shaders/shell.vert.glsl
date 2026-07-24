// Shared vertex stage for the photosphere and every atmosphere shell.
//
// One vertex shader for all passes: they differ only in fragment behaviour, and
// duplicating the vertex stage would be four places to keep a varying in sync.

precision highp float;

varying vec3 vObjectPosition;
varying vec3 vNormal;
varying vec3 vViewDirection;

void main() {
  vObjectPosition = position;
  vNormal = normalize(normalMatrix * normal);

  vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
  vViewDirection = normalize(-viewPosition.xyz);

  gl_Position = projectionMatrix * viewPosition;
}
