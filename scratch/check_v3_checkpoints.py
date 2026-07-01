import torch
import os
import re

paths = [
    "artifacts/sprint14b/checkpoints/model_seed_42_best_tss.pt",
    "artifacts/sprint14b/checkpoints/stage1_seed_42_pretrained.pt",
]
for path in paths:
    if not os.path.exists(path):
        print(f"NOT FOUND: {path}")
        continue
    ck = torch.load(path, map_location="cpu", weights_only=True)
    state = ck.get("model_state_dict", ck.get("model", ck)) if isinstance(ck, dict) else ck
    total = sum(p.numel() for p in state.values() if hasattr(p, "numel"))
    print(f"\n{path}:")
    print(f"  PARAMETER_COUNT: {total:,}")
    if isinstance(ck, dict):
        keys = list(ck.keys())
        print(f"  CHECKPOINT_KEYS (count={len(keys)}): {keys[:15]}...")
    else:
        print("  CHECKPOINT_KEYS: raw_state_dict")
    print(f"  FIRST_10_LAYER_NAMES: {sorted(state.keys())[:10]}")
    
    layer_nums = set()
    for k in state.keys():
        m = re.findall(r'\.(\d+)\.', k)
        for n in m:
            layer_nums.add(int(n))
    if layer_nums:
        print(f"  MAX_LAYER_INDEX_FOUND: {max(layer_nums)}")
        print(f"  ALL_LAYER_INDICES: {sorted(layer_nums)}")
