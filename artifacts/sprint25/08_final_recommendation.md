<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 25 final recommendation on whether to proceed with retraining. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 25 — Final Recommendation

**A. Proceed with retraining under the protocol above.** Sprint 24 established that discrimination is intact (Method C ROC-AUC 0.7482 [0.7309, 0.7669] versus persistence 0.6509 [0.6328, 0.6685], non-overlapping) while the two `SUPPORTED` root causes — distribution shift and threshold instability — are both operating-point failures with concrete, untested training interventions (`artifacts/sprint24/results_d.json`: validation True Skill Score 0.5689 collapsing to test True Skill Score 0.2150), so the evidence points to fixing the training procedure before spending compute on architecture redesign.

## Why A, not C (redesign)

The single strongest number in Sprint 24 is the ROC-AUC gap: the model ranks flare risk materially better than persistence (0.7482 versus 0.6509, confidence intervals non-overlapping, `artifacts/sprint24/results_abc.json`). Redesign is warranted only when discrimination is exhausted; it is not. Root-cause analysis (`01_root_cause_analysis.md`) found zero `SUPPORTED` evidence implicating the architecture and two `SUPPORTED` causes in the operating-point/distribution layer (H1, H3). The correct order is to test the evidence-motivated training interventions first; the campaign's own failure threshold (`04_success_criteria.md`) escalates to redesign automatically if they do not reach the primary endpoint.

## Why A, not B (more Aditya-L1 data)

Sprint 24 evaluated the GOES-only Version 1 model and found it already beats persistence; the bottleneck it exposed is operating-point transfer under the Solar Cycle 24-to-25 shift, not a shortage of instruments. Expanding the Aditya-L1 corpus addresses a different, separately documented question (the unproven multi-instrument benefit, `artifacts/sprint23_5/VERSION3_OPEN_RESEARCH.md`) and would not touch either `SUPPORTED` cause. It remains a valid later phase, not the response to this evidence.

## Why A, not D (evidence insufficient)

The evidence is sufficient to choose: there is a `SUPPORTED` cause (distribution shift) with a directly corresponding, never-tested intervention (regime-inclusive training, experiment E1), and a fully specified, pre-registered protocol to test it against locked success criteria and binding stopping rules. That is precisely the situation Option A exists for. The one genuine uncertainty — whether the +0.0794 True Skill Score margin is the architecture's ceiling — is not resolved by declaring the evidence insufficient; it is resolved by running the campaign, whose stopping rules convert a null result into the redesign decision.

## What proceeding commits to

Executing the baseline B0 plus six single-variable ablations (`03_experiment_matrix.csv`) across five seeds, each scored once through the frozen Sprint 24 harness against the persistence and climatology floors, under the locked endpoints and stopping rules. The campaign is deliberately falsifiable: if no configuration reaches a paired True Skill Score advantage over persistence of +0.1062 in at least three of five seeds, it is declared failed and the project escalates to architecture redesign. Estimated cost is 7 to 10 hours of Metal Performance Shaders wall time (`05_compute_budget.md`). No frozen Version 3 artifact is modified.
