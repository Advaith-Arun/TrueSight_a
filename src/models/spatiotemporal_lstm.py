import torch
import torch.nn as nn

class SpatioTemporalLSTM(nn.Module):
    def __init__(self, input_dim=768, hidden_size=512, num_layers=2, dropout=0.3):
        super(SpatioTemporalLSTM, self).__init__()
        
        self.input_dim = input_dim
        self.hidden_size = hidden_size
        
        # Bidirectional LSTM
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )
        
        # Multi-head attention (for focusing on key frames)
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size * 2,  # *2 because bidirectional
            num_heads=8,
            dropout=dropout,
            batch_first=True
        )
        
        # Temporal feature projection
        self.temporal_proj = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
    def forward(self, spatial_features): # Takes spatial features and outputs temporal features

        lstm_out, (h_n, c_n) = self.lstm(spatial_features)
        
        # Apply self-attention to focus on important frames
        attended, attention_weights = self.attention(
            lstm_out, lstm_out, lstm_out
        )
        
        temporal_features = attended.mean(dim=1) 
        
        # Project to final feature space
        temporal_features = self.temporal_proj(temporal_features)
        
        return temporal_features

# Test the model
if __name__ == '__main__':
    
    model = SpatioTemporalLSTM(input_dim=768, hidden_size=512, num_layers=2)
    
    dummy_input = torch.randn(4, 16, 768)
    output = model(dummy_input)
    
    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")
    print(f"✅ Spatiotemporal LSTM works!")
    
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
