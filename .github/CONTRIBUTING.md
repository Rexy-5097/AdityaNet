# Contributing to AdityaNet

Thank you for your interest. AdityaNet is a research platform whose central claim is that
its evidence is checkable. Contributions are welcome, but that claim is the contract — the
quality gates below are not style preferences, they are what make the platform trustworthy.

## The one rule that overrides all others

**No number is typed by a person.** Every figure shown on the site is resolved at build
time from a committed artifact via a JSON pointer, and the `pnpm budget` gate re‑reads
those artifacts and fails the build if any rendered value drifts from source. If your
change displays a quantity, it must come from an artifact — never a literal in a template.

This is enforced automatically. A pull request that hard‑codes a measurement will fail CI.

## Ground rules

- **Scientific integrity is paramount.** Do not alter, "clean up", or re‑round values in
  `artifacts/` or `web/src/generated/data/`. Those are frozen scientific outputs.
- **Illustration is never data.** Real solar footage is *Artistic* content and must always
  carry the watermark `ILLUSTRATIVE · NASA / SVS · NOT ADITYA‑L1 DATA`. Removing or
  weakening that label is a scientific‑integrity regression, not a style change.
- **Evidence surfaces ship ~0 KB JavaScript.** Do not add client scripts to the evidence
  routes. Scroll and interaction effects there are CSS‑only (`animation-timeline`).
- **No external origins.** The Content‑Security‑Policy forbids them. No CDN scripts, fonts,
  analytics, or remote assets — everything is self‑hosted and inlined or hashed.

## Development setup

Prerequisites: **Node ≥ 22.12** and **pnpm**. The app lives in `web/`.

```bash
pnpm --dir web install
pnpm --dir web dev            # http://localhost:4321
```

## Before you open a pull request

Run the full gate suite locally. All of it must pass:

```bash
pnpm --dir web verify         # generate --check + astro check + tsc + eslint
pnpm --dir web test           # vitest
pnpm --dir web build          # astro build + postbuild
pnpm --dir web budget         # contrast, route budgets, evidence consistency
```

If you changed the deploy‑relevant config, note that `pnpm build` regenerates
`vercel.json` and `render.yaml` from a single header source — commit the regenerated files
so the served CSP cannot drift between hosts.

## Workflow

1. Branch from `main` with a descriptive name (`feature/…`, `fix/…`, `docs/…`).
2. Keep commits focused. Use conventional‑style messages (`feat(web): …`, `fix(deploy): …`).
3. Open a PR against `main` and fill in the template. CI must be green.
4. For anything touching the scientific artifacts, the derivation protocol, or the CSP,
   explain the reasoning in the PR description — these have project‑wide consequences.

## What makes a good change here

- A failing test or gate that catches a real defect is worth more than a feature.
- Prefer deleting code to adding it; the site's quality comes from restraint.
- If a paragraph can be shown visually, show it — the design philosophy is *less reading,
  not fewer words*.

## Reporting problems

- **Bugs and features:** use the issue templates under `.github/ISSUE_TEMPLATE/`.
- **Security:** do **not** open a public issue — see [`SECURITY.md`](SECURITY.md).

By contributing you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md).
