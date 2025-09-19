#!/usr/bin/env python3
"""Test script to debug MCP protocol request formats."""

import asyncio
import json
import subprocess
import time
from typing import Dict, Any, List


class MCPProtocolTester:
    """Test different MCP protocol request formats."""

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

    def create_tools_list_request(self) -> Dict[str, Any]:
        """Create tools/list request."""
        return {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 1
        }

    def create_tool_call_variants(self) -> List[Dict[str, Any]]:
        """Create different variants of tools/call requests."""
        base_arguments = {
            "query": "test search",
            "category": "web",
            "limit": 5,
            "language": "en"
        }

        variants = [
            # Original format (current failing one)
            {
                "name": "Original format with params wrapper",
                "request": {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "search_web",
                        "arguments": base_arguments
                    },
                    "id": 2
                }
            },

            # Without params wrapper
            {
                "name": "Direct format without params wrapper",
                "request": {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "name": "search_web",
                    "arguments": base_arguments,
                    "id": 3
                }
            },

            # Arguments as direct params
            {
                "name": "Arguments as direct params",
                "request": {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": base_arguments,
                    "id": 4
                }
            },

            # Tool name in params
            {
                "name": "Tool name and args in params",
                "request": {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "tool_name": "search_web",
                        **base_arguments
                    },
                    "id": 5
                }
            },

            # Different method name
            {
                "name": "Method name as call_tool",
                "request": {
                    "jsonrpc": "2.0",
                    "method": "call_tool",
                    "params": {
                        "name": "search_web",
                        "arguments": base_arguments
                    },
                    "id": 6
                }
            },

            # Flat structure
            {
                "name": "Flat structure with tool_name",
                "request": {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "tool_name": "search_web",
                    "params": base_arguments,
                    "id": 7
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
                timeout=10
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
            print("❌ TIMEOUT: Server did not respond within 10 seconds")
            return {"success": False, "error": "timeout"}
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return {"success": False, "error": str(e)}

    async def test_initialization(self):
        """Test basic initialization."""
        init_request = self.create_init_request()
        result = await self.test_request([init_request], "Basic Initialization")

        if result["success"] and result["responses"]:
            response = result["responses"][0]
            if "result" in response:
                print("✅ Initialization successful!")
                return True
            elif "error" in response:
                print(f"❌ Initialization failed: {response['error']}")
                return False

        print("❌ No valid initialization response")
        return False

    async def test_tools_list(self):
        """Test tools/list functionality."""
        init_request = self.create_init_request()
        list_request = self.create_tools_list_request()

        result = await self.test_request(
            [init_request, list_request],
            "Tools List"
        )

        if result["success"] and len(result["responses"]) >= 2:
            list_response = result["responses"][1]
            if "result" in list_response:
                tools = list_response["result"]
                print(f"✅ Tools list successful! Found {len(tools)} tools:")
                for tool in tools:
                    print(f"  - {tool.get('name', 'unknown')}: {tool.get('description', 'no description')}")
                return True
            elif "error" in list_response:
                print(f"❌ Tools list failed: {list_response['error']}")
                return False

        print("❌ No valid tools list response")
        return False

    async def test_tool_call_variants(self):
        """Test different tool call request formats."""
        init_request = self.create_init_request()
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
                    successful_variants.append(variant)
                elif "error" in call_response:
                    error = call_response["error"]
                    print(f"❌ FAILED: {variant['name']} - {error.get('message', 'unknown error')}")
                else:
                    print(f"❓ UNCLEAR: {variant['name']} - unexpected response format")
            else:
                print(f"❌ FAILED: {variant['name']} - no valid response")

        return successful_variants

    async def run_comprehensive_test(self):
        """Run comprehensive test of all MCP protocol variants."""
        print("🧪 MCP Protocol Debugging Test Suite")
        print("=" * 60)

        # Test 1: Basic initialization
        print("\n📋 Test 1: Basic Initialization")
        init_success = await self.test_initialization()

        if not init_success:
            print("❌ Cannot proceed - initialization failed")
            return

        # Test 2: Tools list
        print("\n📋 Test 2: Tools List")
        list_success = await self.test_tools_list()

        # Test 3: Tool call variants
        print("\n📋 Test 3: Tool Call Variants")
        successful_variants = await self.test_tool_call_variants()

        # Summary
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)

        print(f"✅ Initialization: {'SUCCESS' if init_success else 'FAILED'}")
        print(f"✅ Tools List: {'SUCCESS' if list_success else 'FAILED'}")
        print(f"✅ Tool Call Variants: {len(successful_variants)} out of {len(self.create_tool_call_variants())} succeeded")

        if successful_variants:
            print("\n🎉 WORKING FORMATS:")
            for variant in successful_variants:
                print(f"  ✅ {variant['name']}")
                print(f"     Request format: {json.dumps(variant['request'], indent=6)}")
        else:
            print("\n❌ NO WORKING FORMATS FOUND")
            print("\nPossible issues:")
            print("  1. MCP server expects different parameter structure")
            print("  2. Tool name 'search_web' might be incorrect")
            print("  3. Method name might be different")
            print("  4. Server might have validation issues")


async def main():
    """Main entry point."""
    tester = MCPProtocolTester()
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())