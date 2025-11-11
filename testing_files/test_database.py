"""
Test script for DatabaseManager.
Tests all database operations including CRUD and statistics.
"""

import sys
import uuid
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.app.database import DatabaseManager, get_database

print("=" * 60)
print("TrueSight Backend - Database Test")
print("=" * 60)

# Use a test database (not the production one)
test_db_path = "results/test_truesight.db"

# Clean up test database if it exists
test_db_file = Path(test_db_path)
if test_db_file.exists():
    test_db_file.unlink()
    print("Cleaned up previous test database")

# Test 1: Create DatabaseManager
print("\n[1/8] Creating DatabaseManager...")
try:
    db = DatabaseManager(db_path=test_db_path)
    print(f"✅ Database created at: {test_db_path}")
    print(f"   Database file size: {test_db_file.stat().st_size} bytes")
except Exception as e:
    print(f"❌ Failed to create database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Create jobs
print("\n[2/8] Creating test jobs...")
try:
    job_id_1 = str(uuid.uuid4())
    job_id_2 = str(uuid.uuid4())
    job_id_3 = str(uuid.uuid4())
    
    job1 = db.create_job(job_id_1, "test_video_1.mp4", 2.5)
    job2 = db.create_job(job_id_2, "test_video_2.mp4", 3.8)
    job3 = db.create_job(job_id_3, "test_video_3.mp4", 1.2)
    
    print(f"✅ Created 3 test jobs")
    print(f"   Job 1: {job_id_1[:8]}... - {job1.filename}")
    print(f"   Job 2: {job_id_2[:8]}... - {job2.filename}")
    print(f"   Job 3: {job_id_3[:8]}... - {job3.filename}")
except Exception as e:
    print(f"❌ Failed to create jobs: {e}")
    sys.exit(1)

# Test 3: Retrieve job
print("\n[3/8] Retrieving job by ID...")
try:
    retrieved_job = db.get_job(job_id_1)
    if retrieved_job:
        print(f"✅ Retrieved job: {retrieved_job.filename}")
        print(f"   Status: {retrieved_job.status}")
        print(f"   File size: {retrieved_job.file_size_mb} MB")
        print(f"   Upload time: {retrieved_job.upload_timestamp}")
    else:
        print("❌ Job not found")
        sys.exit(1)
except Exception as e:
    print(f"❌ Failed to retrieve job: {e}")
    sys.exit(1)

# Test 4: Update status
print("\n[4/8] Updating job status...")
try:
    success = db.update_status(job_id_1, 'processing')
    if success:
        updated_job = db.get_job(job_id_1)
        print(f"✅ Status updated to: {updated_job.status}")
    else:
        print("❌ Failed to update status")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error updating status: {e}")
    sys.exit(1)

# Test 5: Save results
print("\n[5/8] Saving analysis results...")
try:
    success = db.save_results(
        job_id=job_id_1,
        verdict="Fake",
        confidence=73.45,
        probability=0.7345,
        processing_time_seconds=12.5
    )
    if success:
        completed_job = db.get_job(job_id_1)
        print(f"✅ Results saved:")
        print(f"   Verdict: {completed_job.verdict}")
        print(f"   Confidence: {completed_job.confidence}%")
        print(f"   Processing time: {completed_job.processing_time_seconds}s")
        print(f"   Status: {completed_job.status}")
    else:
        print("❌ Failed to save results")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error saving results: {e}")
    sys.exit(1)

# Test 6: Set error
print("\n[6/8] Testing error handling...")
try:
    success = db.set_error(job_id_2, "Test error: No faces detected")
    if success:
        failed_job = db.get_job(job_id_2)
        print(f"✅ Error set:")
        print(f"   Status: {failed_job.status}")
        print(f"   Error: {failed_job.error_message}")
    else:
        print("❌ Failed to set error")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error setting error: {e}")
    sys.exit(1)

# Test 7: Get all jobs
print("\n[7/8] Retrieving all jobs...")
try:
    all_jobs = db.get_all_jobs(limit=10)
    print(f"✅ Retrieved {len(all_jobs)} jobs:")
    for job in all_jobs:
        print(f"   - {job.filename}: {job.status}")
except Exception as e:
    print(f"❌ Failed to retrieve jobs: {e}")
    sys.exit(1)

# Test 8: Get statistics
print("\n[8/8] Getting database statistics...")
try:
    stats = db.get_statistics()
    print(f"✅ Statistics:")
    print(f"   Total jobs: {stats['total_jobs']}")
    print(f"   Completed: {stats['completed_jobs']}")
    print(f"   Failed: {stats['failed_jobs']}")
    print(f"   Processing: {stats['processing_jobs']}")
    print(f"   Queued: {stats['queued_jobs']}")
    print(f"   Real videos: {stats['real_videos']}")
    print(f"   Fake videos: {stats['fake_videos']}")
except Exception as e:
    print(f"❌ Failed to get statistics: {e}")
    sys.exit(1)

# Test 9: Test to_dict() method
print("\n[9/9] Testing JSON serialization...")
try:
    job_dict = completed_job.to_dict()
    print("✅ Job serialized to dictionary:")
    import json
    print(json.dumps(job_dict, indent=2))
except Exception as e:
    print(f"❌ Failed to serialize: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL DATABASE TESTS PASSED!")
print("=" * 60)
print(f"\nTest database created at: {test_db_path}")
print("Database is ready for integration.")
print("\nNext step: Proceed to Phase 5 (Celery Task Queue)")

# Clean up test database
if test_db_file.exists():
    test_db_file.unlink()
    print(f"\n🧹 Cleaned up test database")
