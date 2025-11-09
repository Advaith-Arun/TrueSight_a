import pandas as pd
from PIL import Image
from pathlib import Path
import torch
from torch.utils.data import Dataset
from torchvision import transforms

class DeepfakeDataset(Dataset):
    def __init__(self, csv_path, data_root='data/splits', split='train', num_frames=16): # Load Preprocessed Images

        self.data_root = Path(data_root)
        self.split = split
        self.num_frames = num_frames
        
        # Load CSV
        self.df = pd.read_csv(csv_path)
        
        # Group by video (dataset column)
        self.video_groups = self.df.groupby('dataset')
        self.video_ids = list(self.video_groups.groups.keys())
        
        # Image transforms
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
    def get_label(self, video_id):

        if str(video_id).isdigit():
            return 0  # Real
        elif '__' in str(video_id):
            return 1  # Fake
        else:
            raise ValueError(f"Unknown video ID format: {video_id}")
    
    def __len__(self):
        return len(self.video_ids)
    
    def __getitem__(self, idx):
        video_id = self.video_ids[idx]
        
        # Get label
        label = self.get_label(video_id)
        
        # Get all frames for this video
        video_frames = self.video_groups.get_group(video_id)
        
        # Sample frames uniformly
        if len(video_frames) > self.num_frames:
            step = len(video_frames) / self.num_frames
            indices = [int(i * step) for i in range(self.num_frames)]
            video_frames = video_frames.iloc[indices]
        
        # Load frames
        frames = []
        for _, row in video_frames.iterrows():
            
            img_path = self.data_root / self.split / row['relpath']
            
            try:
                img = Image.open(img_path).convert('RGB')
                img_tensor = self.transform(img)
                frames.append(img_tensor)
            except Exception as e:
                print(f"Error loading {img_path}: {e}")
                continue
        
        # Pad if needed (repeat last frame)
        while len(frames) < self.num_frames:
            if len(frames) > 0:
                frames.append(frames[-1])
            else:
                # If no frames loaded, create blank frame
                frames.append(torch.zeros(3, 224, 224))
        
        # Stack: [num_frames, 3, 224, 224]
        frames_tensor = torch.stack(frames[:self.num_frames])
        
        return frames_tensor, label
