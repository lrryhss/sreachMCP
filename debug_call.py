#!/usr/bin/env python3
"""Debug the tools/call response."""

import asyncio
import json
import subprocess


async def debug_call():
    """Debug the tools/call response."""
    docker_command = [
        "docker", "run", "--rm", "-i",
        "--add-host=host.docker.internal:host-gateway",
        "-e", "SEARXNG_BASE_URL=http://host.docker.internal:8090",
        "-e", "LOG_LEVEL=DEBUG",
        "searxng-mcp-server:latest"
    ]

    # Minimal test with just call
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
                    "query": "test",
                    "limit": 2
                }
            },
            "id": 1
        }
    ]

    full_input = "\n".join([json.dumps(req) for req in requests])

    print("Debugging tools/call...")

    try:
        process = await asyncio.create_subprocess_exec(
            *docker_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=full_input.encode()),
            timeout=30
        )

        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        print("STDOUT:")
        print(stdout_str)
        print("\nSTDERR:")
        print(stderr_str)

    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(debug_call())