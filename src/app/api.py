"""
Flask API Module

REST API for TrueSight deepfake detection backend.
Provides endpoints for video upload, status checking, and results retrieval.
"""

import os
import uuid
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from .database import DatabaseManager
from .tasks import process_video_task

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for frontend integration
CORS(app, resources={r"/*": {"origins": "*"}})

# Load configuration
config_path = Path("configs/config.yaml")
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# API Configuration
MAX_UPLOAD_SIZE_MB = config['app']['max_upload_size_mb']  # 500 MB from config
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}
UPLOAD_FOLDER = Path("src/app/uploads")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE_BYTES
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize database
db = DatabaseManager()

logger.info("Flask API initialized successfully")
logger.info(f"Max upload size: {MAX_UPLOAD_SIZE_MB} MB")
logger.info(f"Allowed extensions: {ALLOWED_EXTENSIONS}")


def allowed_file(filename: str) -> bool:
    """
    Check if file extension is allowed.
    
    Args:
        filename: Name of uploaded file
    
    Returns:
        True if extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_size_mb(file_path: Path) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to file
    
    Returns:
        File size in MB
    """
    return file_path.stat().st_size / (1024 * 1024)


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response with status
    """
    return jsonify({
        'status': 'ok',
        'message': 'TrueSight API is running',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/upload', methods=['POST'])
def upload_video():
    """
    Upload video endpoint.
    
    Accepts video file, saves it, creates database entry,
    and queues Celery task for processing.
    
    Returns:
        JSON response with job_id and status
    """
    logger.info("Received upload request")
    
    # Check if file is in request
    if 'video' not in request.files:
        logger.warning("No file in request")
        return jsonify({
            'error': 'No video file provided',
            'message': 'Please upload a video file with key "video"'
        }), 400
    
    file = request.files['video']
    
    # Check if filename is empty
    if file.filename == '':
        logger.warning("Empty filename")
        return jsonify({
            'error': 'No file selected',
            'message': 'Please select a video file'
        }), 400
    
    # Check file extension
    if not allowed_file(file.filename):
        logger.warning(f"Invalid file extension: {file.filename}")
        return jsonify({
            'error': 'Invalid file type',
            'message': f'Allowed extensions: {", ".join(ALLOWED_EXTENSIONS)}',
            'allowed_extensions': list(ALLOWED_EXTENSIONS)
        }), 400
    
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Secure the filename and create unique name
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{job_id}.{file_extension}"
        file_path = UPLOAD_FOLDER / unique_filename
        
        # Save uploaded file
        file.save(str(file_path))
        logger.info(f"Saved file: {file_path}")
        
        # Get file size
        file_size_mb = get_file_size_mb(file_path)
        logger.info(f"File size: {file_size_mb:.2f} MB")
        
        # Check file size (should be handled by Flask, but double-check)
        if file_size_mb > MAX_UPLOAD_SIZE_MB:
            file_path.unlink()  # Delete file
            logger.warning(f"File too large: {file_size_mb:.2f} MB")
            return jsonify({
                'error': 'File too large',
                'message': f'Maximum file size is {MAX_UPLOAD_SIZE_MB} MB',
                'file_size_mb': round(file_size_mb, 2),
                'max_size_mb': MAX_UPLOAD_SIZE_MB
            }), 413
        
        # Create database entry
        db.create_job(
            job_id=job_id,
            filename=original_filename,
            file_size_mb=file_size_mb
        )
        logger.info(f"Created database entry for job {job_id}")
        
        # Queue Celery task
        task = process_video_task.delay(job_id, str(file_path))
        logger.info(f"Queued Celery task {task.id} for job {job_id}")
        
        # Return response
        return jsonify({
            'job_id': job_id,
            'status': 'queued',
            'message': 'Video uploaded successfully. Processing started.',
            'filename': original_filename,
            'file_size_mb': round(file_size_mb, 2),
            'task_id': task.id
        }), 202  # 202 Accepted
        
    except Exception as e:
        logger.error(f"Error during upload: {e}")
        logger.exception(e)
        
        # Clean up file if it exists
        if file_path.exists():
            file_path.unlink()
        
        return jsonify({
            'error': 'Upload failed',
            'message': str(e)
        }), 500


@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id: str):
    """
    Get job status endpoint.
    
    Args:
        job_id: Job identifier
    
    Returns:
        JSON response with job status
    """
    logger.info(f"Status request for job {job_id}")
    
    # Retrieve job from database
    job = db.get_job(job_id)
    
    if not job:
        logger.warning(f"Job {job_id} not found")
        return jsonify({
            'error': 'Job not found',
            'message': f'No job with ID {job_id}'
        }), 404
    
    # Return status
    response = {
        'job_id': job.job_id,
        'filename': job.filename,
        'status': job.status,
        'upload_timestamp': job.upload_timestamp.isoformat() if job.upload_timestamp else None,
        'completion_timestamp': job.completion_timestamp.isoformat() if job.completion_timestamp else None
    }
    
    # Add error message if failed
    if job.status == 'failed':
        response['error_message'] = job.error_message
    
    logger.info(f"Job {job_id} status: {job.status}")
    return jsonify(response), 200


@app.route('/results/<job_id>', methods=['GET'])
def get_results(job_id: str):
    """
    Get job results endpoint.
    
    Args:
        job_id: Job identifier
    
    Returns:
        JSON response with complete analysis results
    """
    logger.info(f"Results request for job {job_id}")
    
    # Retrieve job from database
    job = db.get_job(job_id)
    
    if not job:
        logger.warning(f"Job {job_id} not found")
        return jsonify({
            'error': 'Job not found',
            'message': f'No job with ID {job_id}'
        }), 404
    
    # Check if job is completed
    if job.status != 'completed':
        logger.warning(f"Job {job_id} not completed yet (status: {job.status})")
        return jsonify({
            'error': 'Analysis not complete',
            'message': f'Job status is "{job.status}". Please wait for completion.',
            'job_id': job.job_id,
            'status': job.status
        }), 400
    
    # Return complete results
    response = job.to_dict()
    
    logger.info(f"Returning results for job {job_id}: {job.verdict}")
    return jsonify(response), 200


@app.route('/jobs', methods=['GET'])
def get_all_jobs():
    """
    Get all jobs endpoint (for admin/monitoring).
    
    Query parameters:
        - limit: Maximum number of jobs to return (default: 50)
        - offset: Number of jobs to skip (default: 0)
        - status: Filter by status (optional)
    
    Returns:
        JSON response with list of jobs
    """
    logger.info("All jobs request")
    
    # Get query parameters
    limit = request.args.get('limit', default=50, type=int)
    offset = request.args.get('offset', default=0, type=int)
    status_filter = request.args.get('status', default=None, type=str)
    
    # Limit bounds
    limit = min(max(1, limit), 100)  # Between 1 and 100
    
    # Get jobs
    if status_filter:
        jobs = db.get_jobs_by_status(status_filter, limit=limit)
    else:
        jobs = db.get_all_jobs(limit=limit, offset=offset)
    
    # Convert to dict
    jobs_list = [job.to_dict() for job in jobs]
    
    logger.info(f"Returning {len(jobs_list)} jobs")
    
    return jsonify({
        'jobs': jobs_list,
        'count': len(jobs_list),
        'limit': limit,
        'offset': offset
    }), 200


@app.route('/stats', methods=['GET'])
def get_statistics():
    """
    Get database statistics endpoint.
    
    Returns:
        JSON response with statistics
    """
    logger.info("Statistics request")
    
    stats = db.get_statistics()
    
    return jsonify(stats), 200


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify({
        'error': 'File too large',
        'message': f'Maximum file size is {MAX_UPLOAD_SIZE_MB} MB',
        'max_size_mb': MAX_UPLOAD_SIZE_MB
    }), 413


@app.errorhandler(500)
def internal_server_error(error):
    """Handle internal server error."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred. Please try again.'
    }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("TrueSight Backend - Flask API Server")
    print("=" * 60)
    print(f"\nAPI running on http://0.0.0.0:5000")
    print(f"Max upload size: {MAX_UPLOAD_SIZE_MB} MB")
    print(f"Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}")
    print("\nEndpoints:")
    print("  GET  /health         - Health check")
    print("  POST /upload         - Upload video")
    print("  GET  /status/<id>    - Get job status")
    print("  GET  /results/<id>   - Get job results")
    print("  GET  /jobs           - Get all jobs")
    print("  GET  /stats          - Get statistics")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
