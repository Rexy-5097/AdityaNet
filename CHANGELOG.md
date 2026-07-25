# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Complete repository documentation overhaul: flagship README, `docs/` set
  (architecture, methodology, deployment, reproducibility, design‑system), community and
  governance files (`CONTRIBUTING`, `CODE_OF_CONDUCT`, `SECURITY`, `CITATION.cff`,
  `CHANGELOG`), and GitHub issue / PR templates.
- Reproducible documentation screenshots captured from the production build
  (`web/scripts/screenshots.mjs`).

## [0.9.0] — 2026‑07‑25 — flagship checkpoint

Tagged `v0.9.0-flagship-checkpoint`. First public‑preview candidate of the web platform.

### Added
- **Responsive pass.** Distinct mobile navigation (a zero‑JavaScript `<details>` disclosure
  menu) and a recomposed mobile hero; landscape, ultrawide, and fluid‑metric handling.
  Verified across 320 → 1920 px.
- **Editorial pass.** Each evidence area split into a scannable *story* surface and a full
  *documentation* surface (`/findings/method`, `/data/schema`, `/build/reproduce`); a
  confidence‑interval comparison graphic that makes the negative result visible.
- **Deployment.** Static hosting on Render with a generated `render.yaml`; alternate
  `vercel.json`; a hash‑based CSP served and verified in production.

### Fixed
- **Typography.** Font tokens referenced `var(--font-plex-sans)` — a variable left over
  from a previous `next/font` setup that nothing defined after the Astro migration. Every
  surface had silently fallen back to the system font stack while the IBM Plex faces
  downloaded unused. Tokens now point at the real `@fontsource` families.
- **Repository self‑containment.** An unanchored `build/` ignore rule excluded two
  directories of committed source (`web/src/pages/build/`, `web/src/generated/data/build/`),
  so a clean checkout could not build. Anchored to the repository root.
- **Deploy toolchain.** Switched hosts to pnpm (npm cannot resolve the lockfile), scoped
  the build to `web/` via `rootDir` (both hosts were auto‑detecting `requirements.txt` and
  compiling pandas from source), and pinned Node ≥ 22.12.

## [0.5.0] — scientific platform (Milestones I–XI)

The pre‑web research phase. Summarised; see `docs/ENGINEERING_JOURNAL.md` and the git
history for the full record.

### Added
- Canonical dataset pipeline: raw ISSDC Level‑1 products → parsed under a frozen contract
  (fail‑loud) → 7 canonical Parquet tables → frozen with per‑table and dataset SHA‑256
  digests (`AdityaNet_v2_dataset_r1`, digest `43fd0e22`).
- Pre‑registered evaluation protocol and the baseline ML benchmark, producing the headline
  **negative result**: machine learning provides no operational benefit over a threshold
  detector on the evaluated flare‑detection tasks; the spectral‑resolution ablation is a
  confirmed null.
- Validation record: six adjudicated contradictions between implementation and
  specification, each folded into a versioned contract.

[Unreleased]: https://github.com/Rexy-5097/AdityaNet/compare/v0.9.0-flagship-checkpoint...HEAD
[0.9.0]: https://github.com/Rexy-5097/AdityaNet/releases/tag/v0.9.0-flagship-checkpoint
