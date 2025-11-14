# DO NOT REMOVE OR CHANGE THE CONTENTS OF THIS FILE, IT IS FOR LOADING THE PREPROCESSED DATA
# ADITI AND ABHINAV I AM TALKING TO YOU (advaith)

import torch
from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image
from pathlib import Path
import numpy as np


class DeepfakeDataset(Dataset):
    """
    PyTorch Dataset for loading preprocessed deepfake videos
    
    Args:
        data_root: Root directory (e.g., 'data_processed/')
        split: 'train', 'val', or 'test'
        num_frames: Number of frames to sample per video (default: 8)
        transform: Optional custom transforms
    """
    
    def __init__(self, data_root, split='train', num_frames=8, transform=None):
        self.data_root = Path(data_root)
        self.split = split
        self.num_frames = num_frames
        
        # Get split directory
        split_dir = self.data_root / split
        
        if not split_dir.exists():
            raise ValueError(f"Split directory not found: {split_dir}")
        
        # Find all video folders
        self.videos = []
        self.labels = []
        
        # Real videos (label = 0)
        real_dir = split_dir / 'real'
        if real_dir.exists():
            real_videos = [d for d in real_dir.iterdir() if d.is_dir()]
            self.videos.extend(real_videos)
            self.labels.extend([0] * len(real_videos))
        
        # Fake videos (label = 1)
        fake_dir = split_dir / 'fake'
        if fake_dir.exists():
            fake_videos = [d for d in fake_dir.iterdir() if d.is_dir()]
            self.videos.extend(fake_videos)
            self.labels.extend([1] * len(fake_videos))
        
        if len(self.videos) == 0:
            raise ValueError(f"No videos found in {split_dir}")
        
        # Setup transforms
        if transform is None:
            self._setup_transforms()
        else:
            self.transform = transform
        
        # Print summary
        num_real = self.labels.count(0)
        num_fake = self.labels.count(1)
        print(f"{split.upper()} - Found {len(self.videos)} videos (Real: {num_real}, Fake: {num_fake})")
    
    def _setup_transforms(self):
        """Setup image transforms with strong augmentation for training"""
        
        if self.split == 'train':
            # STRONG augmentation for training (helps generalization)
            print(f"   Using STRONG augmentation for {self.split}")
            self.transform = transforms.Compose([
                # Geometric augmentation
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(10),
                transforms.RandomResizedCrop(224, scale=(0.85, 1.0)),
                
                # Color augmentation (simulates different lighting/cameras)
                transforms.ColorJitter(
                    brightness=0.3,
                    contrast=0.3,
                    saturation=0.2,
                    hue=0.1
                ),
                
                # Slight blur (simulates compression artifacts)
                transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.5)),
                
                # Normalize
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
        else:
            # NO augmentation for val/test (deterministic evaluation)
            print(f"   Using standard transforms for {self.split}")
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
    
    def __len__(self):
        return len(self.videos)
    
    def __getitem__(self, idx):
        """
        Returns:
            frames: Tensor of shape [num_frames, C, H, W]
            label: 0 for real, 1 for fake
        """
        video_folder = self.videos[idx]
        label = self.labels[idx]
        
        # Get all frame files from the 'crops' subfolder
        crops_dir = video_folder / 'crops'
        
        if not crops_dir.exists():
            raise ValueError(f"No 'crops' subfolder found in {video_folder}")
        
        frame_files = sorted([
            f for f in crops_dir.iterdir() 
            if f.suffix.lower() in ['.jpg', '.jpeg', '.png']
        ])
        
        if len(frame_files) == 0:
            raise ValueError(f"No frames found in {crops_dir}")
        
        # Sample frames uniformly
        if len(frame_files) >= self.num_frames:
            # Uniform sampling
            step = len(frame_files) / self.num_frames
            indices = [int(i * step) for i in range(self.num_frames)]
            sampled_frames = [frame_files[i] for i in indices]
        else:
            # If fewer frames than needed, repeat last frame
            sampled_frames = frame_files + [frame_files[-1]] * (self.num_frames - len(frame_files))
        
        # Load and transform frames
        frames = []
        for frame_path in sampled_frames:
            try:
                img = Image.open(frame_path).convert('RGB')
                img = self.transform(img)
                frames.append(img)
            except Exception as e:
                print(f"Error loading {frame_path}: {e}")
                # Use black frame as fallback
                frames.append(torch.zeros(3, 224, 224))
        
        # Stack frames: [T, C, H, W]
        frames = torch.stack(frames, dim=0)
        
        return frames, label