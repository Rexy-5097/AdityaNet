# Sprint 10G-OB: Alignment Forensics Audit Report

## 1. Executive Summary Table

| Metric | Measured Value |
| :--- | :---: |
| Total Rows | 5760 |
| Target Lineage Mismatches | 0 |
| Shift Direction Match (50 samples) | PASS |
| Causal Ordering Verdict | PASS |
| Train/Test Isolation Verdict | PASS |
| Peak Memory Usage | 963808.00 MB |
| Total Execution Time | 20.767 seconds |

---

## 2. Task 1: Target Lineage Truth Table

Target lineage recomputed directly from `flares_full.parquet`.
Lookahead Window: $(T, T+360]$
Condition: $target = 1$ iff at least one C/M/X flare start time exists in $(T, T+360]$

- Random sample checked: 100 positive rows, 100 negative rows
- Mismatch count on sampled rows: **0**
- Mismatch count across all 5760 rows: **0**
- **Verdict**: **PASS** (mismatch count = 0)

---

## 3. Task 2: Shift Direction Verification

Verifies that the shifted features at $T$ equal the original feature value at $T + 	ext720$ (future shift).

- Random sample checked: 50 rows
- Shifts checked: $+60$m, $+180$m, $+360$m
- Features checked: `hard_soft_ratio`, `soft_band_mean`, `pc1_projection`, `pc2_projection`
- Verification result: **PASS** (100% of checked values matched original future values)

---

## 4. Task 3: Window & Event Overlap Audit

### Geometric Overlap
- Lags (T - h) and contemporaneous (T): No geometric overlap with target lookahead window $[T + 1, T + 360]$.
- Future shifts $+60$m, $+180$m, $+360$m: Geometric overlap exists (feature timestamp falls inside target lookahead window).
- Future shift $+720$m: No geometric overlap (feature timestamp falls outside target lookahead window).

### Event Overlap (Leakage Audit)
Percentage of positive target rows where the feature extraction timestamp falls during or after the flare start time.

| Offset Name | Offset (m) | Geometric Overlap | Event Overlap Count | Event Overlap % |
| :--- | :---: | :---: | :---: | :---: |
| `lag_360m` | -360 | False | 0 | 0.00% |
| `lag_180m` | -180 | False | 0 | 0.00% |
| `lag_60m` | -60 | False | 0 | 0.00% |
| `lag_30m` | -30 | False | 0 | 0.00% |
| `lag_15m` | -15 | False | 0 | 0.00% |
| `lag_5m` | -5 | False | 0 | 0.00% |
| `contemporaneous` | 0 | False | 0 | 0.00% |
| `shift_plus_60m` | 60 | True | 1032 | 27.28% |
| `shift_plus_180m` | 180 | True | 2476 | 65.45% |
| `shift_plus_360m` | 360 | True | 3783 | 100.00% |
| `shift_plus_720m` | 720 | False | 3783 | 100.00% |

---

## 5. Task 4: Causal Ordering Audit

Causality Mutation Test: Mutated all raw channel data at indices $> 0$ with random noise and verified that compressed features at index 0 remain unaffected.

- Mutated Channels: `solexs_sdd2_spec_counts_ch13` to `ch37`
- Original value of `soft_band_mean[0]`: 3.679096
- Mutated value of `soft_band_mean[0]`: 3.679096
- Verification Match: **True**
- **Verdict**: **PASS** (features are strictly contemporaneous and do not access future timestamps)

---

## 6. Task 5: Lead-Lag Reconstruction

Reconstructed predictive information (AUC and Max TSS) at offsets from $-720$m to $+720$m.
History baseline features fixed at lag 60m.

### Feature: `hard_soft_ratio`

| Offset (m) | Baseline AUC | Augmented AUC | Delta AUC | Baseline Max TSS | Augmented Max TSS | Delta Max TSS |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| -720 | 0.718318 | 0.801643 | 0.083325 | 0.403980 | 0.618325 | 0.214345 |
| -360 | 0.705656 | 0.703609 | -0.002047 | 0.400307 | 0.393586 | -0.006721 |
| -180 | 0.631087 | 0.706589 | 0.075502 | 0.318217 | 0.402772 | 0.084555 |
| -60 | 0.608542 | 0.696955 | 0.088413 | 0.247309 | 0.394846 | 0.147538 |
| 0 | 0.608542 | 0.686736 | 0.078194 | 0.247309 | 0.356199 | 0.108890 |
| 60 | 0.598499 | 0.663571 | 0.065072 | 0.214946 | 0.281213 | 0.066267 |
| 180 | 0.578059 | 0.651901 | 0.073842 | 0.171178 | 0.288938 | 0.117760 |
| 360 | 0.545778 | 0.729792 | 0.184014 | 0.106101 | 0.379500 | 0.273399 |
| 720 | 0.636562 | 0.764632 | 0.128070 | 0.283294 | 0.465594 | 0.182300 |

### Feature: `soft_band_mean`

| Offset (m) | Baseline AUC | Augmented AUC | Delta AUC | Baseline Max TSS | Augmented Max TSS | Delta Max TSS |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| -720 | 0.718318 | 0.716325 | -0.001993 | 0.403980 | 0.399905 | -0.004075 |
| -360 | 0.705656 | 0.746576 | 0.040920 | 0.400307 | 0.399776 | -0.000531 |
| -180 | 0.631087 | 0.700243 | 0.069156 | 0.318217 | 0.375009 | 0.056792 |
| -60 | 0.608542 | 0.665470 | 0.056928 | 0.247309 | 0.327200 | 0.079891 |
| 0 | 0.608542 | 0.651424 | 0.042882 | 0.247309 | 0.296339 | 0.049030 |
| 60 | 0.598499 | 0.664688 | 0.066189 | 0.214946 | 0.298076 | 0.083129 |
| 180 | 0.578059 | 0.730488 | 0.152429 | 0.171178 | 0.404129 | 0.232951 |
| 360 | 0.545778 | 0.783224 | 0.237446 | 0.106101 | 0.535934 | 0.429833 |
| 720 | 0.636562 | 0.706541 | 0.069979 | 0.283294 | 0.361564 | 0.078270 |

### Feature: `pc1_projection`

| Offset (m) | Baseline AUC | Augmented AUC | Delta AUC | Baseline Max TSS | Augmented Max TSS | Delta Max TSS |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| -720 | 0.718318 | 0.717424 | -0.000894 | 0.403980 | 0.370364 | -0.033615 |
| -360 | 0.705656 | 0.753206 | 0.047551 | 0.400307 | 0.410467 | 0.010160 |
| -180 | 0.631087 | 0.706998 | 0.075911 | 0.318217 | 0.346265 | 0.028048 |
| -60 | 0.608542 | 0.663741 | 0.055200 | 0.247309 | 0.306391 | 0.059083 |
| 0 | 0.608542 | 0.647676 | 0.039134 | 0.247309 | 0.280974 | 0.033665 |
| 60 | 0.598499 | 0.664397 | 0.065898 | 0.214946 | 0.315870 | 0.100923 |
| 180 | 0.578059 | 0.726320 | 0.148261 | 0.171178 | 0.436653 | 0.265475 |
| 360 | 0.545778 | 0.788001 | 0.242223 | 0.106101 | 0.436632 | 0.330531 |
| 720 | 0.636562 | 0.694648 | 0.058086 | 0.283294 | 0.289735 | 0.006441 |

### Feature: `pc2_projection`

| Offset (m) | Baseline AUC | Augmented AUC | Delta AUC | Baseline Max TSS | Augmented Max TSS | Delta Max TSS |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| -720 | 0.718318 | 0.773085 | 0.054767 | 0.403980 | 0.496336 | 0.092357 |
| -360 | 0.705656 | 0.711665 | 0.006009 | 0.400307 | 0.397687 | -0.002620 |
| -180 | 0.631087 | 0.627712 | -0.003375 | 0.318217 | 0.315177 | -0.003040 |
| -60 | 0.608542 | 0.681859 | 0.073318 | 0.247309 | 0.346131 | 0.098823 |
| 0 | 0.608542 | 0.608685 | 0.000144 | 0.247309 | 0.241994 | -0.005315 |
| 60 | 0.598499 | 0.600839 | 0.002340 | 0.214946 | 0.214610 | -0.000337 |
| 180 | 0.578059 | 0.577445 | -0.000614 | 0.171178 | 0.167043 | -0.004135 |
| 360 | 0.545778 | 0.546093 | 0.000315 | 0.106101 | 0.112446 | 0.006346 |
| 720 | 0.636562 | 0.639271 | 0.002709 | 0.283294 | 0.285540 | 0.002246 |

---

## 7. Task 5B: Train/Test Boundary Audit

Temporal isolation verification across all splits.

| Split | Min Timestamp | Max Timestamp |
| :--- | :--- | :--- |
| **Train** | 2010-01-02 00:30:00 | 2019-12-31 23:59:00 |
| **Validation** | 2020-01-01 00:00:00 | 2022-12-31 23:59:00 |
| **Test** | 2023-01-01 00:00:00 | 2026-06-14 23:51:00 |

### Gap Measurements
- Train to Validation minimum gap: **0.02 hours**
- Validation to Test minimum gap: **0.02 hours**
- Train to Test minimum gap: **1096.00 days**

### Isolation Verification
- $\max(train\_timestamp) < \min(val\_timestamp)$: **True**
- $\max(val\_timestamp) < \min(test\_timestamp)$: **True**
- **Verdict**: **PASS**

