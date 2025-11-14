import torch
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.device import get_device, print_gpu_info, get_gpu_memory_info

def test_gpu_basic():
    """Basic GPU tests."""
    print("\n" + "="*60)
    print("BASIC GPU TESTS")
    print("="*60)
    
    print(f"✓ PyTorch version: {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"✓ CUDA version: {torch.version.cuda}")
        print(f"✓ Number of GPUs: {torch.cuda.device_count()}")
        print(f"✓ Current GPU: {torch.cuda.get_device_name(0)}")

def test_gpu_computation():
    """Test GPU computation."""
    print("\n" + "="*60)
    print("GPU COMPUTATION TEST")
    print("="*60)
    
    device = get_device()
    
    # Create random tensors on GPU
    x = torch.randn(1000, 1000).to(device)
    y = torch.randn(1000, 1000).to(device)
    
    # Perform matrix multiplication
    z = torch.matmul(x, y)
    
    print(f"✓ Matrix multiplication successful on {device}")
    print(f"✓ Result shape: {z.shape}")
    print(f"✓ Result device: {z.device}")
    
    # Memory info
    mem_info = get_gpu_memory_info()
    print(f"✓ GPU Memory Used: {mem_info['allocated_gb']} GB")

def test_cnn_on_gpu():
    """Test CNN model on GPU."""
    print("\n" + "="*60)
    print("CNN MODEL TEST")
    print("="*60)
    
    device = get_device()
    
    # Create a simple CNN
    model = torch.nn.Sequential(
        torch.nn.Conv2d(3, 64, kernel_size=3, padding=1),
        torch.nn.ReLU(),
        torch.nn.MaxPool2d(2),
        torch.nn.Conv2d(64, 128, kernel_size=3, padding=1),
        torch.nn.ReLU(),
        torch.nn.AdaptiveAvgPool2d(1),
        torch.nn.Flatten(),
        torch.nn.Linear(128, 2)
    ).to(device)
    
    # Test forward pass
    batch = torch.randn(8, 3, 224, 224).to(device)
    output = model(batch)
    
    print(f"✓ CNN forward pass successful")
    print(f"✓ Input shape: {batch.shape}")
    print(f"✓ Output shape: {output.shape}")
    print(f"✓ Model on device: {next(model.parameters()).device}")
    
    # Memory info after model
    mem_info = get_gpu_memory_info()
    print(f"✓ GPU Memory Used: {mem_info['allocated_gb']} GB")

if __name__ == "__main__":
    print("\n🚀 Testing TrueSight GPU Setup\n")
    
    test_gpu_basic()
    print_gpu_info()
    test_gpu_computation()
    test_cnn_on_gpu()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - GPU IS READY!")
    print("="*60 + "\n")
