#!/usr/bin/env python3
"""Test script for Research Agent"""

import asyncio
import json
import sys
import time
from typing import Dict, Any
import httpx


class ResearchAgentTester:
    """Test client for Research Agent API"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        """Initialize test client

        Args:
            base_url: Base URL of Research Agent API
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def health_check(self) -> bool:
        """Check if service is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            data = response.json()
            print("🔍 Health Check:")
            print(f"  Status: {data['status']}")
            for service, status in data.get('checks', {}).items():
                status_icon = "✅" if status['status'] == 'healthy' else "❌"
                print(f"  {status_icon} {service}: {status['status']}")
            return data['status'] in ['healthy', 'degraded']
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False

    async def start_research(self, query: str, depth: str = "standard", max_sources: int = 10) -> str:
        """Start a research task

        Args:
            query: Research query
            depth: Research depth (quick, standard, comprehensive)
            max_sources: Maximum number of sources

        Returns:
            Task ID
        """
        payload = {
            "query": query,
            "depth": depth,
            "max_sources": max_sources,
            "output_format": "html"
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/api/research",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            print(f"📝 Research task started: {data['task_id']}")
            return data['task_id']
        except Exception as e:
            print(f"❌ Failed to start research: {e}")
            raise

    async def check_status(self, task_id: str) -> Dict[str, Any]:
        """Check task status

        Args:
            task_id: Task ID

        Returns:
            Task status
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/research/{task_id}/status"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to check status: {e}")
            raise

    async def wait_for_completion(self, task_id: str, timeout: int = 300) -> bool:
        """Wait for task to complete

        Args:
            task_id: Task ID
            timeout: Maximum wait time in seconds

        Returns:
            True if completed successfully
        """
        start_time = time.time()
        last_progress = -1

        while time.time() - start_time < timeout:
            try:
                status = await self.check_status(task_id)
                current_progress = status['progress']['percentage']

                if current_progress != last_progress:
                    progress_bar = "█" * (current_progress // 5) + "░" * (20 - current_progress // 5)
                    print(f"\r⏳ Progress: [{progress_bar}] {current_progress}% - {status['progress']['current_step']}", end="")
                    last_progress = current_progress

                if status['status'] == 'completed':
                    print(f"\n✅ Task completed!")
                    return True
                elif status['status'] == 'failed':
                    print(f"\n❌ Task failed: {status.get('error', 'Unknown error')}")
                    return False
                elif status['status'] == 'cancelled':
                    print(f"\n⚠️ Task cancelled")
                    return False

                await asyncio.sleep(2)

            except Exception as e:
                print(f"\n❌ Error checking status: {e}")
                return False

        print(f"\n⏰ Timeout waiting for task completion")
        return False

    async def get_results(self, task_id: str, format: str = "json") -> Any:
        """Get task results

        Args:
            task_id: Task ID
            format: Output format (json, html, markdown)

        Returns:
            Research results
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/research/{task_id}/result",
                params={"format": format}
            )
            response.raise_for_status()

            if format == "json":
                return response.json()
            else:
                return response.text
        except Exception as e:
            print(f"❌ Failed to get results: {e}")
            raise

    async def save_report(self, task_id: str, filename: str = None):
        """Save research report to file

        Args:
            task_id: Task ID
            filename: Output filename (optional)
        """
        try:
            # Get HTML report
            html_report = await self.get_results(task_id, format="html")

            if filename is None:
                filename = f"research_report_{task_id}.html"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_report)

            print(f"📄 Report saved to: {filename}")

            # Also save JSON version
            json_report = await self.get_results(task_id, format="json")
            json_filename = filename.replace('.html', '.json')

            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(json_report, f, indent=2, ensure_ascii=False)

            print(f"📊 JSON data saved to: {json_filename}")

        except Exception as e:
            print(f"❌ Failed to save report: {e}")

    async def run_test(self, query: str, depth: str = "standard", max_sources: int = 10):
        """Run a complete test

        Args:
            query: Research query
            depth: Research depth
            max_sources: Maximum sources
        """
        print(f"\n🚀 Testing Research Agent")
        print(f"   Query: {query}")
        print(f"   Depth: {depth}")
        print(f"   Max Sources: {max_sources}")
        print("-" * 60)

        # Health check
        if not await self.health_check():
            print("Service is not healthy. Exiting.")
            return

        print("-" * 60)

        # Start research
        task_id = await self.start_research(query, depth, max_sources)

        # Wait for completion
        if await self.wait_for_completion(task_id):
            # Get and display summary
            results = await self.get_results(task_id, format="json")

            print("\n📋 Research Summary:")
            print(f"  Sources Used: {results.get('sources_used', 0)}")

            synthesis = results.get('synthesis', {})
            if synthesis.get('key_findings'):
                print("\n🎯 Key Findings:")
                for i, finding in enumerate(synthesis['key_findings'][:3], 1):
                    confidence = finding.get('confidence', 0) * 100
                    print(f"  {i}. {finding['finding'][:100]}...")
                    print(f"     Confidence: {confidence:.0f}%")

            # Save report
            await self.save_report(task_id)

            print("\n✨ Test completed successfully!")
        else:
            print("\n❌ Test failed")

    async def close(self):
        """Close the client"""
        await self.client.aclose()


async def main():
    """Main test function"""
    # Test queries
    test_queries = [
        ("What are the latest developments in quantum computing?", "quick", 5),
        ("How does transformer architecture work in LLMs?", "standard", 10),
        ("What is the MAVLink 2.0 protocol and how is it used?", "standard", 15),
    ]

    # Check if custom query provided
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        test_queries = [(query, "standard", 10)]

    tester = ResearchAgentTester()

    try:
        for query, depth, max_sources in test_queries:
            await tester.run_test(query, depth, max_sources)
            print("\n" + "="*60 + "\n")

            if len(test_queries) > 1:
                print("Waiting 5 seconds before next test...")
                await asyncio.sleep(5)

    finally:
        await tester.close()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║           Research Agent Test Script                      ║
║                                                           ║
║  Usage:                                                   ║
║    python test_research.py                               ║
║    python test_research.py "Your custom query"           ║
╚══════════════════════════════════════════════════════════╝
    """)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)