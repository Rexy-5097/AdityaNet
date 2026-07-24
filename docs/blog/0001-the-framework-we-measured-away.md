# The framework we measured away

*Engineering notes · 2026-07-23 · Sprint 0*

I chose Next.js for AdityaNet without measuring anything. It is what you reach for.
The architecture document had already concluded — correctly — that the platform needs
no runtime server: the dataset is frozen, every API response is enumerable, and
nothing changes between requests. I wrote `output: 'export'` and moved on.

Then the budget gate ran.

```
initial JS: 184.2 KB gz exceeds the 40 KB budget (9 scripts)
```

That is a page with **zero interactive components**. One heading, three paragraphs,
a horizontal rule. The largest chunk was 71 KB of `react-dom` containing `hydrateRoot`.

My first instinct was that I had misconfigured something. I checked whether it was a
development build by grepping the chunks for React's dev-only warning strings. Nothing.
It was production. The App Router hydrates unconditionally, so React ships whether or
not anything on the page will ever respond to a click.

The interesting part was not the number. It was what the number invalidated.

The specification set a 60 KB budget for the validation page, with an argument
attached: that page carries the project's credibility — the six contradictions where
execution falsified the specification and each was publicly adjudicated — and *a
reviewer's patience is the scarcest resource the project has*. It should be the
fastest page on the site.

At a 184 KB floor, it cannot be. Neither can `/build` at 80 KB, nor `/findings` at
160 KB. Every budget in the document sat below the framework's floor. They were not
ambitious targets I had missed. They were arithmetic that could not be satisfied.

So I measured the alternative instead of arguing about it. A minimal Astro page with
equivalent content:

```
=== scripts referenced in index.html ===
(none)
=== total JS bytes ===
0
```

Zero. Not "small" — absent. No `<script>` tag at all.

That single measurement resolved three problems at once. Evidence surfaces became
free, which is what makes a 450 KB immersive WebGL island affordable on one opt-in
route — cheap pages pay for the expensive one. The strict Content-Security-Policy the
specification asked for became achievable, because Next's inline RSC payload had been
forcing `script-src 'unsafe-inline'` and Astro emits no inline scripts. And Astro's
`client:*` directive turned out to enforce the client-boundary rule as a language
feature, replacing a custom ESLint rule I had planned to write and maintain.

## The lesson, stated honestly

I had made the same mistake twice in one sprint. I estimated the three.js bundle at
220–280 KB gz before the experience-layer decision. Measured: **314.17 KB**. Wrong
again, in the same direction.

Worse, I had pre-registered a fallback — "drop `postprocessing` if over budget" —
which measurement then showed to be worthless: removing `drei` *and* `postprocessing`
saves 21.6 KB, about 7%, in exchange for the entire effects pipeline. three.js core is
~245 KB and irreducible. My contingency plan would have sacrificed everything
interesting to recover almost nothing.

Two estimates, both low, both about a framework's floor. That is not bad luck; it is a
bias. Framework baselines are invisible in the source tree, so they are systematically
underestimated by whoever reads only their own code.

The correction was mechanical rather than resolving to be more careful.
`scripts/check.ts` now measures transfer size by parsing the built HTML for
`<script src>` and gzipping the referenced assets. It does not ask the bundler. It
does not sum the output directory, which would over-count chunks no route loads. It
measures what a browser would actually download, and it fails the build when that
exceeds a number someone agreed to in advance.

The same gate found something else on its first Astro run: 61 macOS AppleDouble files
inside `dist/`, created because the project volume is not HFS+ and generated during
the build itself. They would have been uploaded to a public CDN carrying resource
forks and originating paths. Nothing in the source tree mentions them, and no code
review would have caught them.

Neither finding required cleverness. Both required a gate that measures reality
instead of trusting a report — which is, not coincidentally, the same principle the
scientific half of this project is built on.
