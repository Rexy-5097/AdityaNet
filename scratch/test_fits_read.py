import os
import json
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.time import Time

ROOT = "/Users/soumyadebtripathy/AdityaNet/data/aditya_l1/raw_extracted"

# Let's define one representative file path for each product type
representative_files = {
    "hel1os_czt1_lightcurve": "hel1os/2026/06/10/HLS_20260610_000012_43174sec_lev1_V111/czt/lightcurve_czt1.fits",
    "hel1os_czt2_lightcurve": "hel1os/2026/06/10/HLS_20260610_000012_43174sec_lev1_V111/czt/lightcurve_czt2.fits",
    "hel1os_cdte1_lightcurve": "hel1os/2026/06/10/HLS_20260610_000012_43174sec_lev1_V111/cdte/lightcurve_cdte1.fits",
    "hel1os_cdte2_lightcurve": "hel1os/2026/06/10/HLS_20260610_000012_43174sec_lev1_V111/cdte/lightcurve_cdte2.fits",
    "hel1os_czt_spectra": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/czt/hel1os_czt_spectra_czt1.fits",
    "hel1os_cdte_spectra": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/cdte/hel1os_cdte_spectra_cdte1.fits",
    "hel1os_events": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/events/evt.fits",
    "hel1os_gti_czt1": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/aux/gticzt1.fits",
    "hel1os_gti_czt2": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/aux/gticzt2.fits",
    "hel1os_gti_cdte1": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/aux/gticdte1.fits",
    "hel1os_gti_cdte2": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/aux/gticdte2.fits",
    "hel1os_housekeeping": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/aux/hk.fits",
    "solexs_sdd2_lightcurve": "solexs/AL1_SLX_L1_20260610_v1.0/SDD2/AL1_SOLEXS_20260610_SDD2_L1.lc.gz",
    "solexs_sdd2_spectra": "solexs/AL1_SLX_L1_20260610_v1.0/SDD2/AL1_SOLEXS_20260610_SDD2_L1.pi.gz",
    "solexs_sdd1_gti": "solexs/AL1_SLX_L1_20260610_v1.0/SDD1/AL1_SOLEXS_20260610_SDD1_L1.gti.gz",
    "solexs_sdd2_gti": "solexs/AL1_SLX_L1_20260610_v1.0/SDD2/AL1_SOLEXS_20260610_SDD2_L1.gti.gz"
}

for prod_name, rel_path in representative_files.items():
    abs_path = os.path.join(ROOT, rel_path)
    if not os.path.exists(abs_path):
        print(f"Path does not exist: {abs_path}")
        continue
    
    print(f"\n==================== {prod_name} ====================")
    print(f"File: {rel_path}")
    with fits.open(abs_path) as hdul:
        for idx in range(1, len(hdul)):
            hdu = hdul[idx]
            if hdu.data is None:
                continue
            print(f"HDU {idx}: {hdu.name}, Type: {type(hdu)}")
            print(f"  Rows: {len(hdu.data)}")
            colnames = hdu.data.names
            print(f"  Columns: {colnames}")
            for col in colnames:
                col_data = hdu.data[col]
                dtype = col_data.dtype
                shape = col_data.shape
                # check if varying or constant
                try:
                    # handle array columns like spectra counts
                    if len(shape) > 1:
                        # shape is (rows, elements)
                        # We check if values vary across rows
                        # We can check if any element differs across rows
                        # e.g., comparing row 0 with row 1, or computing std along row axis
                        varies = not np.all(col_data == col_data[0:1])
                    else:
                        if np.issubdtype(dtype, np.number):
                            valid = col_data[np.isfinite(col_data)]
                            if len(valid) == 0:
                                varies = False
                            else:
                                varies = np.nanstd(valid) > 0
                        else:
                            varies = len(np.unique(col_data)) > 1
                except Exception as e:
                    varies = f"error: {e}"
                print(f"    {col}: dtype={dtype}, shape={shape}, varies={varies}")
