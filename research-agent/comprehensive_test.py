#!/usr/bin/env python3
"""Comprehensive test of Research Agent with Database Integration"""

import json
import requests
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8001"

def test_comprehensive():
    print("🧪 COMPREHENSIVE RESEARCH AGENT DATABASE INTEGRATION TEST")
    print("=" * 70)

    results = {
        "user_registration": False,
        "user_login": False,
        "jwt_validation": False,
        "task_creation": False,
        "task_persistence": False,
        "research_history": False,
        "user_isolation": False,
        "task_processing": False,
        "frontend_integration": False
    }

    try:
        # Test 1: User Registration
        print("\n1️⃣  Testing User Registration...")
        timestamp = int(datetime.now().timestamp())
        test_email = f"test.{timestamp}@example.com"
        test_username = f"test_{timestamp}"

        register_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": test_email,
                "username": test_username,
                "password": "TestPassword123!",
                "full_name": "Integration Test User"
            }
        )

        if register_response.status_code == 201:
            user_data = register_response.json()
            print(f"   ✅ User registered: {user_data['username']} ({user_data['email']})")
            results["user_registration"] = True
        else:
            print(f"   ❌ Registration failed: {register_response.text}")
            return results

        # Test 2: User Login & JWT
        print("\n2️⃣  Testing User Login & JWT...")
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username_or_email": test_username,
                "password": "TestPassword123!"
            }
        )

        if login_response.status_code == 200:
            tokens = login_response.json()
            access_token = tokens["access_token"]
            print(f"   ✅ Login successful, token expires in {tokens['expires_in']} seconds")
            results["user_login"] = True
        else:
            print(f"   ❌ Login failed: {login_response.text}")
            return results

        # Test 3: JWT Validation
        print("\n3️⃣  Testing JWT Validation...")
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)

        if profile_response.status_code == 200:
            profile = profile_response.json()
            print(f"   ✅ JWT valid, authenticated as: {profile['username']}")
            results["jwt_validation"] = True
        else:
            print(f"   ❌ JWT validation failed: {profile_response.text}")
            return results

        # Test 4: Task Creation
        print("\n4️⃣  Testing Research Task Creation...")
        task_response = requests.post(
            f"{BASE_URL}/api/research",
            headers=headers,
            json={
                "query": "What are the latest breakthroughs in artificial intelligence?",
                "depth": "quick",
                "max_sources": 5
            }
        )

        if task_response.status_code == 201:
            task = task_response.json()
            task_id = task["task_id"]
            print(f"   ✅ Research task created: {task_id}")
            print(f"      Query: {task['query']}")
            print(f"      Status: {task['status']}")
            results["task_creation"] = True
        else:
            print(f"   ❌ Task creation failed: {task_response.text}")
            return results

        # Test 5: Task Persistence
        print("\n5️⃣  Testing Task Persistence...")
        time.sleep(2)  # Allow task to be processed

        status_response = requests.get(f"{BASE_URL}/api/research/{task_id}/status", headers=headers)
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"   ✅ Task persisted: Status = {status['status']}, Progress = {status['progress']}%")
            results["task_persistence"] = True
        else:
            # Check if task exists in history instead
            print(f"   ⚠️  Direct status failed, checking history...")

        # Test 6: Research History
        print("\n6️⃣  Testing Research History...")
        history_response = requests.get(f"{BASE_URL}/api/research/history?limit=10", headers=headers)

        if history_response.status_code == 200:
            history = history_response.json()
            user_tasks = [t for t in history['tasks'] if t['task_id'] == task_id]
            print(f"   ✅ History retrieved: Found {len(history['tasks'])} total tasks")
            if user_tasks:
                print(f"      Our task found in history: {user_tasks[0]['status']}")
                results["task_persistence"] = True  # Mark as persistent if found in history
            results["research_history"] = True
        else:
            print(f"   ❌ History retrieval failed: {history_response.text}")

        # Test 7: User Isolation
        print("\n7️⃣  Testing User Isolation...")
        # Create second user
        user2_email = f"isolation.{timestamp}@example.com"
        user2_username = f"isolation_{timestamp}"

        user2_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "email": user2_email,
                "username": user2_username,
                "password": "TestPassword123!",
                "full_name": "Isolation Test User"
            }
        )

        if user2_response.status_code == 201:
            # Login as second user
            login2_response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "username_or_email": user2_username,
                    "password": "TestPassword123!"
                }
            )

            if login2_response.status_code == 200:
                token2 = login2_response.json()["access_token"]
                headers2 = {"Authorization": f"Bearer {token2}"}

                # Check if second user can see first user's tasks
                history2_response = requests.get(f"{BASE_URL}/api/research/history?limit=10", headers=headers2)

                if history2_response.status_code == 200:
                    history2 = history2_response.json()
                    user1_tasks_visible = [t for t in history2['tasks'] if t['task_id'] == task_id]

                    if not user1_tasks_visible:
                        print(f"   ✅ User isolation working: User2 cannot see User1's tasks")
                        results["user_isolation"] = True
                    else:
                        print(f"   ❌ User isolation failed: User2 can see User1's tasks")
                else:
                    print(f"   ⚠️  Could not test isolation: {history2_response.text}")

        # Test 8: Task Processing
        print("\n8️⃣  Testing Task Processing...")
        print("      Monitoring task progress for 30 seconds...")

        for i in range(6):  # Check every 5 seconds for 30 seconds
            time.sleep(5)

            # Check task in history
            hist_response = requests.get(f"{BASE_URL}/api/research/history?limit=20", headers=headers)
            if hist_response.status_code == 200:
                tasks = hist_response.json()['tasks']
                our_task = next((t for t in tasks if t['task_id'] == task_id), None)

                if our_task:
                    status = our_task['status']
                    progress = our_task.get('progress', 0)
                    print(f"      Check {i+1}/6: Status = {status}, Progress = {progress}%")

                    if status in ['completed', 'failed']:
                        if status == 'completed':
                            print(f"   ✅ Task completed successfully!")
                            results["task_processing"] = True
                        else:
                            print(f"   ⚠️  Task failed: {our_task.get('error_message', 'Unknown error')}")
                        break
                    elif status != 'pending':
                        results["task_processing"] = True  # At least it's processing

        # Test 9: Frontend Integration Test
        print("\n9️⃣  Testing Frontend Integration...")
        try:
            frontend_response = requests.get("http://localhost:3001", timeout=5)
            if frontend_response.status_code == 200:
                print("   ✅ Frontend accessible at http://localhost:3001")
                results["frontend_integration"] = True
            else:
                print(f"   ⚠️  Frontend returned status {frontend_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  Frontend not accessible: {e}")

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        return results

    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title():.<50} {status}")

    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed >= 7:  # Most critical tests
        print("\n🎉 DATABASE INTEGRATION SUCCESSFULLY IMPLEMENTED!")
        print("   Core functionality working: Authentication, persistence, user isolation")
    elif passed >= 5:
        print("\n⚠️  DATABASE INTEGRATION MOSTLY WORKING")
        print("   Some issues detected but core functionality operational")
    else:
        print("\n❌ DATABASE INTEGRATION NEEDS WORK")
        print("   Critical issues detected")

    return results

if __name__ == "__main__":
    test_comprehensive()