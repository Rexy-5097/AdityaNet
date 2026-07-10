# Sprint 22 — Priority Matrix

**Conclusion:** The weighted matrix selects **B1+B2+B3 combined — the "Honest Decision Layer" rebuild — as the single highest-value improvement (score 8.60/10)**, ahead of extending the Aditya-L1 overlap corpus (7.05) and distribution-shift-aware recalibration (6.75). The three decision-layer bottlenecks are scored jointly because they are one work item: the leaked thresholds (B1), the recall collapse (B2), and the undeployed fix (B3) are all repaired by the same rebuild.

---

## Weights

Weights reflect the stated goal — *operator trustworthiness* first, hackathon submission second, eventual operational use third:

| Criterion | Weight | Rationale |
|-----------|--------|-----------|
| Operator trust improvement | 0.25 | The stated objective of the sprint |
| Expected scientific impact | 0.20 | Validity of every published number |
| Production value | 0.15 | Eventual operational use |
| Hackathon value | 0.15 | Near-term submission |
| Engineering cost (inverted: 10 = cheapest) | 0.10 | No retraining budget assumed |
| Publication value | 0.10 | Research credibility |
| Research novelty | 0.05 | Nice to have; not the goal |

## Scores (0–10 per criterion)

| Bottleneck | Sci impact ×.20 | Op trust ×.25 | Eng cost⁻¹ ×.10 | Novelty ×.05 | Hackathon ×.15 | Publication ×.10 | Production ×.15 | **Weighted** |
|---|---|---|---|---|---|---|---|---|
| **B1+B2+B3 — Honest Decision Layer rebuild** | 9 | 10 | 8 | 4 | 8 | 9 | 9 | **8.60** |
| B5 — Extend Aditya-L1 overlap corpus (rebuild aligned dataset from existing raw archive back to Dec 2023) | 8 | 5 | 6 | 7 | 8 | 9 | 6 | **7.05** |
| B4 — Distribution-shift-aware recalibration (rolling/cycle-conditional) | 8 | 7 | 5 | 7 | 5 | 8 | 7 | **6.75** |
| B9 — Episode-level evaluation as standard harness | 7 | 7 | 8 | 4 | 5 | 8 | 6 | **6.55** |
| B6 — Stealth-flare FN mitigation (feature/architecture research) | 7 | 6 | 3 | 8 | 6 | 7 | 6 | **5.95** |
| B10 — Test suite + auth + Dockerfile + scheduler | 2 | 5 | 5 | 1 | 5 | 1 | 10 | **4.50** |
| B7 — Fix model_v3.py defaults | 3 | 2 | 10 | 1 | 3 | 4 | 5 | **3.80** |
| B12 — Provenance metadata on all decision artifacts | 4 | 4 | 8 | 2 | 2 | 5 | 5 | **4.30** |
| B8 — Explain temperature-scaling failure | 4 | 2 | 7 | 5 | 2 | 5 | 2 | **3.30** |
| B11 — Pin hardware / CPU-deterministic eval path | 3 | 2 | 6 | 1 | 1 | 5 | 4 | **3.00** |

### Scoring notes (why the top rows score as they do)

- **B1+B2+B3 op-trust=10:** the alert boundary is the *only* model output an operator acts on; today it is both leaked and 96%-blind. Nothing else moves trust more per unit effort.
- **B1+B2+B3 sci-impact=9:** repairing it re-baselines every headline operator metric; until then, no downstream improvement (B4, B5, B6) can be measured honestly — the yardstick itself is bent.
- **B1+B2+B3 cost⁻¹=8:** zero retraining. One validation inference pass (1.57M windows, previously completed on this hardware per `refine_thresholds.py` history), threshold sweeps, one final test evaluation, one config swap in `inference.py`.
- **B5 hackathon=8, publication=9 but op-trust=5:** proving/refuting the Aditya-L1 claim is the flagship story, and the raw archive (Oct 2023 →) very likely contains joint flares the current 4-day corpus excludes. But it is a dataset-construction effort whose scientific payoff is uncertain (the ablation and CMI evidence already point to a null result), and it does not change what operators see this quarter.
- **B4 cost⁻¹=5:** requires re-deriving the calibrator/thresholds per-regime and defending the methodology; partially subsumed by the decision-layer rebuild (which re-fits thresholds on the most SC25-like validation data available).
- **B9 is folded into the winner:** episode-level evaluation is a required component of the decision-layer rebuild (see roadmap), scored separately only to show it doesn't independently outrank.
- **B10 production=10 but sci-impact=2:** necessary for deployment, irrelevant to scientific validity; sequenced after the science is honest.

## Ranking

1. **B1+B2+B3 — Honest Decision Layer rebuild — 8.60** ← selected
2. B5 — Extend Aditya-L1 overlap corpus — 7.05
3. B4 — Distribution-shift-aware recalibration — 6.75
4. B9 — Episode-level evaluation harness — 6.55 (absorbed into #1)
5. B6 — Stealth-flare mitigation — 5.95
6. B10 — Engineering hardening — 4.50
7. B12 — Artifact provenance — 4.30 (partially absorbed into #1)
8. B7 — model_v3.py defaults — 3.80 (trivial; do opportunistically)
9. B8 — Temperature scaling forensics — 3.30
10. B11 — Determinism pinning — 3.00
