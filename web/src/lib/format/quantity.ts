import type { Measurement } from "@/generated/measurements";

/**
 * Rendering of measured quantities.
 *
 * The rules here are scientific, not cosmetic. Displayed precision is a property of
 * the artifact: showing 0.95 for a stored 0.9539 discards information the pipeline
 * produced, and showing 0.95390 fabricates precision it never had. `Measurement`
 * carries `precision` for exactly this reason, and these functions may not exceed it.
 */

/** Format a measurement's value at exactly its stored precision. */
export function formatValue(measurement: Measurement): string {
  const { value, precision, unit } = measurement;

  // Byte counts are the one quantity where an exact integer is less informative than
  // a scaled one. The exact value stays available in the source reference.
  if (unit === "bytes") return formatBytes(value);

  const formatted = value.toLocaleString("en-US", {
    minimumFractionDigits: precision,
    maximumFractionDigits: precision,
  });

  return unit === undefined ? formatted : `${formatted} ${unit}`;
}

/** Binary-prefixed byte count. MiB, not MB: this is storage, not marketing. */
export function formatBytes(bytes: number): string {
  const units = ["B", "KiB", "MiB", "GiB", "TiB"] as const;
  let scaled = bytes;
  let index = 0;
  while (scaled >= 1024 && index < units.length - 1) {
    scaled /= 1024;
    index += 1;
  }
  const digits = index === 0 ? 0 : 1;
  return `${scaled.toFixed(digits)} ${units[index]}`;
}

/**
 * Format a 95% confidence interval.
 *
 * Intervals render at the same precision as the estimate they qualify, so the reader
 * is never invited to believe the bound is known more sharply than the point.
 */
export function formatInterval(measurement: Measurement): string | null {
  const { ci95, precision } = measurement;
  if (ci95 === undefined) return null;
  const [low, high] = ci95;
  return `[${low.toFixed(precision)}, ${high.toFixed(precision)}]`;
}

/** Short digest for display. The full value stays in the DOM for screen readers. */
export function formatSha(sha256: string): string {
  return sha256.slice(0, 7);
}

/**
 * A spoken form for assistive technology.
 *
 * "0.9268, 95% confidence interval 0.8750 to 0.9756, from 82 events" is
 * comprehensible read aloud; the visual layout is not.
 */
export function describeMeasurement(measurement: Measurement): string {
  const parts = [`${measurement.label}: ${formatValue(measurement)}`];

  const interval = formatInterval(measurement);
  if (interval !== null) {
    const [low, high] = measurement.ci95 as readonly [number, number];
    parts.push(
      `95% confidence interval ${low.toFixed(measurement.precision)} ` +
        `to ${high.toFixed(measurement.precision)}`,
    );
  }
  if (measurement.n !== undefined) parts.push(`from ${measurement.n} events`);

  return parts.join(", ") + ".";
}
