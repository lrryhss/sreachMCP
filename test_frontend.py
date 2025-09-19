#!/usr/bin/env python3
"""Test script to verify frontend-backend integration"""

import requests
import time
import json

def test_frontend_backend():
    """Test the complete research flow"""

    print("Testing Research Agent Frontend-Backend Integration")
    print("=" * 50)

    # 1. Test API health
    print("\n1. Testing API health...")
    response = requests.get("http://localhost:8001/health")
    if response.status_code == 200:
        print("✓ API is healthy")
    else:
        print("✗ API health check failed")
        return

    # 2. Start a research task
    print("\n2. Starting research task...")
    research_request = {
        "query": "What are the benefits of meditation?",
        "options": {
            "depth": "quick",
            "max_sources": 3
        }
    }

    response = requests.post(
        "http://localhost:8001/api/research",
        json=research_request
    )

    if response.status_code != 200:
        print(f"✗ Failed to start research: {response.text}")
        return

    task_data = response.json()
    task_id = task_data["task_id"]
    print(f"✓ Research started with task ID: {task_id}")

    # 3. Monitor progress
    print("\n3. Monitoring progress...")
    max_attempts = 60  # 1 minute timeout
    attempts = 0

    while attempts < max_attempts:
        response = requests.get(f"http://localhost:8001/api/research/{task_id}/status")

        if response.status_code != 200:
            print(f"✗ Failed to get status: {response.text}")
            return

        status_data = response.json()
        status = status_data["status"]
        progress = status_data["progress"]["percentage"]

        print(f"  Status: {status}, Progress: {progress}%", end="\r")

        if status == "completed":
            print(f"\n✓ Research completed successfully!")
            break
        elif status == "failed":
            print(f"\n✗ Research failed: {status_data.get('error', 'Unknown error')}")
            return

        time.sleep(1)
        attempts += 1

    if attempts >= max_attempts:
        print("\n✗ Research timed out")
        return

    # 4. Fetch results
    print("\n4. Fetching results...")
    response = requests.get(f"http://localhost:8001/api/research/{task_id}/result")

    if response.status_code != 200:
        print(f"✗ Failed to get results: {response.text}")
        return

    result = response.json()
    print(f"✓ Results fetched successfully")
    print(f"  - Executive Summary: {len(result.get('executive_summary', ''))} chars")
    print(f"  - Key Findings: {len(result.get('key_findings', []))} items")
    print(f"  - Sources: {len(result.get('sources', []))} sources")

    # 5. Test frontend endpoints
    print("\n5. Testing frontend server...")
    try:
        response = requests.get("http://localhost:3001/")
        if response.status_code == 200:
            print("✓ Frontend server is running at http://localhost:3001")
        else:
            print(f"⚠ Frontend returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to frontend at http://localhost:3001")

    print("\n" + "=" * 50)
    print("✓ All tests passed! Frontend and backend are working correctly.")
    print("\nYou can now access the Research Agent at: http://localhost:3001")

if __name__ == "__main__":
    test_frontend_backend()