import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
import yaml
from pathlib import Path
from tqdm import tqdm
import sys
import numpy as np

from torch.amp import autocast, GradScaler

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from models.ensemble import TrueSightEnsemble
from preprocessing.dataset import DeepfakeDataset

# Global variable for warmup steps (needed in train_epoch)
warmup_steps = 0
scheduler = None
config = None

# --- NEW MIXUP FUNCTION ---
def mixup_data(x, y, alpha=1.0, device='cuda'):
    '''Returns mixed inputs, pairs of targets, and lambda'''
    if alpha > 0:
        lam = np.random.beta(alpha, alpha)
    else:
        lam = 1

    batch_size = x.size()[0]
    index = torch.randperm(batch_size).to(device)

    mixed_x = lam * x + (1 - lam) * x[index, :]
    y_a, y_b = y, y[index]
    return mixed_x, y_a, y_b, lam

def mixup_criterion(criterion, pred, y_a, y_b, lam):
    return lam * criterion(pred, y_a) + (1 - lam) * criterion(pred, y_b)
# --- END MIXUP ---


def load_config(config_path=None):
    if config_path is None:
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / 'configs' / 'config.yaml'
    
    if not Path(config_path).exists():
        raise FileNotFoundError(
            f"Config file not found at: {config_path}\n"
            f"Current working directory: {Path.cwd()}"
        )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except UnicodeDecodeError:
        with open(config_path, 'r', encoding='latin-1') as f:
            return yaml.safe_load(f)

def create_dataloaders(config):
    train_dataset = DeepfakeDataset(
        data_root=config['paths']['data_root'],
        split='train',
        num_frames=config['training']['num_frames']
    )
    
    val_dataset = DeepfakeDataset(
        data_root=config['paths']['data_root'],
        split='val',
        num_frames=config['training']['num_frames']
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=config['training']['batch_size'],
        shuffle=True,
        num_workers=config['training']['num_workers'],
        pin_memory=config['training']['pin_memory'],
        drop_last=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=config['training']['batch_size'],
        shuffle=False,
        num_workers=config['training']['num_workers'],
        pin_memory=config['training']['pin_memory']
    )
    
    print(f"✅ Train: {len(train_dataset)} videos ({len(train_loader)} batches)")
    print(f"✅ Val: {len(val_dataset)} videos ({len(val_loader)} batches)")
    
    return train_loader, val_loader

def train_epoch(model, train_loader, criterion, optimizer, device, epoch, scaler, mixup_alpha):
    """Train for one epoch"""
    global warmup_steps, scheduler, config
    
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(train_loader, desc=f"Epoch {epoch}")
    for batch_idx, (videos, labels) in enumerate(pbar):
        videos = videos.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True).float().unsqueeze(1)
        
        optimizer.zero_grad()
        
        # --- APPLY MIXUP ---
        videos, targets_a, targets_b, lam = mixup_data(videos, labels, mixup_alpha, device)
        # --- END MIXUP ---
        
        # Forward pass
        with autocast('cuda'):
            logits = model(videos)
            loss = mixup_criterion(criterion, logits, targets_a, targets_b, lam)
        
        # Backward pass
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=config['training']['grad_clip'])
        scaler.step(optimizer)
        scaler.update()
        
        # Step scheduler per batch if using warmup
        if warmup_steps > 0:
            scheduler.step()
        
        # Calculate metrics
        running_loss += loss.item()
        with torch.no_grad():
            threshold = 0.5 # Using 0.5 threshold for accuracy calculation
            predictions = (torch.sigmoid(logits) > threshold).float()
            # Accuracy with mixup is tricky, we check against the dominant label
            correct += (lam * (predictions == targets_a).sum().item() +
                        (1 - lam) * (predictions == targets_b).sum().item())
            total += labels.size(0)
        
        # Update progress bar
        current_acc = 100. * correct / total
        pbar.set_postfix({
            'loss': f'{running_loss / (batch_idx + 1):.4f}',
            'acc': f'{current_acc:.2f}'
        })
    
    epoch_loss = running_loss / len(train_loader)
    epoch_acc = 100. * correct / total
    
    return epoch_loss, epoch_acc

@torch.no_grad()
def validate(model, val_loader, criterion, device):
    """Validate model (no mixup in validation)"""
    global config
    
    model.eval()
    val_loss = 0.0
    correct = 0
    total = 0
    
    for videos, labels in tqdm(val_loader, desc="Validating"):
        videos = videos.to(device)
        labels = labels.to(device).float().unsqueeze(1)
        
        logits = model(videos)
        loss = criterion(logits, labels)
        
        val_loss += loss.item()
        threshold = 0.5 # Using 0.5 threshold for accuracy calculation
        predictions = (torch.sigmoid(logits) > threshold).float()
        correct += (predictions == labels).sum().item()
        total += labels.size(0)
    
    val_loss /= len(val_loader)
    val_acc = 100. * correct / total
    
    return val_loss, val_acc

def main():
    global warmup_steps, scheduler, config
    
    print("="*70)
    print("TRUESIGHT TRAINING")
    print("="*70)
    
    config = load_config()
    
    scaler = GradScaler(enabled=config['training']['mixed_precision'])
    
    device = torch.device(config['training']['device'] if torch.cuda.is_available() else 'cpu')
    print(f"\n🖥️  Device: {device}")
    if torch.cuda.is_available():
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
        print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    Path(config['paths']['model_checkpoints']).mkdir(parents=True, exist_ok=True)
    Path(config['paths']['logs']).mkdir(parents=True, exist_ok=True)
    
    print("\n📊 Loading data...")
    train_loader, val_loader = create_dataloaders(config)
    
    print("\n🧠 Initializing model...")
    model = TrueSightEnsemble(config).to(device)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"   Parameters: {total_params:,} (~{total_params * 4 / 1024 / 1024:.2f} MB)")
    
    criterion = nn.BCEWithLogitsLoss()
    print("✓ Using standard BCEWithLogitsLoss (Mixup will handle smoothing)")
        
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config['training']['learning_rate'],
        weight_decay=config['training']['weight_decay']
    )
    
    # Warmup scheduler implementation
    def get_cosine_schedule_with_warmup(optimizer, num_warmup_steps, num_training_steps, min_lr=1e-6):
        """
        Creates a schedule with linear warmup and cosine decay.
        """
        def lr_lambda(current_step):
            if current_step < num_warmup_steps:
                # Linear warmup
                return float(current_step) / float(max(1, num_warmup_steps))
            # Cosine annealing after warmup
            progress = float(current_step - num_warmup_steps) / float(max(1, num_training_steps - num_warmup_steps))
            cosine_decay = 0.5 * (1.0 + np.cos(np.pi * progress))
            return max(min_lr / config['training']['learning_rate'], cosine_decay)
        
        return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    
    # Calculate total training steps
    steps_per_epoch = len(train_loader)
    total_training_steps = config['training']['num_epochs'] * steps_per_epoch
    warmup_steps = config['training'].get('warmup_epochs', 0) * steps_per_epoch
    
    # Create scheduler with warmup
    if warmup_steps > 0:
        scheduler = get_cosine_schedule_with_warmup(
            optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_training_steps,
            min_lr=config['training'].get('min_lr', 1e-6)
        )
        print(f"✓ Using Cosine Annealing with {config['training']['warmup_epochs']} epoch warmup")
    else:
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=config['training']['num_epochs'] * steps_per_epoch
        )
        print("✓ Using Cosine Annealing (no warmup)")
    
    writer = SummaryWriter(log_dir=config['paths']['logs'])
    
    # Get Mixup alpha from config
    mixup_alpha = config['training'].get('mixup_alpha', 0.0)
    if mixup_alpha > 0.0:
        print(f"✓ Using Mixup with alpha: {mixup_alpha}")
    else:
        print("✓ Not using Mixup")
    
    print(f"\nStarting training for {config['training']['num_epochs']} epochs...")
    best_val_acc = 0.0
    patience_counter = 0
    
    for epoch in range(1, config['training']['num_epochs'] + 1):
        print(f"\n{'='*70}")
        print(f"Epoch {epoch}/{config['training']['num_epochs']}")
        print(f"{'='*70}")
        
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, device, epoch, scaler, mixup_alpha
        )
        
        # Validate
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        
        # Step scheduler (only per epoch if NOT using warmup)
        if warmup_steps == 0:
            scheduler.step()
        
        # Log to TensorBoard
        writer.add_scalar('Loss/train', train_loss, epoch)
        writer.add_scalar('Loss/val', val_loss, epoch)
        writer.add_scalar('Accuracy/train', train_acc, epoch)
        writer.add_scalar('Accuracy/val', val_acc, epoch)
        writer.add_scalar('Learning_Rate', optimizer.param_groups[0]['lr'], epoch)
        
        # Print summary
        print(f"\n📊 Epoch {epoch} Summary:")
        print(f"   Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"   Val Loss:   {val_loss:.4f} | Val Acc:   {val_acc:.2f}%")
        print(f"   LR: {optimizer.param_groups[0]['lr']:.6f}")
        
        # Save checkpoint
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'train_loss': train_loss,
            'val_loss': val_loss,
            'val_acc': val_acc,
            'config': config
        }
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(
                checkpoint,
                Path(config['paths']['model_checkpoints']) / 'best_model.pth'
            )
            print(f"   ✅ Saved best model (Val Acc: {val_acc:.2f}%)")
            patience_counter = 0
        else:
            patience_counter += 1
        
        # Save periodic checkpoint every 5 epochs
        if epoch % 5 == 0:
            torch.save(
                checkpoint,
                Path(config['paths']['model_checkpoints']) / f'checkpoint_epoch{epoch}.pth'
            )
            print(f"   💾 Saved checkpoint")
        
        # Early stopping
        if patience_counter >= config['training']['early_stopping_patience']:
            print(f"\n⚠️  Early stopping triggered after {epoch} epochs")
            break
    
    writer.close()
    
    print(f"\n{'='*70}")
    print(f"✅ TRAINING COMPLETE!")
    print(f"   Best Validation Accuracy: {best_val_acc:.2f}%")
    print(f"   Model saved: {config['paths']['model_checkpoints']}/best_model.pth")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()