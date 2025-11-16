"""
Quick integration test for Grad-CAM Week 2 implementation.
Tests the complete pipeline without running actual inference.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all required imports work."""
    print("🧪 Testing imports...")
    
    try:
        from src.app.config_loader import get_config
        print("  ✅ config_loader imported")
        
        from src.app.database import DatabaseManager, get_database
        print("  ✅ database imported")
        
        from src.app.gradcam import TrueSightGradCAM
        print("  ✅ gradcam imported")
        
        from src.app.inference import InferenceEngine
        print("  ✅ inference imported")
        
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_config():
    """Test configuration loading."""
    print("\n🧪 Testing configuration...")
    
    try:
        from src.app.config_loader import get_config
        config = get_config()
        
        # Check Grad-CAM config
        is_enabled = config.is_gradcam_enabled()
        gradcam_config = config.get_gradcam_config()
        
        print(f"  ✅ Grad-CAM enabled: {is_enabled}")
        print(f"  ✅ Grad-CAM config loaded: {len(gradcam_config)} settings")
        
        return True
    except Exception as e:
        print(f"  ❌ Config test failed: {e}")
        return False


def test_database_schema():
    """Test database has Grad-CAM fields."""
    print("\n🧪 Testing database schema...")
    
    try:
        from src.app.database import get_database
        from sqlalchemy import inspect
        
        db = get_database()
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('analysis_jobs')]
        
        required_columns = [
            'gradcam_enabled',
            'gradcam_dir',
            'gradcam_avg_heatmap',
            'gradcam_frame_count'
        ]
        
        for col in required_columns:
            if col in columns:
                print(f"  ✅ Column '{col}' exists")
            else:
                print(f"  ❌ Column '{col}' MISSING")
                return False
        
        return True
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        return False


def test_database_methods():
    """Test database Grad-CAM methods."""
    print("\n🧪 Testing database methods...")
    
    try:
        from src.app.database import get_database
        
        db = get_database()
        
        # Check methods exist
        assert hasattr(db, 'update_gradcam_paths'), "Missing update_gradcam_paths method"
        assert hasattr(db, 'get_gradcam_paths'), "Missing get_gradcam_paths method"
        
        print("  ✅ update_gradcam_paths method exists")
        print("  ✅ get_gradcam_paths method exists")
        
        return True
    except Exception as e:
        print(f"  ❌ Database methods test failed: {e}")
        return False


def test_inference_gradcam_method():
    """Test InferenceEngine has Grad-CAM method."""
    print("\n🧪 Testing InferenceEngine integration...")
    
    try:
        from src.app.inference import InferenceEngine
        
        # Check method exists (don't actually run it)
        assert hasattr(InferenceEngine, 'predict_with_gradcam'), "Missing predict_with_gradcam method"
        
        print("  ✅ predict_with_gradcam method exists")
        print("  ⚠️  Skipping actual inference (no model loaded)")
        
        return True
    except Exception as e:
        print(f"  ❌ InferenceEngine test failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("🚀 GRAD-CAM INTEGRATION TEST - WEEK 2")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Database Schema", test_database_schema()))
    results.append(("Database Methods", test_database_methods()))
    results.append(("Inference Integration", test_inference_gradcam_method()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Week 2 integration complete!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please review errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
