import json
import os

with open("/Users/soumyadebtripathy/AdityaNet/scratch/detailed_audit_results.json") as f:
    audit_results = json.load(f)

# Structure the final JSON
final_json = {}

# Help function to format column lists
def get_columns_info(hdu):
    return {
        "numerical_columns": hdu["numerical_columns"],
        "varying_columns": hdu["varying_columns"],
        "constant_columns": hdu["constant_columns"],
        "can_aggregate_1min": hdu["can_agg_1m"],
        "can_aggregate_5min": hdu["can_agg_5m"],
        "can_join_goes": hdu["can_join_goes"]
    }

# HEL1OS Lightcurves
for k in ["hel1os_czt1_lightcurve", "hel1os_czt2_lightcurve", "hel1os_cdte1_lightcurve", "hel1os_cdte2_lightcurve"]:
    prod = audit_results[k]
    hdus_info = {}
    total_features = 0
    for hdu in prod["hdus"]:
        # Exclude MJD from scientific features
        scientific_varying_numerical = [c for c in hdu["numerical_columns"] if c in hdu["varying_columns"] and c not in ["MJD", "ISOT"]]
        hdu_features = len(scientific_varying_numerical)
        total_features += hdu_features
        hdus_info[hdu["hdu_name"]] = {
            "columns": hdu["columns"],
            "numerical_varying": scientific_varying_numerical,
            "details": get_columns_info(hdu),
            "candidate_features_count": hdu_features
        }
    final_json[k] = {
        "file_path": prod["file"],
        "product_type": "lightcurve",
        "hdus": hdus_info,
        "total_candidate_features": total_features,
        "description": "HEL1OS lightcurves with 5 energy band extensions. Features represent count rate (CTR) and error (STAT_ERR) per band."
    }

# SoLEXS SDD2 Lightcurve
slx_lc = audit_results["solexs_sdd2_lightcurve"]
hdu = slx_lc["hdus"][0]
varying_num = [c for c in hdu["numerical_columns"] if c in hdu["varying_columns"] and c not in ["TIME"]]
final_json["solexs_sdd2_lightcurve"] = {
    "file_path": slx_lc["file"],
    "product_type": "lightcurve",
    "hdus": {
        hdu["hdu_name"]: {
            "columns": hdu["columns"],
            "numerical_varying": varying_num,
            "details": get_columns_info(hdu),
            "candidate_features_count": len(varying_num)
        }
    },
    "total_candidate_features": len(varying_num),
    "description": "SoLEXS SDD2 lightcurve at 1-second cadence. Single varying feature is COUNTS."
}

# SoLEXS SDD1 Lightcurve
final_json["solexs_sdd1_lightcurve"] = {
    "file_path": None,
    "product_type": "lightcurve",
    "hdus": {},
    "total_candidate_features": 0,
    "description": "No SDD1 lightcurve (.lc.gz) files exist in the telemetry archive."
}

# Spectra products
spec_analysis = audit_results["special_spectra_analysis"]
for k in ["hel1os_czt_spectra", "hel1os_cdte_spectra", "solexs_sdd2_spectra"]:
    prod = audit_results[k]
    hdu = prod["hdus"][0]
    info = spec_analysis[k]
    
    n_chans = info["n_channels"]
    varying_num = [c for c in hdu["numerical_columns"] if c in hdu["varying_columns"]]
    
    total_features = 0
    sc_var = []
    for c in varying_num:
        if c in ["COUNTS", "STAT_ERR"]:
            total_features += n_chans
            sc_var.append(f"{c}_channel_0..{n_chans-1}")
        else:
            total_features += 1
            sc_var.append(c)
            
    final_json[k] = {
        "file_path": prod["file"],
        "product_type": "spectra",
        "hdus": {
            hdu["hdu_name"]: {
                "columns": hdu["columns"],
                "numerical_varying": sc_var,
                "details": get_columns_info(hdu),
                "spectral_channels": n_chans,
                "counts_stats_per_bin": info["counts_stats_per_bin"],
                "energy_bins": "derived from channel index 0..{}".format(n_chans - 1),
                "candidate_features_count": total_features
            }
        },
        "total_candidate_features": total_features,
        "description": "Spectra product. Features can be constructed by treating each spectral channel's count rate as an independent feature."
    }

# Event products
evt_analysis = audit_results["special_events_analysis"]
prod = audit_results["hel1os_events"]
hdus_info = {}
total_features = 0
for hdu in prod["hdus"]:
    info = evt_analysis[hdu["hdu_name"]]
    hdu_features = len(info["photon_counts_per_energy_band"])
    if info["unique_pixels_count"] > 0:
        hdu_features += info["unique_pixels_count"]
    total_features += hdu_features
    
    varying_num = [c for c in hdu["numerical_columns"] if c in hdu["varying_columns"] and c not in ["mjd", "hlsobt", "recnum"]]
    
    hdus_info[hdu["hdu_name"]] = {
        "columns": hdu["columns"],
        "numerical_varying": varying_num,
        "details": get_columns_info(hdu),
        "detector_id": info["detector_id"],
        "event_energy_columns": [info["energy_col"]],
        "pixel_ids_count": info["unique_pixels_count"],
        "pixel_ids_sample": info["pixel_ids_sample"],
        "photon_counts_per_minute_stats": info["photon_counts_per_minute_stats"],
        "photon_counts_per_energy_band": info["photon_counts_per_energy_band"],
        "candidate_features_count": hdu_features
    }
final_json["hel1os_events"] = {
    "file_path": prod["file"],
    "product_type": "event",
    "hdus": hdus_info,
    "total_candidate_features": total_features,
    "description": "Event list files. Candidate features represent photon count rates binned per energy band and per pixel (for CZT) per minute."
}

# HEL1OS Housekeeping
prod = audit_results["hel1os_housekeeping"]
hdu = prod["hdus"][0]
varying_num = [c for c in hdu["numerical_columns"] if c in hdu["varying_columns"] and c not in ["mjd"]]
final_json["hel1os_housekeeping"] = {
    "file_path": prod["file"],
    "product_type": "housekeeping",
    "hdus": {
        hdu["hdu_name"]: {
            "columns": hdu["columns"],
            "numerical_varying": varying_num,
            "details": get_columns_info(hdu),
            "candidate_features_count": len(varying_num)
        }
    },
    "total_candidate_features": len(varying_num),
    "description": "Housekeeping telemetry containing pointing, voltage, and temperature monitor values. Features are 1-minute averages of varying numerical parameters."
}

# GTI products
for k in ["hel1os_gti_czt1", "hel1os_gti_czt2", "hel1os_gti_cdte1", "hel1os_gti_cdte2", "solexs_sdd1_gti", "solexs_sdd2_gti"]:
    prod = audit_results[k]
    if prod["status"] == "missing_file":
        continue
    hdu = prod["hdus"][0]
    final_json[k] = {
        "file_path": prod["file"],
        "product_type": "gti",
        "hdus": {
            hdu["hdu_name"]: {
                "columns": hdu["columns"],
                "numerical_varying": [],
                "details": get_columns_info(hdu),
                "candidate_features_count": 0
            }
        },
        "total_candidate_features": 0,
        "description": "Good Time Interval files containing start/stop boundaries. Not a time series, 0 features."
    }

# Save formatted JSON
with open("/Users/soumyadebtripathy/AdityaNet/scratch/mission_feature_factory_audit.json", "w") as f:
    json.dump(final_json, f, indent=2)

# Build Markdown
md_lines = [
    "# Mission Feature Factory Audit Report",
    "",
    "## 1. Executive Summary",
    "This report provides a systematic audit of all telemetry products discovered in Sprint 10F-A. It contains facts and measured values only, without model discussions, evaluations, recommendations, or conclusions.",
    "",
    "## 2. Product Audits",
    ""
]

def format_col_list(cols):
    if not cols:
        return "None"
    return ", ".join(f"`{c}`" for c in cols)

for k in sorted(final_json.keys()):
    prod = final_json[k]
    md_lines.append(f"### {k}")
    md_lines.append(f"- **Product Type**: {prod['product_type']}")
    md_lines.append(f"- **File Path**: `{prod['file_path']}`")
    md_lines.append(f"- **Total Candidate Features**: {prod['total_candidate_features']}")
    md_lines.append(f"- **Description**: {prod['description']}")
    
    if prod["product_type"] == "gti" or not prod["hdus"]:
        if not prod["hdus"]:
            md_lines.append("- *No extensions or files found.*")
        else:
            for hdu_name, hdu in prod["hdus"].items():
                md_lines.append(f"  - **HDU**: `{hdu_name}`")
                md_lines.append(f"    - **Columns**: {format_col_list(hdu['columns'])}")
                details = hdu["details"]
                md_lines.append(f"    - **Numerical Columns**: {format_col_list(details['numerical_columns'])}")
                md_lines.append(f"    - **Constant Columns**: {format_col_list(details['constant_columns'])}")
                md_lines.append(f"    - **Varying Columns**: {format_col_list(details['varying_columns'])}")
                md_lines.append(f"    - **1-Min Aggregation**: {details['can_aggregate_1min']}")
                md_lines.append(f"    - **5-Min Aggregation**: {details['can_aggregate_5min']}")
                md_lines.append(f"    - **GOES Join**: {details['can_join_goes']}")
        md_lines.append("")
        continue
        
    for hdu_name, hdu in prod["hdus"].items():
        md_lines.append(f"  - **HDU**: `{hdu_name}`")
        md_lines.append(f"    - **Columns**: {format_col_list(hdu['columns'])}")
        details = hdu["details"]
        md_lines.append(f"    - **Numerical Columns**: {format_col_list(details['numerical_columns'])}")
        md_lines.append(f"    - **Constant Columns**: {format_col_list(details['constant_columns'])}")
        md_lines.append(f"    - **Varying Columns**: {format_col_list(details['varying_columns'])}")
        md_lines.append(f"    - **Numerical Varying Columns (Features)**: {format_col_list(hdu['numerical_varying'])}")
        md_lines.append(f"    - **1-Min Aggregation**: {details['can_aggregate_1min']}")
        md_lines.append(f"    - **5-Min Aggregation**: {details['can_aggregate_5min']}")
        md_lines.append(f"    - **GOES Join**: {details['can_join_goes']}")
        md_lines.append(f"    - **Candidate Features Count**: {hdu['candidate_features_count']}")
        
        if prod["product_type"] == "event":
            md_lines.append(f"    - **Detector ID**: `{hdu['detector_id']}`")
            md_lines.append(f"    - **Event Energy Columns**: {format_col_list(hdu['event_energy_columns'])}")
            md_lines.append(f"    - **Pixel IDs Count**: {hdu['pixel_ids_count']}")
            if hdu['pixel_ids_count'] > 0:
                md_lines.append(f"    - **Pixel IDs Sample**: {hdu['pixel_ids_sample']}")
            md_lines.append(f"    - **Photon Counts/Min Stats**: Mean={hdu['photon_counts_per_minute_stats']['mean']:.2f}, Std={hdu['photon_counts_per_minute_stats']['std']:.2f}, Min={hdu['photon_counts_per_minute_stats']['min']}, Max={hdu['photon_counts_per_minute_stats']['max']}, Total={hdu['photon_counts_per_minute_stats']['total']}")
            md_lines.append("    - **Photon Counts per Energy Band**:")
            for bname, bcount in hdu['photon_counts_per_energy_band'].items():
                md_lines.append(f"      - Band `{bname}` keV: {bcount} photons")
                
        if prod["product_type"] == "spectra":
            md_lines.append(f"    - **Spectral Channels**: {hdu['spectral_channels']}")
            md_lines.append(f"    - **Energy Bins**: {hdu['energy_bins']}")
            stats = hdu['counts_stats_per_bin']
            md_lines.append(f"    - **Counts per Bin Stats**: Mean={stats['mean']:.4f}, Std={stats['std']:.4f}, Min={stats['min']}, Max={stats['max']}, Total Sum={stats['sum']}")
            
    md_lines.append("")

# Summary table of features
md_lines.append("## 3. Summary of Obtainable Candidate Features")
md_lines.append("")
md_lines.append("| Telemetry Product | Product Type | Measured Cadence | GOES Join Feasibility | Varying Numerical Columns | Candidate Features Count |")
md_lines.append("| --- | --- | --- | --- | --- | --- |")

for k in sorted(final_json.keys()):
    prod = final_json[k]
    if not prod["hdus"]:
        md_lines.append(f"| {k} | {prod['product_type']} | N/A | False | None | 0 |")
        continue
    
    first_hdu = list(prod["hdus"].values())[0]
    
    # Get the computed cadence
    raw_prod = audit_results.get(k, {})
    raw_hdus = raw_prod.get("hdus", [])
    if raw_hdus:
        med_cad = raw_hdus[0].get("cadence_median_s")
    else:
        med_cad = None
        
    if med_cad is not None:
        if med_cad == 0.0:
            cadence_str = "Sub-second"
        else:
            cadence_str = f"{med_cad:.2f}s"
    else:
        cadence_str = "N/A"
        
    goes_join = "True" if first_hdu["details"]["can_join_goes"] else "False"
    varying_num_count = len(first_hdu["numerical_varying"])
    md_lines.append(f"| {k} | {prod['product_type']} | {cadence_str} | {goes_join} | {varying_num_count} cols | {prod['total_candidate_features']} |")

md_lines.append("")

with open("/Users/soumyadebtripathy/AdityaNet/scratch/mission_feature_factory_audit.md", "w") as f:
    f.write("\n".join(md_lines))

print("Regenerated Markdown successfully!")
