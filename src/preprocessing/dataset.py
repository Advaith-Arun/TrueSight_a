# src/preprocessing/dataset.py
import pandas as pd
from PIL import Image
from pathlib import Path
import torch
from torch.utils.data import Dataset
from torchvision import transforms

class DeepfakeDataset(Dataset):

    def __init__(self, data_root='data', split='train', num_frames=8):

        self.data_root = Path(data_root)
        self.split = split
        self.num_frames = num_frames
        
        # Get video directories
        self.videos = []
        self.labels = []
        
        split_dir = self.data_root / split
        
        if not split_dir.exists():
            raise FileNotFoundError(f"Split directory not found: {split_dir}")
        
        # Load real videos
        real_dir = split_dir / 'real'
        if real_dir.exists():
            for video_folder in real_dir.iterdir():
                if video_folder.is_dir():
                    self.videos.append(video_folder)
                    self.labels.append(0)  # Real = 0
        
        # Load fake videos
        fake_dir = split_dir / 'fake'
        if fake_dir.exists():
            for video_folder in fake_dir.iterdir():
                if video_folder.is_dir():
                    self.videos.append(video_folder)
                    self.labels.append(1)  # Fake = 1
        
        if len(self.videos) == 0:
            raise ValueError(f"No videos found in {split_dir}")
        
        print(f"{split.upper()} - Found {len(self.videos)} videos "
              f"(Real: {self.labels.count(0)}, Fake: {self.labels.count(1)})")
        
        # Image transforms
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        if split == 'train':
            self.transform = transforms.Compose([
                # Geometric transformations
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(10),
                transforms.RandomResizedCrop(224, scale=(0.85, 1.0)),
                
                transforms.ColorJitter(
                    brightness=0.3,   
                    contrast=0.3,     
                    saturation=0.2,   
                    hue=0.1          
                ),
                
                # Slight blur (simulates compression/quality differences)
                transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.5)),
                
                # Resize and normalize
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
        else:
            # Validation/Test: no augmentation
            print(f"   ✅ Using standard transforms for {split}")
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
        video_folder = self.videos[idx]
        label = self.labels[idx]
        
        # Get all frame files in video folder
        frame_files = sorted([
            f for f in video_folder.iterdir() 
            if f.suffix.lower() in ['.jpg', '.png', '.jpeg']
        ])
        
        if len(frame_files) == 0:
            raise ValueError(f"No frames found in {video_folder}")
        
        # Sample frames uniformly
        if len(frame_files) > self.num_frames:
            step = len(frame_files) / self.num_frames
            indices = [int(i * step) for i in range(self.num_frames)]
            frame_files = [frame_files[i] for i in indices]
        
        # Load frames
        frames = []
        for frame_path in frame_files:
            try:
                img = Image.open(frame_path).convert('RGB')
                img_tensor = self.transform(img)
                frames.append(img_tensor)
            except Exception as e:
                print(f"Warning: Error loading {frame_path}: {e}")
                continue
        
        # Pad if needed (repeat last frame)
        while len(frames) < self.num_frames:
            if len(frames) > 0:
                frames.append(frames[-1])
            else:
                frames.append(torch.zeros(3, 224, 224))
        
        # Stack frames: [num_frames, 3, 224, 224]
        frames_tensor = torch.stack(frames[:self.num_frames])
        
        return frames_tensor, label

