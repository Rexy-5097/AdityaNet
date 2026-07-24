# ADR-0006 — Domain A watermark rendered into the frame buffer

**Status:** Accepted · 2026-07-23 · Sprint 3

## Context

P8.1 requires that a viewer can determine which rendering domain they are looking at
**without reading body text**, and that the determination **survives being screenshotted
out of context**.

The concrete risk is specific and likely: someone screenshots the star and captions it
"Aditya-L1 observation". Not maliciously — a journalist, a student, a social post. Once
the image circulates detached from its page, no on-page disclaimer helps. SoLEXS is a
non-imaging photometer; an image implying resolved solar structure is a scientific
falsehood regardless of who wrote the caption.

## Options

| Option | Survives screenshot | Cost | Verdict |
|---|---|---|---|
| DOM overlay `<p>` over the canvas | **No** | ~0 | Fails the requirement outright |
| Text baked into the star's own shader | Yes | 0 draw calls | Couples an honesty mechanism to an artistic material; any future change to the star risks silently removing it |
| `EffectComposer` overlay pass | Yes | pulls in `postprocessing` | Heavy for a job two draw calls do |
| **Second render pass, orthographic camera** | **Yes** | 1 texture, 1 quad, ~1 extra draw call | **Chosen** |

## Decision

Render the label into the WebGL frame buffer with a second pass: a canvas-2D text
texture on a screen-space quad, drawn by an orthographic camera with `autoClear`
disabled, at `useFrame` priority 1.

Taking priority means R3F stops rendering automatically and the component owns the
frame: main scene first, overlay second. The label is composited by the GPU as part of
the image, so it survives screen capture, right-click-save, and `canvas.toDataURL()`.

## Consequences

**Gained.** The honesty guarantee is a property of the pixels rather than of the page.
It cannot be defeated by cropping the DOM, and it travels with any copy of the image.

**Cost.** One extra draw call per frame and a 1024×64 texture (~256 KB GPU memory,
uploaded once). Negligible against a 250 KB three.js runtime.

**Risk.** Owning the frame loop means any future component that also takes priority
must cooperate. Documented in the component header. If a post-processing pass lands in
Sprint 6, the watermark must run after it — a bloom pass applied *over* the label would
smear it, and applied *under* would let bloom obscure it.

**Not covered.** The label is English-only and assumes a legible contrast against both
the bright limb and the dark background, handled with a shadow rather than an opaque
plate — a plate would read as a UI chip rather than part of the image.
