"""
Grad-CAM visualization for TrueSight ensemble model.
Generates heatmaps showing which regions the model focuses on.
"""

import torch
import torch.nn.functional as F
import numpy as np
import cv2
from pathlib import Path
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import BinaryClassifierOutputTarget
import logging

logger = logging.getLogger(__name__)


class TrueSightGradCAM:
    """
    Generate Grad-CAM heatmaps for TrueSight ensemble model.
    
    Focuses on the Spatial CNN (ResNet50) backbone to visualize
    which regions of face frames the model uses for fake detection.
    """
    
    def __init__(self, model, device='cpu'):
        """
        Initialize Grad-CAM.
        
        Args:
            model: TrueSightEnsemble model instance
            device: Device to run on ('cpu' or 'cuda')
        
        Raises:
            ValueError: If model doesn't have expected structure
        """
        if not hasattr(model, 'spatial_cnn'):
            raise ValueError("Model must have 'spatial_cnn' attribute")
        
        if not hasattr(model.spatial_cnn, 'backbone'):
            raise ValueError("Spatial CNN must have 'backbone' attribute")
        
        self.model = model
        self.device = device
        self.model.eval()
        
        # Target layer: For custom Sequential backbone, use last conv layer
        # Your backbone structure: Sequential with layers 0-8
        # Find the last convolutional layer in the Sequential
        try:
            # Iterate backwards to find the last Conv2d layer
            backbone_modules = list(model.spatial_cnn.backbone.children())
            last_conv_layer = None
            
            for idx in range(len(backbone_modules) - 1, -1, -1):
                if isinstance(backbone_modules[idx], (torch.nn.Conv2d, torch.nn.modules.container.Sequential)):
                    last_conv_layer = backbone_modules[idx]
                    logger.info(f"Found Conv layer at index {idx}")
                    break
            
            if last_conv_layer is None:
                # Fallback: use a layer before pooling
                # From your model: (8): AdaptiveAvgPool2d is last
                # So we want the layer before it
                last_conv_layer = backbone_modules[-2]  
                logger.info(f"Using fallback layer at index -2")
            
            self.target_layers = [last_conv_layer]
            logger.info(f"✅ Grad-CAM initialized with target layer: {type(last_conv_layer).__name__}")
            
        except (AttributeError, IndexError) as e:
            raise ValueError(f"Could not access backbone layers: {e}")
        
        # ImageNet normalization constants (used during preprocessing)
        self.mean = np.array([0.485, 0.456, 0.406])
        self.std = np.array([0.229, 0.224, 0.225])

    
    def generate_heatmaps(self, frames_tensor, raw_frames=None, target_class='fake'):
        """
        Generate Grad-CAM heatmaps for all frames in a video.
        
        Args:
            frames_tensor: Preprocessed tensor [1, num_frames, 3, 224, 224]
            raw_frames: Optional list of raw numpy arrays [H, W, 3] for better overlay
                    If None, will denormalize the preprocessed frames
            target_class: Which class to generate Grad-CAM for ('fake' or 'real')
        
        Returns:
            dict containing:
                - 'heatmaps': List of grayscale heatmaps (numpy arrays [224, 224])
                - 'overlays': List of RGB overlay images (numpy arrays [224, 224, 3])
                - 'avg_heatmap': Average heatmap across all frames
                - 'num_frames': Number of frames processed
                - 'target_class': Which class was targeted
        
        Raises:
            ValueError: If input tensor has wrong shape
            RuntimeError: If Grad-CAM computation fails
        """
        # Validate input
        if len(frames_tensor.shape) != 5:
            raise ValueError(f"Expected 5D tensor [batch, frames, channels, height, width], got shape {frames_tensor.shape}")
        
        frames_tensor = frames_tensor.to(self.device)
        batch_size, num_frames, c, h, w = frames_tensor.shape
        
        if c != 3 or h != 224 or w != 224:
            raise ValueError(f"Expected frames of shape [3, 224, 224], got [{c}, {h}, {w}]")
        
        logger.info(f"Generating Grad-CAM for {num_frames} frames (target: {target_class})...")
        
        heatmaps = []
        overlays = []
        
        try:
            # Define custom target that returns a scalar from feature maps
            class FeatureMapTarget:
                def __init__(self):
                    pass
                
                def __call__(self, model_output):
                    # model_output shape: [1, 512, 1, 1]
                    # Return sum of all activations as scalar
                    return model_output.sum()
            
            # Create target for all frames
            targets = [FeatureMapTarget()]
            
            # Process each frame
            for frame_idx in range(num_frames):
                # Extract single frame [1, 3, 224, 224]
                frame = frames_tensor[:, frame_idx, :, :, :]
                
                # Create Grad-CAM object
                cam = GradCAM(
                    model=self.model.spatial_cnn.backbone,
                    target_layers=self.target_layers
                )
                
                # Generate heatmap using our custom target
                grayscale_cam = cam(input_tensor=frame, targets=targets)
                grayscale_cam = grayscale_cam[0, :]  # Extract [224, 224]
                
                # Prepare RGB image for overlay
                if raw_frames is not None and frame_idx < len(raw_frames):
                    # Use provided raw frame
                    rgb_img = self._prepare_raw_frame(raw_frames[frame_idx])
                else:
                    # Denormalize preprocessed frame
                    rgb_img = self._denormalize_frame(frame[0])
                
                # Create overlay
                overlay = show_cam_on_image(rgb_img, grayscale_cam, use_rgb=True)
                
                # Store results
                heatmaps.append((grayscale_cam * 255).astype(np.uint8))
                overlays.append(overlay)
                
                logger.debug(f"  Frame {frame_idx}: heatmap min={grayscale_cam.min():.3f}, max={grayscale_cam.max():.3f}")
            
            # Compute average heatmap
            avg_heatmap = np.mean([h.astype(np.float32) for h in heatmaps], axis=0).astype(np.uint8)
            
            logger.info(f"✅ Generated {len(heatmaps)} Grad-CAM heatmaps successfully")
            
            return {
                'heatmaps': heatmaps,
                'overlays': overlays,
                'avg_heatmap': avg_heatmap,
                'num_frames': num_frames,
                'target_class': target_class
            }
        
        except Exception as e:
            logger.error(f"❌ Grad-CAM generation failed: {e}", exc_info=True)
            raise RuntimeError(f"Grad-CAM computation failed: {e}") from e



    
    def _prepare_raw_frame(self, raw_frame):
        """
        Prepare a raw frame for overlay.
        
        Args:
            raw_frame: Numpy array [H, W, 3] in BGR or RGB
        
        Returns:
            Numpy array [224, 224, 3] in RGB, normalized to [0, 1]
        """
        # Ensure RGB (convert from BGR if needed)
        if len(raw_frame.shape) == 2:
            # Grayscale -> RGB
            raw_frame = cv2.cvtColor(raw_frame, cv2.COLOR_GRAY2RGB)
        elif raw_frame.shape[2] == 4:
            # RGBA -> RGB
            raw_frame = cv2.cvtColor(raw_frame, cv2.COLOR_RGBA2RGB)
        
        # Resize to 224x224
        if raw_frame.shape[:2] != (224, 224):
            raw_frame = cv2.resize(raw_frame, (224, 224))
        
        # Normalize to [0, 1]
        rgb_img = raw_frame.astype(np.float32) / 255.0
        
        # Clip to valid range
        rgb_img = np.clip(rgb_img, 0, 1)
        
        return rgb_img
    
    def _denormalize_frame(self, frame_tensor):
        """
        Denormalize a preprocessed frame tensor back to RGB [0, 1].
        
        Args:
            frame_tensor: [3, 224, 224] normalized tensor
        
        Returns:
            Numpy array [224, 224, 3] in range [0, 1]
        """
        # Move to CPU and convert to numpy
        frame_np = frame_tensor.cpu().numpy().transpose(1, 2, 0)  # [224, 224, 3]
        
        # Denormalize using ImageNet stats
        frame_np = frame_np * self.std + self.mean
        
        # Clip to [0, 1]
        frame_np = np.clip(frame_np, 0, 1)
        
        return frame_np
    
    def save_heatmaps(self, heatmaps_dict, output_dir, video_id):
        """
        Save heatmaps and overlays to disk.
        
        Args:
            heatmaps_dict: Output from generate_heatmaps()
            output_dir: Directory to save images (will be created if doesn't exist)
            video_id: Video identifier for naming files
        
        Returns:
            dict with paths to saved files:
                - 'overlay_paths': List of paths to frame overlays
                - 'avg_heatmap_path': Path to average heatmap
                - 'output_dir': Directory containing all files
        
        Raises:
            IOError: If saving fails
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            overlay_paths = []
            
            # Save individual frame overlays
            for idx, overlay in enumerate(heatmaps_dict['overlays']):
                output_file = output_path / f"frame_{idx:02d}_overlay.jpg"
                # Convert RGB to BGR for OpenCV
                cv2.imwrite(str(output_file), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
                overlay_paths.append(str(output_file))
            
            # Save average heatmap
            avg_file = output_path / "average_heatmap.jpg"
            cv2.imwrite(str(avg_file), heatmaps_dict['avg_heatmap'])
            
            logger.info(f"✅ Saved {len(overlay_paths)} Grad-CAM images to {output_dir}")
            
            return {
                'overlay_paths': overlay_paths,
                'avg_heatmap_path': str(avg_file),
                'output_dir': str(output_path)
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to save Grad-CAM images: {e}", exc_info=True)
            raise IOError(f"Could not save Grad-CAM images: {e}") from e
