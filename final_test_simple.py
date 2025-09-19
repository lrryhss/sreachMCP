#!/usr/bin/env python3
"""Simple final test of the fixed MCP protocol."""

import asyncio
import json
import subprocess


async def test_complete_workflow():
    """Test complete MCP workflow with the fixed protocol."""
    docker_command = [
        "docker", "run", "--rm", "-i",
        "--add-host=host.docker.internal:host-gateway",
        "-e", "SEARXNG_BASE_URL=http://host.docker.internal:8090",
        "-e", "LOG_LEVEL=ERROR",
        "searxng-mcp-server:latest"
    ]

    print("🧪 Testing Complete MCP Workflow")
    print("=" * 50)

    # Step 1: Initialize
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0"
            }
        },
        "id": 0
    }

    # Step 2: Send initialized notification
    initialized_notification = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }

    # Step 3: List tools
    list_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 1
    }

    # Step 4: Call search tool
    call_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "search_web",
            "arguments": {
                "query": "Claude AI programming assistant",
                "category": "web",
                "limit": 5
            }
        },
        "id": 2
    }

    full_input = "\n".join([
        json.dumps(init_request),
        json.dumps(initialized_notification),
        json.dumps(list_request),
        json.dumps(call_request)
    ])

    print("1. Sending MCP requests...")

    try:
        process = await asyncio.create_subprocess_exec(
            *docker_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=full_input.encode()),
            timeout=25
        )

        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        # Parse responses
        responses = []
        if stdout_str:
            for line in stdout_str.split('\n'):
                if line.strip():
                    try:
                        responses.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

        print(f"2. Received {len(responses)} responses")

        # Analyze results
        success_count = 0

        for i, response in enumerate(responses):
            if "result" in response:
                success_count += 1
                req_id = response.get('id')

                if req_id == 0:  # Initialize
                    print("   ✅ Initialize: SUCCESS")
                elif req_id == 1:  # List tools
                    tools = response['result'].get('tools', [])
                    print(f"   ✅ List tools: SUCCESS - Found {len(tools)} tool(s)")
                    if tools:
                        tool = tools[0]
                        print(f"      Tool: {tool.get('name')} - {tool.get('description')}")
                elif req_id == 2:  # Call tool
                    print("   ✅ Call tool: SUCCESS")
                    # The result should be a list of TextContent
                    content = response['result'].get('content', [])
                    if content and len(content) > 0:
                        text_content = content[0].get('text', '')
                        lines = text_content.split('\n')[:3]  # First 3 lines
                        print(f"      Result preview: {' '.join(lines)}")
                    else:
                        print(f"      Result: {response['result']}")
            elif "error" in response:
                error = response['error']
                req_id = response.get('id', 'unknown')
                print(f"   ❌ Request {req_id}: ERROR - {error.get('message', 'unknown error')}")

        print(f"\n3. Summary: {success_count}/{len(responses)} requests successful")

        # Check stderr for additional info
        if "Search completed" in stderr_str:
            print("   ✅ Search execution confirmed in logs")

        if success_count >= 3:  # Initialize, list tools, and call tool
            print("\n🎉 ALL TESTS PASSED! MCP protocol is working correctly.")
            print("\n📋 SOLUTION SUMMARY:")
            print("   ✅ Fixed server to return proper MCP types (types.Tool, types.TextContent)")
            print("   ✅ Fixed client to send proper initialization sequence:")
            print("      1. Send 'initialize' request")
            print("      2. Send 'notifications/initialized' notification")
            print("      3. Then send other requests (tools/list, tools/call)")
            print("   ✅ MCP server now correctly handles tools/list and tools/call")
            return True
        else:
            print(f"\n❌ SOME TESTS FAILED: Only {success_count} out of 3+ requests succeeded")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_complete_workflow())