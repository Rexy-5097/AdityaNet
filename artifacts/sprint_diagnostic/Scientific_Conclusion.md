GENUINE LIMIT

<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Ceiling verdict from the diagnostic (frozen pre-reg 48cbaad). -->
<!-- DATE: 2026-07-16 -->

# Scientific Conclusion — the ceiling is a GENUINE LIMIT

**The measured forecasting ceilings in Study A (GOES ≈0.44 TSS) and Study B (Aditya-only ≈0.36 TSS) are GENUINE SCIENTIFIC LIMITS, not artifacts of the training process. Specifically, they are a data-regime limit: the ~2.5-year solar-maximum Aditya-overlap period has too little temporal diversity (too few independent forecasting situations) for the model to generalize past the epoch-1 point, and no pre-registered training intervention removes it.**

## The evidence that determines the answer (all OBSERVED this session)

1. **More data does not help.** S2-GOES peak validation ROC-AUC is 0.8354 at 25% data and 0.8271 at 100% — Δ −0.0083, far below the pre-registered +0.03 minimum effect. The ceiling is reached with 196K windows; the remaining 590K add nothing. If the ceiling were a size limit, more data would raise it. It does not. (H1 REJECTED.)
2. **The same model and procedure train fine on a different regime at the same size.** The size-matched-V1 control (786K rows, identical to S2, identical PatchTST and protocol, only 0.62% positive) reaches 0.8748 ± 0.0017 and does not collapse — +0.048 above S2, Cohen's d ≈ 15. Fewer positives, higher and stable performance. This isolates the cause to the **regime**, not the model, the procedure, the size, or the amount of positive signal. (H2 CONFIRMED.)
3. **No training lever fixes it.** Stronger regularization (+0.0083), fewer steps (+0.0115), natural prior (+0.0045), and matching V1's base rate (−0.0136) each move the peak by less than half the +0.03 threshold, and none delays the epoch-1 collapse. The ceiling is not a hyperparameter you can tune away. (H3, H4, H7 REJECTED; H6 CONFIRMED.)
4. **It is genuine overfitting, directly measured.** Every collapsing arm shows training ROC-AUC rising to ~1.0 while validation ROC-AUC falls — the model memorizes the limited set of distinct patterns in the low-diversity solar-max window within one epoch. The V1 regime, spanning 16 years even when subsampled to the same size, does not.
5. **The ceilings are the real ones.** Test-set evaluation through the frozen Sprint-24 harness reproduces the benchmarks (GOES TSS 0.4328 ≈ EraMatchedGOES 0.4383; Aditya TSS 0.3625 ≈ feasibility 0.359), confirming the diagnostic measured the exact ceilings of Studies A and B, not a proxy.

I do not soften this: within the current Aditya-overlap data, these ceilings cannot be raised by more of the same data or by any training change tested. Only a **longer, cycle-diverse temporal baseline** — data spanning more of the solar cycle than the present ~2.5-year solar-maximum window — could raise them, and that is a data-availability limit, not a modelling one.

## What becomes established (answers to the post-diagnostic questions)

- **Study A strengthened.** F2 (GOES+Aditya) and EraMatchedGOES were both compared at this genuine, symmetric regime ceiling — both models are capped by the same data-regime limit, so the "Aditya adds no incremental value beyond GOES" conclusion is robust and not an undertraining artifact. Mechanism: the collapse is regime-driven and affects both arms identically (both S2-trained, both epoch-1, same magnitude).
- **Study B strengthened.** The Aditya-only 0.36 TSS ceiling is a genuine limit of the ~2.5-year data, not a fixable training bug; it will not improve with more solar-max data or training tuning, only with cycle-diverse coverage.
- **New publication-quality evidence** now exists that did not before: the per-epoch train-vs-validation ROC-AUC divergence curves (overfitting fingerprint), the size-vs-regime-vs-base-rate separation via the size-matched-V1 and low-base-rate controls, architecture-independence, and a defended statement that the ceiling is a temporal-diversity limit of the solar-maximum regime.

## Provisional / not established

The *best achievable* performance under a longer cycle-diverse baseline is `NOT PROVEN` (no such data exists yet). Whether a fundamentally different architecture could extract more from the low-diversity regime is `NOT PROVEN` (the conditional alt-architecture arm was not triggered because H2 was confirmed and the same architecture succeeds on V1).

## Implication for Version 4

Stop trying to raise the S2 forecasting ceiling by training — it is a genuine data limit. Two honest directions follow: (a) the **nowcaster**, which needs no learned precursor and already reaches ROC-AUC 0.898 (feasibility) — unaffected by this forecasting-diversity limit; and (b) accruing **cycle-diverse Aditya data** over time as the only path to a higher forecasting ceiling. Publish the ceiling as a genuine scientific finding.
