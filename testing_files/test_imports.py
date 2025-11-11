"""
Test script to verify all required imports work correctly.
This ensures Person 1's model, Person 2's preprocessing, and config are accessible.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("TrueSight Backend - Import Verification Test")
print("=" * 60)

# Test 1: Person 1's Model
print("\n[1/5] Testing Person 1's model import...")
try:
    from src.models.ensemble import TrueSightEnsemble
    print("✅ TrueSightEnsemble imported successfully")
except ImportError as e:
    print(f"❌ Failed to import TrueSightEnsemble: {e}")
    sys.exit(1)

# Test 2: Person 2's Preprocessing
print("\n[2/5] Testing Person 2's preprocessing import...")
try:
    from src.preprocessing.preprocess_final import PreprocessFinal
    print("✅ PreprocessFinal imported successfully")
except ImportError as e:
    print(f"❌ Failed to import PreprocessFinal: {e}")
    sys.exit(1)

# Test 3: Config File
print("\n[3/5] Testing config file loading...")
try:
    import yaml
    config_path = project_root / 'configs' / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    print(f"✅ Config loaded successfully")
    print(f"   - Dataset: {config['data']['dataset_name']}")
    print(f"   - Num frames: {config['data']['num_frames']}")
    print(f"   - Frame size: {config['data']['frame_size']}")
except Exception as e:
    print(f"❌ Failed to load config: {e}")
    sys.exit(1)

# Test 4: Model Checkpoint
print("\n[4/5] Testing model checkpoint existence...")
try:
    checkpoint_path = project_root / 'models' / 'checkpoints' / 'best_model.pth'
    if checkpoint_path.exists():
        size_mb = checkpoint_path.stat().st_size / (1024 * 1024)
        print(f"✅ Model checkpoint exists")
        print(f"   - Path: {checkpoint_path}")
        print(f"   - Size: {size_mb:.2f} MB")
    else:
        print(f"❌ Model checkpoint not found at: {checkpoint_path}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error checking checkpoint: {e}")
    sys.exit(1)

# Test 5: New Dependencies
print("\n[5/5] Testing new dependencies...")
try:
    import celery
    import redis
    import flask_sqlalchemy
    print(f"✅ All new dependencies imported")
    print(f"   - Celery version: {celery.__version__}")
    print(f"   - Redis client version: {redis.__version__}")
except ImportError as e:
    print(f"❌ Failed to import new dependencies: {e}")
    print("   Run: pip install -r requirements.txt")
    sys.exit(1)

# Test 6: Redis Connection
print("\n[6/6] Testing Redis server connection...")
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print("✅ Redis server is running and accessible")
except redis.ConnectionError:
    print("❌ Cannot connect to Redis server")
    print("   Make sure Redis is running:")
    print("   - Docker: docker start truesight-redis")
    print("   - Linux: sudo systemctl start redis-server")
    print("   - macOS: brew services start redis")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED! Environment is ready.")
print("=" * 60)
print("\nNext step: Proceed to Phase 2 (Video Processing Integration)")
