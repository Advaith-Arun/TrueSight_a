"""
Video Processor Module

Integrates Person 2's preprocessing pipeline for single-video inference.
Extracts frames, detects faces, crops, and prepares tensors for model inference.
"""

import torch
import shutil
from pathlib import Path
from PIL import Image
from torchvision import transforms
from typing import Tuple, List, Union
import logging

# Import Person 2's preprocessing
from src.preprocessing.preprocess_final import PreprocessFinal

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoProcessor:
    """
    Processes uploaded videos for deepfake detection inference.
    
    Uses Person 2's PreprocessFinal to:
    - Extract frames from video
    - Detect faces using MTCNN
    - Crop and resize faces to 224x224
    
    Then samples 8 frames and applies ImageNet normalization.
    """
    
    def __init__(self, temp_dir: str = "src/app/temp_processing"):
        """
        Initialize VideoProcessor.
        
        Args:
            temp_dir: Directory for temporary preprocessing output
        """
        self.temp_base_dir = Path(temp_dir)
        self.temp_base_dir.mkdir(parents=True, exist_ok=True)
        self.current_output_dir = None  # Track for cleanup
        
        # ImageNet normalization (same as training)
        self.normalize = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        logger.info(f"VideoProcessor initialized. Temp base dir: {self.temp_base_dir}")
    
    def process_video(self, video_path: Union[str, Path], num_frames: int = 8) -> torch.Tensor:
        """
        Process a single video file for inference.
        
        Args:
            video_path: Path to the uploaded video file (string or Path)
            num_frames: Number of frames to sample (default: 8)
            
        Returns:
            Processed video tensor of shape [1, 8, 3, 224, 224] ready for model inference
            
        Raises:
            ValueError: If no faces detected or insufficient frames
            RuntimeError: If preprocessing fails
        """
        logger.info(f"Processing video: {video_path}")
        
        # ✅ FIXED: Convert string to Path object
        video_path = Path(video_path)
        
        # Create unique output directory for this video
        video_name = video_path.stem
        output_dir = self.temp_base_dir / video_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Store for cleanup
        self.current_output_dir = output_dir
        
        try:
            # Step 1: Run Person 2's preprocessing
            logger.info("Running preprocessing pipeline...")
            preprocessor = PreprocessFinal(
                input_paths=[video_path.parent],  # Directory containing the video
                output_dir=output_dir,
                frames_per_second=1.0,  # Extract 1 frame per second
                detect=True,  # Enable face detection
                save_crops=True,  # Save face crops
                augment=False,  # No augmentation for inference
                face_size=224,  # Resize to 224x224
                heatmap=False,  # Don't need heatmaps for inference
                splits=(1.0, 0.0, 0.0),  # All frames go to "train" split
                per_label_split=False  # Use per_label_split instead of split_mode
            )
            
            # Process the video
            preprocessor.process()
            logger.info("Preprocessing completed")
            
            # Step 2: Locate the face crops
            # Person 2's output structure: output_dir/train/*/video_name/crops/
            crops_dir = self._find_crops_directory(output_dir, video_name)
            
            if crops_dir is None:
                raise ValueError(f"No crops directory found. Face detection may have failed.")
            
            # Step 3: Load and sample face crops
            crop_files = sorted(crops_dir.glob("crop_*.jpg"))
            
            # Filter out augmented crops (only use original crops)
            crop_files = [f for f in crop_files if '_aug' not in f.name]
            
            if len(crop_files) == 0:
                raise ValueError(f"No face crops found. Video may not contain detectable faces.")
            
            logger.info(f"Found {len(crop_files)} face crops")
            
            # Step 4: Sample exactly num_frames (default 8)
            sampled_crops = self._sample_frames(crop_files, num_frames)
            logger.info(f"Sampled {len(sampled_crops)} frames")
            
            # Step 5: Load images and apply normalization
            frames = []
            for crop_path in sampled_crops:
                img = Image.open(crop_path).convert('RGB')
                # Apply normalization (includes ToTensor)
                tensor = self.normalize(img)
                frames.append(tensor)
            
            # Step 6: Stack into model input format [1, num_frames, 3, 224, 224]
            video_tensor = torch.stack(frames).unsqueeze(0)
            
            logger.info(f"Created tensor of shape: {video_tensor.shape}")
            
            # Verify shape
            expected_shape = (1, num_frames, 3, 224, 224)
            if video_tensor.shape != expected_shape:
                raise RuntimeError(
                    f"Unexpected tensor shape: {video_tensor.shape}. "
                    f"Expected: {expected_shape}"
                )
            
            # ✅ FIXED: Return only the tensor (cleanup handled separately)
            return video_tensor
            
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            # Clean up on error
            if output_dir.exists():
                shutil.rmtree(output_dir)
            raise RuntimeError(f"Video processing failed: {str(e)}")
    
    def _find_crops_directory(self, output_dir: Path, video_name: str) -> Path:
        """
        Find the crops directory in Person 2's output structure.
        
        Output structure: output_dir/train/*/video_name/crops/
        The middle wildcard is the label (could be real, fake, or the folder name)
        """
        # Search for any crops directory
        crops_dirs = list(output_dir.rglob("crops"))
        
        if len(crops_dirs) == 0:
            return None
        
        # Return the first one found (there should only be one for single video)
        return crops_dirs[0]
    
    def _sample_frames(self, frame_paths: List[Path], num_frames: int = 8) -> List[Path]:
        """
        Sample exactly num_frames uniformly from the available frames.
        
        If fewer frames than requested, pad by repeating the last frame.
        If more frames than requested, sample uniformly.
        
        Args:
            frame_paths: List of paths to frame images
            num_frames: Number of frames to sample
            
        Returns:
            List of sampled frame paths (length = num_frames)
        """
        total_frames = len(frame_paths)
        
        if total_frames >= num_frames:
            # Sample uniformly
            step = total_frames / num_frames
            indices = [int(i * step) for i in range(num_frames)]
            sampled = [frame_paths[i] for i in indices]
        else:
            # Pad by repeating last frame
            sampled = list(frame_paths)
            padding_needed = num_frames - total_frames
            sampled.extend([frame_paths[-1]] * padding_needed)
            logger.warning(
                f"Video has only {total_frames} frames. "
                f"Padding with last frame {padding_needed} times."
            )
        
        return sampled
    
    def cleanup(self):
        """
        Clean up temporary preprocessing files from current processing.
        """
        if self.current_output_dir and self.current_output_dir.exists():
            try:
                shutil.rmtree(self.current_output_dir)
                logger.info(f"Cleaned up temporary directory: {self.current_output_dir}")
                self.current_output_dir = None
            except Exception as e:
                logger.error(f"Error cleaning up {self.current_output_dir}: {e}")


# Convenience function for single-video processing
def process_video_for_inference(video_path: Union[str, Path]) -> torch.Tensor:
    """
    Convenience function to process a single video.
    
    Args:
        video_path: Path to video file (string or Path)
        
    Returns:
        Tensor of shape [1, 8, 3, 224, 224]
    """
    processor = VideoProcessor()
    return processor.process_video(video_path)
