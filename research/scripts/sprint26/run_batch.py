"""
scripts/sprint26/run_batch.py

Launch a batch of Sprint 26 training runs in parallel (each a subprocess),
wait for all, and report per-run exit status. Config list is a JSON file:
[{"run_id":"B0_s42","seed":42,"flags":["--alpha","0.25", ...]}, ...]
"""
import json, subprocess, sys, os, time
os.chdir("/Volumes/T7 Shield/Projects/AI/AdityaNet")
PY = "./venv/bin/python"
LOGDIR = "artifacts/sprint26/logs"; os.makedirs(LOGDIR, exist_ok=True)

cfgs = json.load(open(sys.argv[1]))
procs = []
for c in cfgs:
    cmd = [PY, "scripts/sprint26/train_driver.py", "--run-id", c["run_id"],
           "--seed", str(c["seed"]), "--num-workers", "1"] + c.get("flags", [])
    log = open(os.path.join(LOGDIR, c["run_id"] + ".log"), "w")
    procs.append((c["run_id"], subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT), log))
    print(f"launched {c['run_id']} (pid {procs[-1][1].pid})", flush=True)

t0 = time.time()
status = {}
for rid, p, log in procs:
    rc = p.wait(); log.close(); status[rid] = rc
    print(f"[{rid}] exit={rc} ({time.time()-t0:.0f}s elapsed)", flush=True)
json.dump(status, open(sys.argv[1].replace(".json", "_status.json"), "w"), indent=1)
print("BATCH COMPLETE:", status, flush=True)
