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
from src.app.config_loader import get_config

# Configure logging
logger = logging.getLogger(__name__)

# Initialize database manager
db = DatabaseManager()

def cleanup_old_uploads(upload_dir='src/app/uploads', max_age_hours=24):
    """Delete uploaded videos older than max_age_hours."""
    upload_path = Path(upload_dir)
    if not upload_path.exists():
        return
    
    current_time = time.time()
    for video_file in upload_path.glob('*.mp4'):
        # Check file age
        file_age_hours = (current_time - video_file.stat().st_mtime) / 3600
        if file_age_hours > max_age_hours:
            video_file.unlink()
            logger.info(f"Deleted old upload: {video_file.name} (age: {file_age_hours:.1f} hours)")

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
    cleanup_old_uploads()
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
        
        config = get_config()
        if config.is_gradcam_enabled():
            logger.info(f"Job {job_id}: Grad-CAM enabled - generating explainability visualizations...")
            result = inference_engine.predict_with_gradcam(
                video_tensor=video_tensor,
                raw_frames=None
            )
        else:
            logger.info(f"Job {job_id}: Running standard inference...")
            result = inference_engine.predict(video_tensor)

        logger.info(f"Job {job_id}: Inference completed - Verdict: {result['verdict']}, Confidence: {result['confidence']}%")
        
        # ✨ NEW: Save Grad-CAM visualizations if generated
        gradcam_dir = None
        gradcam_avg_path = None
        gradcam_frame_count = 0

        if result.get('gradcam_enabled') and result.get('gradcam') is not None:
            try:
                logger.info(f"Job {job_id}: Saving Grad-CAM visualizations...")
                
                # Get Grad-CAM config
                gradcam_config = config.get_gradcam_config()
                base_output_dir = Path(gradcam_config.get('output_dir', 'results/gradcam'))
                
                # Create job-specific directory
                job_output_dir = base_output_dir / job_id
                job_output_dir.mkdir(parents=True, exist_ok=True)
                
                gradcam_result = result['gradcam']
                
                # Save individual overlays if enabled
                if gradcam_config.get('save_overlays', True):
                    from PIL import Image
                    overlays_dir = job_output_dir / 'overlays'
                    overlays_dir.mkdir(exist_ok=True)
                    
                    for idx, overlay in enumerate(gradcam_result['overlays']):
                        overlay_img = Image.fromarray(overlay)
                        overlay_path = overlays_dir / f'frame_{idx:03d}_overlay.jpg'
                        overlay_img.save(overlay_path, quality=95)
                    
                    logger.info(f"Job {job_id}: Saved {len(gradcam_result['overlays'])} overlay images")
                
                # Save average heatmap if enabled
                if gradcam_config.get('save_average_heatmap', True):
                    from PIL import Image
                    avg_heatmap = Image.fromarray(gradcam_result['avg_heatmap'])
                    gradcam_avg_path = str(job_output_dir / 'average_heatmap.jpg')
                    avg_heatmap.save(gradcam_avg_path, quality=95)
                    logger.info(f"Job {job_id}: Saved average heatmap to {gradcam_avg_path}")
                
                gradcam_dir = str(job_output_dir)
                gradcam_frame_count = gradcam_result['num_frames']
                
                logger.info(f"Job {job_id}: ✅ Grad-CAM visualizations saved to {gradcam_dir}")
                
            except Exception as e:
                logger.error(f"Job {job_id}: ⚠️  Failed to save Grad-CAM visualizations: {e}")
                # Don't fail the job, just log the error



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
        
        #Update Grad-CAM paths if generated
        if gradcam_dir is not None:
            db.update_gradcam_paths(
                job_id=job_id,
                gradcam_dir=gradcam_dir,
                avg_heatmap_path=gradcam_avg_path or '',
                frame_count=gradcam_frame_count
            )
            logger.info(f"Job {job_id}: ✅ Updated database with Grad-CAM paths")

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
