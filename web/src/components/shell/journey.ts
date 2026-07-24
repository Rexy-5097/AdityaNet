/**
 * The descent — the single source of truth for the product's through-line.
 *
 * AdityaNet is not six pages. It is one journey from an impression you cannot verify
 * to the command that reproduces it, and each surface is a depth on that descent:
 *
 *   0  impression   a beautiful star, honestly labelled as artistic
 *   1  trust        why anything that follows should be believed
 *   2  claim        what was concluded, including the negative result
 *   3  machinery    how the claim was manufactured
 *   4  measurement  the raw numbers themselves
 *   5  reproduction you leave, and run it yourself
 *
 * Depth 0 is Domain A. Depths 1-5 are Domain B. The journey axis and the honesty
 * architecture are the same axis — which is why the descent is worth building rather
 * than decorating.
 *
 * Navigation, the depth gauge, and every end-of-surface handoff derive from this list,
 * so the descent can never disagree with itself.
 */

export interface Depth {
  readonly href: string;
  /** Short label for navigation. */
  readonly label: string;
  /** What epistemic state the reader is in at this depth. */
  readonly state: string;
  /** Why a reader would continue from the previous depth to this one. */
  readonly invitation: string;
  readonly domain: "A" | "B";
}

export const DESCENT: readonly Depth[] = [
  {
    href: "/overview/",
    label: "Overview",
    state: "Impression",
    invitation: "Begin with something you cannot yet verify.",
    domain: "A",
  },
  {
    href: "/validation/",
    label: "Validation",
    state: "Trust",
    invitation:
      "Six times, execution falsified the specification. See how each was ruled on before believing anything that follows.",
    domain: "B",
  },
  {
    href: "/findings/",
    label: "Findings",
    state: "Claim",
    invitation:
      "With the method established, read what it actually concluded — including the result that says machine learning did not help.",
    domain: "B",
  },
  {
    href: "/pipeline/",
    label: "Pipeline",
    state: "Machinery",
    invitation:
      "A conclusion is only as good as the machine that produced it. See how raw archive products became evidence.",
    domain: "B",
  },
  {
    href: "/data/",
    label: "Data",
    state: "Measurement",
    invitation:
      "Beneath the machinery are the measurements themselves. Look at any observation day directly.",
    domain: "B",
  },
  {
    href: "/build/",
    label: "Build",
    state: "Reproduction",
    invitation:
      "The end of the descent is not another page. It is the digest and the commands to rebuild all of this yourself.",
    domain: "B",
  },
];

/** Index of the depth matching a pathname, or 0 for the surface. */
export function depthOf(pathname: string): number {
  // The landing scene ("/") and the Overview are both depth 0: the film and the front
  // door of the archive are the same rung of the descent, reached one after the other.
  if (pathname === "/") return 0;
  const found = DESCENT.findIndex((d) => pathname.startsWith(d.href));
  return found === -1 ? 0 : found;
}
