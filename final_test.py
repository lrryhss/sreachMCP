#!/usr/bin/env python3
"""Final test of the fixed MCP client."""

import asyncio
import sys
import os

# Add the research-agent src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'research-agent', 'src'))

from clients.mcp_client import MCPSearchClient


async def test_mcp_client():
    """Test the fixed MCP client."""
    print("🧪 Testing Fixed MCP Client")
    print("=" * 50)

    client = MCPSearchClient(timeout=30)

    # Test health check
    print("1. Testing health check...")
    try:
        is_healthy = await client.health_check()
        print(f"   Health check: {'✅ PASS' if is_healthy else '❌ FAIL'}")
    except Exception as e:
        print(f"   Health check: ❌ ERROR - {e}")

    # Test search
    print("\n2. Testing search functionality...")
    try:
        result = await client.search(
            query="Python programming tutorial",
            category="web",
            limit=5
        )

        print(f"   Search result keys: {list(result.keys())}")

        if "results" in result:
            results = result["results"]
            print(f"   Found {len(results)} results")

            if results:
                print("\n   Sample results:")
                for i, res in enumerate(results[:3], 1):
                    print(f"   {i}. {res.get('title', 'No title')}")
                    print(f"      URL: {res.get('url', 'No URL')}")
                    print(f"      Snippet: {res.get('snippet', 'No snippet')[:100]}...")
                    print()
                print("   ✅ Search functionality working!")
            else:
                print("   ⚠️  No search results returned")
        elif "error" in result:
            print(f"   ❌ Search error: {result['error']}")
        else:
            print(f"   ❓ Unexpected result format: {result}")

    except Exception as e:
        print(f"   ❌ Search failed: {e}")

    print("\n" + "=" * 50)
    print("🎯 Test Complete")


if __name__ == "__main__":
    asyncio.run(test_mcp_client())