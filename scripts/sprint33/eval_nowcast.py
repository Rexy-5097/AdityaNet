"""Sprint 33 feasibility — window-level nowcast eval (Aditya-only). Simplest
measure: infer on the nowcast test set, report ROC-AUC and best-threshold TSS
at window level. No episode/bootstrap machinery (nowcast semantics differ from
the forecast harness; a proper nowcast episode metric is deferred to Sprint 33
proper). Sealed: metrics written to disk, not printed."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np, torch
from sklearn.metrics import roc_auc_score
from app.services.ml.model import PatchTST
from app.services.ml.dataset import SolarFlareWindowDataset, make_eval_loader
from app.services.ml.metrics import find_best_threshold, compute_metrics

run_id, ck_path, feat, test_pq = sys.argv[1:5]
feats = json.load(open(feat))
ck = torch.load(ck_path, map_location="cpu", weights_only=True)
dev = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
m = PatchTST(n_features=len(feats)); m.load_state_dict(ck["model"]); m.to(dev).eval()
ds = SolarFlareWindowDataset(test_pq, feature_cols=feats, split_name=run_id + "_nc")
loader = make_eval_loader(ds, batch_size=512, num_workers=1, shuffle=False)
probs = []
with torch.no_grad():
    for X, _ in loader:
        probs.append(torch.sigmoid(m(X.to(dev))).squeeze(-1).cpu().numpy())
p = np.concatenate(probs).astype(np.float64); y = ds.get_labels().astype(np.int8)
auc = float(roc_auc_score(y, p))
thr, _ = find_best_threshold(y, p, metric="tss"); mm = compute_metrics(y, (p >= thr).astype(int))
out = {"run_id": run_id, "task": "nowcast", "n": int(len(y)), "pos": int(y.sum()),
       "roc_auc": round(auc, 4), "tss": round(mm["tss"], 4), "best_thr": round(float(thr), 4),
       "recall": round(mm.get("recall", 0), 4), "precision": round(mm.get("precision", 0), 4)}
rd = os.path.join("artifacts", "sprint33", "runs", run_id); os.makedirs(rd, exist_ok=True)
json.dump(out, open(os.path.join(rd, "nowcast_eval.json"), "w"), indent=1)
print(f"[{run_id}] nowcast sealed -> nowcast_eval.json", flush=True)
