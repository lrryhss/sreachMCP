#!/usr/bin/env python3
"""Test research without authentication - for testing progress display fix"""

import requests
import time
import json

API_URL = "http://localhost:8001"

def test_research():
    print("Starting Quick Research Test")
    print("=" * 50)

    # Skip authentication and use the test endpoint if available
    # or create a mock research task

    # Check if there's a recent completed task we can check
    print("\n1. Checking for recent completed research task...")

    # The task that completed earlier
    task_id = "res_435a74afa92d"

    print(f"\n2. Checking status of task: {task_id}")

    # Try to get status without auth (this might work for testing)
    try:
        # Check the backend logs directly for the status
        import subprocess
        result = subprocess.run(
            ["docker", "logs", "research-agent", "--tail", "200"],
            capture_output=True,
            text=True
        )

        # Look for the task completion in logs
        if f"{task_id}.*100.*completed" in result.stderr or f"{task_id}.*100.*completed" in result.stdout:
            print("✓ Task shows as COMPLETED at 100% in backend logs")
        else:
            # Find the last status update for this task
            lines = (result.stderr + result.stdout).split('\n')
            for line in reversed(lines):
                if task_id in line and "progress=" in line:
                    print(f"Last status found: {line}")
                    break
    except Exception as e:
        print(f"Could not check backend logs: {e}")

    print("\n3. Testing frontend display...")
    print("Navigate to http://localhost:3002/research/" + task_id)
    print("The progress should show 100% if the fix is working")

if __name__ == "__main__":
    test_research()