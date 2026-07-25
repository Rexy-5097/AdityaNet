# Sprint DA-03D — Recovery Refresh Report

**Generated:** 2026-06-18 15:50:24Z  
**Pipeline:** `1.5.0-SprintDA03C`  
**Dataset:** `dataset_v3` | **Instrument:** HEL1OS  
**Final Result:** ✅ **COMPLETE — ALL PASSED**

---

## Protocol Comparison

| Parameter | Status |
|---|---|
| Cookie structure | UNCHANGED (`FGTServer` + `JSESSIONID×2` + `OAuth_Token_Request_State`) |
| Duplicate JSESSIONID | **PRESERVED** (2 keys, verbatim raw-header injection) |
| Base URL | UNCHANGED (`https://pradan1.issdc.gov.in`) |
| Download path | UNCHANGED (`/al1/protected/downloadData/hel1os/level1/`) |
| Keep-alive endpoint | UNCHANGED (`/al1/protected/payload.xhtml`) |
| Query parameter | UNCHANGED (`?hel1os`) |
| User-Agent | UNCHANGED (`Wget/1.21.1`) |
| Old session cookie MD5 | `de48ade8f746e4b5429dcf9c3ae9e416` (DA-03C, expired) |
| New session cookie MD5 | `dfba0cdf8ce50c73b353bab67b9e44f3` (DA-03D, fresh) |

> **No protocol changes required.** Only session token values rotated.

---

## Acquisition Summary

| Metric | Value |
|---|---|
| Total URLs in manifest | 391 |
| Pre-verified (DA-03C session, skipped) | **216** |
| Newly downloaded (DA-03D session) | **175** |
| **Total Verified** | **391 / 391** |
| Failed | **0** |
| Queued | **0** |

---

## Final Validation Results

| Check | Result |
|---|---|
| ZIP integrity sweep (391 archives) | ✅ **PASS — 0 failures** |
| ZIP signature (`PK\x03\x04`) | ✅ All valid |
| HTML responses stored as archives | ✅ None (0) |
| Missing files on disk | ✅ None (0) |
| SHA256 duplicates | ✅ None (all unique) |
| Disk vs manifest consistency | ✅ Perfect (0 discrepancies) |
| FITS metadata rows | 391 |
| Unique observation dates | 189 |
| Scientific date range | `20251207` → `20260617` |
| Scientific coverage | **97.93%** (189 observed / 193 expected days) |
| Downloader integrity assertions | ✅ **ALL PASSED** |

---

## DA-03C Transport Hardening — Live Evidence

One `ChunkedEncodingError` was recovered automatically during this run:

```
[W1] Transport ChunkedEncodingError for HLS_20260119_115959_43198sec_lev1_V111.zip
     at byte 1568210944. Retry 4/8
     TCP pool reset (auth headers preserved).
[W1] Resume HLS_20260119_115959_43198sec_lev1_V111.zip from byte 1568210944
[W1] Verified: HLS_20260119_115959_43198sec_lev1_V111.zip
```

**Result:** Zero data loss. Transport layer recovered automatically without auth invalidation.

| Transport metric | Value |
|---|---|
| Total retries (transport) | 4 |
| Network interruptions | 8 |
| Auth failures | **0** |
| DNS failures | **0** |
| Session refreshes needed | **0** |

---

## Session Cookie Audit

| Session | Cookie MD5 | Archives |
|---|---|---|
| DA-03C (original) | `de48ade8f746e4b5429dcf9c3ae9e416` | 216 |
| DA-03D (refresh) | `dfba0cdf8ce50c73b353bab67b9e44f3` | 175 |

---

## Assertion Results

```
ALL INTEGRITY ASSERTIONS PASSED
PASS
```

**Elapsed (DA-03D session):** 5371.3s (~89.5 minutes)
