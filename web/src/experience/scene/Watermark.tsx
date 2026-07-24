import { useMemo, useEffect } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

/**
 * Domain A watermark, rendered INTO the WebGL frame buffer.
 *
 * P8.1 requires that a viewer can tell which rendering domain they are looking at, and
 * that the determination survives being screenshotted out of context. A DOM overlay
 * satisfies the first and fails the second: the failure mode this guards against is
 * someone screenshotting the star and captioning it "Aditya-L1 observation".
 *
 * So the label is composited by the GPU as part of the image. It survives screen
 * capture, right-click-save, and `canvas.toDataURL()`.
 *
 * IMPLEMENTATION. A second render pass with an orthographic camera and `autoClear`
 * disabled, driven at `useFrame` priority 2.
 *
 * FRAME OWNERSHIP. EffectComposer takes priority 1 and renders the scene through the
 * bloom chain. This must run strictly after it, hence priority 2 and no main-scene
 * render of its own. Order matters in both directions: composited *before* bloom the
 * label would smear; drawn by a second scene render it would overwrite the bloom.
 *
 * REJECTED ALTERNATIVES.
 *  - DOM overlay: does not survive capture. Fails the requirement outright.
 *  - Baking text into the star's own shader: couples an honesty mechanism to an
 *    artistic material, so any future change to the star risks silently removing it.
 *  - EffectComposer pass: pulls in postprocessing for a job two draw calls can do.
 */

const TEXT = "ARTISTIC RENDERING · NOT OBSERVATIONAL DATA";

/** Device-pixel width of the label texture. Generous so the text stays crisp on
 *  high-DPI displays without needing mipmaps. */
const TEXTURE_WIDTH = 1024;
const TEXTURE_HEIGHT = 64;

function createLabelTexture(): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = TEXTURE_WIDTH;
  canvas.height = TEXTURE_HEIGHT;

  const context = canvas.getContext("2d");
  if (context === null) throw new Error("2D context unavailable for watermark");

  context.clearRect(0, 0, TEXTURE_WIDTH, TEXTURE_HEIGHT);
  context.font = "500 26px 'IBM Plex Mono', ui-monospace, monospace";
  context.textBaseline = "middle";
  context.textAlign = "left";

  // A soft dark shadow keeps the label legible over both the bright limb and the dark
  // background, without needing an opaque plate that would look like a UI chip.
  context.shadowColor = "rgba(0, 0, 0, 0.9)";
  context.shadowBlur = 8;
  context.fillStyle = "rgba(232, 235, 237, 0.82)";
  context.fillText(TEXT, 8, TEXTURE_HEIGHT / 2);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.minFilter = THREE.LinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.needsUpdate = true;
  return texture;
}

export function Watermark() {
  const { gl, size } = useThree();

  const overlay = useMemo(() => {
    const texture = createLabelTexture();
    const overlayScene = new THREE.Scene();

    // Unit-square NDC space: the quad is positioned in pixels and converted below.
    const overlayCamera = new THREE.OrthographicCamera(0, 1, 1, 0, 0, 1);

    const material = new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      depthTest: false,
      depthWrite: false,
    });

    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), material);
    overlayScene.add(mesh);

    return { overlayScene, overlayCamera, mesh, material, texture };
  }, []);

  // Keep the label a constant physical size regardless of viewport, anchored bottom
  // left. Recomputed on resize only, not per frame.
  useEffect(() => {
    const widthFraction = Math.min(0.62, 420 / Math.max(size.width, 1));
    const heightFraction = (widthFraction * TEXTURE_HEIGHT) / TEXTURE_WIDTH;
    const marginX = 20 / Math.max(size.width, 1);
    const marginY = 20 / Math.max(size.height, 1);

    overlay.mesh.scale.set(widthFraction, heightFraction, 1);
    overlay.mesh.position.set(
      marginX + widthFraction / 2,
      marginY + heightFraction / 2,
      0,
    );
  }, [size.width, size.height, overlay]);

  useEffect(() => {
    return () => {
      overlay.material.dispose();
      overlay.mesh.geometry.dispose();
      overlay.texture.dispose();
    };
  }, [overlay]);

  useFrame(() => {
    // The composer has already drawn the scene at priority 1. Composite on top.
    gl.autoClear = false;
    gl.render(overlay.overlayScene, overlay.overlayCamera);
    gl.autoClear = true;
  }, 2);

  return null;
}
