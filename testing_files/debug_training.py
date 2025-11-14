"""
Debug script to verify training setup before running full training
Run: python testing_files/debug_training.py
"""

import sys
from pathlib import Path
import torch
import yaml
import numpy as np

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from preprocessing.dataset import DeepfakeDataset
from models.ensemble import TrueSightEnsemble
from torch.utils.data import DataLoader


def load_config():
    """Load configuration"""
    config_path = Path(__file__).parent.parent / 'configs' / 'config.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_1_data_loading():
    """Test 1: Data Loading"""
    print("\n" + "="*70)
    print("TEST 1: DATA LOADING")
    print("="*70)
    
    try:
        # Test train dataset
        print("\n📊 Testing TRAIN dataset...")
        train_ds = DeepfakeDataset('data_processed', 'train', 8)
        frames, label = train_ds[0]
        
        print(f"✅ Dataset loaded: {len(train_ds)} videos")
        print(f"✅ Frames shape: {frames.shape}")
        print(f"✅ Label: {label} (0=real, 1=fake)")
        print(f"✅ Frame range: [{frames.min():.3f}, {frames.max():.3f}]")
        print(f"   (Should be around [-2, +2] after normalization)")
        
        # Test val dataset
        print("\n📊 Testing VAL dataset...")
        val_ds = DeepfakeDataset('data_processed', 'val', 8)
        print(f"✅ Val dataset: {len(val_ds)} videos")
        
        # Check class balance
        train_labels = [train_ds.labels[i] for i in range(len(train_ds))]
        num_real = train_labels.count(0)
        num_fake = train_labels.count(1)
        print(f"\n📊 Class balance:")
        print(f"   Real: {num_real} ({100*num_real/len(train_ds):.1f}%)")
        print(f"   Fake: {num_fake} ({100*num_fake/len(train_ds):.1f}%)")
        
        if abs(num_real - num_fake) > 100:
            print("   ⚠️  WARNING: Significant class imbalance detected")
        else:
            print("   ✅ Class balance looks good")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_2_model_initialization():
    """Test 2: Model Initialization"""
    print("\n" + "="*70)
    print("TEST 2: MODEL INITIALIZATION")
    print("="*70)
    
    try:
        config = load_config()
        
        print("\n🧠 Initializing model...")
        model = TrueSightEnsemble(config).cuda()
        
        # Count parameters
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        
        print(f"✅ Model initialized successfully")
        print(f"✅ Total parameters: {total_params:,}")
        print(f"✅ Trainable parameters: {trainable_params:,}")
        print(f"✅ Model size: {total_params * 4 / (1024**2):.1f} MB")
        
        # Test forward pass
        print("\n🔍 Testing forward pass...")
        test_input = torch.randn(2, 8, 3, 224, 224).cuda()
        output = model(test_input)
        
        print(f"✅ Input shape: {test_input.shape}")
        print(f"✅ Output shape: {output.shape}")
        
        if output.shape != (2, 1):
            print(f"❌ WARNING: Expected output shape (2, 1), got {output.shape}")
            return False
        
        print(f"✅ Output range: [{output.min():.3f}, {output.max():.3f}]")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_3_loss_function():
    """Test 3: Loss Function"""
    print("\n" + "="*70)
    print("TEST 3: LOSS FUNCTION")
    print("="*70)
    
    try:
        print("\n🔍 Testing BCE Loss...")
        criterion = torch.nn.BCEWithLogitsLoss()
        
        # Test case 1: Perfect predictions
        logits = torch.tensor([[5.0], [-5.0]])  # High confidence
        labels = torch.tensor([[1.0], [0.0]])   # Correct labels
        loss = criterion(logits, labels)
        
        print(f"✅ Test 1 - Perfect predictions:")
        print(f"   Loss: {loss.item():.4f} (should be low, ~0.01)")
        
        # Test case 2: Random predictions
        logits = torch.randn(4, 1)
        labels = torch.randint(0, 2, (4, 1)).float()
        loss = criterion(logits, labels)
        
        print(f"✅ Test 2 - Random predictions:")
        print(f"   Loss: {loss.item():.4f} (should be ~0.6-0.7)")
        
        # Test case 3: Wrong predictions
        logits = torch.tensor([[5.0], [-5.0]])
        labels = torch.tensor([[0.0], [1.0]])  # Wrong labels
        loss = criterion(logits, labels)
        
        print(f"✅ Test 3 - Wrong predictions:")
        print(f"   Loss: {loss.item():.4f} (should be high, >5)")
        
        if loss.item() < 3.0:
            print("   ⚠️  WARNING: Loss seems too low for wrong predictions")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_dataloader():
    """Test 4: DataLoader"""
    print("\n" + "="*70)
    print("TEST 4: DATALOADER")
    print("="*70)
    
    try:
        config = load_config()
        
        print("\n📦 Creating DataLoader...")
        train_ds = DeepfakeDataset('data_processed', 'train', 8)
        train_loader = DataLoader(
            train_ds,
            batch_size=config['training']['batch_size'],
            shuffle=True,
            num_workers=2,
            pin_memory=True
        )
        
        print(f"✅ DataLoader created")
        print(f"✅ Batch size: {config['training']['batch_size']}")
        print(f"✅ Number of batches: {len(train_loader)}")
        
        # Test one batch
        print("\n🔍 Testing batch loading...")
        batch_videos, batch_labels = next(iter(train_loader))
        
        print(f"✅ Batch videos shape: {batch_videos.shape}")
        print(f"✅ Batch labels shape: {batch_labels.shape}")
        print(f"✅ Labels in batch: {batch_labels.numpy()}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_5_gpu_memory():
    """Test 5: GPU Memory"""
    print("\n" + "="*70)
    print("TEST 5: GPU MEMORY")
    print("="*70)
    
    try:
        if not torch.cuda.is_available():
            print("❌ CUDA not available")
            return False
        
        print(f"\n🖥️  GPU: {torch.cuda.get_device_name(0)}")
        
        # Get memory info
        total_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
        allocated = torch.cuda.memory_allocated(0) / 1024**3
        reserved = torch.cuda.memory_reserved(0) / 1024**3
        free = total_mem - allocated
        
        print(f"✅ Total memory: {total_mem:.2f} GB")
        print(f"✅ Allocated: {allocated:.2f} GB")
        print(f"✅ Reserved: {reserved:.2f} GB")
        print(f"✅ Free: {free:.2f} GB")
        
        if free < 2.0:
            print("⚠️  WARNING: Less than 2GB free memory")
            print("   Consider reducing batch_size")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_6_full_forward_pass():
    """Test 6: Full Forward Pass (Model + Loss)"""
    print("\n" + "="*70)
    print("TEST 6: FULL FORWARD PASS")
    print("="*70)
    
    try:
        config = load_config()
        
        print("\n🔍 Running full forward pass...")
        
        # Load model and data
        model = TrueSightEnsemble(config).cuda()
        train_ds = DeepfakeDataset('data_processed', 'train', 8)
        train_loader = DataLoader(train_ds, batch_size=2, shuffle=True)
        criterion = torch.nn.BCEWithLogitsLoss()
        
        # Get one batch
        videos, labels = next(iter(train_loader))
        videos = videos.cuda()
        labels = labels.cuda().float().unsqueeze(1)
        
        print(f"✅ Input shape: {videos.shape}")
        print(f"✅ Labels shape: {labels.shape}")
        
        # Forward pass
        with torch.no_grad():
            logits = model(videos)
            loss = criterion(logits, labels)
            predictions = (torch.sigmoid(logits) > 0.5).float()
            accuracy = (predictions == labels).float().mean().item()
        
        print(f"✅ Output shape: {logits.shape}")
        print(f"✅ Loss: {loss.item():.4f}")
        print(f"✅ Predictions: {predictions.squeeze().cpu().numpy()}")
        print(f"✅ Labels: {labels.squeeze().cpu().numpy()}")
        print(f"✅ Accuracy: {accuracy*100:.1f}%")
        
        if loss.item() < 0.01 or loss.item() > 10:
            print("⚠️  WARNING: Loss seems unusual")
            print("   Check if model/loss are working correctly")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("TRUESIGHT TRAINING DEBUG SUITE")
    print("="*70)
    
    tests = [
        ("Data Loading", test_1_data_loading),
        ("Model Initialization", test_2_model_initialization),
        ("Loss Function", test_3_loss_function),
        ("DataLoader", test_4_dataloader),
        ("GPU Memory", test_5_gpu_memory),
        ("Full Forward Pass", test_6_full_forward_pass),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR in {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED - READY TO TRAIN!")
        print("   Run: python src/training/train.py")
    else:
        print("❌ SOME TESTS FAILED - FIX ISSUES BEFORE TRAINING")
    print("="*70)
    
    return all_passed


if __name__ == '__main__':
    main()
