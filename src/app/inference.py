"""
TrueSight Inference Engine

Handles loading the trained model and running inference on preprocessed video data.
"""

import torch
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class InferenceEngine:
    """
    Inference engine for TrueSight deepfake detection model.
    
    Loads the trained TrueSightEnsemble model and provides inference capabilities
    for preprocessed video tensors.
    """
    
    def __init__(
        self,
        model_path: str = 'models/checkpoints/best_model.pth',
        device: str = 'auto',
        threshold: float = 0.5  # ✅ CHANGED: Model 4 uses 0.5 threshold (was 0.3)
    ):
        """
        Initialize the inference engine.
        
        Args:
            model_path: Path to the trained model checkpoint
            device: Device to run inference on ('cpu', 'cuda', or 'auto')
            threshold: Classification threshold (0.5 for Model 4)
        """
        self.model_path = Path(model_path)
        self.threshold = threshold
        
        # Set device
        if device == 'auto':
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        logger.info(f"Using device: {self.device}")
        
        # Load model
        self.model = self._load_model()
        self.model.to(self.device)
        self.model.eval()
        
        logger.info("✅ InferenceEngine initialized successfully")
    
    def _load_model(self):
        """Load the TrueSightEnsemble model from checkpoint."""
        logger.info("Loading TrueSightEnsemble model...")
        
        from src.models.ensemble import TrueSightEnsemble
        
        # Initialize model
        model = TrueSightEnsemble()
        
        # Log model structure
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        logger.info(f"Model initialized: {total_params:,} total parameters ({trainable_params:,} trainable)")
        
        # Load checkpoint
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model checkpoint not found: {self.model_path}")
        
        logger.info(f"Loading checkpoint from {self.model_path}...")
        checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)
        
        # Log checkpoint info
        logger.info(f"Checkpoint keys: {list(checkpoint.keys())}")
        
        # Load model state
        if 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
            logger.info(f"State dict has {len(state_dict)} keys")
            
            # Log first few layer names
            layer_names = list(state_dict.keys())[:5]
            logger.info(f"First 5 layers: {layer_names}")
            
            # Check weight values
            first_key = layer_names[0]
            first_weight = state_dict[first_key]
            logger.info(f"First layer '{first_key}' shape: {first_weight.shape}")
            logger.info(f"First layer weight stats: min={first_weight.min().item():.6f}, max={first_weight.max().item():.6f}, mean={first_weight.mean().item():.6f}")
            
            # Load weights
            model.load_state_dict(state_dict)
            logger.info("✅ Loaded model_state_dict from checkpoint")
            
            # Verify weights were loaded by checking again
            model_first_weight = dict(model.named_parameters())[first_key]
            logger.info(f"After loading - First layer weight stats: min={model_first_weight.min().item():.6f}, max={model_first_weight.max().item():.6f}, mean={model_first_weight.mean().item():.6f}")
            
            # Log training metadata
            if 'epoch' in checkpoint:
                logger.info(f"Checkpoint from epoch: {checkpoint['epoch']}")
            if 'best_acc' in checkpoint:
                logger.info(f"Best accuracy: {checkpoint['best_acc']:.2f}%")
        else:
            model.load_state_dict(checkpoint)
            logger.info("Loaded model state directly from checkpoint")
        
        logger.info("Model loaded and ready for inference")
        return model

    
    def predict(self, video_tensor: torch.Tensor) -> Dict[str, Any]:
        """
        Run inference on a preprocessed video tensor with detailed logging.
        """
        logger.info("=" * 60)
        logger.info("INFERENCE DEBUG START")
        logger.info("=" * 60)
        
        # Log input
        logger.info(f"Input tensor shape: {video_tensor.shape}")
        logger.info(f"Input tensor device: {video_tensor.device}")
        logger.info(f"Input tensor dtype: {video_tensor.dtype}")
        logger.info(f"Input tensor min/max: {video_tensor.min().item():.4f} / {video_tensor.max().item():.4f}")
        logger.info(f"Input tensor mean/std: {video_tensor.mean().item():.4f} / {video_tensor.std().item():.4f}")
        
        # Ensure model is in eval mode
        self.model.eval()
        
        # Move tensor to device
        video_tensor = video_tensor.to(self.device)
        logger.info(f"Tensor moved to device: {self.device}")
        
        # Run inference
        with torch.no_grad():
            logger.info("Calling model forward pass...")
            
            try:
                output = self.model(video_tensor)
                logger.info(f"✅ Forward pass successful")
            except Exception as e:
                logger.error(f"❌ Forward pass FAILED: {e}")
                raise
            
            # Log raw output
            logger.info(f"Raw model output (logit): {output.item():.8f}")
            logger.info(f"Output tensor shape: {output.shape}")
            logger.info(f"Output tensor dtype: {output.dtype}")
            
            # Apply sigmoid
            probability = torch.sigmoid(output).item()
            logger.info(f"After sigmoid (probability): {probability:.8f}")
            logger.info(f"Probability as percentage: {probability * 100:.4f}%")
        
        # Classify
        is_fake = probability >= self.threshold
        verdict = "Fake" if is_fake else "Real"
        confidence = probability * 100
        
        logger.info(f"Classification threshold: {self.threshold}")
        logger.info(f"Is fake? {probability:.4f} >= {self.threshold} = {is_fake}")
        logger.info(f"Final verdict: {verdict}")
        logger.info(f"Final confidence: {confidence:.2f}%")
        logger.info("=" * 60)
        logger.info("INFERENCE DEBUG END")
        logger.info("=" * 60)
        
        result = {
            "verdict": verdict,
            "confidence": round(confidence, 2),
            "probability": round(probability, 4),
            "threshold": self.threshold
        }
        
        return result

    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model metadata
        """
        info = {
            "model_path": str(self.model_path),
            "device": str(self.device),
            "threshold": self.threshold,
            "model_type": "TrueSightEnsemble (Three-Stream: Spatial + Frequency + Temporal)"
        }
        
        # Count parameters
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        info["total_parameters"] = total_params
        info["trainable_parameters"] = trainable_params
        
        return info


def test_inference():
    """Test the inference engine with a dummy video tensor."""
    logger.info("Testing InferenceEngine...")
    
    # Create inference engine
    engine = InferenceEngine()
    
    # Print model info
    info = engine.get_model_info()
    logger.info(f"Model Info: {info}")
    
    # Create dummy video tensor [1, 8, 3, 224, 224]
    dummy_video = torch.randn(1, 8, 3, 224, 224)
    
    # Run inference
    result = engine.predict(dummy_video)
    
    logger.info(f"Test inference result: {result}")
    logger.info("✅ InferenceEngine test complete!")
    
    return result


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    test_inference()
