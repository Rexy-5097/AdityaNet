# Future Roadmap (Post-v1)

This roadmap outlines future improvements scheduled for AgentOS in subsequent minor and major updates.

---

## 1. Upgrade Paths

### v1.1
- **Enhanced Cache Policies:** Integrate Redis or memory database caches to share execution plans across parallel runners.
- **Dynamic Routing Overrides:** Allow mapping routing patterns using glob regex rules instead of basenames.

### v1.2
- **Unified Telemetry:** Emit execution durations and token counts directly to Prometheus or Grafana.

---

## 2. Experimental Concepts (v2.0)

- **Loop Parallelization:** Run multiple refinement loops on independent branches concurrently, then merge results using consensus rules.
- **Self-Improving Policies:** Implement standard optimization modules that tune the routing and context budgets dynamically based on past run outcomes.
