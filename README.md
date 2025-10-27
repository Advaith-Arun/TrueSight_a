# TrueSight: Visual Forensics Against AI-Generated Human Manipulations

## Team Members
- Abhinav Singh (LORD-VADER66)
- Aditi D (aditisgit)
- Advaith Arun Kashyap (Advaith-Arun)
- Akanksha Lakshmi Acharya (akankshaa0205)

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