#!/usr/bin/env python3
"""Test with longer timeout to see if response comes through."""

import asyncio
import json
import subprocess


async def test_with_timeout():
    """Test with longer timeout."""
    docker_command = [
        "docker", "run", "--rm", "-i",
        "--add-host=host.docker.internal:host-gateway",
        "-e", "SEARXNG_BASE_URL=http://host.docker.internal:8090",
        "-e", "LOG_LEVEL=ERROR",  # Reduce noise
        "searxng-mcp-server:latest"
    ]

    requests = [
        {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            },
            "id": 0
        },
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        },
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "search_web",
                "arguments": {
                    "query": "test search",
                    "limit": 3
                }
            },
            "id": 1
        }
    ]

    full_input = "\n".join([json.dumps(req) for req in requests])

    print("Testing with extended timeout to catch response...")

    try:
        process = await asyncio.create_subprocess_exec(
            *docker_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Wait for output with timeout and send input
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=full_input.encode()),
                timeout=5
            )
        except asyncio.TimeoutError:
            # Try to get what we have so far
            print("Timeout reached, getting partial output...")
            try:
                stdout_data = await process.stdout.read()
                stderr_data = await process.stderr.read()
                stdout = stdout_data
                stderr = stderr_data
            except:
                stdout = b""
                stderr = b""

        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        print("STDOUT:")
        if stdout_str:
            responses = []
            for line in stdout_str.split('\n'):
                if line.strip():
                    try:
                        response = json.loads(line)
                        responses.append(response)
                        print(f"  Response {response.get('id', 'notification')}: {json.dumps(response, indent=4)}")
                    except json.JSONDecodeError:
                        print(f"  Raw: {line}")

            # Check if we got the tool response
            for response in responses:
                if response.get('id') == 1:  # tools/call response
                    if "result" in response:
                        print("\n🎉 SUCCESS! Tool call response received:")
                        result = response['result']
                        if 'content' in result and result['content']:
                            content = result['content'][0].get('text', '')
                            print(f"   Content preview: {content[:200]}...")
                        return True
                    elif "error" in response:
                        print(f"\n❌ Tool call failed: {response['error']}")

        else:
            print("  (no stdout)")

        print(f"\nSTDERR (last 5 lines):")
        if stderr_str:
            lines = stderr_str.split('\n')
            for line in lines[-5:]:
                if line.strip():
                    print(f"  {line}")

    except Exception as e:
        print(f"ERROR: {e}")

    return False


if __name__ == "__main__":
    asyncio.run(test_with_timeout())