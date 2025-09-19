#!/usr/bin/env python3
"""Simple test with empty dict params instead of null."""

import asyncio
import json
import subprocess


async def test_simple_fix():
    """Test with empty dict params instead of null."""
    docker_command = [
        "docker", "run", "--rm", "-i",
        "--add-host=host.docker.internal:host-gateway",
        "-e", "SEARXNG_BASE_URL=http://host.docker.internal:8090",
        "-e", "LOG_LEVEL=ERROR",
        "searxng-mcp-server:latest"
    ]

    # Test with empty dict params instead of null
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

    list_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},  # Empty dict instead of null
        "id": 1
    }

    full_input = json.dumps(init_request) + "\n" + json.dumps(list_request)

    print("Testing with empty dict params...")
    print(f"Init: {json.dumps(init_request, indent=2)}")
    print(f"List: {json.dumps(list_request, indent=2)}")

    try:
        process = await asyncio.create_subprocess_exec(
            *docker_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=full_input.encode()),
            timeout=10
        )

        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        print("\nStdout:")
        if stdout_str:
            for line in stdout_str.split('\n'):
                if line.strip():
                    try:
                        response = json.loads(line)
                        print(f"  {json.dumps(response, indent=4)}")
                    except json.JSONDecodeError:
                        print(f"  {line}")

        print("\nStderr:")
        if stderr_str:
            for line in stderr_str.split('\n'):
                if line.strip():
                    print(f"  {line}")

        # Check if list response is successful
        responses = []
        if stdout_str:
            for line in stdout_str.split('\n'):
                if line.strip():
                    try:
                        responses.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

        if len(responses) >= 2:
            list_response = responses[1]
            if "result" in list_response:
                print("\n✅ SUCCESS: tools/list worked with empty dict params!")
                return True
            else:
                print(f"\n❌ FAILED: {list_response.get('error', 'unknown error')}")
        else:
            print("\n❌ FAILED: No valid response")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")

    return False


if __name__ == "__main__":
    asyncio.run(test_simple_fix())