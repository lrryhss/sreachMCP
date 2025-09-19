#!/usr/bin/env python3
"""Test script for the Research Agent API with authentication"""

import json
import requests
import time

BASE_URL = "http://localhost:8001"

def test_api():
    print("=" * 50)
    print("Testing Research Agent API with Database")
    print("=" * 50)

    # 1. Login to get token
    print("\n1. Testing login...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "username_or_email": "testuser",
            "password": "securePassword123"
        }
    )

    if login_response.status_code == 200:
        tokens = login_response.json()
        access_token = tokens["access_token"]
        print(f"✓ Login successful! Token: {access_token[:50]}...")
    else:
        print(f"✗ Login failed: {login_response.text}")
        return

    # 2. Create a research task
    print("\n2. Creating research task...")
    headers = {"Authorization": f"Bearer {access_token}"}

    research_response = requests.post(
        f"{BASE_URL}/api/research",
        headers=headers,
        json={
            "query": "What are the latest developments in quantum computing?",
            "depth": "quick",
            "max_sources": 5
        }
    )

    if research_response.status_code == 201:
        task = research_response.json()
        task_id = task["task_id"]
        print(f"✓ Research task created! Task ID: {task_id}")
        print(f"  Status: {task['status']}")
        print(f"  Query: {task['query']}")
    else:
        print(f"✗ Failed to create task: {research_response.text}")
        return

    # 3. Check research history
    print("\n3. Fetching research history...")
    history_response = requests.get(
        f"{BASE_URL}/api/research/history",
        headers=headers,
        params={"limit": 10}
    )

    if history_response.status_code == 200:
        history = history_response.json()
        print(f"✓ Research history retrieved! Found {len(history['tasks'])} tasks")
        for task in history['tasks']:
            print(f"  - {task['task_id']}: {task['query'][:50]}... [{task['status']}]")
    else:
        print(f"✗ Failed to get history: {history_response.text}")

    # 4. Check specific task status
    print(f"\n4. Checking status of task {task_id}...")
    for i in range(5):
        status_response = requests.get(
            f"{BASE_URL}/api/research/{task_id}/status",
            headers=headers
        )

        if status_response.status_code == 200:
            status = status_response.json()
            print(f"  Attempt {i+1}: Status = {status['status']}, Progress = {status['progress']}%")
            if status['status'] in ['completed', 'failed']:
                break
        else:
            print(f"✗ Failed to get status: {status_response.text}")
            break

        time.sleep(2)

    print("\n" + "=" * 50)
    print("Testing complete!")
    print("=" * 50)

if __name__ == "__main__":
    test_api()