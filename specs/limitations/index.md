# Limitation clauses

How the frozen dataset constrains **model choice**, **evaluation**, **loss functions**, **validation strategy**, and **achievable scientific claims**. Each limitation is stated with the measurement behind it and the concrete constraint it imposes.

---

Clauses are cited by ID and never restated ([ADR-0013](../../adr/ADR-0013.md)).

| ID | Title | Origin |
| --- | --- | --- |
| [L-01](L-01.md) | The effective sample size is 581, not 564,160 | migrated |
| [L-02](L-02.md) | Forecast skill is horizon-flat: it is activity-state persistence, not precursor detection | migrated |
| [L-03](L-03.md) | No instrument response: physical severity targets are unconstructible | migrated |
| [L-04](L-04.md) | The combined-instrument arm is 171 days | migrated |
| [L-05](L-05.md) | Spectral features carry little marginal information; hardness ratios carry none for prediction | migrated |
| [L-06](L-06.md) | Class imbalance and its interaction with event scarcity | migrated |
| [L-07](L-07.md) | Missingness must be masked, never imputed | migrated |
| [L-08](L-08.md) | GTI semantics are not fully characterised | migrated |
| [L-09](L-09.md) | Labels are exogenous and instrument-mismatched | migrated |
| [L-10](L-10.md) | Single detector, single solar-cycle phase | migrated |
| [L-11](L-11.md) | Pre-bitemporal observations carry no ingest time | authored |

Clauses marked `migrated` are carried verbatim from `artifacts/v2/ml/DATASET_LIMITATIONS_FOR_ML.md`. Clauses marked `authored` state the
consequence of a decision that postdates that report and cite the governing ADR instead.

## Summary — what can and cannot be claimed

> Carried verbatim from `artifacts/v2/ml/DATASET_LIMITATIONS_FOR_ML.md` (2026-07-18).

**Supportable with this dataset**
- M/X flare **nowcast/detection** performance, event-level, with CIs — the signal is strong and verified (AUC 0.954 from one raw column).
- **Improvement over persistence** for short-horizon prediction, *if* demonstrated against the mandatory baselines.
- **Ablation results**: does spectral resolution help? does HEL1OS help? — as measured deltas with CIs.
- **Operational characterisation**: recall, false-alarm attribution, latency, the full frontier.

**Not supportable**
- Calibrated flux or severity regression (**no RMF**).
- Raw forecasting AUC presented as precursor skill (**horizon-flat**).
- Standalone X-class conclusions (**47 events**).
- Cross-cycle or multi-detector generalisation (**one phase, one detector**).
- Any claim in keV or physical spectral units (**ordinal channels only**).

**The through-line:** this dataset's strength is *detection*, and its strength there is genuine and large. Its forecasting signal is real but is an activity-state effect, and its severity axis is physically unavailable. A programme that leads with detection, controls forecasting against persistence, and treats spectra and HEL1OS as measured ablations will produce defensible results. One that leads with forecasting AUC or severity regression will produce claims this dataset cannot support.
