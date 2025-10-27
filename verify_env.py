#!/usr/bin/env python3
"""Verify TrueSight environment setup."""

import sys
import torch

def verify_imports():
    """Check if all required packages can be imported."""
    packages = {
        'torch': 'PyTorch',
        'torchvision': 'TorchVision',
        'cv2': 'OpenCV',
        'PIL': 'Pillow',
        'facenet_pytorch': 'FaceNet PyTorch',
        'sklearn': 'Scikit-learn',
        'numpy': 'NumPy',
        'pandas': 'Pandas',
        'yaml': 'PyYAML',
        'streamlit': 'Streamlit'
    }
    
    failed = []
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} - FAILED")
            failed.append(name)
    
    if failed:
        print(f"\n❌ Failed to import: {', '.join(failed)}")
        return False
    
    print("\n✅ All packages imported successfully!")
    return True

def check_cuda():
    """Check CUDA availability."""
    import torch
    if torch.cuda.is_available():
        print(f"\n✅ CUDA available: {torch.cuda.get_device_name(0)}")
    else:
        print("\n⚠️  CUDA not available - using CPU")

if __name__ == "__main__":
    print("Verifying TrueSight Environment Setup\n")
    print(f"Python version: {sys.version}\n")

    if verify_imports():
        check_cuda()
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        print(f"CUDA version (PyTorch): {torch.version.cuda}")
        print(f"Number of GPUs: {torch.cuda.device_count()}")
        print(f"Current GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

        sys.exit(0)
    else:
        sys.exit(1)
