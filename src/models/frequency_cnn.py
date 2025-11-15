import torch
import torch.nn as nn
import torch.fft

import torch
import torch.nn as nn
import torch.fft
import torchvision.models as models
from torchvision.models import EfficientNet_B0_Weights

class FrequencyCNN(nn.Module): # Frequency Analyzer using 2D Fast Fourier Transform

    def __init__(self, input_channels=3, feature_dim=256, pretrained=True):
        super(FrequencyCNN, self).__init__()
        
        # Load pre-trained EfficientNet-B0
        if pretrained:
            weights = EfficientNet_B0_Weights.IMAGENET1K_V1
        else:
            weights = None
            
        efficientnet = models.efficientnet_b0(weights=weights)
        
        # Use the feature extractor part of EfficientNet
        self.backbone = efficientnet.features
        
        # Use the pooling layer from EfficientNet
        self.pool = efficientnet.avgpool
        
        # Get the number of features EfficientNet outputs (it's 1280 for B0)
        in_features = efficientnet.classifier[1].in_features
        
        # New feature projection layer to match the required feature_dim
        self.feature_proj = nn.Sequential(
            nn.Flatten(),
            nn.Linear(in_features, feature_dim),
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        
    def forward(self, x): # Returns frequency features

        # Calculate FFT
        fft_result = torch.fft.fft2(x)
        
        magnitude = torch.abs(fft_result)
        magnitude_log = torch.log(magnitude + 1e-8)
        
        # Shift zero-frequency component to center
        magnitude_log = torch.fft.fftshift(magnitude_log, dim=(-2, -1))
        
        # Extract frequency features using the EfficientNet backbone
        features = self.backbone(magnitude_log)
        features = self.pool(features)
        freq_features = self.feature_proj(features)
        
        return freq_features
