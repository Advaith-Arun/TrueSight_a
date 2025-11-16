"""
Unit tests for Grad-CAM functionality.
"""

import pytest
import torch
import numpy as np
from pathlib import Path
import shutil

from src.models.ensemble import TrueSightEnsemble
from src.app.gradcam import TrueSightGradCAM


@pytest.fixture
def dummy_model():
    """Create a dummy TrueSightEnsemble model for testing."""
    model = TrueSightEnsemble()  # ✅ Fixed: No arguments
    model.eval()
    return model


@pytest.fixture
def dummy_frames():
    """Create dummy frame tensor [1, 8, 3, 224, 224]."""
    return torch.randn(1, 8, 3, 224, 224)


@pytest.fixture
def gradcam_instance(dummy_model):
    """Create TrueSightGradCAM instance."""
    return TrueSightGradCAM(dummy_model, device='cpu')


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "gradcam_output"
    output_dir.mkdir()
    yield output_dir
    # Cleanup
    if output_dir.exists():
        shutil.rmtree(output_dir)


class TestTrueSightGradCAM:
    """Test suite for TrueSightGradCAM class."""
    
    def test_initialization(self, dummy_model):
        """Test Grad-CAM initialization."""
        gradcam = TrueSightGradCAM(dummy_model, device='cpu')
        assert gradcam.model is not None
        assert gradcam.device == 'cpu'
        assert len(gradcam.target_layers) == 1
    
    def test_initialization_invalid_model(self):
        """Test initialization with invalid model."""
        class InvalidModel:
            pass
        
        with pytest.raises(ValueError, match="must have 'spatial_cnn'"):
            TrueSightGradCAM(InvalidModel(), device='cpu')
    
    def test_generate_heatmaps_shape(self, gradcam_instance, dummy_frames):
        """Test that generated heatmaps have correct shape."""
        result = gradcam_instance.generate_heatmaps(dummy_frames)
        
        assert 'heatmaps' in result
        assert 'overlays' in result
        assert 'avg_heatmap' in result
        assert 'num_frames' in result
        
        assert len(result['heatmaps']) == 8
        assert len(result['overlays']) == 8
        assert result['num_frames'] == 8
        
        # Check individual heatmap shapes
        for heatmap in result['heatmaps']:
            assert heatmap.shape == (224, 224)
            assert heatmap.dtype == np.uint8
        
        # Check overlay shapes
        for overlay in result['overlays']:
            assert overlay.shape == (224, 224, 3)
        
        # Check average heatmap
        assert result['avg_heatmap'].shape == (224, 224)
        assert result['avg_heatmap'].dtype == np.uint8
    
    def test_generate_heatmaps_invalid_shape(self, gradcam_instance):
        """Test error handling for invalid input shape."""
        invalid_tensor = torch.randn(8, 3, 224, 224)  # Missing batch dimension
        
        with pytest.raises(ValueError, match="Expected 5D tensor"):
            gradcam_instance.generate_heatmaps(invalid_tensor)
    
    def test_generate_heatmaps_target_class(self, gradcam_instance, dummy_frames):
        """Test Grad-CAM with different target classes."""
        result_fake = gradcam_instance.generate_heatmaps(dummy_frames, target_class='fake')
        result_real = gradcam_instance.generate_heatmaps(dummy_frames, target_class='real')
        
        assert result_fake['target_class'] == 'fake'
        assert result_real['target_class'] == 'real'
    
    def test_save_heatmaps(self, gradcam_instance, dummy_frames, temp_output_dir):
        """Test saving heatmaps to disk."""
        result = gradcam_instance.generate_heatmaps(dummy_frames)
        saved_paths = gradcam_instance.save_heatmaps(result, temp_output_dir, 'test_video')
        
        assert 'overlay_paths' in saved_paths
        assert 'avg_heatmap_path' in saved_paths
        assert 'output_dir' in saved_paths
        
        # Verify files exist
        assert len(saved_paths['overlay_paths']) == 8
        for path in saved_paths['overlay_paths']:
            assert Path(path).exists()
        
        assert Path(saved_paths['avg_heatmap_path']).exists()
    
    def test_denormalize_frame(self, gradcam_instance):
        """Test frame denormalization."""
        # Create a normalized frame
        frame = torch.randn(3, 224, 224)
        
        denormalized = gradcam_instance._denormalize_frame(frame)
        
        assert denormalized.shape == (224, 224, 3)
        assert denormalized.min() >= 0.0
        assert denormalized.max() <= 1.0
    
    def test_prepare_raw_frame(self, gradcam_instance):
        """Test raw frame preparation."""
        # Test with different input shapes
        raw_bgr = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        prepared = gradcam_instance._prepare_raw_frame(raw_bgr)
        
        assert prepared.shape == (224, 224, 3)
        assert prepared.min() >= 0.0
        assert prepared.max() <= 1.0


def test_integration_with_real_model(tmp_path):
    """
    Integration test with actual model (if available).
    This test will be skipped if model checkpoint doesn't exist.
    """
    model_path = Path('models/checkpoints/best_model.pth')
    
    if not model_path.exists():
        pytest.skip("Model checkpoint not found")
    
    # Load model
    model = TrueSightEnsemble()
    
    try:
        checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()
    except Exception as e:
        pytest.skip(f"Could not load checkpoint: {e}")
    
    # Create Grad-CAM
    gradcam = TrueSightGradCAM(model, device='cpu')
    
    # Generate dummy frames
    frames = torch.randn(1, 8, 3, 224, 224)
    
    # Generate heatmaps
    result = gradcam.generate_heatmaps(frames)
    
    # Save
    output_dir = tmp_path / "integration_test"
    saved = gradcam.save_heatmaps(result, output_dir, 'test')
    
    # Verify
    assert len(saved['overlay_paths']) == 8
    assert Path(saved['avg_heatmap_path']).exists()

