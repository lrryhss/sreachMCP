#!/usr/bin/env python3
"""Create demo user for testing"""

import requests
import json

API_URL = "http://localhost:8001"

def create_demo_user():
    """Create the demo user account"""

    # Register demo user
    register_data = {
        "email": "demo@example.com",
        "username": "demo",
        "password": "demo123456",
        "full_name": "Demo User"
    }

    print("Creating demo user...")

    try:
        resp = requests.post(
            f"{API_URL}/api/auth/register",
            json=register_data
        )

        if resp.status_code == 201:
            print("✓ Demo user created successfully!")
            return True
        elif resp.status_code == 409:
            print("✓ Demo user already exists")
            return True
        else:
            print(f"✗ Failed to create demo user: {resp.status_code}")
            print(f"Response: {resp.text}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = create_demo_user()
    if success:
        print("\nYou can now login with:")
        print("  Email: demo@example.com")
        print("  Password: demo123456")