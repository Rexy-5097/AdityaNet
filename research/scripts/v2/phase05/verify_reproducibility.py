"""
scripts/v2/phase05/verify_reproducibility.py — Milestone IX reproducibility proof.

Rebuilds a sample of canonical tables FROM THE RAW ARCHIVE and compares them
against the frozen dataset. Reports byte-identity and content-identity
separately, because they are different claims:

  * CONTENT identity  — the values are identical. This is what a rebuild must
    reproduce and what the science depends on.
  * BYTE identity     — the parquet file bytes are identical. Parquet embeds
    writer metadata, so byte-identity is a property of the frozen ARTIFACT
    (pinned by file SHA-256), not something a rebuild is guaranteed to give
    across environments.

Nothing is modified. The frozen dataset is opened read-only.
"""
import glob, hashlib, io, json, os, re, sys, time, warnings
from datetime import datetime, timezone

sys.path.insert(0, "/Volumes/T7 Shield/Projects/AI/AdityaNet")
os.chdir("/Volumes/T7 Shield/Projects/AI/AdityaNet")
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

from app.v2.builders.canonical import build_T1, build_T2
from app.v2.parsers.solexs_gti import SolexsGtiParser
from app.v2.parsers.solexs_lc import SolexsLcParser
from app.v2.parsers.solexs_pi import SolexsPiParser

CANON = "artifacts/v2/phase05/canonical"
STORE = "data/aditya_l1/real_l1_v1"
N_SAMPLE = 12          # spread across the archive span

MANIFEST = {m["stem"]: m["sha256"]
            for m in json.load(open("artifacts/v2/phase05/archive_manifest.json"))}


def content_hash(df: pd.DataFrame) -> str:
    """Value-level hash. Handles array columns (T2 counts is list[340])."""
    h = hashlib.sha256()
    for c in sorted(df.columns):
        h.update(c.encode())
        col = df[c]
        if col.dtype == object and len(col) and isinstance(col.iloc[0], (np.ndarray, list)):
            h.update(np.ascontiguousarray(np.vstack(col.to_numpy()),
                                          dtype=np.float64).tobytes())
        else:
            h.update(pd.util.hash_pandas_object(col, index=False).values.tobytes())
    return h.hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    days = sorted(d for d in glob.glob(f"{STORE}/solexs/AL1_SLX_L1_*") if "/._" not in d)
    built = {os.path.basename(p).replace(".parquet", "")
             for p in glob.glob(f"{CANON}/T1/*.parquet")}
    # only sample days that are IN the frozen dataset
    cand = [d for d in days if re.search(r"(\d{8})", d).group(1) in built]
    idx = np.linspace(0, len(cand) - 1, N_SAMPLE).astype(int)

    results, t0 = [], time.time()
    for i in idx:
        d = cand[i]
        stem = os.path.basename(d)
        date = re.search(r"(\d{8})", stem).group(1)
        sha = MANIFEST.get(stem, "")
        try:
            inner = glob.glob(f"{d}/*/SDD2/AL1_SOLEXS_{date}_SDD2_L1.lc.gz")
            if not inner:
                inner = [p for p in glob.glob(f"{d}/**/*_L1.lc.gz", recursive=True)
                         if "/._" not in p]
            b = inner[0][:-6]                       # strip ".lc.gz"
            t_start = time.time()
            lc = SolexsLcParser().parse(b + ".lc.gz", sha256=sha)
            g = SolexsGtiParser().parse(b + ".gti.gz", sha256=sha)
            t1_new = build_T1(lc, g).df
            pi = SolexsPiParser().parse(b + ".pi.gz", sha256=sha,
                                        lc_tstart=lc.data.tstart_unix)
            t2_new = build_T2(pi, g).df
            elapsed = time.time() - t_start

            rec = {"date": date, "rebuild_s": round(elapsed, 2)}
            for tid, new in (("T1", t1_new), ("T2", t2_new)):
                frozen_path = f"{CANON}/{tid}/{date}.parquet"
                frozen = pd.read_parquet(frozen_path)
                # content identity (the scientific claim)
                ch_new, ch_old = content_hash(new), content_hash(frozen)
                # byte identity of a freshly-written parquet vs the frozen file
                buf = io.BytesIO(); new.to_parquet(buf, index=False)
                bytes_match = hashlib.sha256(buf.getvalue()).hexdigest() == file_sha(frozen_path)
                rec[tid] = {"content_match": ch_new == ch_old,
                            "content_hash": ch_new[:16],
                            "byte_match": bytes_match,
                            "rows_new": len(new), "rows_frozen": len(frozen)}
            results.append(rec)
            print(f"  {date}: T1 content={rec['T1']['content_match']} byte={rec['T1']['byte_match']} "
                  f"| T2 content={rec['T2']['content_match']} | {elapsed:.1f}s", flush=True)
        except Exception as e:
            results.append({"date": date, "error": f"{type(e).__name__}: {e}"[:200]})
            print(f"  {date}: ERROR {type(e).__name__}: {e}", flush=True)

    ok = [r for r in results if "T1" in r]
    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "n_sampled": len(results), "n_compared": len(ok),
        "content_identity": {
            "T1": sum(r["T1"]["content_match"] for r in ok),
            "T2": sum(r["T2"]["content_match"] for r in ok),
            "all_match": all(r["T1"]["content_match"] and r["T2"]["content_match"] for r in ok)},
        "byte_identity": {
            "T1": sum(r["T1"]["byte_match"] for r in ok),
            "T2": sum(r["T2"]["byte_match"] for r in ok)},
        "timing_s": {"total": round(time.time() - t0, 1),
                     "per_day_median": float(np.median([r["rebuild_s"] for r in ok])) if ok else None},
        "environment": {"python": sys.version.split()[0],
                        "numpy": np.__version__, "pandas": pd.__version__},
        "per_day": results,
    }
    json.dump(out, open("artifacts/v2/phase05/reproducibility_check.json", "w"), indent=1)
    print(f"\ncontent identity: T1 {out['content_identity']['T1']}/{len(ok)} "
          f"| T2 {out['content_identity']['T2']}/{len(ok)}")
    print(f"byte identity   : T1 {out['byte_identity']['T1']}/{len(ok)} "
          f"| T2 {out['byte_identity']['T2']}/{len(ok)}")


if __name__ == "__main__":
    main()
