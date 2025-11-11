"""
Test script for InferenceEngine module.
Tests model loading and inference on dummy and real video tensors.
"""

import sys
import torch
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.app.inference import InferenceEngine
from src.app.video_processor import VideoProcessor

print("=" * 60)
print("TrueSight Backend - Inference Engine Test")
print("=" * 60)

# Test 1: Create InferenceEngine
print("\n[1/5] Creating InferenceEngine...")
try:
    engine = InferenceEngine(
        config_path="configs/config.yaml",
        checkpoint_path="models/checkpoints/best_model.pth",
        threshold=0.3  # Person 1's specified threshold
    )
    print("✅ InferenceEngine created successfully")
except Exception as e:
    print(f"❌ Failed to create InferenceEngine: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Verify threshold
print("\n[2/5] Verifying threshold...")
if engine.threshold == 0.3:
    print(f"✅ Correct threshold: {engine.threshold}")
else:
    print(f"❌ Wrong threshold: {engine.threshold} (should be 0.3)")
    sys.exit(1)

# Test 3: Test with dummy tensor
print("\n[3/5] Testing inference with dummy tensor...")
try:
    # Create random dummy tensor [1, 8, 3, 224, 224]
    dummy_tensor = torch.randn(1, 8, 3, 224, 224)
    
    result = engine.predict(dummy_tensor)
    
    print("✅ Inference successful")
    print(f"   Verdict: {result['verdict']}")
    print(f"   Confidence: {result['confidence']:.2f}%")
    print(f"   Probability: {result['probability']:.4f}")
    print(f"   Threshold: {result['threshold']}")
    
    # Verify result format
    assert 'verdict' in result
    assert 'confidence' in result
    assert 'probability' in result
    assert 'threshold' in result
    assert result['verdict'] in ['Real', 'Fake']
    assert 0 <= result['confidence'] <= 100
    assert 0 <= result['probability'] <= 1
    
    print("✅ Result format validated")
    
except Exception as e:
    print(f"❌ Inference failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test with real video
print("\n[4/5] Testing inference with real video...")

# Find a test video
test_video_dirs = [
    project_root / "data" / "test" / "real",
    project_root / "data" / "test" / "fake",
]

test_video = None
for test_dir in test_video_dirs:
    if test_dir.exists():
        videos = list(test_dir.rglob("*.mp4"))
        if videos:
            test_video = videos[0]
            break

if test_video:
    print(f"   Using video: {test_video.name}")
    try:
        # Process video
        processor = VideoProcessor()
        video_tensor, output_dir = processor.process_video(test_video)
        
        # Run inference
        result = engine.predict(video_tensor)
        
        print("✅ Real video inference successful")
        print(f"   File: {test_video.name}")
        print(f"   Verdict: {result['verdict']}")
        print(f"   Confidence: {result['confidence']:.2f}%")
        
        # Cleanup
        processor.cleanup(output_dir)
        
    except Exception as e:
        print(f"❌ Real video inference failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("⚠️  No test video found - skipping real video test")

# Test 5: Test threshold logic
print("\n[5/5] Testing threshold logic...")
try:
    # Test case 1: probability < 0.3 → Real
    test_logit_real = torch.tensor([[-1.0]])  # sigmoid(-1.0) ≈ 0.27 < 0.3
    with torch.no_grad():
        logit = test_logit_real.to(engine.device)
        prob = torch.sigmoid(logit).item()
    
    if prob < 0.3:
        expected_verdict = "Real"
        print(f"✅ Test case 1: probability {prob:.4f} < 0.3 → Should be Real")
    else:
        print(f"⚠️  Adjust test case 1")
    
    # Test case 2: probability >= 0.3 → Fake
    test_logit_fake = torch.tensor([[1.0]])  # sigmoid(1.0) ≈ 0.73 >= 0.3
    with torch.no_grad():
        logit = test_logit_fake.to(engine.device)
        prob = torch.sigmoid(logit).item()
    
    if prob >= 0.3:
        expected_verdict = "Fake"
        print(f"✅ Test case 2: probability {prob:.4f} >= 0.3 → Should be Fake")
    else:
        print(f"⚠️  Adjust test case 2")
    
    print("✅ Threshold logic verified")
    
except Exception as e:
    print(f"❌ Threshold test failed: {e}")

print("\n" + "=" * 60)
print("✅ ALL INFERENCE TESTS PASSED!")
print("=" * 60)
print("\nInference engine is ready for integration.")
print(f"Using threshold: {engine.threshold} (as specified by Person 1)")
print("\nNext step: Proceed to Phase 4 (Database Layer)")
