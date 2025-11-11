"""
Celery Worker Runner

Script to start the Celery worker for processing video tasks.

Usage:
    python src/app/run_celery.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.app.celery_config import celery_app

if __name__ == '__main__':
    print("=" * 60)
    print("TrueSight Backend - Celery Worker")
    print("=" * 60)
    print("\nStarting Celery worker for video processing...")
    print("Press Ctrl+C to stop\n")
    
    # Start worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=1',  # Process one video at a time
        '--pool=solo',  # Use solo pool (simpler, good for development)
    ])
