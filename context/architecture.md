<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Living context document; pre-Sprint-23 statements presenting thresholds 0.46/0.88 as production were stale and are corrected inline below with [SUPERSEDED — Sprint 23] markers; original text preserved. -->
<!-- SUPERSEDED BY: Sprint 23 (artifacts/policies/operator_policy_v2.json); proof: artifacts/sprint22_5/FINAL_VERDICT.md; clean baseline: artifacts/sprint23_5/VERSION3_SCIENTIFIC_BASELINE.md -->
<!-- DATE: 2026-07-03 -->

# Architecture — SuryaNet / AdityaNet

> **Owner:** Soumyadeb Tripathy
> **Update:** Before any architectural change; read before any architectural task
> **Cross-refs:** `context/decisions.md` · `context/tech_stack.md`

---

## System Overview

SuryaNet is a two-layer system: a **research layer** (training, calibration, evaluation) and an
**operational layer** (real-time API + database + alert service). Only the V1 model connects these
two layers today; V3 exists in research only.

```
┌─────────────────────────────────────────────────────────────────┐
│                       RESEARCH LAYER                            │
│                                                                 │
│  GOES Archive (8.6M records)  +  Aditya-L1 SoLEXS/HEL1OS      │
│        ↓                              ↓                         │
│  features.py (14 feats)      dataset_v3.py (36 feats total)    │
│        ↓                              ↓                         │
│  trainer.py → V1 PatchTST    trainer_v3.py → V3 LateFusion     │
│        ↓                              ↓                         │
│  patchtst_best.pt             model_seed_42_stage2_best.pt      │
│  (9.96 MB, 822K params)       (17.57 MB, 4.35M params)         │
│        ↓                              ↓                         │
│  Isotonic calibration         Isotonic calibration              │
│  calibrator.pkl               (fitted per V3 eval run)          │
│        ↓                                                        │
│  operator_thresholds.json     (NOT wired to API — GAP-007)     │
│  (yellow=0.46, red=0.88)                                        │
└────────────────────────┬────────────────────────────────────────┘
                         │ V1 only
┌────────────────────────▼────────────────────────────────────────┐
│                    OPERATIONAL LAYER                            │
│                                                                 │
│  GOES Real-time Feed → TimescaleDB (localhost:5433)            │
│           ↓                    ↑                                │
│    Backfill scripts    goes_flux / flare_events tables          │
│           ↓                    ↓                                │
│    POST /predict/nowcast  ←→  Redis (localhost:6379)           │
│           ↓                                                     │
│    inference.py                                                 │
│    ├── Load V1 PatchTST                                         │
│    ├── Compute 14 features                                      │
│    ├── MC Dropout (50 passes)                                   │
│    ├── Isotonic calibration                                     │
│    ├── Uncertainty suppression                                  │
│    ├── RED confirmation (rolling 3-sample + gradient check)     │
│    └── GREEN / YELLOW / RED + confidence + attention patches    │
│           ↓                                                     │
│    JSON response to operator                                    │
└─────────────────────────────────────────────────────────────────┘
```

> **[SUPERSEDED — Sprint 23]** Two elements of the diagram above are stale. (1) `operator_thresholds.json (yellow=0.46, red=0.88)` was proven test-set derived (`artifacts/sprint22_5/FINAL_VERDICT.md`) and quarantined; the operational layer now loads `artifacts/policies/operator_policy_v2.json` (yellow=0.14, red=0.95) through the provenance-gated `app/services/ml/policy.py` (schema, self-hash, leakage guard, and nine startup checks before the service starts). (2) The V1 alert-tier example below the diagram ("prob ≥ 0.88 → RED, prob ≥ 0.46 → YELLOW") shows the void thresholds; the logic is unchanged but the boundary values are now 0.14/0.95.

---

## V1 Model Architecture (ACTIVE)

```
Input: [batch, 360, 14]  (360 minutes × 14 GOES features)
    ↓
PatchEmbedding: unfold → [batch, 44, 128]  (44 patches × embed_dim=128)
    + CLS token → [batch, 45, 128]
    ↓
PositionalEncoding (learnable)
    ↓
4 × CustomEncoderLayer
    Pre-LN → Multi-Head Attention (8 heads) → Pre-LN → FFN (512 dim)
    (Attention weights accessible per-head for explainability)
    ↓
CLS token extraction: [batch, 128]
    ↓
Linear head: [batch, 1]  (raw logit)
    ↓
MC Dropout (50 forward passes with dropout=0.2 active):
    mean_prob, std_prob  (calibrated probability + uncertainty)
    ↓
Isotonic regression → calibrated probability
    ↓
Alert tier + uncertainty suppression:
    unc > 0.20 → GREEN (any input)
    unc > 0.15 → floor at GREEN
    unc > 0.10 → cap at YELLOW (no RED)
    prob ≥ 0.88 AND rolling 3-sample mean ≥ 0.88 AND slope > 0 AND hard X-ray gradient > 0 → RED
    prob ≥ 0.46 → YELLOW
    else → GREEN
```

**Parameters:** 822,401 trainable + 5,760 positional encoding buffers = 828,161 total in checkpoint

---

## V3 Model Architecture (RESEARCH)

```
Inputs:
    GOES:   [batch, 360, 14]
    SoLEXS: [batch, 360, 18]   ← BUG-001: model_v3.py defaults say 25, use 18
    HEL1OS: [batch, 360, 4]    ← BUG-001: model_v3.py defaults say 10, use 4
    mask_solexs: [batch, 1]    ← 1.0=available, 0.0=missing (use learnable missing token)
    mask_hel1os: [batch, 1]
    ↓
Parallel PatchTST encoders (asymmetric):
    GOES encoder:   4 layers, embed_dim=128  → attention pooling → [batch, 128]
    SoLEXS encoder: 5 layers, embed_dim=160 → attention pooling → [batch, 160] → project → [batch, 128]
    HEL1OS encoder: 5 layers, embed_dim=160 → attention pooling → [batch, 160] → project → [batch, 128]
    (if mask=0: replace with learnable missing_token_solexs / missing_token_hel1os)
    ↓
Cross-attention fusion:
    Query: GOES embedding
    Key/Value: stack([GOES, SoLEXS, HEL1OS]) in fusion_dim=128
    → [batch, 128]
    ↓
Concatenate: [GOES, SoLEXS, HEL1OS] → [batch, 384] → Linear → [batch, 1]
```

**Parameters:** 4,353,217 trainable + 20,160 PE buffers = 4,373,377 total in checkpoint

---

## Database Schema

```
TimescaleDB (localhost:5433, db: suryanet)
├── goes_flux (hypertable, partitioned by time)
│   ├── timestamp (TIMESTAMPTZ, PK)
│   ├── short_flux (FLOAT8)
│   ├── long_flux (FLOAT8)
│   ├── satellite (VARCHAR)
│   ├── quality_flag (INT)
│   └── source (VARCHAR)
│
└── flare_events
    ├── id (UUID, PK)
    ├── start_time (TIMESTAMPTZ)
    ├── peak_time (TIMESTAMPTZ)
    ├── end_time (TIMESTAMPTZ)
    ├── goes_class (VARCHAR)   -- 'M1.0', 'X2.3', etc.
    └── satellite (VARCHAR)
```

---

## API Endpoints

| Method | Path | Purpose | Model |
|--------|------|---------|-------|
| GET | /health | Health check | — |
| GET | /solar/flux | Recent GOES flux | — |
| GET | /flares | Recent flare events | — |
| GET | /system/status | System resource status | — |
| POST | /predict/nowcast | 6-hour flare forecast | V1 only |

**Nowcast request:** Array of 360–362 `{timestamp, short_flux, long_flux}` records  
**Nowcast response:** `{alert_level, probability, uncertainty, confidence_level, confirmation, top_attention_patches, mission_impact}`

---

## Directory Layout (Key Paths)

```
AdityaNet/
├── AGENTOS.md                  AgentOS protocol
├── PROJECT_CONFIG.yaml         Active profile: adityanet
├── context/                    Project knowledge (vision, state, arch, tech_stack, decisions)
├── agents/                     AgentOS agent specifications
├── standards/                  Engineering standards
├── workflows/                  SOPs
├── checklists/                 Quality gate checklists
├── tools/                      Validator, bootstrap, harness
├── profiles/                   All profiles (includes adityanet.yaml)
│
├── app/                        FastAPI application
│   ├── api/v1/endpoints/       5 endpoint groups
│   ├── core/                   Config, Redis, DB connection
│   ├── db/                     ORM models
│   ├── models/                 Pydantic schemas
│   └── services/
│       ├── ml/                 ALL ML code
│       │   ├── model.py        V1 PatchTST ← production
│       │   ├── model_v3.py     V3 LateFusion ← BUG-001 in defaults
│       │   ├── inference.py    ← production inference (V1 only)
│       │   ├── features.py     14 GOES feature engineering
│       │   ├── metrics.py      TSS, HSS, MCC, ECE, PR-AUC, bootstrap
│       │   └── ...
│       ├── backfill/           GOES + flare backfill scripts
│       └── operations/         ISRO impact assessment
│
├── scripts/                    Training + calibration + eval scripts
├── scratch/                    Experimental auditing scripts
├── data_pipeline/              PRADAN/NOAA download manager
├── data/aditya_l1/processed/  Raw Aditya-L1 parquets (SoLEXS: 915, HEL1OS: 960)
│
├── artifacts/
│   ├── models/                 V1 checkpoints (patchtst_best.pt)
│   ├── models_v3/              V3 test checkpoint (UNTRAINED — 52 MB)
│   ├── sprint14c/              V3 best checkpoints + evaluation results
│   ├── research/               V1 train/val/test parquets
│   ├── research_v3/            V3 multi-instrument parquets
│   ├── calibration/            calibrator.pkl + calibration reports
│   ├── aditya_l1/              Overlap dataset + audit reports
│   └── sprint20b/              Sprint 20B audit artifacts
│
├── alembic/                    DB migrations (1 migration: a541577be3f5)
├── docker-compose.yml          TimescaleDB 2.15.3-pg16 + Redis 7.2.4
└── requirements.txt
```

---

## Critical Architectural Decisions (Pre-ADR)

These decisions predate AgentOS and have no formal ADR — document them next:

1. **Late fusion over early fusion** — each instrument encoded independently; only embeddings fused. Allows graceful degradation when instruments unavailable.
2. **Learnable missing tokens** — represents absent Aditya-L1 streams explicitly. Alternative (zero-fill) would conflate absence with quiet sun.
3. **MC Dropout for uncertainty** — 50 stochastic forward passes with dropout active. Simple, well-understood, cheap. Alternative (deep ensembles) would be 5–10× more expensive.
4. **Isotonic regression over temperature scaling** — temperature scaling produces TSS=0.00 on V3 test set (breaks decision boundary at T=1.4168). Isotonic regression is primary calibration.
5. **Chronological split** — no random shuffling. SC24 train / SC25 test. Required for realistic operational evaluation; random split would inflate metrics.
6. **6-hour forecast horizon** — enough lead time for satellite safing operations. Shorter would be operationally useless; longer would have weaker signal.
7. **14 GOES features** — raw flux + log + rolling stats (15m/60m mean/var) + peaks (30m/60m) + gradients (5m/15m) + accelerations (5m/15m) + minutes_since_last_flare (capped at 7 days). History features dominate (information gap audit: removing them collapses TSS to 0.0).

---

*Last updated: 2026-07-03 · AgentOS onboarding*
