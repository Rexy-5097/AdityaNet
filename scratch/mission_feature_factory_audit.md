# Mission Feature Factory Audit Report

## 1. Executive Summary
This report provides a systematic audit of all telemetry products discovered in Sprint 10F-A. It contains facts and measured values only, without model discussions, evaluations, recommendations, or conclusions.

## 2. Product Audits

### hel1os_cdte1_lightcurve
- **Product Type**: lightcurve
- **File Path**: `hel1os/2026/06/10/HLS_20260610_000012_43174sec_lev1_V111/cdte/lightcurve_cdte1.fits`
- **Total Candidate Features**: 10
- **Description**: HEL1OS lightcurves with 5 energy band extensions. Features represent count rate (CTR) and error (STAT_ERR) per band.
  - **HDU**: `CDTE1_LC_BAND_5.00KEV_TO_20.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CDTE1_LC_BAND_20.00KEV_TO_30.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CDTE1_LC_BAND_30.00KEV_TO_40.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CDTE1_LC_BAND_40.00KEV_TO_60.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CDTE1_LC_BAND_1.80KEV_TO_90.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2

### hel1os_cdte2_lightcurve
- **Product Type**: lightcurve
- **File Path**: `hel1os/2026/06/10/HLS_20260610_000012_43174sec_lev1_V111/cdte/lightcurve_cdte2.fits`
- **Total Candidate Features**: 10
- **Description**: HEL1OS lightcurves with 5 energy band extensions. Features represent count rate (CTR) and error (STAT_ERR) per band.
  - **HDU**: `CDTE2_LC_BAND_5.00KEV_TO_20.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CDTE2_LC_BAND_20.00KEV_TO_30.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CDTE2_LC_BAND_30.00KEV_TO_40.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CDTE2_LC_BAND_40.00KEV_TO_60.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CDTE2_LC_BAND_1.80KEV_TO_90.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2

### hel1os_cdte_spectra
- **Product Type**: spectra
- **File Path**: `hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/cdte/hel1os_cdte_spectra_cdte1.fits`
- **Total Candidate Features**: 1026
- **Description**: Spectra product. Features can be constructed by treating each spectral channel's count rate as an independent feature.
  - **HDU**: `SPECTRUM`
    - **Columns**: `SPEC_NUM`, `CHANNEL`, `COUNTS`, `STAT_ERR`, `ROWID`, `TSTART`, `TSTOP`, `EXPOSURE`
    - **Numerical Columns**: `SPEC_NUM`, `CHANNEL`, `COUNTS`, `STAT_ERR`, `TSTART`, `TSTOP`, `EXPOSURE`
    - **Constant Columns**: `CHANNEL`
    - **Varying Columns**: `SPEC_NUM`, `COUNTS`, `STAT_ERR`, `ROWID`, `TSTART`, `TSTOP`, `EXPOSURE`
    - **Numerical Varying Columns (Features)**: `SPEC_NUM`, `COUNTS_channel_0..510`, `STAT_ERR_channel_0..510`, `TSTART`, `TSTOP`, `EXPOSURE`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 1026
    - **Spectral Channels**: 511
    - **Energy Bins**: derived from channel index 0..510
    - **Counts per Bin Stats**: Mean=0.0098, Std=0.1041, Min=0.0, Max=5.0, Total Sum=10981.0

### hel1os_czt1_lightcurve
- **Product Type**: lightcurve
- **File Path**: `hel1os/2026/06/10/HLS_20260610_000012_43174sec_lev1_V111/czt/lightcurve_czt1.fits`
- **Total Candidate Features**: 10
- **Description**: HEL1OS lightcurves with 5 energy band extensions. Features represent count rate (CTR) and error (STAT_ERR) per band.
  - **HDU**: `CZT1_LC_BAND_20.00KEV_TO_40.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CZT1_LC_BAND_40.00KEV_TO_60.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CZT1_LC_BAND_60.00KEV_TO_80.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CZT1_LC_BAND_80.00KEV_TO_150.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CZT1_LC_BAND_18.00KEV_TO_160.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2

### hel1os_czt2_lightcurve
- **Product Type**: lightcurve
- **File Path**: `hel1os/2026/06/10/HLS_20260610_000012_43174sec_lev1_V111/czt/lightcurve_czt2.fits`
- **Total Candidate Features**: 10
- **Description**: HEL1OS lightcurves with 5 energy band extensions. Features represent count rate (CTR) and error (STAT_ERR) per band.
  - **HDU**: `CZT2_LC_BAND_20.00KEV_TO_40.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CZT2_LC_BAND_40.00KEV_TO_60.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CZT2_LC_BAND_60.00KEV_TO_80.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CZT2_LC_BAND_80.00KEV_TO_150.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2
  - **HDU**: `CZT2_LC_BAND_18.00KEV_TO_160.00KEV`
    - **Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Columns**: `MJD`, `CTR`, `STAT_ERR`
    - **Constant Columns**: None
    - **Varying Columns**: `MJD`, `ISOT`, `CTR`, `STAT_ERR`
    - **Numerical Varying Columns (Features)**: `CTR`, `STAT_ERR`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 2

### hel1os_czt_spectra
- **Product Type**: spectra
- **File Path**: `hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/czt/hel1os_czt_spectra_czt1.fits`
- **Total Candidate Features**: 686
- **Description**: Spectra product. Features can be constructed by treating each spectral channel's count rate as an independent feature.
  - **HDU**: `SPECTRUM`
    - **Columns**: `SPEC_NUM`, `CHANNEL`, `COUNTS`, `STAT_ERR`, `ROWID`, `TSTART`, `TSTOP`, `EXPOSURE`
    - **Numerical Columns**: `SPEC_NUM`, `CHANNEL`, `COUNTS`, `STAT_ERR`, `TSTART`, `TSTOP`, `EXPOSURE`
    - **Constant Columns**: `CHANNEL`
    - **Varying Columns**: `SPEC_NUM`, `COUNTS`, `STAT_ERR`, `ROWID`, `TSTART`, `TSTOP`, `EXPOSURE`
    - **Numerical Varying Columns (Features)**: `SPEC_NUM`, `COUNTS_channel_0..340`, `STAT_ERR_channel_0..340`, `TSTART`, `TSTOP`, `EXPOSURE`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 686
    - **Spectral Channels**: 341
    - **Energy Bins**: derived from channel index 0..340
    - **Counts per Bin Stats**: Mean=1.4420, Std=4.1685, Min=0.0, Max=79.0, Total Sum=1075897.0

### hel1os_events
- **Product Type**: event
- **File Path**: `hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/events/evt.fits`
- **Total Candidate Features**: 466
- **Description**: Event list files. Candidate features represent photon count rates binned per energy band and per pixel (for CZT) per minute.
  - **HDU**: `CDTE1-EVENTS`
    - **Columns**: `mjd`, `hlsobt`, `currtemp`, `chn`, `ener`, `recnum`, `utc-isot`
    - **Numerical Columns**: `mjd`, `hlsobt`, `currtemp`, `chn`, `ener`, `recnum`
    - **Constant Columns**: None
    - **Varying Columns**: `mjd`, `hlsobt`, `currtemp`, `chn`, `ener`, `recnum`, `utc-isot`
    - **Numerical Varying Columns (Features)**: `currtemp`, `chn`, `ener`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 5
    - **Detector ID**: `CDTE1`
    - **Event Energy Columns**: `ener`
    - **Pixel IDs Count**: 0
    - **Photon Counts/Min Stats**: Mean=15.06, Std=13.40, Min=1, Max=145, Total=11009
    - **Photon Counts per Energy Band**:
      - Band `5-20` keV: 4267 photons
      - Band `20-30` keV: 564 photons
      - Band `30-40` keV: 610 photons
      - Band `40-60` keV: 2729 photons
      - Band `1.8-90` keV: 10958 photons
  - **HDU**: `CDTE2-EVENTS`
    - **Columns**: `mjd`, `hlsobt`, `currtemp`, `chn`, `ener`, `recnum`, `utc-isot`
    - **Numerical Columns**: `mjd`, `hlsobt`, `currtemp`, `chn`, `ener`, `recnum`
    - **Constant Columns**: None
    - **Varying Columns**: `mjd`, `hlsobt`, `currtemp`, `chn`, `ener`, `recnum`, `utc-isot`
    - **Numerical Varying Columns (Features)**: `currtemp`, `chn`, `ener`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 5
    - **Detector ID**: `CDTE2`
    - **Event Energy Columns**: `ener`
    - **Pixel IDs Count**: 0
    - **Photon Counts/Min Stats**: Mean=28.31, Std=17.15, Min=4, Max=181, Total=20696
    - **Photon Counts per Energy Band**:
      - Band `5-20` keV: 9205 photons
      - Band `20-30` keV: 1258 photons
      - Band `30-40` keV: 1015 photons
      - Band `40-60` keV: 5978 photons
      - Band `1.8-90` keV: 20601 photons
  - **HDU**: `CZT1-EVENTS`
    - **Columns**: `mjd`, `hlsobt`, `currtemp`, `pix`, `chn`, `offsetchn`, `ener`, `recnum`, `utc-isot`
    - **Numerical Columns**: `mjd`, `hlsobt`, `currtemp`, `pix`, `chn`, `offsetchn`, `ener`, `recnum`
    - **Constant Columns**: `currtemp`
    - **Varying Columns**: `mjd`, `hlsobt`, `pix`, `chn`, `offsetchn`, `ener`, `recnum`, `utc-isot`
    - **Numerical Varying Columns (Features)**: `pix`, `chn`, `offsetchn`, `ener`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 214
    - **Detector ID**: `CZT1`
    - **Event Energy Columns**: `ener`
    - **Pixel IDs Count**: 209
    - **Pixel IDs Sample**: [1, 3, 4, 10, 11, 12, 14, 18, 19, 20]
    - **Photon Counts/Min Stats**: Mean=1823.40, Std=248.91, Min=346, Max=2624, Total=1332903
    - **Photon Counts per Energy Band**:
      - Band `20-40` keV: 557860 photons
      - Band `40-60` keV: 77518 photons
      - Band `60-80` keV: 66296 photons
      - Band `80-150` keV: 197191 photons
      - Band `18-160` keV: 1072961 photons
  - **HDU**: `CZT2-EVENTS`
    - **Columns**: `mjd`, `hlsobt`, `currtemp`, `pix`, `chn`, `offsetchn`, `ener`, `recnum`, `utc-isot`
    - **Numerical Columns**: `mjd`, `hlsobt`, `currtemp`, `pix`, `chn`, `offsetchn`, `ener`, `recnum`
    - **Constant Columns**: `currtemp`
    - **Varying Columns**: `mjd`, `hlsobt`, `pix`, `chn`, `offsetchn`, `ener`, `recnum`, `utc-isot`
    - **Numerical Varying Columns (Features)**: `pix`, `chn`, `offsetchn`, `ener`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 242
    - **Detector ID**: `CZT2`
    - **Event Energy Columns**: `ener`
    - **Pixel IDs Count**: 237
    - **Pixel IDs Sample**: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    - **Photon Counts/Min Stats**: Mean=1670.67, Std=240.36, Min=195, Max=2274, Total=1221259
    - **Photon Counts per Energy Band**:
      - Band `20-40` keV: 520292 photons
      - Band `40-60` keV: 116985 photons
      - Band `60-80` keV: 78260 photons
      - Band `80-150` keV: 237169 photons
      - Band `18-160` keV: 1022306 photons

### hel1os_gti_cdte1
- **Product Type**: gti
- **File Path**: `hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/aux/gticdte1.fits`
- **Total Candidate Features**: 0
- **Description**: Good Time Interval files containing start/stop boundaries. Not a time series, 0 features.
  - **HDU**: `GTI_CDTE1`
    - **Columns**: `tstart`, `tstop`
    - **Numerical Columns**: `tstart`, `tstop`
    - **Constant Columns**: `tstart`, `tstop`
    - **Varying Columns**: None
    - **1-Min Aggregation**: False
    - **5-Min Aggregation**: False
    - **GOES Join**: True

### hel1os_gti_cdte2
- **Product Type**: gti
- **File Path**: `hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/aux/gticdte2.fits`
- **Total Candidate Features**: 0
- **Description**: Good Time Interval files containing start/stop boundaries. Not a time series, 0 features.
  - **HDU**: `GTI_CDTE2`
    - **Columns**: `tstart`, `tstop`
    - **Numerical Columns**: `tstart`, `tstop`
    - **Constant Columns**: `tstart`, `tstop`
    - **Varying Columns**: None
    - **1-Min Aggregation**: False
    - **5-Min Aggregation**: False
    - **GOES Join**: True

### hel1os_gti_czt1
- **Product Type**: gti
- **File Path**: `hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/aux/gticzt1.fits`
- **Total Candidate Features**: 0
- **Description**: Good Time Interval files containing start/stop boundaries. Not a time series, 0 features.
  - **HDU**: `GTI_CZT1`
    - **Columns**: `tstart`, `tstop`
    - **Numerical Columns**: `tstart`, `tstop`
    - **Constant Columns**: `tstart`, `tstop`
    - **Varying Columns**: None
    - **1-Min Aggregation**: False
    - **5-Min Aggregation**: False
    - **GOES Join**: True

### hel1os_gti_czt2
- **Product Type**: gti
- **File Path**: `hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/aux/gticzt2.fits`
- **Total Candidate Features**: 0
- **Description**: Good Time Interval files containing start/stop boundaries. Not a time series, 0 features.
  - **HDU**: `GTI_CZT2`
    - **Columns**: `tstart`, `tstop`
    - **Numerical Columns**: `tstart`, `tstop`
    - **Constant Columns**: `tstart`, `tstop`
    - **Varying Columns**: None
    - **1-Min Aggregation**: False
    - **5-Min Aggregation**: False
    - **GOES Join**: True

### hel1os_housekeeping
- **Product Type**: housekeeping
- **File Path**: `hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/aux/hk.fits`
- **Total Candidate Features**: 37
- **Description**: Housekeeping telemetry containing pointing, voltage, and temperature monitor values. Features are 1-minute averages of varying numerical parameters.
  - **HDU**: `HLSHK`
    - **Columns**: `l0recnum`, `l0grtyr`, `l0grtmon`, `l0grtdy`, `l0grthr`, `l0grtmin`, `l0grtsc`, `l0grtmsc`, `l0utcyr`, `l0utcmon`, `l0utcdy`, `l0utchr`, `l0utcmin`, `l0utcsc`, `l0utcmsc`, `l0framecnt`, `l0dhobt`, `mjd`, `czt1temp`, `czt2temp`, `czt1bunpxst`, `czt2bunpxst`, `pagestim`, `cdte1ctr`, `pagenum`, `czt1ctr`, `czt1enth`, `czt2ctr`, `czt2enth`, `cdte2ctr`, `czt1pktm`, `czt2pktm`, `fehkstat`, `czt1hotpix`, `czt1hotpixcnt`, `czt1hotpixlgcstat`, `czt1hotpixthr`, `czt2hotpix`, `czt2hotpixcnt`, `czt2hotpixlgcstat`, `czt2hotpixthr`, `cdte1enerthr`, `cdte2enerthr`, `czthvmon`, `cdtehvmon`, `cdte1temp`, `cdte2temp`, `cdte1pilectr`, `cdte2pilectr`, `czt1satctr1`, `czt2satctr1`, `czt1bunpxctr`, `czt2bunpxctr`, `sunradeg`, `sundecdeg`, `suninfov`, `sun2yawdeg`, `sun2rolldeg`, `sun2pitchdeg`, `yawradeg`, `yawdecdeg`, `lastevtmjd`
    - **Numerical Columns**: `l0recnum`, `l0grtyr`, `l0grtmon`, `l0grtdy`, `l0grthr`, `l0grtmin`, `l0grtsc`, `l0grtmsc`, `l0utcyr`, `l0utcmon`, `l0utcdy`, `l0utchr`, `l0utcmin`, `l0utcsc`, `l0utcmsc`, `l0framecnt`, `l0dhobt`, `mjd`, `czt1temp`, `czt2temp`, `czt1bunpxst`, `czt2bunpxst`, `pagestim`, `cdte1ctr`, `pagenum`, `czt1ctr`, `czt1enth`, `czt2ctr`, `czt2enth`, `cdte2ctr`, `czt1pktm`, `czt2pktm`, `fehkstat`, `czt1hotpix`, `czt1hotpixcnt`, `czt1hotpixlgcstat`, `czt1hotpixthr`, `czt2hotpix`, `czt2hotpixcnt`, `czt2hotpixlgcstat`, `czt2hotpixthr`, `cdte1enerthr`, `cdte2enerthr`, `czthvmon`, `cdtehvmon`, `cdte1temp`, `cdte2temp`, `cdte1pilectr`, `cdte2pilectr`, `czt1satctr1`, `czt2satctr1`, `czt1bunpxctr`, `czt2bunpxctr`, `sunradeg`, `sundecdeg`, `suninfov`, `sun2yawdeg`, `sun2rolldeg`, `sun2pitchdeg`, `yawradeg`, `yawdecdeg`, `lastevtmjd`
    - **Constant Columns**: `l0grtyr`, `l0grtmon`, `l0grtdy`, `l0grthr`, `l0utcyr`, `l0utcmon`, `czt1temp`, `czt2temp`, `czt1bunpxst`, `czt2bunpxst`, `czt1enth`, `czt2enth`, `fehkstat`, `czt1hotpix`, `czt1hotpixcnt`, `czt1hotpixlgcstat`, `czt1hotpixthr`, `czt2hotpix`, `czt2hotpixcnt`, `czt2hotpixlgcstat`, `czt2hotpixthr`, `cdte1enerthr`, `cdte2enerthr`, `suninfov`
    - **Varying Columns**: `l0recnum`, `l0grtmin`, `l0grtsc`, `l0grtmsc`, `l0utcdy`, `l0utchr`, `l0utcmin`, `l0utcsc`, `l0utcmsc`, `l0framecnt`, `l0dhobt`, `mjd`, `pagestim`, `cdte1ctr`, `pagenum`, `czt1ctr`, `czt2ctr`, `cdte2ctr`, `czt1pktm`, `czt2pktm`, `czthvmon`, `cdtehvmon`, `cdte1temp`, `cdte2temp`, `cdte1pilectr`, `cdte2pilectr`, `czt1satctr1`, `czt2satctr1`, `czt1bunpxctr`, `czt2bunpxctr`, `sunradeg`, `sundecdeg`, `sun2yawdeg`, `sun2rolldeg`, `sun2pitchdeg`, `yawradeg`, `yawdecdeg`, `lastevtmjd`
    - **Numerical Varying Columns (Features)**: `l0recnum`, `l0grtmin`, `l0grtsc`, `l0grtmsc`, `l0utcdy`, `l0utchr`, `l0utcmin`, `l0utcsc`, `l0utcmsc`, `l0framecnt`, `l0dhobt`, `pagestim`, `cdte1ctr`, `pagenum`, `czt1ctr`, `czt2ctr`, `cdte2ctr`, `czt1pktm`, `czt2pktm`, `czthvmon`, `cdtehvmon`, `cdte1temp`, `cdte2temp`, `cdte1pilectr`, `cdte2pilectr`, `czt1satctr1`, `czt2satctr1`, `czt1bunpxctr`, `czt2bunpxctr`, `sunradeg`, `sundecdeg`, `sun2yawdeg`, `sun2rolldeg`, `sun2pitchdeg`, `yawradeg`, `yawdecdeg`, `lastevtmjd`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 37

### solexs_sdd1_gti
- **Product Type**: gti
- **File Path**: `solexs/AL1_SLX_L1_20260610_v1.0/SDD1/AL1_SOLEXS_20260610_SDD1_L1.gti.gz`
- **Total Candidate Features**: 0
- **Description**: Good Time Interval files containing start/stop boundaries. Not a time series, 0 features.
  - **HDU**: `GTI`
    - **Columns**: `START`, `STOP`
    - **Numerical Columns**: `START`, `STOP`
    - **Constant Columns**: `START`, `STOP`
    - **Varying Columns**: None
    - **1-Min Aggregation**: False
    - **5-Min Aggregation**: False
    - **GOES Join**: False

### solexs_sdd1_lightcurve
- **Product Type**: lightcurve
- **File Path**: `None`
- **Total Candidate Features**: 0
- **Description**: No SDD1 lightcurve (.lc.gz) files exist in the telemetry archive.
- *No extensions or files found.*

### solexs_sdd2_gti
- **Product Type**: gti
- **File Path**: `solexs/AL1_SLX_L1_20260610_v1.0/SDD2/AL1_SOLEXS_20260610_SDD2_L1.gti.gz`
- **Total Candidate Features**: 0
- **Description**: Good Time Interval files containing start/stop boundaries. Not a time series, 0 features.
  - **HDU**: `GTI`
    - **Columns**: `START`, `STOP`
    - **Numerical Columns**: `START`, `STOP`
    - **Constant Columns**: None
    - **Varying Columns**: `START`, `STOP`
    - **1-Min Aggregation**: False
    - **5-Min Aggregation**: False
    - **GOES Join**: True

### solexs_sdd2_lightcurve
- **Product Type**: lightcurve
- **File Path**: `solexs/AL1_SLX_L1_20260610_v1.0/SDD2/AL1_SOLEXS_20260610_SDD2_L1.lc.gz`
- **Total Candidate Features**: 1
- **Description**: SoLEXS SDD2 lightcurve at 1-second cadence. Single varying feature is COUNTS.
  - **HDU**: `RATE`
    - **Columns**: `TIME`, `COUNTS`
    - **Numerical Columns**: `TIME`, `COUNTS`
    - **Constant Columns**: None
    - **Varying Columns**: `TIME`, `COUNTS`
    - **Numerical Varying Columns (Features)**: `COUNTS`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 1

### solexs_sdd2_spectra
- **Product Type**: spectra
- **File Path**: `solexs/AL1_SLX_L1_20260610_v1.0/SDD2/AL1_SOLEXS_20260610_SDD2_L1.pi.gz`
- **Total Candidate Features**: 342
- **Description**: Spectra product. Features can be constructed by treating each spectral channel's count rate as an independent feature.
  - **HDU**: `SPECTRUM`
    - **Columns**: `TSTART`, `TELAPSE`, `SPEC_NUM`, `CHANNEL`, `COUNTS`, `EXPOSURE`
    - **Numerical Columns**: `TSTART`, `TELAPSE`, `SPEC_NUM`, `CHANNEL`, `COUNTS`, `EXPOSURE`
    - **Constant Columns**: `TELAPSE`, `CHANNEL`, `EXPOSURE`
    - **Varying Columns**: `TSTART`, `SPEC_NUM`, `COUNTS`
    - **Numerical Varying Columns (Features)**: `TSTART`, `SPEC_NUM`, `COUNTS_channel_0..339`
    - **1-Min Aggregation**: True
    - **5-Min Aggregation**: True
    - **GOES Join**: True
    - **Candidate Features Count**: 342
    - **Spectral Channels**: 340
    - **Energy Bins**: derived from channel index 0..339
    - **Counts per Bin Stats**: Mean=0.2935, Std=1.2972, Min=0.0, Max=34.0, Total Sum=8621419.0

## 3. Summary of Obtainable Candidate Features

| Telemetry Product | Product Type | Measured Cadence | GOES Join Feasibility | Varying Numerical Columns | Candidate Features Count |
| --- | --- | --- | --- | --- | --- |
| hel1os_cdte1_lightcurve | lightcurve | 1.00s | True | 2 cols | 10 |
| hel1os_cdte2_lightcurve | lightcurve | 1.00s | True | 2 cols | 10 |
| hel1os_cdte_spectra | spectra | 20.00s | True | 6 cols | 1026 |
| hel1os_czt1_lightcurve | lightcurve | 1.00s | True | 2 cols | 10 |
| hel1os_czt2_lightcurve | lightcurve | 1.00s | True | 2 cols | 10 |
| hel1os_czt_spectra | spectra | 20.00s | True | 6 cols | 686 |
| hel1os_events | event | Sub-second | True | 3 cols | 466 |
| hel1os_gti_cdte1 | gti | N/A | True | 0 cols | 0 |
| hel1os_gti_cdte2 | gti | N/A | True | 0 cols | 0 |
| hel1os_gti_czt1 | gti | N/A | True | 0 cols | 0 |
| hel1os_gti_czt2 | gti | N/A | True | 0 cols | 0 |
| hel1os_housekeeping | housekeeping | 7.91s | True | 37 cols | 37 |
| solexs_sdd1_gti | gti | N/A | False | 0 cols | 0 |
| solexs_sdd1_lightcurve | lightcurve | N/A | False | None | 0 |
| solexs_sdd2_gti | gti | 18640.00s | True | 0 cols | 0 |
| solexs_sdd2_lightcurve | lightcurve | 1.00s | True | 1 cols | 1 |
| solexs_sdd2_spectra | spectra | 1.00s | True | 3 cols | 342 |
