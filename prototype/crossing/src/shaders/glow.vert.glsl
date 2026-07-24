precision highp float;
varying vec2 vUv;
void main() {
  vUv = uv;
  // Billboard: strip rotation from the model-view so the quad always faces camera.
  vec3 scale = vec3(length(modelMatrix[0].xyz), length(modelMatrix[1].xyz), length(modelMatrix[2].xyz));
  vec4 mv = modelViewMatrix * vec4(0.0,0.0,0.0,1.0);
  mv.xy += position.xy * scale.xy;
  gl_Position = projectionMatrix * mv;
}
