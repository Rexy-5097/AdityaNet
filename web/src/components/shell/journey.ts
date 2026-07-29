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
      "ROC, precision-recall, calibration and error analysis, computed from 192,541 held-out predictions. See the evidence before believing the claim.",
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

/**
 * Secondary surfaces — the reference layer beneath the descent.
 *
 * These are not depths. The descent is a reading order: you go down it once, and each
 * rung changes what you believe. A reviewer arriving at "why should I trust the model?"
 * is not at a depth — they are looking something up, and a linear spine is the wrong
 * shape for that. So these live in one flat, grouped index reachable from every page.
 *
 * Kept in this file rather than in the footer that renders it, because the footer is
 * not the only consumer: /start routes each audience into a subset of these, and the
 * evidence chain links into them by href. One list, three readers, no drift.
 */
export interface Resource {
  readonly href: string;
  readonly label: string;
  /** One line, in the reader's terms, of what the surface answers. */
  readonly summary: string;
  readonly group: "evidence" | "engineering" | "orientation";
}

export const RESOURCES: readonly Resource[] = [
  {
    href: "/journey/",
    label: "Research journey",
    summary: "The investigation in order — question, hypothesis, baseline, the result nobody wanted.",
    group: "orientation",
  },
  {
    href: "/start/",
    label: "Where to start",
    summary: "Five routes through the platform, one per kind of visitor.",
    group: "orientation",
  },
  {
    href: "/models/",
    label: "Model cards",
    summary: "Every detector benchmarked: intended use, evaluation, failure modes, limitations.",
    group: "evidence",
  },
  {
    href: "/data/card/",
    label: "Dataset card",
    summary: "Seven tables, their coverage, their known biases, and what they cannot support.",
    group: "evidence",
  },
  {
    href: "/evidence/",
    label: "Evidence traceability",
    summary: "Every headline claim, traced to the artifact bytes and commit behind it.",
    group: "evidence",
  },
  {
    href: "/architecture/",
    label: "Architecture",
    summary: "How the archive becomes a rendered number, drawn end to end.",
    group: "engineering",
  },
  {
    href: "/reproducibility/",
    label: "Reproducibility",
    summary: "Environment, digests, determinism — and what remains unverified.",
    group: "engineering",
  },
  {
    href: "/engineering/provenance/",
    label: "Engineering record",
    summary: "Six times execution falsified the specification, and how each was ruled on.",
    group: "engineering",
  },
  {
    href: "/archive/",
    label: "Static archive",
    summary: "Every published payload, addressable and downloadable as JSON.",
    group: "engineering",
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
