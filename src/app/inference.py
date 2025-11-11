"""
Inference Engine Module

Loads Person 1's trained TrueSightEnsemble model and runs deepfake detection inference.
Uses the correct threshold (0.3) as specified by Person 1.
"""

import torch
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

# Import Person 1's model
from src.models.ensemble import TrueSightEnsemble

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InferenceEngine:
    """
    Deepfake detection inference engine.
    
    Loads the trained TrueSightEnsemble model and runs predictions
    with the correct threshold (0.3 as per Person 1's specification).
    """
    
    def __init__(
        self,
        config_path: str = "configs/config.yaml",
        checkpoint_path: str = "models/checkpoints/best_model.pth",
        threshold: float = 0.3  # CRITICAL: Use 0.3, not 0.5
    ):
        """
        Initialize the inference engine.
        
        Args:
            config_path: Path to config.yaml
            checkpoint_path: Path to trained model checkpoint
            threshold: Classification threshold (0.3 as per Person 1)
        """
        self.config_path = Path(config_path)
        self.checkpoint_path = Path(checkpoint_path)
        self.threshold = threshold
        
        logger.info("Initializing InferenceEngine...")
        logger.info(f"Config: {self.config_path}")
        logger.info(f"Checkpoint: {self.checkpoint_path}")
        logger.info(f"Threshold: {self.threshold}")
        
        # Load config
        self.config = self._load_config()
        
        # Determine device (GPU if available)
        self.device = self._get_device()
        logger.info(f"Using device: {self.device}")
        
        # Load model
        self.model = self._load_model()
        logger.info("✅ InferenceEngine initialized successfully")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info("Config loaded successfully")
        return config
    
    def _get_device(self) -> torch.device:
        """
        Determine the device to use (GPU if available, else CPU).
        
        Returns:
            torch.device object
        """
        # Check config preference
        use_cuda = self.config.get('hardware', {}).get('use_cuda', True)
        
        if use_cuda and torch.cuda.is_available():
            device = torch.device('cuda')
            logger.info(f"GPU available: {torch.cuda.get_device_name(0)}")
        else:
            device = torch.device('cpu')
            if use_cuda and not torch.cuda.is_available():
                logger.warning("CUDA requested but not available. Using CPU.")
        
        return device
    
    def _load_model(self) -> TrueSightEnsemble:
        """
        Load the TrueSightEnsemble model with trained weights.
        
        Returns:
            Loaded model in evaluation mode
        """
        logger.info("Loading TrueSightEnsemble model...")
        
        # Initialize model with config
        model = TrueSightEnsemble(self.config)
        
        # Load checkpoint
        if not self.checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {self.checkpoint_path}")
        
        logger.info(f"Loading checkpoint from {self.checkpoint_path}...")
        checkpoint = torch.load(
            self.checkpoint_path,
            map_location=self.device,
            weights_only=False  # Person 1's checkpoint includes optimizer state
        )
        
        # Load model weights
        if 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
            logger.info("Loaded model_state_dict from checkpoint")
            
            # Log training info if available
            if 'epoch' in checkpoint:
                logger.info(f"Checkpoint from epoch: {checkpoint['epoch']}")
            if 'best_acc' in checkpoint:
                logger.info(f"Best accuracy: {checkpoint['best_acc']:.2f}%")
        else:
            # Fallback if checkpoint is just state dict
            model.load_state_dict(checkpoint)
            logger.info("Loaded state_dict directly")
        
        # Move to device and set to evaluation mode
        model = model.to(self.device)
        model.eval()
        
        logger.info("Model loaded and ready for inference")
        return model
    
    def predict(self, video_tensor: torch.Tensor) -> Dict[str, Any]:
        """
        Run inference on a preprocessed video tensor.
        
        Args:
            video_tensor: Tensor of shape [1, 8, 3, 224, 224]
        
        Returns:
            Dictionary containing:
                - verdict: "Real" or "Fake"
                - confidence: Confidence percentage (0-100)
                - probability: Raw probability (0-1)
                - threshold: Threshold used for classification
        """
        # Verify input shape
        expected_shape = (1, 8, 3, 224, 224)
        if video_tensor.shape != expected_shape:
            raise ValueError(
                f"Invalid input shape: {video_tensor.shape}. "
                f"Expected: {expected_shape}"
            )
        
        logger.info("Running inference...")
        
        # Move tensor to device
        video_tensor = video_tensor.to(self.device)
        
        # Run inference (no gradient computation needed)
        with torch.no_grad():
            # Forward pass
            logits = self.model(video_tensor)
            
            # Apply sigmoid to get probability
            probability = torch.sigmoid(logits).item()
        
        # Apply threshold to get verdict
        # CRITICAL: Use 0.3 threshold as per Person 1's specification
        is_fake = probability >= self.threshold
        verdict = "Fake" if is_fake else "Real"
        
        # Convert to confidence percentage
        confidence = probability * 100
        
        result = {
            "verdict": verdict,
            "confidence": round(confidence, 2),
            "probability": round(probability, 4),
            "threshold": self.threshold
        }
        
        logger.info(f"Inference complete: {verdict} (confidence: {confidence:.2f}%)")
        
        return result
    
    def predict_batch(self, video_tensors: torch.Tensor) -> list[Dict[str, Any]]:
        """
        Run inference on multiple videos at once.
        
        Args:
            video_tensors: Tensor of shape [batch_size, 8, 3, 224, 224]
        
        Returns:
            List of prediction dictionaries
        """
        batch_size = video_tensors.shape[0]
        logger.info(f"Running batch inference on {batch_size} videos...")
        
        # Move to device
        video_tensors = video_tensors.to(self.device)
        
        # Run inference
        with torch.no_grad():
            logits = self.model(video_tensors)
            probabilities = torch.sigmoid(logits)
        
        # Process each result
        results = []
        for i, prob in enumerate(probabilities):
            probability = prob.item()
            is_fake = probability >= self.threshold
            verdict = "Fake" if is_fake else "Real"
            confidence = probability * 100
            
            results.append({
                "verdict": verdict,
                "confidence": round(confidence, 2),
                "probability": round(probability, 4),
                "threshold": self.threshold
            })
        
        logger.info(f"Batch inference complete: {batch_size} videos processed")
        return results


# Convenience function for single prediction
def predict_video(video_tensor: torch.Tensor) -> Dict[str, Any]:
    """
    Convenience function to run inference on a single video.
    
    Args:
        video_tensor: Tensor of shape [1, 8, 3, 224, 224]
    
    Returns:
        Prediction dictionary
    """
    engine = InferenceEngine()
    return engine.predict(video_tensor)
