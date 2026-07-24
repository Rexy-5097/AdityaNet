import { useCallback, useEffect, useState } from "react";

/**
 * T1 light curve for one observation day. Domain B — measured evidence.
 *
 * SCIENTIFIC RULES THIS COMPONENT ENFORCES:
 *
 *  - Gaps are gaps. Minutes with no finite rate break the path; they are never
 *    interpolated across and never drawn as zero. A gap means the instrument was not
 *    observing, and filling it would fabricate an observation.
 *  - The y-axis is logarithmic and says so. Count rate spans four decades across the
 *    archive; a linear axis renders every quiet day as a flat line at the bottom.
 *  - Decimation is declared. If the series is reduced for drawing, the footer says by
 *    how much, so a reader always knows whether they are seeing every sample.
 *
 * Rendered as SVG rather than canvas: 1,440 points is well inside what SVG handles, and
 * it keeps the curve inspectable, selectable, and printable.
 */

interface DayPayload {
  date: string;
  minutes: number;
  observed: number;
  rate: (number | null)[];
  live_time_total_s: number;
}

interface Props {
  initialDate: string;
  /** Served from public/api/v1/days — static, immutable, cacheable forever. */
  endpoint?: string;
}

const WIDTH = 960;
const HEIGHT = 260;
const PAD = { top: 12, right: 12, bottom: 26, left: 52 };

export default function LightCurve({ initialDate, endpoint = "/api/v1/days" }: Props) {
  const [date, setDate] = useState(initialDate);
  const [day, setDay] = useState<DayPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (target: string) => {
      setError(null);
      setDay(null);
      try {
        const response = await fetch(`${endpoint}/${target}.json`);
        if (!response.ok) throw new Error(`${response.status}`);
        setDay((await response.json()) as DayPayload);
      } catch {
        // A missing day is a legitimate scientific answer, not necessarily a fault —
        // so the message names the possibility rather than asserting a failure.
        setError(`No T1 record served for ${target}. The day may not be in the dataset.`);
      }
    },
    [endpoint],
  );

  useEffect(() => {
    void load(date);
  }, [date, load]);

  // Listen for calendar selections. A custom event keeps the static Astro calendar and
  // this island decoupled — the calendar ships zero JavaScript of its own.
  useEffect(() => {
    const onSelect = (event: Event) => {
      const detail = (event as CustomEvent<{ date: string }>).detail;
      if (detail?.date) setDate(detail.date);
    };
    window.addEventListener("adityanet:select-day", onSelect);
    return () => window.removeEventListener("adityanet:select-day", onSelect);
  }, []);

  if (error !== null) {
    return (
      <p className="rounded-md border border-line-subtle bg-surface p-5 text-sm text-fg-muted">
        {error}
      </p>
    );
  }

  if (day === null) {
    // Reserve the final height so the panel does not shift when data arrives.
    return (
      <div
        className="animate-pulse rounded-md border border-line-subtle bg-surface"
        style={{ height: HEIGHT }}
        aria-live="polite"
        aria-label={`Loading light curve for ${date}`}
      />
    );
  }

  const finite = day.rate.filter((v): v is number => v !== null && v > 0);
  const min = Math.min(...finite);
  const max = Math.max(...finite);
  const logMin = Math.log10(Math.max(min, 0.1));
  const logMax = Math.log10(max);
  const span = Math.max(logMax - logMin, 0.5);

  const plotW = WIDTH - PAD.left - PAD.right;
  const plotH = HEIGHT - PAD.top - PAD.bottom;

  const x = (i: number) => PAD.left + (i / Math.max(day.rate.length - 1, 1)) * plotW;
  const y = (v: number) =>
    PAD.top + plotH - ((Math.log10(Math.max(v, 0.1)) - logMin) / span) * plotH;

  // Break the path at every gap rather than bridging it.
  const segments: string[] = [];
  let current: string[] = [];
  day.rate.forEach((v, i) => {
    if (v === null || v <= 0) {
      if (current.length > 1) segments.push(current.join(" "));
      current = [];
      return;
    }
    current.push(`${current.length === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`);
  });
  if (current.length > 1) segments.push(current.join(" "));

  const decades = [];
  for (let d = Math.ceil(logMin); d <= Math.floor(logMax); d += 1) decades.push(d);

  return (
    <figure className="m-0">
      <div className="overflow-x-auto rounded-md border border-line-subtle bg-sunken">
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          className="block h-auto w-full min-w-[640px]"
          role="img"
          aria-label={`SoLEXS total count rate for ${day.date}. ${day.observed} of ${day.minutes} minutes observed. Peak ${max.toFixed(1)} counts per second.`}
        >
          {decades.map((d) => (
            <g key={d}>
              <line
                x1={PAD.left}
                x2={WIDTH - PAD.right}
                y1={y(10 ** d)}
                y2={y(10 ** d)}
                stroke="currentColor"
                className="text-line-subtle"
                strokeWidth="1"
              />
              <text
                x={PAD.left - 8}
                y={y(10 ** d) + 3}
                textAnchor="end"
                className="fill-fg-subtle font-mono"
                style={{ fontSize: 9 }}
              >
                1e{d}
              </text>
            </g>
          ))}

          {segments.map((d, i) => (
            <path
              key={i}
              d={d}
              fill="none"
              stroke="currentColor"
              className="text-data-1"
              strokeWidth="1.1"
              strokeLinejoin="round"
            />
          ))}

          <text
            x={PAD.left}
            y={HEIGHT - 8}
            className="fill-fg-subtle font-mono"
            style={{ fontSize: 9 }}
          >
            00:00 UTC
          </text>
          <text
            x={WIDTH - PAD.right}
            y={HEIGHT - 8}
            textAnchor="end"
            className="fill-fg-subtle font-mono"
            style={{ fontSize: 9 }}
          >
            24:00 UTC
          </text>
        </svg>
      </div>

      <figcaption className="mt-3 font-mono text-2xs text-fg-subtle">
        {day.date} · {day.observed.toLocaleString("en-US")} of{" "}
        {day.minutes.toLocaleString("en-US")} minutes observed · peak {max.toFixed(1)} ·
        median-scale log₁₀ axis · gaps shown as breaks, never interpolated · all{" "}
        {day.rate.length.toLocaleString("en-US")} samples drawn, no decimation
      </figcaption>
    </figure>
  );
}
