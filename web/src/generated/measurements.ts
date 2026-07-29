/*
 * GENERATED FILE — DO NOT EDIT.
 * Source: web/src/generated/data/measurements.json   Generator: web/scripts/generate.ts
 * Run scripts/web/derive.py, then `pnpm generate`. CI fails if this file drifts.
 */

/** A quantity measured by the pipeline, bound to the artifact that produced it. */
export interface Measurement {
  readonly value: number;
  /** Decimal places the value is STORED with. Rendering may not exceed it. */
  readonly precision: number;
  readonly artifact: string;
  /** RFC 6901 pointer into `artifact`. */
  readonly pointer: string;
  readonly sha256: string;
  readonly commit: string;
  readonly label: string;
  readonly unit?: string;
  /** Denominator, where one exists. A count without its denominator is a claim. */
  readonly n?: number;
  readonly ci95?: readonly [number, number];
}

/** Every measurement the platform may display. Anything else is a type error. */
export type MeasurementKey =
  | "artifacts/v2/ml/benchmark_results.json#/M~1X NOWCAST/results/threshold_rate/event/event_recall"
  | "artifacts/v2/ml/benchmark_results.json#/M~1X NOWCAST/results/threshold_rate/minute/roc_auc"
  | "artifacts/v2/phase05/freeze_manifest.json#/identity/n_parquet_files"
  | "artifacts/v2/phase05/freeze_manifest.json#/identity/total_bytes"
  | "artifacts/v2/phase05/freeze_manifest.json#/tables/T1/n_files"
  | "artifacts/v2/phase05/freeze_manifest.json#/tables/T4/n_files"
  ;

/**
 * The measurement registry.
 *
 * Typed as Record<MeasurementKey, Measurement> rather than `as const`: literal
 * value types buy nothing here, and they make optional fields inaccessible
 * through a key union because absent properties do not exist on every member.
 * The key union is the part that carries the guarantee.
 */
export const M: Readonly<Record<MeasurementKey, Measurement>> = {
  "artifacts/v2/ml/benchmark_results.json#/M~1X NOWCAST/results/threshold_rate/event/event_recall": {"value":0.926829268292683,"precision":4,"artifact":"artifacts/v2/ml/benchmark_results.json","pointer":"/M~1X NOWCAST/results/threshold_rate/event/event_recall","sha256":"3a1d425e7cb29bf945b428144f297dbc579ca7f27ef84762c19791d508bb48be","commit":"99af630","label":"Threshold nowcast event recall","n":82,"ci95":[0.875,0.975609756097561]},
  "artifacts/v2/ml/benchmark_results.json#/M~1X NOWCAST/results/threshold_rate/minute/roc_auc": {"value":0.953889401574726,"precision":4,"artifact":"artifacts/v2/ml/benchmark_results.json","pointer":"/M~1X NOWCAST/results/threshold_rate/minute/roc_auc","sha256":"3a1d425e7cb29bf945b428144f297dbc579ca7f27ef84762c19791d508bb48be","commit":"99af630","label":"Threshold nowcast ROC-AUC","ci95":[0.9396726855158811,0.966399848937842]},
  "artifacts/v2/phase05/freeze_manifest.json#/identity/n_parquet_files": {"value":1985,"precision":0,"artifact":"artifacts/v2/phase05/freeze_manifest.json","pointer":"/identity/n_parquet_files","sha256":"5aaab68db13d7108eb576a0b052cbd3125cf7db54ce4caa8551e5a119eb6cb3b","commit":"99af630","label":"Parquet files"},
  "artifacts/v2/phase05/freeze_manifest.json#/identity/total_bytes": {"value":596917461,"precision":0,"artifact":"artifacts/v2/phase05/freeze_manifest.json","pointer":"/identity/total_bytes","sha256":"5aaab68db13d7108eb576a0b052cbd3125cf7db54ce4caa8551e5a119eb6cb3b","commit":"99af630","label":"Dataset size","unit":"bytes"},
  "artifacts/v2/phase05/freeze_manifest.json#/tables/T1/n_files": {"value":424,"precision":0,"artifact":"artifacts/v2/phase05/freeze_manifest.json","pointer":"/tables/T1/n_files","sha256":"5aaab68db13d7108eb576a0b052cbd3125cf7db54ce4caa8551e5a119eb6cb3b","commit":"99af630","label":"SoLEXS observation days"},
  "artifacts/v2/phase05/freeze_manifest.json#/tables/T4/n_files": {"value":389,"precision":0,"artifact":"artifacts/v2/phase05/freeze_manifest.json","pointer":"/tables/T4/n_files","sha256":"5aaab68db13d7108eb576a0b052cbd3125cf7db54ce4caa8551e5a119eb6cb3b","commit":"99af630","label":"HEL1OS housekeeping orbits"},
};
