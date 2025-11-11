"""
Celery Tasks Module

Defines asynchronous tasks for video processing and deepfake detection.
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any

from .celery_config import celery_app
from .video_processor import VideoProcessor
from .inference import InferenceEngine
from .database import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(name='process_video_task', bind=True)
def process_video_task(self, job_id: str, video_path: str) -> Dict[str, Any]:
    """
    Asynchronous task to process a video for deepfake detection.
    
    This task:
    1. Updates job status to 'processing'
    2. Extracts and preprocesses video frames
    3. Runs inference with the trained model
    4. Saves results to database
    5. Cleans up temporary files
    
    Args:
        self: Celery task instance (for retry/logging)
        job_id: Unique job identifier
        video_path: Path to uploaded video file
    
    Returns:
        Dictionary with processing results
    """
    start_time = time.time()
    video_path = Path(video_path)
    temp_output_dir = None
    
    logger.info(f"Starting video processing for job {job_id}")
    logger.info(f"Video: {video_path}")
    
    # Initialize components
    db = DatabaseManager()
    video_processor = VideoProcessor()
    inference_engine = None  # Initialize lazily to save memory
    
    try:
        # Step 1: Update status to processing
        logger.info(f"Job {job_id}: Updating status to 'processing'")
        db.update_status(job_id, 'processing')
        
        # Step 2: Check if video file exists
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Step 3: Process video (extract frames, detect faces, crop)
        logger.info(f"Job {job_id}: Processing video...")
        video_tensor, temp_output_dir = video_processor.process_video(
            video_path=video_path,
            num_frames=8
        )
        logger.info(f"Job {job_id}: Video preprocessing completed")
        
        # Step 4: Run inference
        logger.info(f"Job {job_id}: Loading model and running inference...")
        inference_engine = InferenceEngine(
            config_path="configs/config.yaml",
            checkpoint_path="models/checkpoints/best_model.pth",
            threshold=0.3
        )
        
        result = inference_engine.predict(video_tensor)
        logger.info(
            f"Job {job_id}: Inference completed - "
            f"Verdict: {result['verdict']}, Confidence: {result['confidence']:.2f}%"
        )
        
        # Step 5: Calculate processing time
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Step 6: Save results to database
        logger.info(f"Job {job_id}: Saving results to database...")
        db.save_results(
            job_id=job_id,
            verdict=result['verdict'],
            confidence=result['confidence'],
            probability=result['probability'],
            processing_time_seconds=processing_time
        )
        
        # Step 7: Cleanup temporary files
        logger.info(f"Job {job_id}: Cleaning up temporary files...")
        if temp_output_dir and temp_output_dir.exists():
            video_processor.cleanup(temp_output_dir)
        
        if video_path.exists():
            video_path.unlink()  # Delete uploaded video
            logger.info(f"Job {job_id}: Deleted uploaded video file")
        
        logger.info(
            f"Job {job_id}: Processing completed successfully in {processing_time:.2f}s"
        )
        
        return {
            'job_id': job_id,
            'status': 'completed',
            'verdict': result['verdict'],
            'confidence': result['confidence'],
            'processing_time': processing_time
        }
        
    except FileNotFoundError as e:
        # Handle missing video file
        error_msg = f"Video file not found: {str(e)}"
        logger.error(f"Job {job_id}: {error_msg}")
        
        db.set_error(job_id, error_msg)
        
        # Cleanup
        if temp_output_dir and temp_output_dir.exists():
            video_processor.cleanup(temp_output_dir)
        if video_path.exists():
            video_path.unlink()
        
        return {
            'job_id': job_id,
            'status': 'failed',
            'error': error_msg
        }
        
    except ValueError as e:
        # Handle preprocessing errors (e.g., no faces detected)
        error_msg = f"Preprocessing error: {str(e)}"
        logger.error(f"Job {job_id}: {error_msg}")
        
        db.set_error(job_id, error_msg)
        
        # Cleanup
        if temp_output_dir and temp_output_dir.exists():
            video_processor.cleanup(temp_output_dir)
        if video_path.exists():
            video_path.unlink()
        
        return {
            'job_id': job_id,
            'status': 'failed',
            'error': error_msg
        }
        
    except Exception as e:
        # Handle any other errors
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Job {job_id}: {error_msg}")
        logger.exception(e)  # Log full traceback
        
        db.set_error(job_id, error_msg)
        
        # Cleanup (best effort)
        try:
            if temp_output_dir and temp_output_dir.exists():
                video_processor.cleanup(temp_output_dir)
            if video_path.exists():
                video_path.unlink()
        except Exception as cleanup_error:
            logger.error(f"Job {job_id}: Cleanup failed: {cleanup_error}")
        
        return {
            'job_id': job_id,
            'status': 'failed',
            'error': error_msg
        }
