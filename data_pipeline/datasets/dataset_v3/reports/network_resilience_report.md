# Network Resilience Report — Sprint DA-03C

**Generated:** 2026-06-18 15:48:12Z
**Pipeline:** `1.5.0-SprintDA03C`

## Transport Event Summary

| Metric | Value |
|---|---|
| Total transport events | 4 |
| Recovered automatically | 0 |
| Recovery success rate | 0.0% |
| BrokenPipe events | 0 |
| DNS failure events | 0 |
| ReadTimeout events | 0 |
| Total download retries | 4 |
| Average retries per file | 0.02 |

## Session Health

| Metric | Value |
|---|---|
| Session refreshes | 0 |
| Auth downtime (s) | 0.0 |
| Network interruptions | 4 |
| DNS failures | 0 |

## Acquisition Summary

| Metric | Value |
|---|---|
| Downloaded & verified | 175 |
| Skipped (pre-verified) | 216 |
| Still failed | 0 |
| Scientific coverage | 97.93% |
| Total elapsed | 5371.3s |

## DA-03C Hardening Applied

- BrokenPipe → TCP reset + HTTP Range resume (no session invalidation)
- ReadTimeout → Range resume, up to 8 retries
- DNS failure → 2/5/10/20/30s backoff, no session invalidation
- State machine: Healthy|NetworkInterrupted|TemporarilyUnavailable|Refreshing|Expired
- Auth failures ONLY on confirmed HTTP login redirects
- Worker isolation: per-worker consecutive failure counter
