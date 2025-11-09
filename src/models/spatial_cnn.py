import torch
import torch.nn as nn
import torchvision.models as models
from torchvision.models import ResNet50_Weights

class SpatialCNN(nn.Module):
    """
    Spatial feature extractor using ResNet-50
    Detects intra-frame artifacts in RGB space
    """
    def __init__(self, pretrained=True, feature_dim=512):
        super(SpatialCNN, self).__init__()
        
        # Load pre-trained ResNet-50 (updated API)
        if pretrained:
            weights = ResNet50_Weights.IMAGENET1K_V1  # or ResNet50_Weights.DEFAULT
        else:
            weights = None
            
        resnet = models.resnet50(weights=weights)
        
        # Remove final classification layer
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])
        
        # Feature projection
        self.feature_proj = nn.Sequential(
            nn.Flatten(),
            nn.Linear(2048, feature_dim),
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        
    def forward(self, x):
        """
        Args:
            x: [batch, C, H, W] - RGB frames (224x224)
        Returns:
            features: [batch, feature_dim] - Spatial features
        """
        features = self.backbone(x)
        features = self.feature_proj(features)
        return features

if __name__ == '__main__':
    model = SpatialCNN(pretrained=True, feature_dim=512)
    
    # Test with dummy input
    dummy_input = torch.randn(4, 3, 224, 224)
    output = model(dummy_input)
    
    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")
    print(f"✅ Spatial CNN works!")
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
