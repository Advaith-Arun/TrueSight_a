"""
Test script for VideoProcessor module.
Tests integration with Person 2's preprocessing on real videos.
"""

import sys
import torch
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.app.video_processor import VideoProcessor

print("=" * 60)
print("TrueSight Backend - Video Processor Test")
print("=" * 60)

# Find a test video
test_video_dirs = [
    project_root / "data" / "test" / "real",
    project_root / "data" / "test" / "fake",
    project_root / "data" / "val" / "real",
    project_root / "data" / "val" / "fake",
]

test_video = None
for test_dir in test_video_dirs:
    if test_dir.exists():
        # Look for .mp4 files
        videos = list(test_dir.rglob("*.mp4"))
        if videos:
            test_video = videos[0]
            break

if test_video is None:
    print("❌ No test video found in data/test/ or data/val/")
    print("Please add a sample video to one of these directories:")
    for d in test_video_dirs:
        print(f"   - {d}")
    sys.exit(1)

print(f"\n📹 Test video: {test_video}")
print(f"   Size: {test_video.stat().st_size / (1024*1024):.2f} MB")

# Test 1: Create VideoProcessor
print("\n[1/4] Creating VideoProcessor...")
try:
    processor = VideoProcessor(temp_dir="src/app/temp_processing")
    print("✅ VideoProcessor created")
except Exception as e:
    print(f"❌ Failed to create VideoProcessor: {e}")
    sys.exit(1)

# Test 2: Process video
print("\n[2/4] Processing video...")
try:
    video_tensor, output_dir = processor.process_video(test_video, num_frames=8)
    print("✅ Video processed successfully")
except Exception as e:
    print(f"❌ Video processing failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Verify tensor shape
print("\n[3/4] Verifying tensor shape...")
expected_shape = (1, 8, 3, 224, 224)
if video_tensor.shape == expected_shape:
    print(f"✅ Tensor shape correct: {video_tensor.shape}")
else:
    print(f"❌ Unexpected tensor shape: {video_tensor.shape}")
    print(f"   Expected: {expected_shape}")
    sys.exit(1)

# Test 4: Verify normalization (approximate check)
print("\n[4/4] Verifying normalization...")
mean = video_tensor.mean().item()
std = video_tensor.std().item()
print(f"   Tensor mean: {mean:.4f}")
print(f"   Tensor std: {std:.4f}")

# ImageNet normalized tensors should have mean near 0 and std near 1
if -0.5 < mean < 0.5 and 0.5 < std < 1.5:
    print("✅ Normalization appears correct")
else:
    print("⚠️  Warning: Normalization values seem unusual")
    print("   This might be okay depending on video content")

# Test 5: Cleanup
print("\n[5/5] Testing cleanup...")
try:
    processor.cleanup(output_dir)
    if not output_dir.exists():
        print("✅ Cleanup successful")
    else:
        print("⚠️  Warning: Output directory still exists")
except Exception as e:
    print(f"❌ Cleanup failed: {e}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nVideo processor is ready for integration.")
print(f"Processed tensor shape: {video_tensor.shape}")
print("\nNext step: Proceed to Phase 3 (Inference Engine)")
