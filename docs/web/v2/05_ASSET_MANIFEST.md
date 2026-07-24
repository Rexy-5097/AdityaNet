# 5 · Asset Manifest

Every byte shipped to a browser, with verified licence. Nothing is vendored without a
licence confirmed against the publisher's own policy page.

## 5.1 Verified licence sources

| Asset class | Verified finding | Source |
|---|---|---|
| NASA imagery/video/3D | "Generally not subject to copyright." Acknowledge NASA; no implied endorsement; third-party material marked separately | [NASA Brand Center](https://www.nasa.gov/nasa-brand-center/images-and-media/) |
| NASA SVS media | "All of our content is in the public domain (unless otherwise noted)… free to download, use, and redistribute for whatever purposes you see fit." **Some videos carry licensed music that is NOT public domain** | [SVS Help](https://svs.gsfc.nasa.gov/help/) |
| NASA 3D Resources | Free, copyright-free, `.glb`/`.usdz`, Draco-compressed | [NASA 3D Resources](https://www.nasa.gov/3d-resources/) |

## 5.2 Visual assets

| Asset | Source | Licence | Budget | Notes |
|---|---|---|---|---|
| **Solar footage** | NASA SVS — [SDO 4K galleries](https://svs.gsfc.nasa.gov/gallery/sdo4k-content/), [slow-rotation Sun](https://svs.gsfc.nasa.gov/12613/) | Public domain ✅ | **≤5 MB** | Transcode to 1080p + 720p, H.264 **and** WebM. **Strip audio (`-an`)** — the one way NASA content carries an encumbrance. Never ship the 4.9 GB master |
| **Solar still** (poster / reduced-motion / no-WebGL) | SDO `latest_1024_0171.jpg` | Public domain ✅ | ~190 KB | Already vendored and working |
| **HMI continuum still** (optional alt) | SDO `latest_1024_HMIIC.jpg` | Public domain ✅ | ~190 KB | Already vendored |
| **Star field** | drei `<Stars>` | MIT | ~0 (procedural points) | Tier-3 ambient, static |
| **LUTs** (3 × register grades) | Authored in any grading tool as `.cube` | Ours / CC0 | ~50 KB total | See §6 open question |
| **Fonts** | Inter, IBM Plex Mono | SIL OFL 1.1 ✅ | ~120 KB subset | Self-hosted `woff2`, Latin subset. **Never Google Fonts CDN** |
| **Icons** | Lucide | ISC ✅ | ~2 KB used | Per-icon tree-shaken SVG |

## 5.3 The spacecraft — resolved

Carried forward from the [v2 integration plan](../V2_INTEGRATION_PLAN.md) §7. Verified:
**NASA 3D Resources has no Aditya-L1** (it is an ISRO mission), and every located model is
third-party stock ([CGTrader ~$4](https://www.cgtrader.com/3d-models/space/spaceship/isro-aditya-l1-3d-model-india-mission-to-sun),
[Sketchfab Store](https://sketchfab.com/3d-models/aditya-l1-satellite-89fe9cc3359e410ba285862dec53e5dc)),
one described as built "using images from ISRO's website." No CC-BY/CC0 version confirmed.

**Decision: no mesh asset. The spacecraft is a diagram assembled from three.js primitives.**

Two independent grounds:

1. **Licence.** Stock-3D terms typically forbid redistribution in extractable form; a `.glb`
   served to a browser is inherently downloadable. Genuine risk, not theoretical.
2. **Honesty (decisive).** These are artists' interpretations, not engineering data.
   Presenting fan-made geometry as Aditya-L1's structure claims fidelity nothing backs — the
   exact failure AdityaNet exists to repudiate. **A photoreal model would make the project
   less honest, not more finished.**

Register S *requires* a diagram. A box bus, two plane wings, seven labelled markers, drei
`<Text>` labels, `<Line>` leaders. Zero licence risk, zero mesh bytes, correct register.

**Payload names are facts, not copyrightable expression** — SUIT, VELC, HEL1OS, ASPEX, PAPA,
MAG, SoLEXS, cited to ISRO/eoPortal, are safe to state. **ISRO diagrams and photographs are
a different matter: treat as ©ISRO / all-rights-reserved unless a specific open licence is
confirmed. Do not vendor ISRO imagery on current evidence.**

## 5.4 Data assets (Register B)

| Asset | Source | Notes |
|---|---|---|
| SoLEXS light curve, 2024-05-14 | `AdityaNet_v2_dataset_r1`, hash `43fd0e22…` | 1440 minutes, X8.7 flare, peak 29036.25. **Real archive data** |
| First observed minute | Same | `112.98` — the number the crossing resolves to |
| Artefact pointers | T1 `solexs_lc_1min` | Every displayed number carries artefact + JSON pointer + hash |

Data ships as static JSON, pre-reduced at build time. No runtime fetch for first paint.

## 5.5 Total budget

| Category | Budget |
|---|---|
| Solar video (largest, lazy, `preload="none"`) | ≤ 5 MB |
| Fonts (subset woff2) | ≤ 120 KB |
| Stills | ≤ 400 KB |
| LUTs | ≤ 50 KB |
| Data JSON | ≤ 80 KB |
| **JS — experience island (gz)** | **≤ 350 KB** |
| **JS — evidence surfaces** | **~0 KB** (hard requirement) |

## 5.6 Open questions for the owner

1. **Which SVS clip?** Recommend a **slow-rotation loop** over a flare event — the hero must
   not upstage the crossing. Needs your pick; each candidate's page must be checked for a
   "licensed music" note before vendoring.
2. **LUT authoring.** Three `.cube` files (warm / cool / neutral). No mature open library of
   *scientifically neutral* LUTs exists; these are small, authored artefacts. Do you want
   them authored, or should the register shift use plain `HueSaturation` +
   `BrightnessContrast` (stock effects, zero new assets, slightly less filmic)?
3. **ISRO imagery** — confirmed treated as all-rights-reserved. Blocks nothing; the
   schematic path avoids it entirely.
