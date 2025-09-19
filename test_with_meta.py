#!/usr/bin/env python3
"""Test with proper _meta field in params."""

import asyncio
import json
import subprocess


async def test_with_meta():
    """Test with proper _meta field."""
    docker_command = [
        "docker", "run", "--rm", "-i",
        "--add-host=host.docker.internal:host-gateway",
        "-e", "SEARXNG_BASE_URL=http://host.docker.internal:8090",
        "-e", "LOG_LEVEL=ERROR",
        "searxng-mcp-server:latest"
    ]

    # Test different variations with _meta field
    test_cases = [
        {
            "name": "Empty dict params",
            "list_request": {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 1
            }
        },
        {
            "name": "Null params",
            "list_request": {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": None,
                "id": 2
            }
        },
        {
            "name": "With _meta field",
            "list_request": {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {
                    "_meta": None
                },
                "id": 3
            }
        },
        {
            "name": "With cursor field",
            "list_request": {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {
                    "cursor": None
                },
                "id": 4
            }
        },
        {
            "name": "With both _meta and cursor",
            "list_request": {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {
                    "_meta": None,
                    "cursor": None
                },
                "id": 5
            }
        }
    ]

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

    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {test_case['name']}")
        print(f"{'='*60}")

        full_input = json.dumps(init_request) + "\n" + json.dumps(test_case['list_request'])

        print(f"List request: {json.dumps(test_case['list_request'], indent=2)}")

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
                    print(f"\n✅ SUCCESS: {test_case['name']} worked!")
                    print(f"Tools: {json.dumps(list_response['result'], indent=2)}")
                    return True
                else:
                    print(f"\n❌ FAILED: {list_response.get('error', 'unknown error')}")
            else:
                print("\n❌ FAILED: No valid response")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")

    print("\n" + "="*60)
    print("All test cases failed")
    return False


if __name__ == "__main__":
    asyncio.run(test_with_meta())