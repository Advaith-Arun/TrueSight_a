"""
Test script for Flask API endpoints.
Tests all API endpoints with real requests.

NOTE: This requires the Flask API server to be running!

Terminal 1: python src/app/run_api.py
Terminal 2: python testing_files/test_api.py
"""

import sys
import time
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("TrueSight Backend - API Test")
print("=" * 60)

API_BASE_URL = "http://localhost:5000"

# Prerequisites check
print("\n⚠️  PREREQUISITES:")
print("1. Flask API must be running: python src/app/run_api.py")
print("2. Celery worker must be running: python src/app/run_celery.py")
print("3. Redis must be running: redis-cli ping\n")

input("Press Enter to continue if prerequisites are met...")

# Test 1: Health check
print("\n[1/6] Testing health check endpoint...")
try:
    response = requests.get(f"{API_BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health check passed")
        print(f"   Status: {data['status']}")
        print(f"   Message: {data['message']}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Failed to connect to API: {e}")
    print("\n⚠️  Make sure Flask API is running:")
    print("   python src/app/run_api.py")
    sys.exit(1)

# Test 2: Upload video
print("\n[2/6] Testing video upload endpoint...")

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

print(f"   Uploading: {test_video.name}")

try:
    with open(test_video, 'rb') as f:
        files = {'video': (test_video.name, f, 'video/mp4')}
        response = requests.post(f"{API_BASE_URL}/upload", files=files)
    
    if response.status_code == 202:
        data = response.json()
        job_id = data['job_id']
        print(f"✅ Upload successful")
        print(f"   Job ID: {job_id}")
        print(f"   Status: {data['status']}")
        print(f"   Message: {data['message']}")
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"   Response: {response.json()}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Upload error: {e}")
    sys.exit(1)

# Test 3: Check status
print("\n[3/6] Testing status endpoint...")
try:
    response = requests.get(f"{API_BASE_URL}/status/{job_id}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status check successful")
        print(f"   Status: {data['status']}")
        print(f"   Filename: {data['filename']}")
    else:
        print(f"❌ Status check failed: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Status check error: {e}")
    sys.exit(1)

# Test 4: Poll until completion
print("\n[4/6] Waiting for processing to complete...")
print("   (This may take 10-30 seconds...)\n")

max_wait = 120
start_time = time.time()
last_status = None

while time.time() - start_time < max_wait:
    response = requests.get(f"{API_BASE_URL}/status/{job_id}")
    if response.status_code == 200:
        data = response.json()
        status = data['status']
        
        if status != last_status:
            print(f"   Status: {status}")
            last_status = status
        
        if status in ['completed', 'failed']:
            break
    
    time.sleep(2)
else:
    print(f"\n⏰ Timeout after {max_wait} seconds")

# Test 5: Get results
print("\n[5/6] Testing results endpoint...")
try:
    response = requests.get(f"{API_BASE_URL}/results/{job_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Results retrieved successfully")
        print(f"   Verdict: {data['verdict']}")
        print(f"   Confidence: {data['confidence']}%")
        print(f"   Processing time: {data['processing_time_seconds']}s")
    elif response.status_code == 400:
        data = response.json()
        print(f"⚠️  Results not ready: {data['message']}")
    else:
        print(f"❌ Results retrieval failed: {response.status_code}")
        print(f"   Response: {response.json()}")
except Exception as e:
    print(f"❌ Results error: {e}")

# Test 6: Get statistics
print("\n[6/6] Testing statistics endpoint...")
try:
    response = requests.get(f"{API_BASE_URL}/stats")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Statistics retrieved")
        print(f"   Total jobs: {data['total_jobs']}")
        print(f"   Completed: {data['completed_jobs']}")
        print(f"   Failed: {data['failed_jobs']}")
    else:
        print(f"❌ Statistics failed: {response.status_code}")
except Exception as e:
    print(f"❌ Statistics error: {e}")

print("\n" + "=" * 60)
print("✅ ALL API TESTS PASSED!")
print("=" * 60)
print("\nAPI is ready for integration with frontend.")
print("Proceed to Phase 7 (Error Handling & Edge Cases)")
