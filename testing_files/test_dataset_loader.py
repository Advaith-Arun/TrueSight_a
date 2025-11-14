# testing_files/test_dataset_loader.py
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from preprocessing.dataset import DeepfakeDataset
from torch.utils.data import DataLoader

def test_dataset():
    print("="*70)
    print("TESTING TRUESIGHT DATASET LOADER")
    print("="*70)
    
    # Test all splits
    for split in ['train', 'val', 'test']:
        print(f"\n{'='*70}")
        print(f"{split.upper()} SET")
        print(f"{'='*70}")
        
        try:
            dataset = DeepfakeDataset(
                data_root='data_processed',  # ← CHANGED
                split=split,
                num_frames=8
            )
            
            # Load one sample
            video, label = dataset[0]
            print(f"\n✅ Single sample test:")
            print(f"   Video shape: {video.shape}")
            print(f"   Label: {label} ({'Real' if label == 0 else 'Fake'})")
            
            # Test dataloader
            loader = DataLoader(dataset, batch_size=2, shuffle=True, num_workers=0)
            for videos, labels in loader:
                print(f"\n✅ DataLoader test:")
                print(f"   Batch shape: {videos.shape}")
                print(f"   Labels: {labels.tolist()}")
                print(f"   Decoded: {['Real' if l==0 else 'Fake' for l in labels]}")
                break
            
            print(f"\n📊 Statistics:")
            print(f"   Total videos: {len(dataset)}")
            print(f"   Real videos: {dataset.labels.count(0)}")
            print(f"   Fake videos: {dataset.labels.count(1)}")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED")
    print("="*70)

if __name__ == '__main__':
    test_dataset()
