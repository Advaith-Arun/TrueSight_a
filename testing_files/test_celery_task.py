"""
Test script for Celery task.
Tests the complete video processing pipeline asynchronously.

NOTE: This requires Redis and Celery worker to be running!

Terminal 1: python src/app/run_celery.py
Terminal 2: python testing_files/test_celery_task.py
"""

import sys
import time
import uuid
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.app.tasks import process_video_task
from src.app.database import DatabaseManager

print("=" * 60)
print("TrueSight Backend - Celery Task Test")
print("=" * 60)

# Prerequisites check
print("\n⚠️  PREREQUISITES:")
print("1. Redis server must be running (redis-cli ping)")
print("2. Celery worker must be running in another terminal:")
print("   python src/app/run_celery.py\n")

input("Press Enter to continue if prerequisites are met...")

# Find a test video
test_video_dirs = [
    project_root / "data" / "test" / "real",
    project_root / "data" / "test" / "fake",
]

test_video = None
for test_dir in test_video_dirs:
    if test_dir.exists():
        videos = list(test_dir.rglob("*.mp4"))
        if videos:
            test_video = videos[0]
            break

if test_video is None:
    print("❌ No test video found")
    sys.exit(1)

print(f"\n📹 Test video: {test_video}")

# Copy video to temporary location (since task will delete it)
temp_upload_dir = project_root / "src" / "app" / "uploads"
temp_upload_dir.mkdir(parents=True, exist_ok=True)

job_id = str(uuid.uuid4())
temp_video_path = temp_upload_dir / f"{job_id}.mp4"
shutil.copy(test_video, temp_video_path)

print(f"📁 Copied to: {temp_video_path}")

# Create database entry
db = DatabaseManager()
file_size_mb = temp_video_path.stat().st_size / (1024 * 1024)
db.create_job(job_id, test_video.name, file_size_mb)

print(f"📝 Created database entry with job_id: {job_id}")

# Queue the task
print("\n[1/3] Queuing Celery task...")
try:
    task = process_video_task.delay(job_id, str(temp_video_path))
    print(f"✅ Task queued with ID: {task.id}")
    print(f"   Job ID: {job_id}")
except Exception as e:
    print(f"❌ Failed to queue task: {e}")
    print("\n⚠️  Make sure:")
    print("   1. Redis is running: redis-cli ping")
    print("   2. Celery worker is running: python src/app/run_celery.py")
    sys.exit(1)

# Poll for completion
print("\n[2/3] Waiting for task to complete...")
print("   (This may take 10-30 seconds...)\n")

max_wait = 120  # 2 minutes timeout
start_time = time.time()
last_status = None

while time.time() - start_time < max_wait:
    job = db.get_job(job_id)
    
    if job.status != last_status:
        print(f"   Status: {job.status}")
        last_status = job.status
    
    if job.status == 'completed':
        print("\n✅ Task completed successfully!")
        break
    elif job.status == 'failed':
        print(f"\n❌ Task failed: {job.error_message}")
        break
    
    time.sleep(2)  # Check every 2 seconds
else:
    print(f"\n⏰ Timeout after {max_wait} seconds")
    print("   Task may still be processing...")

# Display results
print("\n[3/3] Retrieving results...")
job = db.get_job(job_id)

if job:
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Job ID: {job.job_id}")
    print(f"Filename: {job.filename}")
    print(f"Status: {job.status}")
    
    if job.status == 'completed':
        print(f"Verdict: {job.verdict}")
        print(f"Confidence: {job.confidence}%")
        print(f"Probability: {job.probability}")
        print(f"Processing Time: {job.processing_time_seconds:.2f}s")
        print("\n✅ Celery task test PASSED!")
    elif job.status == 'failed':
        print(f"Error: {job.error_message}")
        print("\n❌ Task failed")
    else:
        print(f"\n⚠️  Task still {job.status}")
    
    print("=" * 60)
else:
    print("❌ Could not retrieve job from database")

print("\nNext step: Proceed to Phase 6 (Flask API Development)")
