# Metrics: Performance

> **Owner:** Tech Lead | **Consumers:** `performance-reviewer` · All engineers
> **Update Frequency:** Per release · When performance changes significantly
> **Max Size:** ~800 tokens | **Cross-refs:** `standards/ui_ux.md` · `standards/api_design.md` · `metrics/quality.md`

---

## Purpose

Define measurable performance targets for every component type. Performance targets prevent "it feels fast" as a substitute for evidence.

**Rule:** If a metric has no target, it has no standard. Every target must be defined before measurement begins.

---

## How to Use This File

1. Identify which component categories apply to your project.
2. Set project-specific targets in the **Project Targets** column.
3. If no project-specific target is set, the Production Grade column is the default.
4. Measure against targets before every release (`checklists/release.md`).

---

## API Performance

| Metric | Definition | Minimum | Recommended | Production | Flagship | Method |
|--------|-----------|---------|-------------|------------|---------|--------|
| P50 latency | Median response time | < 500ms | < 200ms | < 100ms | < 50ms | Load test (k6, locust) |
| P95 latency | 95th percentile response | < 2000ms | < 500ms | < 200ms | < 100ms | Load test |
| P99 latency | 99th percentile response | < 5000ms | < 1000ms | < 500ms | < 200ms | Load test |
| Throughput | Requests per second | > 10 rps | > 100 rps | Project-defined | Project-defined | Load test |
| Error rate | % of 5xx responses | < 5% | < 1% | < 0.1% | < 0.01% | APM / logs |
| Availability | Uptime | > 95% | > 99% | > 99.9% | > 99.99% | Monitoring |
| Cold start | First request after idle | No limit | < 5s | < 2s | < 500ms | Timed deployment |

---

## Frontend / UI Performance (Core Web Vitals)

| Metric | Definition | Minimum | Recommended | Production | Flagship | Method |
|--------|-----------|---------|-------------|------------|---------|--------|
| LCP | Largest Contentful Paint | < 4.0s | < 2.5s | < 2.5s | < 1.5s | Lighthouse / CrUX |
| INP | Interaction to Next Paint | < 500ms | < 200ms | < 200ms | < 100ms | Lighthouse / CrUX |
| CLS | Cumulative Layout Shift | < 0.25 | < 0.1 | < 0.1 | < 0.05 | Lighthouse / CrUX |
| TTFB | Time to First Byte | < 1800ms | < 800ms | < 600ms | < 200ms | Lighthouse |
| Bundle size (JS, gzipped) | Total compressed JS | No limit | < 300KB | < 200KB | < 150KB | Build tool |

Measure on: simulated 4G throttle · Moto G4 class device (mobile baseline).

---

## ML / AI Performance

| Metric | Definition | Target | Method | Frequency |
|--------|-----------|--------|--------|----------|
| Inference latency (P50) | Median prediction time | Project-defined | Load test | Per release |
| Inference latency (P99) | 99th percentile | < 2× P50 | Load test | Per release |
| Batch throughput | Records per second | Project-defined | Benchmark run | Per release |
| GPU utilization | % of GPU capacity used | > 60% target utilization | nvidia-smi / profiler | During training |
| Memory usage (GPU) | Peak VRAM | ≤ device limit | nvidia-smi | During training |
| Training time | Full epoch duration | Project-defined | Experiment log | Per training run |
| Model size | Serialized artifact size | Project-defined | File size | Per release |

---

## System / Infrastructure

| Metric | Definition | Minimum | Production | Method |
|--------|-----------|---------|------------|--------|
| CPU usage (steady state) | CPU % during normal load | < 80% | < 60% | APM / metrics |
| Memory usage (steady state) | RAM % during normal load | < 85% | < 70% | APM / metrics |
| Startup time | Service ready after deploy | < 60s | < 10s | Deployment timer |
| Database query time (P95) | 95th percentile DB query | < 1000ms | < 100ms | DB query log |
| Background job latency | Time from enqueue to start | < 5min | < 30s | Job queue metrics |
| Disk I/O | Read/write throughput | Project-defined | Project-defined | OS metrics |

---

## Measurement Frequency

| Component | Measure When | Responsible |
|-----------|-------------|------------|
| API | Every load test · Pre-release | Tech Lead |
| Frontend | Every PR · Lighthouse CI | UI Lead |
| ML Inference | Per model release | ML Lead |
| Training | Per training run (experiment log) | ML Lead |
| Infrastructure | Continuous (monitoring) | DevOps / Tech Lead |

---

## Project Targets (Fill In Per Project)

| Metric | Project Target | Set By | Date |
|--------|--------------|--------|------|
| API P50 latency | [ms] | | |
| API availability | [%] | | |
| LCP | [s] | | |
| Inference P50 | [ms] | | |

---

*Performance targets that are not defined are not enforced.*
