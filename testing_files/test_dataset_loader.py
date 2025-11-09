#!/usr/bin/env python3
"""Test TrueSight dataset loader"""

import sys
import yaml
from pathlib import Path
import torch
from torch.utils.data import DataLoader

sys.path.append('src')
from preprocessing.dataset import DeepfakeDataset

def test_dataset_loader():
    print("="*70)
    print("TESTING TRUESIGHT DATASET LOADER")
    print("="*70)
    
    # Load config
    with open('configs/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"\n1️⃣  Configuration:")
    print(f"   Data root: {config['paths']['data_root']}")
    print(f"   Train CSV: {config['paths']['train_csv']}")
    print(f"   Num frames: {config['training']['num_frames']}")
    
    # Check paths exist
    print(f"\n2️⃣  Checking paths...")
    data_root = Path(config['paths']['data_root'])
    if not data_root.exists():
        print(f"   ❌ Data root not found: {data_root}")
        return False
    print(f"   ✅ Data root exists")
    
    for split in ['train', 'val', 'test']:
        csv_path = Path(config['paths'][f'{split}_csv'])
        split_dir = data_root / split
        
        if not csv_path.exists():
            print(f"   ❌ {split}.csv not found: {csv_path}")
            return False
        if not split_dir.exists():
            print(f"   ❌ {split}/ folder not found: {split_dir}")
            return False
        
        print(f"   ✅ {split}.csv and {split}/ folder exist")
    
    # Create datasets
    print(f"\n3️⃣  Creating datasets...")
    try:
        train_dataset = DeepfakeDataset(
            csv_path=config['paths']['train_csv'],
            data_root=config['paths']['data_root'],
            split='train',
            num_frames=config['training']['num_frames']
        )
        print(f"   ✅ Train dataset: {len(train_dataset)} videos")
        
        val_dataset = DeepfakeDataset(
            csv_path=config['paths']['val_csv'],
            data_root=config['paths']['data_root'],
            split='val',
            num_frames=config['training']['num_frames']
        )
        print(f"   ✅ Val dataset: {len(val_dataset)} videos")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Load sample
    print(f"\n4️⃣  Loading sample...")
    try:
        video, label = train_dataset[0]
        print(f"   ✅ Sample loaded")
        print(f"   - Shape: {video.shape}")
        print(f"   - Label: {label} ({'Real' if label == 0 else 'Fake'})")
        print(f"   - Range: [{video.min():.3f}, {video.max():.3f}]")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test DataLoader
    print(f"\n5️⃣  Testing DataLoader...")
    try:
        train_loader = DataLoader(
            train_dataset,
            batch_size=config['training']['batch_size'],
            shuffle=True,
            num_workers=0
        )
        
        for videos, labels in train_loader:
            print(f"   ✅ Batch loaded")
            print(f"   - Videos shape: {videos.shape}")
            print(f"   - Labels: {['Real' if l == 0 else 'Fake' for l in labels]}")
            break
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Label distribution
    print(f"\n6️⃣  Label distribution:")
    real = sum(1 for i in range(len(train_dataset)) 
               if train_dataset.get_label(train_dataset.video_ids[i]) == 0)
    fake = len(train_dataset) - real
    print(f"   Real: {real} ({real/len(train_dataset)*100:.1f}%)")
    print(f"   Fake: {fake} ({fake/len(train_dataset)*100:.1f}%)")
    
    print(f"\n{'='*70}")
    print("✅ ALL TESTS PASSED!")
    print("='*70}")
    return True

if __name__ == '__main__':
    success = test_dataset_loader()
    sys.exit(0 if success else 1)
