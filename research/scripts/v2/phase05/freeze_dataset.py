"""
scripts/v2/phase05/freeze_dataset.py — Milestone IX dataset freeze.

Computes the immutable identity of the canonical dataset: per-file SHA-256 of
every parquet, per-table aggregate hashes, a single dataset hash, and a snapshot
of the environment. Writes freeze_manifest.json which the manifest/reproducibility
reports format. READ-ONLY over the dataset; it hashes, it never modifies.
"""
import hashlib, json, os, subprocess, sys, glob, platform
from datetime import datetime, timezone

sys.path.insert(0, "/Volumes/T7 Shield/Projects/AI/AdityaNet")
os.chdir("/Volumes/T7 Shield/Projects/AI/AdityaNet")

import pandas as pd

CANON = "artifacts/v2/phase05/canonical"
DATASET_VERSION = "AdityaNet_v2_dataset_r1"

# T7 carries parsed_at_utc (build wall-clock). Everything else is deterministic,
# so the reproducible content-hash of T7 EXCLUDES this one column. Recorded
# explicitly so reproducibility is a documented fact, not an assumption.
NON_REPRODUCIBLE_COLUMNS = {"parsed_at_utc"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def content_hash(path):
    """Value-level hash: reproducible across builds/environments (parquet FILE
    bytes are not, due to embedded library metadata). Excludes build-timestamp
    columns so a faithful rebuild reproduces this hash exactly."""
    df = pd.read_parquet(path)
    cols = [c for c in df.columns if c not in NON_REPRODUCIBLE_COLUMNS]
    h = hashlib.sha256()
    for c in sorted(cols):
        h.update(c.encode())
        h.update(pd.util.hash_pandas_object(df[c], index=False).values.tobytes())
    return h.hexdigest()


def table_files(sub):
    if os.path.isdir(f"{CANON}/{sub}"):
        return sorted(f for f in glob.glob(f"{CANON}/{sub}/*.parquet") if "/._" not in f)
    p = f"{CANON}/{sub}.parquet"
    return [p] if os.path.exists(p) else []


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def main():
    tables = {
        "T1": ("solexs_lc_1min", table_files("T1")),
        "T2": ("solexs_spec_1min", table_files("T2")),
        "T3": ("hel1os_lc_1min", table_files("T3")),
        "T4": ("hel1os_hk_1min", table_files("T4")),
        "T5": ("hel1os_spec_1min", table_files("T5")),
        "T6": ("gti_intervals", table_files("T6")),
        "T7": ("provenance_manifest",
               [f"{CANON}/T7_provenance.parquet"] if os.path.exists(f"{CANON}/T7_provenance.parquet") else []),
    }

    manifest = {"dataset_version": DATASET_VERSION,
                "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
                "tables": {}}
    all_hashes = []          # feeds the single dataset hash, order-independent
    total_bytes = 0
    for tid, (name, files) in tables.items():
        per_file = []
        for f in files:
            h = sha256(f)
            sz = os.path.getsize(f)
            total_bytes += sz
            per_file.append({"file": os.path.relpath(f, CANON), "sha256": h, "bytes": sz})
            all_hashes.append(h)
        # per-table aggregate hash = sha256 of the sorted per-file hashes
        agg = hashlib.sha256("".join(sorted(x["sha256"] for x in per_file)).encode()).hexdigest()
        manifest["tables"][tid] = {"name": name, "n_files": len(files),
                                   "table_hash": agg, "files": per_file}

    # single dataset hash: order-independent over every file in the dataset
    dataset_hash = hashlib.sha256("".join(sorted(all_hashes)).encode()).hexdigest()
    prov_files = tables["T7"][1]
    provenance_hash = sha256(prov_files[0]) if prov_files else None

    lock = "artifacts/v2/phase05/requirements.lock"
    manifest["identity"] = {
        "dataset_hash": dataset_hash,
        "provenance_hash": provenance_hash,
        "total_bytes": total_bytes,
        "n_parquet_files": len(all_hashes),
        "build_commit": git("rev-parse", "HEAD"),
        "build_commit_short": git("rev-parse", "--short", "HEAD"),
        "specification_revision": "r6",
        "parser_revision": "M-V/r5 (family DETCHANS) + r6-consistent",
        "builder_revision": "M-VII/r5 + T3 long-form (r6)",
        "validation_revision": "M-VIII",
        "archive_span": "2024-02-01 .. 2026-06-17 (UTC)",
    }
    manifest["environment"] = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "lockfile": lock,
        "lockfile_sha256": sha256(lock) if os.path.exists(lock) else None,
    }
    json.dump(manifest, open("artifacts/v2/phase05/freeze_manifest.json", "w"), indent=1)
    print(f"dataset_version : {DATASET_VERSION}")
    print(f"dataset_hash    : {dataset_hash}")
    print(f"parquet files   : {len(all_hashes)}  ({total_bytes/1e6:.1f} MB)")
    print(f"provenance_hash : {provenance_hash}")
    print(f"build commit    : {manifest['identity']['build_commit_short']}")
    for tid, t in manifest["tables"].items():
        print(f"  {tid} {t['name']:22s} {t['n_files']:4d} files  {t['table_hash'][:16]}")


if __name__ == "__main__":
    main()
