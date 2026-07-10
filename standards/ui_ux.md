# Standard: UI/UX

> **Tier:** Component — applies to all user-facing interfaces
> **Owner:** UI Lead / Design Lead | **Reviewer:** `ui-reviewer`
> **Consumers:** `ui-reviewer` | **Max:** ~1400 tokens
> **Cross-refs:** `standards/code_quality.md` · `standards/testing.md` · `standards/documentation.md` · `standards/security.md`

---

## Purpose

Ensure that user interfaces are accessible, performant, consistent, and usable by real people — including people with disabilities, on slow connections, and on diverse devices — without requiring perfection in the happy path.

## Scope

**Governs:** Frontend interfaces, interactive components, design system usage, accessibility, performance budgets, interaction patterns.
**Does NOT govern:** Backend logic behind APIs (→ `standards/api_design.md`), frontend security (CORS, CSP → `standards/security.md`), component code quality (→ `standards/code_quality.md`).

---

## Guiding Principles

1. **Accessibility is not optional.** An interface that excludes users with disabilities is a broken interface.
2. **Design for the slowest device and connection.** Performance on mid-range hardware on 4G is the target — not a MacBook on fiber.
3. **Error states are as important as success states.** Every interaction that can fail must handle failure gracefully.
4. **Consistency reduces cognitive load.** Reuse patterns; don't reinvent per feature.
5. **Progressive disclosure.** Show what users need now; reveal complexity on demand.
6. **Touch and keyboard are both first-class.** Mouse-only interfaces exclude users; keyboard-only interfaces exclude more.
7. **Measure real user experience.** Lab testing is insufficient; real user metrics (Core Web Vitals) are required at production grade.

---

## Quality Levels

| Dimension | Minimum Acceptable | Recommended | Production Grade | Flagship Grade |
|-----------|-------------------|-------------|-----------------|----------------|
| Accessibility | Semantic HTML · alt text | WCAG 2.1 AA | WCAG 2.1 AA audited | WCAG 2.2 AAA |
| Keyboard navigation | Focusable elements | Tab order correct | Full keyboard flow | + Skip links + focus traps managed |
| Responsive design | Mobile renders | Mobile-first | Tested on 3+ device sizes | + Tested on real devices |
| Performance (LCP) | < 4.0s | < 2.5s | < 2.5s (Core Web Vitals green) | < 1.5s |
| Performance (CLS) | < 0.25 | < 0.1 | < 0.1 (Core Web Vitals green) | < 0.05 |
| Performance (INP) | < 500ms | < 200ms | < 200ms (Core Web Vitals green) | < 100ms |
| Error handling | Errors shown | User-friendly messages | Recovery actions offered | + Contextual help |
| Design system usage | None required | Partial | Design tokens used | Full design system compliance |

---

## Accessibility Requirements (WCAG 2.1 AA)

| Category | Requirement | Test Method |
|---------|------------|------------|
| Perceivable | All images have meaningful alt text | Automated scan + manual |
| Perceivable | Color contrast ≥ 4.5:1 (text) · 3:1 (large text) | Contrast analyzer |
| Operable | All functionality keyboard-accessible | Manual keyboard test |
| Operable | Focus indicators visible | Visual inspection |
| Operable | No content flashes more than 3× per second | Automated scan |
| Understandable | Form inputs have visible labels | Automated scan + manual |
| Understandable | Error messages identify the field and describe the fix | Manual |
| Robust | HTML validates · ARIA roles are correct | Automated scan |

---

## Performance Budgets

| Metric | Minimum | Recommended | Production | Flagship |
|--------|---------|-------------|------------|---------|
| LCP | < 4.0s | < 2.5s | < 2.5s | < 1.5s |
| INP | < 500ms | < 200ms | < 200ms | < 100ms |
| CLS | < 0.25 | < 0.1 | < 0.1 | < 0.05 |
| Total JS (compressed) | No limit | < 300KB | < 200KB | < 150KB |
| Total images | No limit | Lazy loading | WebP / AVIF | WebP / AVIF + CDN |

Measure on: Simulated 4G (throttled) · Moto G4 class device (for mobile) · Desktop baseline.

---

## Best Practices

- **Label every form control explicitly.** Never rely on placeholder text as a label.
- **Never convey meaning by color alone.** Add icons, text, or patterns alongside color coding.
- **Manage focus.** When a modal opens, focus moves inside it. When it closes, focus returns to the trigger.
- **Test keyboard flow end-to-end.** Close the mouse and complete the primary user workflow using only the keyboard.
- **Write error messages in plain language.** "Invalid input" is not an error message. "Email must include an @ symbol" is.
- **Use loading states.** Every async operation must have a loading indicator and a timeout or error state.
- **Preload critical resources.** LCP image and key fonts should be preloaded.
- **Design system first.** Use design system components before building custom ones.

---

## Anti-patterns

| Anti-pattern | Why It Fails |
|-------------|-------------|
| `<div>` for buttons and links | Non-focusable; not keyboard accessible; no semantic role |
| Color as the only error indicator | Invisible to colorblind users |
| Missing `alt` text | Screen readers cannot describe the image |
| Placeholder text as label | Disappears when typing; fails accessibility scan |
| `outline: none` on focusable elements | Keyboard users cannot track focus |
| Loading without a timeout or error state | User has no recovery option on failure |
| Hardcoded pixel widths | Breaks on small screens; excludes users |
| Autoplaying media with sound | Disruptive; violates WCAG |

---

## Common Failure Modes

| Failure | Why It Happens | Detection | Recovery |
|---------|---------------|-----------|---------|
| Accessibility regression | Semantic HTML replaced with styled divs | Automated scan in CI | Replace with semantic elements; add accessibility CI gate |
| Performance regression | Large image or JS added without budget check | Lighthouse CI | Optimize asset; add performance budget enforcement |
| Focus trap escape | Modal closed without returning focus | Manual keyboard test | Implement focus management in modal component |
| Color contrast failure | Designer uses brand colors without checking contrast | Contrast analyzer | Adjust color; update design tokens |

---

## Acceptance Criteria

| Level | Required to Pass |
|-------|-----------------|
| Minimum | All pages render · Core functionality works · No broken images |
| Recommended | + WCAG 2.1 AA · Keyboard navigable · Responsive · LCP < 2.5s |
| Production | + Accessibility audit passed · Core Web Vitals green · Error states tested · Design tokens used |
| Flagship | + WCAG 2.2 AAA · Real user monitoring deployed · Usability research conducted · Design system compliant |

---

## Reviewer Questions

```
UI/UX REVIEW CHECKLIST
□ Do all interactive elements have visible focus indicators?
□ Is all functionality operable by keyboard alone?
□ Do all images have meaningful alt text?
□ Does color contrast meet ≥ 4.5:1 for normal text?
□ Are all form inputs labeled explicitly (not by placeholder)?
□ Are error messages specific and actionable?
□ Does every async operation have a loading state and error state?
□ Do Core Web Vitals (LCP, INP, CLS) meet the project's quality level targets?
□ Is the interface tested on mobile / small screen?
□ Are ARIA roles used correctly where semantic HTML is insufficient?
```

---

## Completion Criteria

- [ ] Accessibility scan passes with zero critical or serious issues
- [ ] Keyboard navigation test complete for all primary workflows
- [ ] Core Web Vitals meet the target for the project's quality level
- [ ] Error states implemented for all async operations
- [ ] Acceptance criteria for the project's quality level are met
- [ ] `ui-reviewer` has reviewed and approved

---

## Cross-references

| Topic | Standard |
|-------|---------|
| Component code quality | `standards/code_quality.md` |
| UI component tests | `standards/testing.md` |
| CORS and CSP (frontend security) | `standards/security.md` |
| UI documentation | `standards/documentation.md` |
| Performance metrics | `metrics/performance.md` |
