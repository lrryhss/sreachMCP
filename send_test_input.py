#!/usr/bin/env python3
"""Send test input to see debug output."""

import asyncio
import json
import subprocess


async def send_test_input():
    """Send test input to MCP server with debug logging."""
    docker_command = [
        "docker", "run", "--rm", "-i",
        "--add-host=host.docker.internal:host-gateway",
        "-e", "SEARXNG_BASE_URL=http://host.docker.internal:8090",
        "-e", "LOG_LEVEL=DEBUG",
        "searxng-mcp-server:latest"
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

    list_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 1
    }

    full_input = json.dumps(init_request) + "\n" + json.dumps(list_request)

    print("Sending to MCP server:")
    print(f"Input: {full_input}")
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
            timeout=15
        )

        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        print("STDOUT:")
        print(stdout_str)
        print("\n" + "="*60)
        print("STDERR:")
        print(stderr_str)

    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(send_test_input())