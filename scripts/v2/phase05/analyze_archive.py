"""
scripts/v2/phase05/analyze_archive.py

Phase 0.5.1 reporting + falsification pass. Consumes the extraction outputs;
never re-extracts. Produces coverage, duplicate, integrity, and structure
findings, and actively tries to falsify the inventory.

Deliverables 3-10 of the Phase 0.5.1 brief.
"""
import glob, json, os, re, sys
from collections import Counter, defaultdict
from datetime import date, timedelta

sys.path.insert(0, "/Volumes/T7 Shield/Projects/AI/AdityaNet")
os.chdir("/Volumes/T7 Shield/Projects/AI/AdityaNet")

OUT = "artifacts/v2/phase05"
man = json.load(open(f"{OUT}/archive_manifest.json"))
mem = json.load(open(f"{OUT}/member_inventory.json"))

R = {}

# ── 1. storage + status ──────────────────────────────────────────────────────
R["status_counts"] = dict(Counter(m["status"] for m in man))
R["integrity_counts"] = dict(Counter(str(m["integrity"]) for m in man))
R["storage"] = {
    "n_archives": len(man),
    "compressed_GB": round(sum(m["size_bytes"] for m in man) / 1e9, 3),
    "uncompressed_GB": round(sum(m["uncompressed_bytes"] or 0 for m in man) / 1e9, 3),
    "extracted_members": len(mem),
    "extracted_GB": round(sum(m["size_bytes"] for m in mem) / 1e9, 3),
}

# ── 2. instrument inventory ──────────────────────────────────────────────────
inst = defaultdict(lambda: {"archives": 0, "members": 0, "GB": 0.0})
for m in man:
    inst[m["instrument"]]["archives"] += 1
for m in mem:
    inst[m["instrument"]]["members"] += 1
    inst[m["instrument"]]["GB"] += m["size_bytes"] / 1e9
R["instrument_inventory"] = {k: {**v, "GB": round(v["GB"], 2)} for k, v in inst.items()}

# ── 3. product-type inventory (what kinds of files exist) ────────────────────
def ptype(member):
    b = os.path.basename(member)
    for pat, name in ((r"\.lc\.gz$", "solexs_lightcurve"), (r"\.pi\.gz$", "solexs_spectrum"),
                      (r"\.gti\.gz$", "solexs_gti"), (r"^evt\.fits$", "hel1os_events"),
                      (r"lightcurve_czt\d*\.fits$", "hel1os_lc_czt"),
                      (r"lightcurve_cdte\d*\.fits$", "hel1os_lc_cdte"),
                      (r"_czt_spectra_czt\d*\.fits$", "hel1os_spec_czt"),
                      (r"_cdte_spectra_cdte\d*\.fits$", "hel1os_spec_cdte"),
                      (r"^hk\.fits$", "hel1os_housekeeping"),
                      (r"^gticdte\d*\.fits$", "hel1os_gti_cdte"),
                      (r"^gticzt\d*\.fits$", "hel1os_gti_czt"),
                      (r"dispix\.txt$", "hel1os_pixmap"), (r"\.png$", "png")):
        if re.search(pat, b):
            return name
    return f"OTHER:{os.path.splitext(b)[1] or b}"
pt = defaultdict(lambda: [0, 0.0])
for m in mem:
    k = ptype(m["member"])
    pt[k][0] += 1
    pt[k][1] += m["size_bytes"] / 1e9
R["product_types"] = {k: {"n": v[0], "GB": round(v[1], 3)} for k, v in sorted(pt.items())}

# ── 4. coverage (dates parsed from archive stems) ────────────────────────────
def stem_date(stem):
    m = re.search(r"(20\d{6})", stem)
    return m.group(1) if m else None
cov = defaultdict(set)
undated = []
for m in man:
    d = stem_date(m["stem"])
    if d is None:
        undated.append(m["stem"])
    elif m["status"] == "EXTRACTED":
        cov[m["instrument"]].add(d)
R["undated_archives"] = undated
R["coverage"] = {}
for k, ds in cov.items():
    sd = sorted(ds)
    R["coverage"][k] = {"unique_days": len(sd), "first": sd[0], "last": sd[-1]}

# monthly summary
monthly = defaultdict(lambda: defaultdict(int))
for k, ds in cov.items():
    for d in ds:
        monthly[d[:6]][k] += 1
R["monthly_coverage"] = {mo: dict(v) for mo, v in sorted(monthly.items())}

# missing days per instrument across its own span
R["missing_days"] = {}
for k, ds in cov.items():
    sd = sorted(ds)
    d0 = date(int(sd[0][:4]), int(sd[0][4:6]), int(sd[0][6:]))
    d1 = date(int(sd[-1][:4]), int(sd[-1][4:6]), int(sd[-1][6:]))
    allc = {(d0 + timedelta(days=i)).strftime("%Y%m%d") for i in range((d1 - d0).days + 1)}
    miss = sorted(allc - ds)
    gaps, run = [], []
    for d in miss:
        if run and (date(int(d[:4]), int(d[4:6]), int(d[6:])) -
                    date(int(run[-1][:4]), int(run[-1][4:6]), int(run[-1][6:]))).days == 1:
            run.append(d)
        else:
            if run: gaps.append((run[0], run[-1], len(run)))
            run = [d]
    if run: gaps.append((run[0], run[-1], len(run)))
    R["missing_days"][k] = {"n_missing": len(miss), "span_days": len(allc),
                            "largest_gaps": sorted(gaps, key=lambda g: -g[2])[:5]}

# ── 5. duplicates ────────────────────────────────────────────────────────────
by_sha = defaultdict(list)
for m in man:
    if m["sha256"]:
        by_sha[m["sha256"]].append(m["archive"])
R["duplicate_archives_identical_content"] = {k: v for k, v in by_sha.items() if len(v) > 1}
by_date = defaultdict(list)
for m in man:
    d = stem_date(m["stem"])
    if d:
        by_date[(m["instrument"], d)].append(os.path.basename(m["archive"]))
R["duplicate_dates"] = {f"{k[0]}:{k[1]}": v for k, v in by_date.items() if len(v) > 1}

# member-level duplicate content (same sha, different archives)
mem_sha = defaultdict(set)
for m in mem:
    mem_sha[m["sha256"]].add(m["archive_stem"])
R["member_sha_shared_across_archives"] = sum(1 for v in mem_sha.values() if len(v) > 1)

# ── 6. structural consistency (falsification: do archives match expectation?) ─
struct = defaultdict(list)
for m in mem:
    struct[m["archive_stem"]].append(ptype(m["member"]))
sol_prof, hel_prof = Counter(), Counter()
for m in man:
    if m["status"] != "EXTRACTED":
        continue
    prof = tuple(sorted(Counter(struct[m["stem"]]).items()))
    (sol_prof if m["instrument"] == "solexs" else hel_prof)[prof] += 1
R["solexs_structure_profiles"] = [{"n_archives": c, "profile": dict(p)}
                                  for p, c in sol_prof.most_common()]
R["hel1os_structure_profiles"] = [{"n_archives": c, "profile": dict(p)}
                                  for p, c in hel_prof.most_common(6)]
R["hel1os_n_distinct_profiles"] = len(hel_prof)

# zero-byte / suspicious members
R["zero_byte_members"] = [m["member"] for m in mem if m["size_bytes"] == 0][:20]
R["n_zero_byte_members"] = sum(1 for m in mem if m["size_bytes"] == 0)

# ── 7. corrupted-dir inventory (v1 left a downloads/corrupted dir) ───────────
cor = glob.glob("data_pipeline/downloads/corrupted/**/*", recursive=True)
cor_f = [c for c in cor if os.path.isfile(c)]
R["corrupted_dir"] = {"n_files": len(cor_f),
                      "GB": round(sum(os.path.getsize(c) for c in cor_f) / 1e9, 3),
                      "examples": [os.path.basename(c) for c in cor_f[:5]]}

json.dump(R, open(f"{OUT}/analysis.json", "w"), indent=1, default=str)

# ── console summary ──────────────────────────────────────────────────────────
print("=== STATUS ===", R["status_counts"], R["integrity_counts"])
print("=== STORAGE ===", R["storage"])
print("=== INSTRUMENTS ===", json.dumps(R["instrument_inventory"], indent=1))
print("=== PRODUCT TYPES ===", json.dumps(R["product_types"], indent=1))
print("=== COVERAGE ===", json.dumps(R["coverage"], indent=1))
print("=== MISSING ===", json.dumps(R["missing_days"], indent=1, default=str))
print("=== DUP DATES ===", json.dumps(R["duplicate_dates"], indent=1))
print("=== DUP CONTENT ===", len(R["duplicate_archives_identical_content"]), "sha groups")
print("=== SOLEXS STRUCT ===", json.dumps(R["solexs_structure_profiles"], indent=1))
print("=== HEL1OS STRUCT (top) ===", json.dumps(R["hel1os_structure_profiles"][:3], indent=1),
      "| distinct profiles:", R["hel1os_n_distinct_profiles"])
print("=== ZERO-BYTE MEMBERS ===", R["n_zero_byte_members"])
print("=== CORRUPTED DIR ===", R["corrupted_dir"])
print("=== UNDATED ===", R["undated_archives"][:5])
print("=== MONTHLY ===", json.dumps(R["monthly_coverage"], indent=1))
