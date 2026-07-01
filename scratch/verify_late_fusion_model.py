import sys
import os
import time
import torch

# Add root directory to path to enable imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.model_v3 import LateFusionPatchTST

def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def run_verification():
    print("==================================================")
    print("LateFusionPatchTST Architecture Verification")
    print("==================================================")

    # Initialize model
    model = LateFusionPatchTST()
    model.eval()

    # 1. Count parameters
    params = count_parameters(model)
    print(f"Total trainable parameters: {params:,}")
    assert params < 5_000_000, f"Parameter count {params:,} exceeds 5M cap!"
    print("✓ Parameter budget assertion PASSED.")

    # Mock inputs
    batch_size = 8
    seq_len = 360
    
    x_goes = torch.randn(batch_size, seq_len, 14)
    x_solexs = torch.randn(batch_size, seq_len, 25)
    x_hel1os = torch.randn(batch_size, seq_len, 10)
    
    mask_solexs = torch.ones(batch_size, 1)
    mask_hel1os = torch.ones(batch_size, 1)
    
    # 2. Verify Scenario A: All present
    print("\nRunning Scenario A: All instruments present...")
    with torch.no_grad():
        out = model(x_goes, x_solexs, x_hel1os, mask_solexs, mask_hel1os)
    print(f"Output shape: {list(out.shape)}")
    assert out.shape == (batch_size, 1), f"Unexpected output shape: {out.shape}"
    print("✓ Scenario A shape PASSED.")

    # 3. Verify Scenario B: SoLEXS missing
    print("\nRunning Scenario B: SoLEXS missing...")
    mask_solexs_missing = torch.zeros(batch_size, 1)
    with torch.no_grad():
        out = model(x_goes, x_solexs, x_hel1os, mask_solexs_missing, mask_hel1os)
    print(f"Output shape: {list(out.shape)}")
    assert out.shape == (batch_size, 1), f"Unexpected output shape: {out.shape}"
    print("✓ Scenario B shape (masking) PASSED.")

    # 4. Verify Scenario C: SoLEXS None (raw missing stream)
    print("\nRunning Scenario C: SoLEXS input is None...")
    with torch.no_grad():
        out = model(x_goes, None, x_hel1os, None, mask_hel1os)
    print(f"Output shape: {list(out.shape)}")
    assert out.shape == (batch_size, 1), f"Unexpected output shape: {out.shape}"
    print("✓ Scenario C shape (None input) PASSED.")

    # 5. Verify Scenario D: Both SoLEXS and HEL1OS None (GOES-only fallback)
    print("\nRunning Scenario D: Both SoLEXS and HEL1OS inputs are None (GOES-only)...")
    with torch.no_grad():
        out = model(x_goes, None, None, None, None)
    print(f"Output shape: {list(out.shape)}")
    assert out.shape == (batch_size, 1), f"Unexpected output shape: {out.shape}"
    print("✓ Scenario D shape (Both None inputs) PASSED.")

    # 6. Latency test
    print("\nProfiling latency over 100 runs...")
    times = []
    # Warmup
    for _ in range(10):
        _ = model(x_goes, x_solexs, x_hel1os)
        
    for _ in range(100):
        t0 = time.perf_counter()
        _ = model(x_goes, x_solexs, x_hel1os)
        t1 = time.perf_counter()
        times.append(t1 - t0)
        
    mean_latency = sum(times) / len(times)
    print(f"Average latency per forward pass (batch={batch_size}): {mean_latency * 1000:.2f} ms")
    
    # Save validation metadata
    import json
    report = {
        "verification_status": "PASSED",
        "total_parameters": params,
        "parameter_cap": 5000000,
        "batch_size": batch_size,
        "average_latency_ms": mean_latency * 1000,
        "scenarios_passed": ["all_present", "solexs_masked", "solexs_none", "both_none_goes_only"]
    }
    
    os.makedirs("artifacts/sprint12a", exist_ok=True)
    with open("artifacts/sprint12a/integration_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print("\n✓ Integration report saved to artifacts/sprint12a/integration_report.json")

if __name__ == "__main__":
    run_verification()
