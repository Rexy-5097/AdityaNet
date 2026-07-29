/**
 * The editorial half of the model cards.
 *
 * A model card is two things fused: measurements, and judgements about what those
 * measurements permit. They are kept in separate files on purpose.
 *
 * The measurements live in `generated/data/findings/models.json`, derived from
 * `artifacts/v2/ml/benchmark_results.json` by scripts/derive.py. NOTHING numeric appears
 * in this file — not a metric, not a count, not a threshold. If a sentence here needs a
 * number, the page interpolates it from the artifact instead, so a figure can never be
 * kept alive in prose after the artifact behind it changes.
 *
 * What IS here is the part no artifact can supply: what the model is for, what it must
 * not be used for, and how it fails. Those claims are traceable to the written record —
 * `DATASET_LIMITATIONS_FOR_ML.md` (L-1 … L-10), `EVALUATION_PROTOCOL.md`, and
 * `MODEL_COMPARISON.md` — and each card names the limitation clauses it rests on so a
 * reviewer can check the judgement against its source rather than against its author.
 */

export interface ModelCopy {
  /** Short name used in headings. */
  readonly name: string;
  /** One line: what the model does, mechanically. */
  readonly mechanism: string;
  /** Why it is in the benchmark at all. */
  readonly purpose: string;
  readonly intendedUse: string;
  readonly outOfScope: string;
  readonly inputs: string;
  readonly outputs: string;
  readonly training: string;
  readonly strengths: readonly string[];
  readonly failureModes: readonly string[];
  /** Limitation clause IDs from DATASET_LIMITATIONS_FOR_ML.md. */
  readonly limitations: readonly string[];
  readonly ethical: string;
  /** Trivial reference point rather than a candidate detector. */
  readonly reference: boolean;
}

const FEATURE_INPUTS =
  "Fourteen features per minute, all derived from the SoLEXS 1-minute count rate in T1: " +
  "the log rate, rolling means over 5/15/30/60 minutes, a 15-minute rolling maximum, " +
  "rolling standard deviations, a background-excess term, two rise rates, and three data-" +
  "quality terms (GTI fraction, seconds present, partial-minute flag).";

const TRAINING_PROTOCOL =
  "Chronological split with a held-out test period beginning at the frozen test start " +
  "date; no shuffling, so no future minute can inform a past one. The protocol — split, " +
  "seed, metric set and bootstrap scheme — was fixed in EVALUATION_PROTOCOL.md before any " +
  "model was fitted.";

export const MODEL_COPY: Readonly<Record<string, ModelCopy>> = {
  threshold_rate: {
    name: "Threshold on the count rate",
    mechanism:
      "Raises an alarm whenever the SoLEXS 1-minute count rate exceeds a single fixed value.",
    purpose:
      "The operational recommendation. It exists to answer the question every ML benchmark " +
      "should have to answer first: what does the simplest thing that could possibly work do?",
    intendedUse:
      "Flagging minutes of elevated soft X-ray flux in the frozen archive for human review, " +
      "and serving as the baseline any proposed detector must beat before it is worth deploying.",
    outOfScope:
      "Not a forecaster — it describes the present minute, not a future one. Not a severity " +
      "estimate: without an instrument response there is no calibrated flux, so a rate cannot " +
      "be converted to a GOES class.",
    inputs: "One number per minute: the SoLEXS count rate from T1 `rate_total`.",
    outputs:
      "A binary alarm per minute. The score is a physical rate, not a probability, which is " +
      "why no reliability diagram is published for it — there is nothing to be calibrated against.",
    training:
      "No fitting in the machine-learning sense. The threshold is selected on the training " +
      "period only and then frozen; the test period never influences it.",
    strengths: [
      "Auditable end to end — the decision rule is one comparison, inspectable by anyone.",
      "No training artifacts, no serialised weights, no dependency on a modelling library.",
      "Degrades transparently: when it is wrong, the reason is visible in the light curve.",
    ],
    failureModes: [
      "Blind to any flare whose peak rate stays below the threshold, regardless of shape.",
      "Fires on instrument artifacts that raise the rate without a solar cause.",
      "Alarm runs cluster: an active day produces many alarms, so the burden is uneven in time.",
    ],
    limitations: ["L-1", "L-3", "L-9", "L-10"],
    ethical:
      "The main risk is misplaced authority. This is a detector over one archive from one " +
      "detector on one instrument, in one phase of the solar cycle. It is not a space-weather " +
      "warning service and must never be presented as one.",
    reference: false,
  },

  logistic: {
    name: "Logistic regression",
    mechanism: "A linear model over the fourteen features, squashed to a probability.",
    purpose:
      "The lowest-capacity learned model, included to separate 'learning helps' from " +
      "'flexibility helps'. If a linear combination matches an ensemble, the extra capacity " +
      "was buying nothing.",
    intendedUse:
      "Understanding which features carry the signal, via coefficients that can be read directly.",
    outOfScope:
      "Its coefficients are correlational, not causal, and the features are strongly " +
      "collinear — several rolling means measure nearly the same thing. A negative coefficient " +
      "is not evidence that the quantity suppresses flares.",
    inputs: FEATURE_INPUTS,
    outputs: "A probability per minute.",
    training: TRAINING_PROTOCOL,
    strengths: [
      "Coefficients are directly readable, including their sign.",
      "Low capacity, which matters when the effective sample size is events rather than minutes.",
    ],
    failureModes: [
      "Collinear features split credit unstably between themselves.",
      "A linear decision surface cannot express 'high rate but flat and quiet', which is what " +
      "separates a real rise from a noisy plateau.",
    ],
    limitations: ["L-1", "L-6", "L-7"],
    ethical:
      "Readable coefficients invite over-interpretation. Presenting them as physical " +
      "mechanism would be the misuse this card exists to pre-empt.",
    reference: false,
  },

  random_forest: {
    name: "Random forest",
    mechanism: "An ensemble of decision trees, averaged.",
    purpose:
      "A high-capacity, low-tuning learner. If nonlinearity and feature interaction were the " +
      "missing ingredient, this is where it should have shown up.",
    intendedUse: "Benchmark comparison and impurity-based feature attribution.",
    outOfScope:
      "Impurity importance is biased toward high-cardinality continuous features and says " +
      "nothing about direction. It is not a substitute for a physical account.",
    inputs: FEATURE_INPUTS,
    outputs: "A probability per minute, from the fraction of trees voting positive.",
    training: TRAINING_PROTOCOL,
    strengths: [
      "Captures interactions and thresholds without them being specified.",
      "Insensitive to feature scaling and to monotone transforms.",
    ],
    failureModes: [
      "Capacity far exceeds the effective sample size, so it can fit event-specific noise (L-1).",
      "Probabilities from vote fractions are not calibrated by construction.",
    ],
    limitations: ["L-1", "L-5", "L-6"],
    ethical:
      "Its opacity makes an unexplained alarm hard to contest. On a surface where every " +
      "claim must be checkable, that is a cost, not a neutral property.",
    reference: false,
  },

  lightgbm: {
    name: "LightGBM",
    mechanism: "Gradient-boosted decision trees.",
    purpose:
      "The strongest candidate in the benchmark and the one that makes the negative result " +
      "worth publishing: it is what a practitioner would actually reach for.",
    intendedUse:
      "Ranking minutes by flare likelihood, and testing whether better ranking translates " +
      "into better operational detection. On this dataset it does not.",
    outOfScope:
      "Its ranking advantage must not be reported as a detection advantage. At the base rate " +
      "of this dataset, ranking and alarm burden come apart, and the operational question is " +
      "settled by the second, not the first.",
    inputs: FEATURE_INPUTS,
    outputs: "A calibrated-scale probability per minute; a reliability diagram is published.",
    training: TRAINING_PROTOCOL,
    strengths: [
      "The best minute-level ranking of any model evaluated.",
      "Emits probabilities that can be checked against observed frequency.",
    ],
    failureModes: [
      "Raises substantially more false alarm runs than the threshold at comparable recall — " +
      "the finding that decides the benchmark.",
      "Effective capacity outruns the event count, so apparent gains may not transfer to a " +
      "different solar-cycle phase.",
    ],
    limitations: ["L-1", "L-2", "L-5", "L-6", "L-10"],
    ethical:
      "This is the model a positive-result incentive would push to the front page. It is " +
      "published with the result that does not flatter it, which is the point.",
    reference: false,
  },

  random: {
    name: "Random",
    mechanism: "Assigns a uniform random score to every minute.",
    purpose: "The floor. Any detector that does not clear this is measuring nothing.",
    intendedUse: "Reference point only.",
    outOfScope: "Everything else.",
    inputs: "None.",
    outputs: "A uniform random score per minute.",
    training: "None.",
    strengths: ["Establishes what chance performance looks like at this base rate."],
    failureModes: ["It is chance."],
    limitations: [],
    ethical: "None — it is a ruler, not a detector.",
    reference: true,
  },

  majority: {
    name: "Majority",
    mechanism: "Always predicts the majority class.",
    purpose:
      "Shows what accuracy is worth on an imbalanced problem: this model can look excellent " +
      "on accuracy while detecting nothing at all.",
    intendedUse: "Reference point only.",
    outOfScope: "Everything else.",
    inputs: "None.",
    outputs: "A constant.",
    training: "None.",
    strengths: ["Makes the case for reporting PR-AUC and event recall instead of accuracy."],
    failureModes: ["Detects no events, by construction."],
    limitations: ["L-6"],
    ethical: "None — it is a ruler, not a detector.",
    reference: true,
  },

  climatology: {
    name: "Climatology",
    mechanism: "Predicts the historical base rate, ignoring the observation.",
    purpose: "Separates 'knows about flares in general' from 'knows about this minute'.",
    intendedUse: "Reference point only.",
    outOfScope: "Everything else.",
    inputs: "The training-period base rate.",
    outputs: "A constant probability.",
    training: "Estimated on the training period only.",
    strengths: ["A well-calibrated model that has no discriminative skill whatsoever."],
    failureModes: ["Cannot distinguish any minute from any other."],
    limitations: ["L-6"],
    ethical: "None — it is a ruler, not a detector.",
    reference: true,
  },

  persistence: {
    name: "Persistence",
    mechanism: "Predicts that the next label equals the previous one.",
    purpose:
      "The most important reference point on the board. It scores high not because it " +
      "forecasts but because the label is autocorrelated — flares last longer than a minute. " +
      "Any forecasting claim that does not beat persistence is a claim about autocorrelation.",
    intendedUse:
      "Mandatory baseline for every forecasting result, per L-2. Reporting a forecast AUC " +
      "without it would make the number uninterpretable.",
    outOfScope: "Not a detector and not a forecaster.",
    inputs: "The previous minute's label.",
    outputs: "A copy of the previous label.",
    training: "None.",
    strengths: ["Quantifies exactly how much of any apparent forecast skill is persistence."],
    failureModes: ["Cannot anticipate an onset — it can only report one after it began."],
    limitations: ["L-2"],
    ethical: "None — it is a ruler, not a detector.",
    reference: true,
  },
};
