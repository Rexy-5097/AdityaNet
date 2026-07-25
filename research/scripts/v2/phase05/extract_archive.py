"""
scripts/v2/phase05/extract_archive.py

Phase 0.5.1 — Extraction & Archive Manifest (AdityaNet v2, roadmap r1 @ 6b37fb8).

Treats data_pipeline/downloads/raw/ as IMMUTABLE EVIDENCE: opened read-only,
never written to, never moved. Extracts to a separate versioned store.

FAIL-LOUD RULE (roadmap r1 charter): no failure is ever silently skipped. Every
archive and every member is recorded with an explicit status; errors are logged
with their exception text and counted. There is no fallback path and no
simulation.

Outputs (artifacts/v2/phase05/):
  archive_manifest.json   — one record per archive: sha256, size, integrity, members
  member_inventory.json   — one record per extracted member: path, size, sha256
  extraction_log.json     — per-archive extraction status + errors
"""
import hashlib, json, os, sys, time, zipfile
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, "/Volumes/T7 Shield/Projects/AI/AdityaNet")
os.chdir("/Volumes/T7 Shield/Projects/AI/AdityaNet")

SRC = "data_pipeline/downloads/raw"
DEST = "data/aditya_l1/real_l1_v1"
OUT = "artifacts/v2/phase05"
CHUNK = 1 << 20


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(CHUNK), b""):
            h.update(c)
    return h.hexdigest()


def discover():
    """All archives under SRC. Instrument inferred from path, not assumed."""
    out = []
    for root, _, files in os.walk(SRC):
        for fn in files:
            if not fn.lower().endswith(".zip"):
                continue
            p = os.path.join(root, fn)
            if "/solex" in root:
                inst = "solexs"
            elif "/hel1os" in root:
                inst = "hel1os"
            else:
                inst = "UNKNOWN"          # logged, never guessed
            out.append((p, inst))
    return sorted(out)


def safe_target(dest_root, member_name):
    """Reject path traversal; ISSDC archives are trusted but never assumed."""
    t = os.path.normpath(os.path.join(dest_root, member_name))
    if not os.path.abspath(t).startswith(os.path.abspath(dest_root) + os.sep):
        raise ValueError(f"path traversal attempt: {member_name!r}")
    return t


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(DEST, exist_ok=True)
    archives = discover()
    print(f"[discover] {len(archives)} archives under {SRC}", flush=True)

    manifest, members, exlog = [], [], []
    t0 = time.time()

    for n, (path, inst) in enumerate(archives, 1):
        stem = os.path.splitext(os.path.basename(path))[0]
        rec = {"archive": path, "instrument": inst, "stem": stem,
               "size_bytes": os.path.getsize(path),
               "sha256": None, "integrity": None, "n_members": None,
               "uncompressed_bytes": None, "status": None, "error": None}
        try:
            rec["sha256"] = sha256_file(path)
            with zipfile.ZipFile(path) as zf:          # read-only
                bad = zf.testzip()                     # None if all CRCs good
                rec["integrity"] = "OK" if bad is None else f"CRC_FAIL:{bad}"
                infos = [i for i in zf.infolist() if not i.is_dir()]
                rec["n_members"] = len(infos)
                rec["uncompressed_bytes"] = sum(i.file_size for i in infos)
                if bad is not None:
                    rec["status"] = "INTEGRITY_FAIL_NOT_EXTRACTED"
                    exlog.append({"archive": path, "status": rec["status"],
                                  "error": f"testzip reported {bad}"})
                    manifest.append(rec)
                    print(f"[{n}/{len(archives)}] INTEGRITY FAIL {stem}", flush=True)
                    continue
                droot = os.path.join(DEST, inst, stem)
                n_ok = n_err = 0
                for i in infos:
                    try:
                        tgt = safe_target(droot, i.filename)
                        os.makedirs(os.path.dirname(tgt), exist_ok=True)
                        h = hashlib.sha256()
                        with zf.open(i) as src, open(tgt, "wb") as dst:
                            while True:
                                c = src.read(CHUNK)
                                if not c:
                                    break
                                h.update(c)
                                dst.write(c)
                        members.append({"archive_stem": stem, "instrument": inst,
                                        "member": i.filename,
                                        "extracted_path": tgt,
                                        "size_bytes": i.file_size,
                                        "sha256": h.hexdigest()})
                        n_ok += 1
                    except Exception as e:                       # per-member, logged
                        n_err += 1
                        exlog.append({"archive": path, "member": i.filename,
                                      "status": "MEMBER_FAIL", "error": repr(e)[:300]})
                rec["status"] = "EXTRACTED" if n_err == 0 else f"PARTIAL:{n_err}_member_errors"
                exlog.append({"archive": path, "status": rec["status"],
                              "members_ok": n_ok, "members_failed": n_err})
        except Exception as e:                                    # per-archive, logged
            rec["status"] = "ARCHIVE_FAIL"
            rec["error"] = repr(e)[:300]
            exlog.append({"archive": path, "status": "ARCHIVE_FAIL", "error": repr(e)[:300]})
            print(f"[{n}/{len(archives)}] ARCHIVE FAIL {stem}: {e}", flush=True)
        manifest.append(rec)
        if n % 25 == 0 or n == len(archives):
            el = time.time() - t0
            print(f"[{n}/{len(archives)}] {el/60:.1f} min | "
                  f"{sum(1 for m in manifest if m['status']=='EXTRACTED')} extracted", flush=True)

    json.dump(manifest, open(f"{OUT}/archive_manifest.json", "w"), indent=1)
    json.dump(members, open(f"{OUT}/member_inventory.json", "w"), indent=1)
    json.dump(exlog, open(f"{OUT}/extraction_log.json", "w"), indent=1)

    st = defaultdict(int)
    for m in manifest:
        st[m["status"]] += 1
    print("\n=== STATUS ===")
    for k, v in sorted(st.items()):
        print(f"  {k}: {v}")
    print(f"members extracted: {len(members)}")
    print(f"generated: {datetime.utcnow().isoformat()}Z  elapsed {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
