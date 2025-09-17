#!/usr/bin/env python3
"""Test script to verify SearXNG connection and search functionality."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config
from searxng_client import SearXNGClient


async def test_connection():
    """Test SearXNG connection and basic search."""
    print("=== SearXNG MCP Server Test ===\n")

    # Load configuration
    config = Config.from_env()
    print(f"✓ Configuration loaded")
    print(f"  SearXNG URL: {config.searxng_url}")
    print(f"  Transport: {config.transport}")
    print()

    # Setup auth if configured
    auth = None
    if config.searxng_auth_user and config.searxng_auth_pass:
        auth = (config.searxng_auth_user, config.searxng_auth_pass)
        print(f"  Using authentication: {config.searxng_auth_user}")

    # Create client
    client = SearXNGClient(
        base_url=config.searxng_url,
        auth=auth,
        timeout=config.request_timeout,
        max_retries=config.retry_attempts
    )

    # Test health check
    print("Testing SearXNG connectivity...")
    async with client as c:
        is_healthy = await c.health_check()
        if is_healthy:
            print("✓ SearXNG instance is accessible\n")
        else:
            print("✗ SearXNG instance is not accessible")
            print("  Please check:")
            print(f"  1. Is SearXNG running at {config.searxng_url}?")
            print("  2. Is the URL correct in your .env file?")
            print("  3. Are there any firewall/network issues?")
            return False

    # Test search functionality
    print("Testing search functionality...")
    test_query = "Python programming"

    async with client as c:
        try:
            results = await c.search(
                query=test_query,
                category="web",
                limit=3
            )

            print(f"✓ Search completed successfully")
            print(f"  Query: '{test_query}'")
            print(f"  Results found: {results.get('number_of_results', 0)}")
            print(f"  Response time: {results.get('response_time', 0):.2f}s")
            print()

            # Display sample results
            if results.get('results'):
                print("Sample results:")
                for i, result in enumerate(results['results'][:3], 1):
                    print(f"\n  {i}. {result.get('title', 'No title')}")
                    print(f"     URL: {result.get('url', 'No URL')}")
                    print(f"     Engine: {result.get('engine', 'Unknown')}")
                    if result.get('content'):
                        snippet = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
                        print(f"     Snippet: {snippet}")

            return True

        except Exception as e:
            print(f"✗ Search failed: {e}")
            return False


async def test_mcp_server():
    """Test MCP server initialization."""
    print("\n\nTesting MCP Server initialization...")

    from server import SearXNGMCPServer

    config = Config.from_env()
    server = SearXNGMCPServer(config)

    try:
        await server.initialize()
        print("✓ MCP Server initialized successfully")

        # Test tool registry
        tools = server.tool_registry.list_tools()
        print(f"✓ Tools registered: {len(tools)}")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")

        return True
    except Exception as e:
        print(f"✗ MCP Server initialization failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("Starting SearXNG MCP Server tests...\n")

    # Check for .env file
    if not os.path.exists('.env'):
        print("Creating .env file from template...")
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✓ Created .env file from .env.example")
            print("  Please edit .env to match your SearXNG configuration\n")
        else:
            print("✗ No .env or .env.example file found")
            return

    # Run tests
    connection_ok = await test_connection()

    if connection_ok:
        server_ok = await test_mcp_server()

        if server_ok:
            print("\n" + "="*50)
            print("✓ All tests passed!")
            print("\nYour SearXNG MCP server is ready to use.")
            print("\nTo add it to Claude Code, use the configuration in package.json")
        else:
            print("\n✗ MCP Server tests failed")
    else:
        print("\n✗ Connection tests failed")
        print("Please fix the connection issues before proceeding")


if __name__ == "__main__":
    asyncio.run(main())