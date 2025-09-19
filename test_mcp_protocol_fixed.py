#!/usr/bin/env python3
"""Test script to debug MCP protocol with correct formats based on MCP types."""

import asyncio
import json
import subprocess
import time
from typing import Dict, Any, List


class MCPProtocolTesterFixed:
    """Test MCP protocol with correct request formats."""

    def __init__(self):
        """Initialize the tester."""
        self.docker_command = [
            "docker", "run", "--rm", "-i",
            "--add-host=host.docker.internal:host-gateway",
            "-e", "SEARXNG_BASE_URL=http://host.docker.internal:8090",
            "-e", "LOG_LEVEL=ERROR",
            "searxng-mcp-server:latest"
        ]

    def create_init_request(self) -> Dict[str, Any]:
        """Create initialization request."""
        return {
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

    def create_correct_tools_list_request(self) -> Dict[str, Any]:
        """Create correct tools/list request based on MCP types."""
        # Based on ListToolsRequest - should be PaginatedRequest with optional cursor
        return {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": None,  # PaginatedRequest allows null params
            "id": 1
        }

    def create_correct_tool_call_request(self) -> Dict[str, Any]:
        """Create correct tools/call request based on MCP types."""
        # Based on CallToolRequest and CallToolRequestParams
        return {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "search_web",
                "arguments": {
                    "query": "test search",
                    "category": "web",
                    "limit": 5,
                    "language": "en"
                }
            },
            "id": 2
        }

    def create_tool_call_variants(self) -> List[Dict[str, Any]]:
        """Create different variants to test edge cases."""
        variants = [
            # Correct format
            {
                "name": "Correct MCP format",
                "request": self.create_correct_tool_call_request()
            },

            # With null arguments
            {
                "name": "Correct format with null arguments",
                "request": {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "search_web",
                        "arguments": None
                    },
                    "id": 3
                }
            },

            # Without arguments field
            {
                "name": "Correct format without arguments field",
                "request": {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "search_web"
                    },
                    "id": 4
                }
            },

            # Empty params
            {
                "name": "Empty params",
                "request": {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {},
                    "id": 5
                }
            }
        ]
        return variants

    async def test_request(self, requests: List[Dict[str, Any]], description: str = "") -> Dict[str, Any]:
        """Test a sequence of requests against the MCP server."""
        print(f"\n{'='*60}")
        print(f"Testing: {description}")
        print(f"{'='*60}")

        try:
            # Prepare input
            input_lines = []
            for req in requests:
                input_lines.append(json.dumps(req))
                print(f"Sending: {json.dumps(req, indent=2)}")

            full_input = "\n".join(input_lines)

            # Run the MCP server
            print(f"\nRunning MCP server...")
            process = await asyncio.create_subprocess_exec(
                *self.docker_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=full_input.encode()),
                timeout=15
            )

            # Parse responses
            stdout_str = stdout.decode().strip()
            stderr_str = stderr.decode().strip()

            print(f"\nStdout:")
            if stdout_str:
                for line in stdout_str.split('\n'):
                    if line.strip():
                        try:
                            response = json.loads(line)
                            print(f"  {json.dumps(response, indent=4)}")
                        except json.JSONDecodeError:
                            print(f"  {line}")
            else:
                print("  (empty)")

            print(f"\nStderr:")
            if stderr_str:
                for line in stderr_str.split('\n'):
                    if line.strip():
                        print(f"  {line}")
            else:
                print("  (empty)")

            # Analyze responses
            responses = []
            if stdout_str:
                for line in stdout_str.split('\n'):
                    if line.strip():
                        try:
                            responses.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass

            return {
                "success": len(responses) > 0,
                "responses": responses,
                "stdout": stdout_str,
                "stderr": stderr_str
            }

        except asyncio.TimeoutError:
            print("❌ TIMEOUT: Server did not respond within 15 seconds")
            return {"success": False, "error": "timeout"}
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return {"success": False, "error": str(e)}

    async def test_corrected_formats(self):
        """Test the corrected MCP formats."""
        print("🧪 MCP Protocol Test - Corrected Formats Based on MCP Types")
        print("=" * 60)

        # Test 1: Initialization
        print("\n📋 Test 1: Initialization")
        init_request = self.create_init_request()
        result = await self.test_request([init_request], "Initialization")

        init_success = False
        if result["success"] and result["responses"]:
            response = result["responses"][0]
            if "result" in response:
                print("✅ Initialization successful!")
                init_success = True
            elif "error" in response:
                print(f"❌ Initialization failed: {response['error']}")

        if not init_success:
            print("❌ Cannot proceed - initialization failed")
            return

        # Test 2: Corrected tools/list
        print("\n📋 Test 2: Corrected Tools/List")
        init_request = self.create_init_request()
        list_request = self.create_correct_tools_list_request()

        result = await self.test_request(
            [init_request, list_request],
            "Corrected Tools List"
        )

        list_success = False
        if result["success"] and len(result["responses"]) >= 2:
            list_response = result["responses"][1]
            if "result" in list_response:
                tools = list_response["result"]
                print(f"✅ Tools list successful! Response: {json.dumps(tools, indent=2)}")
                list_success = True

                # Check if tools is a dict with 'tools' key or direct list
                tool_list = tools.get("tools", []) if isinstance(tools, dict) else tools
                if tool_list:
                    print(f"Found {len(tool_list)} tools:")
                    for tool in tool_list:
                        print(f"  - {tool.get('name', 'unknown')}: {tool.get('description', 'no description')}")
                else:
                    print("No tools found in response")

            elif "error" in list_response:
                print(f"❌ Tools list failed: {list_response['error']}")

        # Test 3: Corrected tools/call variants
        print("\n📋 Test 3: Corrected Tools/Call")
        variants = self.create_tool_call_variants()
        successful_variants = []

        for variant in variants:
            print(f"\n{'-'*40}")
            print(f"Testing variant: {variant['name']}")
            print(f"{'-'*40}")

            result = await self.test_request(
                [init_request, variant['request']],
                f"Tool Call - {variant['name']}"
            )

            if result["success"] and len(result["responses"]) >= 2:
                call_response = result["responses"][1]
                if "result" in call_response:
                    print(f"✅ SUCCESS: {variant['name']} worked!")
                    print(f"   Result: {json.dumps(call_response['result'], indent=4)}")
                    successful_variants.append(variant)
                elif "error" in call_response:
                    error = call_response["error"]
                    print(f"❌ FAILED: {variant['name']} - {error.get('message', 'unknown error')}")
                    print(f"   Error code: {error.get('code', 'unknown')}")
                else:
                    print(f"❓ UNCLEAR: {variant['name']} - unexpected response format")
            else:
                print(f"❌ FAILED: {variant['name']} - no valid response")

        # Summary
        print("\n" + "=" * 60)
        print("🎯 CORRECTED TEST SUMMARY")
        print("=" * 60)

        print(f"✅ Initialization: {'SUCCESS' if init_success else 'FAILED'}")
        print(f"✅ Tools List: {'SUCCESS' if list_success else 'FAILED'}")
        print(f"✅ Tool Call Variants: {len(successful_variants)} out of {len(variants)} succeeded")

        if successful_variants:
            print("\n🎉 WORKING TOOL CALL FORMATS:")
            for variant in successful_variants:
                print(f"  ✅ {variant['name']}")
        else:
            print("\n❌ NO WORKING TOOL CALL FORMATS FOUND")

        if list_success:
            print("\n📝 RECOMMENDATION:")
            print("The tools/list request works with null params. Update your client to use:")
            print('{"jsonrpc": "2.0", "method": "tools/list", "params": null, "id": 1}')

        if successful_variants:
            print("\nUse the successful tool call format for your implementation.")
        else:
            print("\nInvestigate server-side tool call handling - the issue may be in the server implementation.")


async def main():
    """Main entry point."""
    tester = MCPProtocolTesterFixed()
    await tester.test_corrected_formats()


if __name__ == "__main__":
    asyncio.run(main())