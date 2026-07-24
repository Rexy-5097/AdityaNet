import { useCallback, useRef, type RefObject } from "react";

/**
 * ORBIT — the first of the five interaction verbs.
 *
 * THE ARCHITECTURAL RULE THIS FILE EXISTS TO ENFORCE: input never passes through
 * React. Pointer events write into a mutable ref; the render loop reads it inside
 * `useFrame`. React state changes only on discrete semantic events — a mode change, a
 * selection — roughly once a second rather than sixty times.
 *
 * Routing a drag through `setState` would reconcile the component tree on every
 * pointer move. It works, it is what most examples do, and it is why most WebGL React
 * pages feel a frame behind the cursor.
 */

export interface OrbitState {
  dragging: boolean;
  /** Radians accumulated since the last frame consumed them. */
  deltaAzimuth: number;
  deltaElevation: number;
}

export type OrbitInput = RefObject<OrbitState>;

/** Radians of rotation per pixel dragged. Tuned so a full turn is roughly one
 *  comfortable swipe across a laptop trackpad. */
const RADIANS_PER_PIXEL = 0.0062;

export interface OrbitBinding {
  readonly state: OrbitInput;
  /**
   * Callback ref. Attach with `ref={orbit.attach}`.
   *
   * WHY A CALLBACK REF RATHER THAN useEffect + RefObject. The host mounts its
   * container only after quality-tier detection resolves, so on first render the ref
   * holds `null`. An effect keyed on the ref object never re-runs when the node
   * finally attaches — the ref identity is stable — so listeners were silently never
   * bound and the star did not respond to a drag at all.
   *
   * Nothing failed: it built, typed, and screenshotted correctly. It was caught by
   * reading `cursor` off the container in a live browser and finding `auto` where
   * `grab` should have been. A callback ref fires exactly when the node arrives and
   * again with `null` when it leaves, which is precisely the lifecycle needed here.
   */
  readonly attach: (element: HTMLElement | null) => void;
}

export function useOrbitInput(): OrbitBinding {
  const state = useRef<OrbitState>({
    dragging: false,
    deltaAzimuth: 0,
    deltaElevation: 0,
  });
  const detach = useRef<(() => void) | null>(null);

  const attach = useCallback((element: HTMLElement | null) => {
    detach.current?.();
    detach.current = null;
    if (element === null) return;

    let pointerId: number | null = null;
    let lastX = 0;
    let lastY = 0;

    const onPointerDown = (event: PointerEvent) => {
      // Ignore secondary buttons and additional touches: a second finger is the
      // APPROACH verb (pinch), a different gesture that lands in Sprint 6.
      if (pointerId !== null || event.button !== 0) return;

      pointerId = event.pointerId;
      lastX = event.clientX;
      lastY = event.clientY;
      state.current.dragging = true;

      // Capture so a drag that leaves the canvas keeps tracking, rather than the star
      // sticking mid-rotation when the cursor crosses into the text column.
      element.setPointerCapture(event.pointerId);
      element.style.cursor = "grabbing";
    };

    const onPointerMove = (event: PointerEvent) => {
      if (event.pointerId !== pointerId) return;

      // Accumulate rather than assign. Browsers coalesce pointer events, so several
      // moves can arrive between frames; overwriting would silently discard motion and
      // make fast drags travel less far than slow ones.
      state.current.deltaAzimuth -= (event.clientX - lastX) * RADIANS_PER_PIXEL;
      state.current.deltaElevation += (event.clientY - lastY) * RADIANS_PER_PIXEL;

      lastX = event.clientX;
      lastY = event.clientY;
    };

    const endDrag = (event: PointerEvent) => {
      if (event.pointerId !== pointerId) return;
      pointerId = null;
      state.current.dragging = false;
      element.style.cursor = "grab";
    };

    element.style.cursor = "grab";
    element.addEventListener("pointerdown", onPointerDown);
    element.addEventListener("pointermove", onPointerMove);
    element.addEventListener("pointerup", endDrag);
    element.addEventListener("pointercancel", endDrag);

    detach.current = () => {
      element.removeEventListener("pointerdown", onPointerDown);
      element.removeEventListener("pointermove", onPointerMove);
      element.removeEventListener("pointerup", endDrag);
      element.removeEventListener("pointercancel", endDrag);
    };
  }, []);

  return { state, attach };
}
