import torch
import torch.nn as nn
import yaml
from pathlib import Path
import sys

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import your models (absolute imports)
from models.spatial_cnn import SpatialCNN
from models.frequency_cnn import FrequencyCNN
from models.spatiotemporal_lstm import SpatioTemporalLSTM

class TrueSightEnsemble(nn.Module):

    def __init__(self, config=None):
        super(TrueSightEnsemble, self).__init__()
        
        if config is None:
            config_path = Path(__file__).parent.parent.parent / 'configs' / 'config.yaml'
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        
        # Extract model configurations
        spatial_config = config['model']['spatial']
        freq_config = config['model']['frequency']
        lstm_config = config['model']['spatiotemporal']
        ensemble_config = config['model']['ensemble']
        
        # Initialize three branches
        self.spatial_cnn = SpatialCNN(
            pretrained=spatial_config['pretrained'],
            feature_dim=spatial_config['feature_dim']
        )
        
        self.frequency_cnn = FrequencyCNN(
            input_channels=3,
            feature_dim=freq_config['feature_dim']
        )
        
        # Combined feature dimension for LSTM
        combined_dim = spatial_config['feature_dim'] + freq_config['feature_dim']
        
        self.lstm = SpatioTemporalLSTM(
            input_dim=combined_dim,
            hidden_size=lstm_config['lstm_hidden_size'],
            num_layers=lstm_config['lstm_num_layers'],
            dropout=lstm_config['dropout']
        )
        
        classifier_input = lstm_config['lstm_hidden_size']
        self.classifier = nn.Sequential(
            nn.Linear(classifier_input, ensemble_config['classifier_hidden']),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(ensemble_config['classifier_hidden'], 1)  # Binary classification
        )
        
        # if hasattr(self.spatial_cnn.backbone, 'gradient_checkpointing_enable'):
        #     self.spatial_cnn.backbone.gradient_checkpointing_enable()
        
    def forward(self, video_frames):

        batch_size, seq_len = video_frames.shape[:2] # Even if batch_size is not used, it is useful for holding the batch size data in place
        
        # Process each frame through spatial and frequency branches
        frame_features = []
        for t in range(seq_len):
            frame = video_frames[:, t]
            
            spatial_feat = self.spatial_cnn(frame)
            freq_feat = self.frequency_cnn(frame)
            
            combined_feat = torch.cat([spatial_feat, freq_feat], dim=1) 
            frame_features.append(combined_feat)
        
        frame_features = torch.stack(frame_features, dim=1)
        temporal_features = self.lstm(frame_features)
        
        logits = self.classifier(temporal_features)
        
        return logits
    
    def predict(self, video_frames):
        
        self.eval()
        with torch.no_grad():
            logits = self.forward(video_frames)
            probabilities = torch.sigmoid(logits).squeeze()
            predictions = (probabilities > 0.5).long()
        
        return predictions, probabilities
    
if __name__ == '__main__':
    print("="*70)
    print("TESTING TRUESIGHT ENSEMBLE MODEL (ensemble.py)")
    print("="*70)
    
    # Load config to get num_frames
    try:
        default_config_path = Path(__file__).parent.parent.parent / 'configs' / 'config.yaml'
        with open(default_config_path, 'r') as f:
            test_config = yaml.safe_load(f)
        
        NUM_FRAMES = test_config['data']['num_frames']
        print(f"✓ Loaded config. Using num_frames = {NUM_FRAMES}")
        
        print("\n1️⃣  Initializing model...")
        # We pass the config to the constructor
        model = TrueSightEnsemble(config=test_config)
        print("   ✅ Model initialized successfully.")
        
        print("\n2️⃣  Creating test input...")
        # Shape: [batch_size, num_frames, channels, height, width]
        dummy_input = torch.randn(2, NUM_FRAMES, 3, 224, 224)
        print(f"   Input shape: {dummy_input.shape}")
        
        print("\n3️⃣  Running forward pass...")
        output_logits = model(dummy_input)
        print(f"   ✅ Forward pass successful.")
        print(f"   Output logits shape: {output_logits.shape} (Expected: [2, 1])")
        
        print("\n4️⃣  Running predict method...")
        predictions, probabilities = model.predict(dummy_input)
        print(f"   ✅ Predict method successful.")
        print(f"   Predictions: {predictions}")
        print(f"   Probabilities: {probabilities}")

        print("\n5️⃣  Model statistics:")
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(f"   Total parameters: {total_params:,}")
        print(f"   Trainable parameters: {trainable_params:,}")
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED! Ensemble is ready for training.")
        print("="*70)
        
    except FileNotFoundError:
        print("\n❌ ERROR: Could not find 'configs/config.yaml'.")
        print("   Please run this test from the project's root directory.")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    