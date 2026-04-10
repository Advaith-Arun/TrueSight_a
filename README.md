# TrueSight: Visual Forensics Against AI-Generated Human Manipulations

## Team Members
- Abhinav Singh (LORD-VADER66)
- Aditi D (aditisgit)
- Advaith Arun Kashyap (Advaith-Arun)
- Akanksha Lakshmi Acharya (akankshaa0205)

## Project Description
TrueSight is a production-ready deepfake detection system that achieves 87% validation accuracy and 84% Recall on FaceForensics++ and Celeb-DF datasets through advanced spatiotemporal modeling and robust preprocessing.

## Key Features
1. Face-Centric Preprocessing using MTCNN for 3-5% accuracy boost.
2. Multi-Modal Architecture:
  - Spatial CNN (ResNet-50)
  - Frequency CNN (EfficientNet-B0)
  - Spatiotemporal LSTM (Bi-LSTM)
  - Late fusion ensemble
3. Video Training Set:
  - 1000 Videos from FaceForensics++: https://www.kaggle.com/datasets/xdxd003/ff-c23
  - 6,229 Videos from Celeb-DF (v2): https://www.kaggle.com/datasets/reubensuju/celeb-df-v2
4. Strong Data Augmentation (rotation, color jitter, compression simulation)
5. Optimized Training with NVIDIA GeForce RTX 4060
6. Config-Driven (YAML for easy hyperparameter tuning)

## Quick Start

### 1. Clone Repository

git clone <https://github.com/Advaith-Arun/TrueSight_a.git>
cd TrueSight

### 2. Environment Setup

Make setup script executable (Linux/Mac)
chmod +x setup_env.sh
./setup_env.sh

Or manually:
python -m venv truesight_env
truesight_env\Scripts\activate # Windows
source truesight_env/bin/activate # Linux/Mac
pip install -r requirements.txt

### 3. Download Datasets
Place FaceForensics++ dataset in `data/datasets/faceforensics/`

### 4. Run Training
python src/training/train.py --config configs/config.yaml

### 5. Launch Application
streamlit run src/app/streamlit_app.py

## Project Structure
- `src/`: Source code modules
- `data/`: Dataset storage
- `models/`: Model checkpoints
- `configs/`: Configuration files
- `notebooks/`: Jupyter experiments
- `logs/`: Training logs
