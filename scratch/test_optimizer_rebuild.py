import torch
import torch.nn as nn
import torch.optim as optim

class TinyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(5, 5)
        self.fc2 = nn.Linear(5, 1)

def main():
    print("Testing optimizer state preservation and scheduler reconstruction...")
    model = TinyModel()
    
    # Initially freeze fc2
    for p in model.fc2.parameters():
        p.requires_grad = False
        
    # Create optimizer
    trainable_params = list(filter(lambda p: p.requires_grad, model.parameters()))
    optimizer = optim.AdamW(trainable_params, lr=1e-3)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=10)
    
    # Run a dummy step to populate optimizer state
    x = torch.randn(2, 5)
    y = torch.randn(2, 1)
    
    out = model.fc1(x)
    loss = out.sum()
    loss.backward()
    optimizer.step()
    scheduler.step()
    
    # Check that fc1 parameters have optimizer state
    fc1_param = next(model.fc1.parameters())
    print(f"fc1 param state present before rebuild: {fc1_param in optimizer.state}")
    old_state = optimizer.state[fc1_param].copy()
    print(f"fc1 param step count: {old_state['step']}")
    
    # Now unfreeze fc2
    for p in model.fc2.parameters():
        p.requires_grad = True
        
    # Rebuild optimizer and preserve state
    new_trainable_params = list(filter(lambda p: p.requires_grad, model.parameters()))
    new_optimizer = optim.AdamW(new_trainable_params, lr=1e-3)
    
    for p in new_trainable_params:
        if p in optimizer.state:
            new_optimizer.state[p] = optimizer.state[p]
            
    # Check if state is preserved
    print(f"fc1 param state present after rebuild: {fc1_param in new_optimizer.state}")
    new_state = new_optimizer.state[fc1_param]
    print(f"fc1 param step count after rebuild: {new_state['step']}")
    assert torch.equal(new_state['exp_avg'], old_state['exp_avg']), "State mismatch!"
    print("✓ Optimizer state successfully preserved for active parameters.")
    
    # Rebuild scheduler at epoch 1
    current_epoch = 1
    # Initialize initial_lr for new optimizer groups to prevent KeyError
    for group in new_optimizer.param_groups:
        group.setdefault('initial_lr', 1e-3)
        
    new_scheduler = optim.lr_scheduler.CosineAnnealingLR(new_optimizer, T_max=10, last_epoch=current_epoch)
    print(f"New scheduler last_epoch: {new_scheduler.last_epoch}")
    print(f"New scheduler base LRs: {new_scheduler.base_lrs}")
    print(f"New scheduler current LR: {new_scheduler.get_last_lr()}")
    
    print("Test passed successfully!")

if __name__ == "__main__":
    main()
