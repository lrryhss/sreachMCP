#!/usr/bin/env python3
"""Start a research task directly for testing"""

import requests
import json
import time
import sys

API_URL = "http://localhost:8001"

def create_test_user_and_token():
    """Create a test user and get auth token"""

    # First try to register a test user
    register_data = {
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }

    try:
        # Try to register
        resp = requests.post(f"{API_URL}/api/auth/register", json=register_data)
        if resp.status_code != 201 and resp.status_code != 409:  # 409 means user exists
            print(f"Registration response: {resp.status_code}")
    except:
        pass

    # Now login
    login_data = {
        "username": "test@example.com",
        "password": "testpass123"
    }

    resp = requests.post(
        f"{API_URL}/api/auth/token",
        data=login_data,  # Use form data for OAuth2
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if resp.status_code == 200:
        token_data = resp.json()
        return token_data.get("access_token")

    return None

def start_research(token):
    """Start a quick research task"""

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    research_data = {
        "query": "Test research for progress display - quantum computing basics",
        "depth": "quick",
        "max_sources": 5
    }

    resp = requests.post(
        f"{API_URL}/api/research",
        json=research_data,
        headers=headers
    )

    if resp.status_code in [200, 201]:
        result = resp.json()
        return result.get("task_id")
    else:
        print(f"Failed to start research: {resp.status_code} - {resp.text}")
        return None

def monitor_progress(token, task_id):
    """Monitor research progress until completion"""

    headers = {
        "Authorization": f"Bearer {token}"
    }

    print(f"\nMonitoring progress for task: {task_id}")
    print("-" * 50)

    last_progress = -1

    while True:
        resp = requests.get(
            f"{API_URL}/api/research/{task_id}/status",
            headers=headers
        )

        if resp.status_code == 200:
            status = resp.json()
            progress = status.get("progress", 0)
            task_status = status.get("status", "unknown")

            if progress != last_progress:
                print(f"Progress: {progress}% - Status: {task_status}")
                last_progress = progress

            if task_status == "completed":
                print("\n✓ Research COMPLETED at 100%!")
                return True
            elif task_status == "failed":
                print(f"\n✗ Research failed: {status.get('error')}")
                return False

        time.sleep(2)

def main():
    print("Testing Research Progress Display Fix")
    print("=" * 50)

    # Get auth token
    print("\n1. Getting authentication token...")
    token = create_test_user_and_token()

    if not token:
        print("✗ Failed to get auth token")
        return

    print("✓ Got auth token")

    # Start research
    print("\n2. Starting new research task...")
    task_id = start_research(token)

    if not task_id:
        print("✗ Failed to start research")
        return

    print(f"✓ Started research task: {task_id}")

    # Monitor progress
    print("\n3. Monitoring progress (should reach 100%)...")
    success = monitor_progress(token, task_id)

    if success:
        print(f"\n✓ SUCCESS! Research completed at 100%")
        print(f"\nView results at: http://localhost:3002/research/{task_id}")
    else:
        print("\n✗ Research did not complete successfully")

if __name__ == "__main__":
    main()