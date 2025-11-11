"""
Celery Configuration Module

Configures Celery app for asynchronous video processing tasks.
Uses Redis as message broker and result backend.
"""

from celery import Celery
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    'truesight_backend',
    broker='redis://localhost:6379/0',  # Redis database 0 for broker
    backend='redis://localhost:6379/1',  # Redis database 1 for results
    include=['src.app.tasks']  # Include tasks module
)

# Configure Celery
celery_app.conf.update(
    # Task execution settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task time limits
    task_time_limit=300,  # Hard limit: 5 minutes
    task_soft_time_limit=240,  # Soft limit: 4 minutes
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)
    
    # Task acknowledgment
    task_acks_late=True,  # Acknowledge task after completion (enables retry on failure)
    task_reject_on_worker_lost=True,  # Reject task if worker crashes
    
    # Result expiration
    result_expires=3600,  # Results expire after 1 hour
    
    # Logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s',
)

logger.info("Celery app configured successfully")
