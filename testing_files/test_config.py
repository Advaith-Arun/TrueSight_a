import yaml
with open('configs/config.yaml', 'r') as f:
    config = yaml.safe_load(f)
    
print("Config loaded successfully!")
print(f"Data root: {config['paths']['data_root']}")
print(f"Batch size: {config['training']['batch_size']}")
print(f"Num frames: {config['training']['num_frames']}")
print(f"Experiment: {config['experiment']['name']}")