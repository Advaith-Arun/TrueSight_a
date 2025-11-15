"""
Celery tasks for asynchronous video processing.
"""

import logging
from celery import Task
from pathlib import Path
import time

from src.app.celery_config import celery_app
from src.app.database import DatabaseManager
from src.app.video_processor import VideoProcessor
from src.app.inference import InferenceEngine

# Configure logging
logger = logging.getLogger(__name__)

# Initialize database manager
db = DatabaseManager()

class CallbackTask(Task):
    """Custom task class that includes callback on completion."""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task completes successfully."""
        logger.info(f"Task {task_id} succeeded: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(f"Task {task_id} failed: {exc}")


@celery_app.task(base=CallbackTask, bind=True)
def process_video_task(self, job_id: str, video_path: str):
    """
    Process a video file: preprocessing -> inference -> save results.
    
    Args:
        job_id: Unique job identifier
        video_path: Path to the uploaded video file
    
    Returns:
        Dictionary with processing results
    """
    logger.info(f"Job {job_id}: Starting video processing...")
    
    start_time = time.time()
    
    try:
        # Update job status to processing
        db.update_status(job_id, 'processing')
        
        # Step 1: Video Preprocessing
        logger.info(f"Job {job_id}: Starting video preprocessing...")
        
        # ✅ FIXED: VideoProcessor doesn't take job_id parameter
        processor = VideoProcessor()
        
        video_tensor = processor.process_video(video_path)
        
        logger.info(f"Job {job_id}: Video preprocessing completed")
        
        # Step 2: Model Inference
        logger.info(f"Job {job_id}: Loading model and running inference...")
        
        # Initialize inference engine with Model 4 settings
        inference_engine = InferenceEngine(
            model_path='models/checkpoints/best_model.pth',
            device='auto',
            threshold=0.5  # Model 4 uses 0.5 threshold
        )
        
        result = inference_engine.predict(video_tensor)
        
        logger.info(f"Job {job_id}: Inference completed - Verdict: {result['verdict']}, Confidence: {result['confidence']}%")
        
        # Step 3: Save results to database
        logger.info(f"Job {job_id}: Saving results to database...")
        
        processing_time = time.time() - start_time
        
        # Save results using the save_results method
        db.save_results(
            job_id=job_id,
            verdict=result['verdict'],
            confidence=result['confidence'],
            probability=result['probability'],
            processing_time_seconds=processing_time
        )
        
        logger.info(f"Job {job_id} completed: {result['verdict']} (confidence: {result['confidence']}%, time: {processing_time:.2f}s)")
        
        # Step 4: Cleanup temporary files
        logger.info(f"Job {job_id}: Cleaning up temporary files...")
        processor.cleanup()
        
        # Delete uploaded video file
        video_file = Path(video_path)
        if video_file.exists():
            video_file.unlink()
            logger.info(f"Job {job_id}: Deleted uploaded video file")
        
        logger.info(f"Job {job_id}: Processing completed successfully in {processing_time:.2f}s")
        
        return {
            'job_id': job_id,
            'status': 'completed',
            'verdict': result['verdict'],
            'confidence': result['confidence'],
            'processing_time': processing_time
        }
    
    except Exception as e:
        logger.error(f"Job {job_id}: Unexpected error: {str(e)}")
        logger.error(str(e), exc_info=True)
        
        # Update job status to failed using set_error method
        db.set_error(job_id, f"Unexpected error: {str(e)}")
        
        # Cleanup on error
        try:
            if 'processor' in locals():
                processor.cleanup()
        except:
            pass
        
        # Try to delete uploaded video even on failure
        try:
            video_file = Path(video_path)
            if video_file.exists():
                video_file.unlink()
        except:
            pass
        
        return {
            'job_id': job_id,
            'status': 'failed',
            'error': f"Unexpected error: {str(e)}"
        }
