"""
TrueSight Training Script
"""
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
import yaml
from pathlib import Path
from tqdm import tqdm
import sys

from torch.cuda.amp import autocast, GradScaler

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from models.ensemble import TrueSightEnsemble
from preprocessing.dataset import DeepfakeDataset


def load_config(config_path='configs/config.yaml'):
    """Load configuration"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def create_dataloaders(config):
    """Create train/val/test dataloaders"""
    
    train_dataset = DeepfakeDataset(
        csv_path=config['paths']['train_csv'],
        data_root=config['paths']['data_root'],
        split='train',
        num_frames=config['training']['num_frames']
    )
    
    val_dataset = DeepfakeDataset(
        csv_path=config['paths']['val_csv'],
        data_root=config['paths']['data_root'],
        split='val',
        num_frames=config['training']['num_frames']
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=config['training']['batch_size'],
        shuffle=True,
        num_workers=config['training'].get('num_workers', 4),
        pin_memory=config['training'].get('pin_memory', True),
        drop_last=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=config['training']['batch_size'],
        shuffle=False,
        num_workers=config['training'].get('num_workers', 4),
        pin_memory=config['training'].get('pin_memory', True)
    )
    
    print(f"✅ Train dataset: {len(train_dataset)} videos ({len(train_loader)} batches)")
    print(f"✅ Val dataset: {len(val_dataset)} videos ({len(val_loader)} batches)")
    
    return train_loader, val_loader


def train_epoch(model, train_loader, criterion, optimizer, device, epoch, scaler=None):
    """Train for one epoch with mixed precision"""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    pbar = tqdm(train_loader, desc=f"Epoch {epoch}")
    for batch_idx, (videos, labels) in enumerate(pbar):
        videos = videos.to(device)
        labels = labels.to(device).float().unsqueeze(1)
        
        optimizer.zero_grad()
        
        # Mixed precision forward pass
        with autocast():
            logits = model(videos)
            loss = criterion(logits, labels)
        
        # Mixed precision backward pass
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        scaler.step(optimizer)
        scaler.update()
        
        # Metrics
        running_loss += loss.item()
        with torch.no_grad():
            predictions = (torch.sigmoid(logits) > 0.5).float()
            correct += (predictions == labels).sum().item()
            total += labels.size(0)
        
        pbar.set_postfix({
            'loss': running_loss / (batch_idx + 1),
            'acc': 100. * correct / total
        })
    
    epoch_loss = running_loss / len(train_loader)
    epoch_acc = 100. * correct / total
    
    return epoch_loss, epoch_acc


@torch.no_grad()
def validate(model, val_loader, criterion, device):
    """Validate model"""
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
        predictions = (torch.sigmoid(logits) > 0.5).float()
        correct += (predictions == labels).sum().item()
        total += labels.size(0)
    
    val_loss /= len(val_loader)
    val_acc = 100. * correct / total
    
    return val_loss, val_acc


def main():
    print("="*70)
    print("TRUESIGHT TRAINING")
    print("="*70)
    
    # Load config
    config = load_config()

    scaler = GradScaler()
    
    # Setup device
    device = torch.device(config['training']['device'] if torch.cuda.is_available() else 'cpu')
    print(f"\n🖥️  Device: {device}")
    if torch.cuda.is_available():
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
        print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # Create directories
    Path(config['paths']['model_checkpoints']).mkdir(parents=True, exist_ok=True)
    Path(config['logging']['tensorboard_dir']).mkdir(parents=True, exist_ok=True)
    
    # Create dataloaders
    print("\n📊 Loading data...")
    train_loader, val_loader = create_dataloaders(config)
    
    # Initialize model
    print("\n🧠 Initializing model...")
    model = TrueSightEnsemble(config).to(device)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"   Parameters: {total_params:,} (~{total_params * 4 / 1024 / 1024:.2f} MB)")
    
    # Loss and optimizer
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config['training']['learning_rate'],
        weight_decay=config['training']['weight_decay']
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=config['training']['num_epochs']
    )
    
    # TensorBoard
    writer = SummaryWriter(log_dir=config['logging']['tensorboard_dir'])
    
    # Training loop
    print(f"\nStarting training for {config['training']['num_epochs']} epochs...")
    best_val_acc = 0.0
    patience_counter = 0
    
    for epoch in range(1, config['training']['num_epochs'] + 1):
        print(f"\n{'='*70}")
        print(f"Epoch {epoch}/{config['training']['num_epochs']}")
        print(f"{'='*70}")
        
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, device, epoch, scaler
        )
        
        # Validate
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        
        # Step scheduler
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
        
        # Save periodic checkpoint
        if epoch % config['logging']['save_interval'] == 0:
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
