import torch
import torch.nn as nn

print(f"PyTorch version: {torch.__version__}")
print(f"MPS available: {torch.backends.mps.is_available()}")

if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("Testing MPS behavior...")
    
    # Check if we can instantiate GradScaler for CPU (as done in trainer_v3.py)
    try:
        scaler = torch.amp.GradScaler("cpu")
        print("✓ GradScaler('cpu') instantiated successfully.")
    except Exception as e:
        print(f"✗ GradScaler('cpu') failed: {e}")

    try:
        # Create a simple model and move to MPS
        model = nn.Linear(10, 1).to(device)
        x = torch.randn(2, 10).to(device)
        y = torch.randn(2, 1).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        
        # Test autocast device_type='cpu' with MPS tensors
        try:
            with torch.amp.autocast(device_type="cpu"):
                out = model(x)
                loss = nn.functional.mse_loss(out, y)
            print("✓ autocast(device_type='cpu') completed without crash for MPS tensors.")
        except Exception as e:
            print(f"✗ autocast(device_type='cpu') failed for MPS tensors: {e}")
            
        # Test backward and step with CPU scaler on MPS gradients
        try:
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            print("✓ Backward and scaler step completed successfully.")
        except Exception as e:
            print(f"✗ Backward or scaler step failed: {e}")
            
    except Exception as e:
        print(f"Overall test failed: {e}")
else:
    print("MPS is not available, skipping test.")
