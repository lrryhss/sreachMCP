#!/usr/bin/env python3
"""Test with proper MCP initialization sequence."""

import asyncio
import json
import subprocess


async def test_proper_sequence():
    """Test with proper MCP initialization sequence."""
    docker_command = [
        "docker", "run", "--rm", "-i",
        "--add-host=host.docker.internal:host-gateway",
        "-e", "SEARXNG_BASE_URL=http://host.docker.internal:8090",
        "-e", "LOG_LEVEL=DEBUG",
        "searxng-mcp-server:latest"
    ]

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

    # Step 2: Send initialized notification (NO id field for notifications)
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

    # Step 4: Call tool
    call_request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "search_web",
            "arguments": {
                "query": "test search",
                "category": "web",
                "limit": 3
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

    print("Sending proper MCP sequence:")
    print(f"1. Initialize: {json.dumps(init_request, indent=2)}")
    print(f"2. Initialized notification: {json.dumps(initialized_notification, indent=2)}")
    print(f"3. List tools: {json.dumps(list_request, indent=2)}")
    print(f"4. Call tool: {json.dumps(call_request, indent=2)}")
    print("\n" + "="*60)

    try:
        process = await asyncio.create_subprocess_exec(
            *docker_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=full_input.encode()),
            timeout=20
        )

        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        print("STDOUT:")
        if stdout_str:
            for line in stdout_str.split('\n'):
                if line.strip():
                    try:
                        response = json.loads(line)
                        print(f"  {json.dumps(response, indent=4)}")
                    except json.JSONDecodeError:
                        print(f"  {line}")

        print("\n" + "="*60)
        print("STDERR (last 10 lines):")
        stderr_lines = stderr_str.split('\n')
        for line in stderr_lines[-10:]:
            if line.strip():
                print(f"  {line}")

        # Analyze responses
        responses = []
        if stdout_str:
            for line in stdout_str.split('\n'):
                if line.strip():
                    try:
                        responses.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

        print(f"\n" + "="*60)
        print("ANALYSIS:")
        print(f"Received {len(responses)} responses")

        for i, response in enumerate(responses):
            if "result" in response:
                print(f"  Response {i}: SUCCESS - {response.get('id', 'notification')}")
                if response.get('id') == 1:  # tools/list response
                    tools = response['result'].get('tools', [])
                    print(f"    Found {len(tools)} tools")
                elif response.get('id') == 2:  # tools/call response
                    print(f"    Tool call result: {response['result']}")
            elif "error" in response:
                print(f"  Response {i}: ERROR - {response['error']}")

    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(test_proper_sequence())