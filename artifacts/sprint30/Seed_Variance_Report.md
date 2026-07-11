<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 30 Phase 5 — across-seed variance analysis and escalation record. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-11 -->

# Sprint 30 — Seed Variance Report

**The across-seed spread of F1's test True Skill Score is large: range 0.0640 (0.3343 to 0.3983), sample standard deviation 0.0276 over 5 seeds (OBSERVED). This is more than three times the pre-registered minimum effect of interest (+0.02) — the first direct measurement of the seed-noise band that Sprint 28's external review flagged as unmeasured (Unresolved Criticism U1), and it retroactively validates both the escalation rule and the choice of a +0.02 minimum effect: single-seed results in this pipeline can differ by more than double that value on seed luck alone.**

## Escalation record (protocol-mandated, not discretionary)

| Step | Event |
|------|-------|
| 1 | Pre-registered seeds 42/43/44 trained and sealed-evaluated |
| 2 | Phase 5 unsealing: TSS range 0.0426 > 0.015 → `F1.json:seed_escalation_rule` fires ("escalate to 5 seeds before any verdict") |
| 3 | 5-seed majority criterion (≥3 of 5) pre-declared and committed (`89a688d`) BEFORE seeds 45/46 ran |
| 4 | Seeds 45/46 trained under the identical frozen protocol, evaluations sealed |
| 5 | Final 5-seed analysis; verdict issued |

Seeds 45 and 46 turned out to bracket the distribution (best and worst respectively), widening the range from 0.0426 to 0.0640 — the escalation strengthened the measurement rather than changing the direction.

## Across-seed statistics (OBSERVED / DERIVED)

| Quantity | Value | Label |
|----------|-------|-------|
| F1 TSS per seed (42/43/44/45/46) | 0.3851 / 0.3543 / 0.3426 / 0.3983 / 0.3343 | OBSERVED |
| F1 TSS mean ± std (ddof=1) | 0.3629 ± 0.0276 | DERIVED |
| F1 TSS range | 0.0640 | DERIVED |
| Paired ΔTSS per seed | −0.0089 / −0.0397 / −0.0514 / +0.0043 / −0.0597 | OBSERVED |
| ΔTSS mean ± std | −0.0311 ± 0.0276 | DERIVED |
| Cohen's d (one-sample, pre-declared form) | −1.13 | DERIVED |
| F0 (fixed frozen reference — no seed distribution by pre-registration) | TSS 0.3940, within-run 95% CI [0.3559, 0.4298] | OBSERVED |
| Best-epoch validation TSS per seed | 0.6138 / 0.6142 / 0.6199 / 0.6140 / 0.6044 (std 0.0056) | OBSERVED |

Within-run bootstrap uncertainty and across-seed variance are reported separately and never pooled (pre-registered plan §2). Notably the two uncertainty sources are comparable in size: a single run's 95% CI half-width is ≈ 0.035 and the seed std is 0.028 — consistent with the observation that the three "significantly negative" seeds and the two "no significant difference" seeds differ mainly by seed luck around a mean of about −0.03.

## Interpretation limits

Validation-side seed variance is small (std 0.0056) while test-side variance is five times larger (std 0.0276): seeds that look interchangeable at selection time diverge in the 2023–2026 test regime. Consequences: (a) any future single-seed test-set claim from this pipeline is noise-level until proven otherwise; (b) the Sprint 26 single-seed screening results should continue to be treated as exploratory, exactly as they were labeled; (c) the F2/F3 arms (Sprint 31) inherit the 3-seed minimum + escalation rule with this measured band as prior evidence that escalation is likely to fire again.
