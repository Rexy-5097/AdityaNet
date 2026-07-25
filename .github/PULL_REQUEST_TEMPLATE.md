<!--
Thank you for contributing. The quality gates are the contract on this project — please
make sure the checklist below passes before requesting review.
-->

## Summary

<!-- What does this change and why? One or two sentences. -->

## Type of change

- [ ] Bug fix
- [ ] Feature
- [ ] Documentation
- [ ] Build / CI / deployment
- [ ] Refactor (no behaviour change)

## Checklist

- [ ] `pnpm --dir web verify` passes (generate‑check, `astro check`, `tsc`, eslint).
- [ ] `pnpm --dir web test` passes.
- [ ] `pnpm --dir web build` succeeds.
- [ ] `pnpm --dir web budget` passes (contrast, route budgets, evidence consistency).
- [ ] No displayed number is hand‑typed — every value resolves to a committed artifact.
- [ ] No new external origin is introduced (the CSP forbids them).
- [ ] Evidence surfaces still ship ~0 KB JavaScript.
- [ ] If real solar footage is shown, the `ILLUSTRATIVE · NASA / SVS · NOT ADITYA‑L1 DATA`
      watermark is present.

## Scientific / integrity impact

<!--
If this touches artifacts, the derivation protocol, displayed measurements, the CSP, or the
deploy configuration, explain the reasoning — these have project-wide consequences. If not,
write "none".
-->

## Screenshots / evidence

<!-- For any visible change, include before/after screenshots. For a build/deploy change,
     paste the relevant gate output. -->
