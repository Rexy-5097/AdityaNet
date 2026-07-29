"""
scripts/v2/phase05/build_canonical.py — archive-wide canonical build (M-VII).

Orchestration only. It calls parsers, feeds their outputs to builders, and writes
canonical tables. The BUILDERS never see a path; this driver never touches FITS
except through the frozen parser layer.

FAIL-LOUD SEPARATION: builders and parsers terminate on any contract violation.
This driver catches those terminations PER PRODUCT, records them with their rule
id in `skipped`, and reports them in the profile. Explicit + logged is not silent
-- one bad file must not destroy 435 good days, but it must never vanish either.
Archive-wide TERMINATION on violations is Milestone VIII's job (A-8/A-9/A-11/A-12).
"""
import glob, json, os, re, sys, time
from collections import Counter

sys.path.insert(0, "/Volumes/T7 Shield/Projects/AI/AdityaNet")
os.chdir("/Volumes/T7 Shield/Projects/AI/AdityaNet")

import pandas as pd

from app.v2.builders.canonical import (build_T1, build_T2, build_T3, build_T4,
                                       build_T5, build_T6, build_T7)
from app.v2.models.metadata import FailLoud
from app.v2.parsers.hel1os import (HEL1OSHkParser, HEL1OSLcParser,
                                   HEL1OSSpectraParser)
from app.v2.parsers.solexs_gti import SolexsGtiParser
from app.v2.parsers.solexs_lc import SolexsLcParser
from app.v2.parsers.solexs_pi import SolexsPiParser
from app.v2.resolution.version_engine import OrbitCandidate, build_coverage_map

OUT = "artifacts/v2/phase05/canonical"
STORE = "data/aditya_l1/real_l1_v1"
DETS = ("CZT1", "CZT2", "CDTE1", "CDTE2")
HLS = re.compile(r"HLS_(\d{8})_(\d{6})_(\d+)sec_lev1_V(\d{3})")

stats = {"skipped": [], "checks": Counter(), "failures": []}


def _sha(manifest, stem):
    return manifest.get(stem, "")


def main():
    t0 = time.time()
    for t in ("T1", "T2", "T3", "T4", "T5", "T6"):
        os.makedirs(f"{OUT}/{t}", exist_ok=True)
    man = {m["stem"]: m["sha256"] for m in
           json.load(open("artifacts/v2/phase05/archive_manifest.json"))}

    provs, t6_rows = [], []
    n_sol = n_hel = 0

    # ── SoLEXS: T1, T2, T6 ─────────────────────────────────────────────────
    days = sorted(glob.glob(f"{STORE}/solexs/AL1_SLX_L1_*"))
    days = [d for d in days if "/._" not in d]
    print(f"[solexs] {len(days)} archives", flush=True)
    for i, d in enumerate(days, 1):
        stem = os.path.basename(d)
        date = re.search(r"(\d{8})", stem).group(1)
        try:
            lcs = [x for x in glob.glob(f"{d}/**/*_L1.lc.gz", recursive=True) if "/._" not in x]
            pis = [x for x in glob.glob(f"{d}/**/*_L1.pi.gz", recursive=True) if "/._" not in x]
            gts = [x for x in glob.glob(f"{d}/**/*_L1.gti.gz", recursive=True) if "/._" not in x]
            if not lcs or not pis:
                stats["skipped"].append({"product": stem, "reason": "no .lc/.pi (SDD1-only)"})
                continue
            gti_by_det = {}
            for g in gts:
                gp = SolexsGtiParser().parse(g, sha256=_sha(man, stem))
                gti_by_det[gp.data.detector] = gp
                provs.append(gp.provenance)
                t6_rows.append(gp)
                stats["checks"]["solexs_gti_parsed"] += 1
                if not gp.detector_active:
                    stats["checks"]["solexs_detector_inactive_F12"] += 1

            lc = SolexsLcParser().parse(lcs[0], sha256=_sha(man, stem))
            gti = gti_by_det[lc.data.detector]
            t1 = build_T1(lc, gti)                       # runs NaN<->GTI (F-09)
            stats["checks"]["nan_gti_bijection_ok"] += 1
            t1.df.to_parquet(f"{OUT}/T1/{date}.parquet", index=False)
            provs.append(lc.provenance)

            pi = SolexsPiParser().parse(pis[0], sha256=_sha(man, stem),
                                        lc_tstart=lc.data.tstart_unix)
            stats["checks"]["V_PI_3_lc_pi_tstart_match"] += 1
            t2 = build_T2(pi, gti)
            t2.df.to_parquet(f"{OUT}/T2/{date}.parquet", index=False)
            provs.append(pi.provenance)
            del pi, t2
            n_sol += 1
        except FailLoud as e:
            stats["skipped"].append({"product": stem, "rule": e.rule,
                                     "reason": str(e)[:220]})
            stats["failures"].append({"product": stem, "rule": e.rule})
        except Exception as e:
            stats["skipped"].append({"product": stem, "rule": "UNEXPECTED",
                                     "reason": f"{type(e).__name__}: {e}"[:220]})
            stats["failures"].append({"product": stem, "rule": "UNEXPECTED"})
        if i % 50 == 0:
            print(f"  [{i}/{len(days)}] {(time.time()-t0)/60:.1f} min", flush=True)

    t6 = build_T6(t6_rows)
    t6.df.to_parquet(f"{OUT}/T6/gti_intervals.parquet", index=False)
    print(f"[T6] {len(t6.df)} intervals", flush=True)

    # ── HEL1OS: coverage map first, then T3/T4/T5 ──────────────────────────
    orbits = [d for d in sorted(glob.glob(f"{STORE}/hel1os/HLS_*")) if "/._" not in d]
    cands = []
    for d in orbits:
        m = HLS.search(d)
        if not m:
            stats["skipped"].append({"product": os.path.basename(d),
                                     "reason": "orbit id unparseable"})
            continue
        date, start, dur, ver = m.groups()
        t = pd.Timestamp(f"{date[:4]}-{date[4:6]}-{date[6:]}T{start[:2]}:{start[2:4]}:{start[4:]}Z")
        cands.append(OrbitCandidate(orbit_id=m.group(0), path=d,
                                    sha256=_sha(man, m.group(0)), version=int(ver),
                                    duration_s=int(dur), t_start_utc=t,
                                    t_stop_utc=t + pd.Timedelta(seconds=int(dur)),
                                    detectors=DETS))
    cm = build_coverage_map(cands)
    vlog = cm.resolution_log()
    print(f"[coverage] {len(cm)} owned pairs | {vlog['n_conflicting_minute_detector_pairs']} conflicts", flush=True)

    for i, d in enumerate(orbits, 1):
        stem = os.path.basename(d)
        try:
            lcs, sps = [], []
            for p in glob.glob(f"{d}/**/lightcurve_*.fits", recursive=True):
                if "/._" in p: continue
                lcs.append(HEL1OSLcParser().parse(p, sha256=_sha(man, stem)))
            for p in glob.glob(f"{d}/**/*_spectra_*.fits", recursive=True):
                if "/._" in p: continue
                sps.append(HEL1OSSpectraParser().parse(p, sha256=_sha(man, stem)))
            hkp = [x for x in glob.glob(f"{d}/**/hk.fits", recursive=True) if "/._" not in x]
            hks = [HEL1OSHkParser().parse(hkp[0], sha256=_sha(man, stem))] if hkp else []

            if lcs:
                t3 = build_T3(lcs, cm)
                if len(t3.df):
                    t3.df.to_parquet(f"{OUT}/T3/{stem}.parquet", index=False)
                provs += [p.provenance for p in lcs]
                stats["checks"]["hel1os_lc_built"] += 1
            if hks:
                t4 = build_T4(hks, cm)
                if len(t4.df):
                    t4.df.to_parquet(f"{OUT}/T4/{stem}.parquet", index=False)
                provs += [p.provenance for p in hks]
                stats["checks"]["hel1os_hk_built"] += 1
                stats.setdefault("hk_inversions", []).append(
                    {"orbit": stem, "n": hks[0].header["n_out_of_order"],
                     "max_s": hks[0].header["max_backward_step_s"]})
            if sps:
                t5 = build_T5(sps, cm)
                if len(t5.df):
                    t5.df.to_parquet(f"{OUT}/T5/{stem}.parquet", index=False)
                provs += [p.provenance for p in sps]
                stats["checks"]["hel1os_spec_built"] += 1
                for p in sps:
                    stats.setdefault("r1_kinds", Counter())[p.header["epoch_kind"]] += 1
            n_hel += 1
            del lcs, sps, hks
        except FailLoud as e:
            stats["skipped"].append({"product": stem, "rule": e.rule,
                                     "reason": str(e)[:220]})
            stats["failures"].append({"product": stem, "rule": e.rule})
        except Exception as e:
            stats["skipped"].append({"product": stem, "rule": "UNEXPECTED",
                                     "reason": f"{type(e).__name__}: {e}"[:220]})
            stats["failures"].append({"product": stem, "rule": "UNEXPECTED"})
        if i % 50 == 0:
            print(f"  [hel1os {i}/{len(orbits)}] {(time.time()-t0)/60:.1f} min", flush=True)

    t7 = build_T7(provs)
    t7.df.to_parquet(f"{OUT}/T7_provenance.parquet", index=False)
    print(f"[T7] {len(t7.df)} provenance rows", flush=True)

    out = {"solexs_archives_processed": n_sol, "hel1os_orbits_processed": n_hel,
           "n_solexs_available": len(days), "n_hel1os_available": len(orbits),
           "skipped": stats["skipped"], "failures": stats["failures"],
           "checks": dict(stats["checks"]),
           "r1_kinds": dict(stats.get("r1_kinds", {})),
           "hk_inversions": stats.get("hk_inversions", []),
           "version_resolution": {k: vlog[k] for k in
                                  ("n_candidates", "n_owned_minute_detector_pairs",
                                   "n_conflicting_minute_detector_pairs",
                                   "n_distinct_conflicts", "rules_invoked")},
           "elapsed_min": round((time.time() - t0) / 60, 2)}
    json.dump(out, open("artifacts/v2/phase05/canonical_build_stats.json", "w"),
              indent=1, default=str)
    print(f"\n=== BUILD DONE === solexs {n_sol}/{len(days)} | hel1os {n_hel}/{len(orbits)} "
          f"| skipped {len(stats['skipped'])} | {out['elapsed_min']} min", flush=True)


if __name__ == "__main__":
    main()
