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
