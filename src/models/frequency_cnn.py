import torch
import torch.nn as nn
import torch.fft

class FrequencyCNN(nn.Module): # Frequency Analyzer using 2D Fast Fourier Transform

    def __init__(self, input_channels=3, feature_dim=256):
        super(FrequencyCNN, self).__init__()
        
        # CNN for processing frequency magnitude spectrum
        self.freq_cnn = nn.Sequential(
            # First conv block
            nn.Conv2d(input_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            # Second conv block
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            # Third conv block
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            # Fourth conv block
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
            
            # Flatten and project
            nn.Flatten(),
            nn.Linear(256, feature_dim),
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        
    def forward(self, x): # Returns frequency features

        fft_result = torch.fft.fft2(x)
        
        magnitude = torch.abs(fft_result)
        magnitude_log = torch.log(magnitude + 1e-8)
        
        # Shift zero-frequency component to center
        magnitude_log = torch.fft.fftshift(magnitude_log, dim=(-2, -1))
        
        # Extract frequency features using CNN
        freq_features = self.freq_cnn(magnitude_log)
        
        return freq_features

# Test the model
if __name__ == '__main__':
    model = FrequencyCNN(input_channels=3, feature_dim=256)
    
    dummy_input = torch.randn(4, 3, 224, 224)
    output = model(dummy_input)
    
    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")
    print(f"✅ Frequency CNN works!")
    
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
