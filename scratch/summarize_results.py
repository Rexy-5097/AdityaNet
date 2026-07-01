import json

with open("/Users/soumyadebtripathy/AdityaNet/scratch/detailed_audit_results.json") as f:
    data = json.load(f)

for key in sorted(data.keys()):
    if key in ["special_events_analysis", "special_spectra_analysis"]:
        continue
    val = data[key]
    print(f"Product: {key}")
    if val["status"] == "missing_file":
        print(f"  Missing file: {val['file']}")
        continue
    
    print(f"  File: {val['file']}")
    for hdu in val["hdus"]:
        print(f"    HDU: {hdu['hdu_name']} (index {hdu['hdu_index']})")
        print(f"      Rows: {hdu['n_rows']}")
        print(f"      Columns: {hdu['columns']}")
        print(f"      Numerical: {hdu['numerical_columns']}")
        print(f"      Varying: {hdu['varying_columns']}")
        print(f"      Constant: {hdu['constant_columns']}")
        print(f"      Cadence median: {hdu['cadence_median_s']} s")
        print(f"      Can agg 1m: {hdu['can_agg_1m']}")
        print(f"      Can agg 5m: {hdu['can_agg_5m']}")
        print(f"      Can join GOES: {hdu['can_join_goes']} (overlap: {hdu['goes_overlap_info']})")

print("\n==================== SPECIAL EVENTS ANALYSIS ====================")
if "special_events_analysis" in data:
    for hdu_name, info in data["special_events_analysis"].items():
        print(f"HDU: {hdu_name}")
        print(f"  Detector: {info['detector_id']}")
        print(f"  Energy col: {info['energy_col']}")
        print(f"  Rows: {info['n_rows']}")
        print(f"  Unique pixels: {info['unique_pixels_count']}")
        print(f"  Photon counts/min stats: {info['photon_counts_per_minute_stats']}")
        print(f"  Photon counts per energy band: {info['photon_counts_per_energy_band']}")

print("\n==================== SPECIAL SPECTRA ANALYSIS ====================")
if "special_spectra_analysis" in data:
    for prod, info in data["special_spectra_analysis"].items():
        print(f"Product: {prod}")
        print(f"  N Channels: {info['n_channels']}")
        print(f"  Counts stats per bin: {info['counts_stats_per_bin']}")
        print(f"  Has EBounds: {info['has_ebounds']}")
