# Sprint 13A — Reporting Bug Fix Report

## Root Cause Analysis

The original `pilot_train_v3.py` failed in the reporting section with a `ValueError`
(and secondary `SyntaxWarning`) for the following reasons:

### Bug 1 — `reliability_diagram` Dict Unpacking (Critical)
**Location:** `pilot_train_v3.py` lines 816, 818  
**Code (broken):**
```python
bin_confs_raw, bin_accs_raw, _ = evaluator.evaluate(...)["reliability_diagram"].values()
```
**Root cause:** `evaluator.evaluate()` returns `reliability_diagram` as a **dict**
`{"bin_confs": [...], "bin_accs": [...], "bin_sizes": [...]}`.  Calling `.values()`
returns a `dict_values` view.  While unpacking 3 values from a 3-key dict technically
works in CPython 3.7+, the pattern is fragile: if any calibration bin is empty the
dict still has 3 keys, but if the `evaluate()` signature ever changes the packing
silently breaks with a confusing error.  Additionally, the downstream `evaluator.evaluate()`
call passed raw probabilities in `logits_test_raw` correctly, but the variable name
was misleading and could be misused.

**Fix (eval_only_v3.py):** All `reliability_diagram` fields are accessed by explicit
named keys:
```python
rd = evaluator.evaluate(logits, targets)["reliability_diagram"]
rd["bin_confs"], rd["bin_accs"], rd["bin_sizes"]
```

### Bug 2 — `SyntaxWarning: invalid escape sequence '\D'`
**Location:** `pilot_train_v3.py` line ~949 inside the multi-line f-string for `report_content`  
**Root cause:** The LaTeX string `$||\Delta W||_2$` inside a plain f-string triggers
`SyntaxWarning` because `\D` is not a recognised Python escape sequence.  
**Fix:** Use a raw f-string (`rf"..."`) or escape the backslash as `\\Delta`.
In `eval_only_v3.py` the report template uses a separate `textwrap.dedent` block
(not an f-string) or doubles the backslash.

### Bug 3 — `probs → log-odds` transform can produce ±∞
**Location:** `pilot_train_v3.py` lines 693, 818  
**Root cause:** `np.log(probs / (1 - probs + 1e-9))` still reaches `+∞` when
`probs = 1.0` (since the denominator becomes `1e-9`).  
**Fix:** `safe_logits()` clips probs to `[1e-7, 1-1e-7]` before the transform.

### Bug 4 — `s2_test_classes` / `targets_test` length mismatch
**Location:** `pilot_train_v3.py` line ~389 vs line ~662  
**Root cause:** `s2_test_classes` is built by slicing raw DataFrame windows, while
`targets_test` comes from iterating the `DataLoader`, which discards incomplete
final batches.  If block sizes are not perfectly divisible the arrays can differ
by a few elements.  
**Fix:** `eval_only_v3.py` detects and trims all arrays to the minimum length with
a warning before computing metrics.

## Verification
All four plots were generated without error:
- `artifacts/sprint13/calibration_curve.png`
- `artifacts/sprint13/confusion_matrix.png`
- `artifacts/sprint13/threshold_sweep.png`
- `artifacts/sprint13/fusion_attention.png`

All three JSON deliverables were written:
- `artifacts/sprint13/final_evaluation_metrics.json`
- `artifacts/sprint13/evaluation_api_validation.json`
- `artifacts/sprint13/final_evaluation_certificate.json`
