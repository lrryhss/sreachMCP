#!/usr/bin/env python
"""Test GraphRAG Chat functionality"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_chat():
    """Test the GraphRAG chat system"""

    # API configuration
    API_BASE = "http://localhost:8001/api"

    async with aiohttp.ClientSession() as session:
        # First, login to get a token
        print("1. Logging in...")
        login_data = {
            "username_or_email": "demo@example.com",
            "password": "demo123456"
        }

        async with session.post(f"{API_BASE}/auth/login", json=login_data) as resp:
            if resp.status != 200:
                print(f"Login failed: {resp.status}")
                text = await resp.text()
                print(text)
                return

            auth_data = await resp.json()
            access_token = auth_data.get("access_token")
            print(f"✓ Logged in successfully")

        # Set auth header
        headers = {"Authorization": f"Bearer {access_token}"}

        # Create a chat session
        print("\n2. Creating chat session...")
        session_data = {
            "title": f"Test Chat {datetime.now().isoformat()}"
        }

        async with session.post(f"{API_BASE}/chat/sessions",
                                json=session_data,
                                headers=headers) as resp:
            if resp.status != 200:
                print(f"Session creation failed: {resp.status}")
                text = await resp.text()
                print(text)
                return

            session_info = await resp.json()
            session_id = session_info.get("id")
            print(f"✓ Created session: {session_id}")

        # Send a test message
        print("\n3. Sending test message...")
        message_data = {
            "session_id": session_id,
            "content": "What are the main findings from recent AI research in the database?",
            "stream": False
        }

        async with session.post(f"{API_BASE}/chat/messages",
                                json=message_data,
                                headers=headers) as resp:
            if resp.status != 200:
                print(f"Message send failed: {resp.status}")
                text = await resp.text()
                print(text)
                return

            response = await resp.json()
            print(f"✓ Received response:")
            print(f"   Content: {response.get('content')[:200]}...")
            if response.get('sources'):
                print(f"   Sources: {len(response.get('sources'))} sources found")
                for source in response.get('sources')[:3]:
                    print(f"     - {source.get('title', 'Unknown')}")

        print("\n✓ GraphRAG Chat test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_chat())