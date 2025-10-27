#!/bin/bash

echo "Setting up TrueSight environment..."

# Create virtual environment
python -m venv truesight_env

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source truesight_env/Scripts/activate
else
    source truesight_env/bin/activate
fi

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p data/{raw,processed,datasets}
mkdir -p models/{checkpoints,trained,pretrained}
mkdir -p logs/tensorboard
mkdir -p results
mkdir -p notebooks/experiments
mkdir -p tests

# Create .gitkeep files
touch data/raw/.gitkeep
touch data/processed/.gitkeep
touch models/checkpoints/.gitkeep
touch models/trained/.gitkeep
touch logs/.gitkeep
touch results/.gitkeep

echo "Environment setup complete!"
echo "Activate the environment with:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "  truesight_env\\Scripts\\activate"
else
    echo "  source truesight_env/bin/activate"
fi
