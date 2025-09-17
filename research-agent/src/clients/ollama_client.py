"""Ollama LLM client for Research Agent"""

import json
import asyncio
from typing import AsyncGenerator, Dict, List, Optional, Any
import httpx
from structlog import get_logger

logger = get_logger()


class OllamaClient:
    """Client for interacting with Ollama LLM"""

    def __init__(self, base_url: str, model: str, timeout: int = 120):
        """Initialize Ollama client

        Args:
            base_url: Ollama API base URL
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.session = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()

    async def health_check(self) -> bool:
        """Check if Ollama is accessible

        Returns:
            True if Ollama is running and model is available
        """
        try:
            if not self.session:
                async with httpx.AsyncClient(timeout=5) as client:
                    # Check if Ollama is running
                    response = await client.get(f"{self.base_url}/api/tags")
                    if response.status_code != 200:
                        return False

                    # Check if model is available
                    models = response.json().get("models", [])
                    model_names = [m.get("name") for m in models]
                    return self.model in model_names
            else:
                response = await self.session.get(f"{self.base_url}/api/tags")
                if response.status_code != 200:
                    return False
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models]
                return self.model in model_names
        except Exception as e:
            logger.warning("Ollama health check failed", error=str(e))
            return False

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> str:
        """Generate text using Ollama

        Args:
            prompt: The prompt to generate from
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response

        Returns:
            Generated text
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        if system:
            payload["system"] = system

        try:
            response = await self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()

            if stream:
                return response.text
            else:
                data = response.json()
                return data.get("response", "")

        except Exception as e:
            logger.error("Ollama generation failed", error=str(e))
            raise

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """Chat with Ollama using conversation history

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Assistant's response
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        try:
            response = await self.session.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")

        except Exception as e:
            logger.error("Ollama chat failed", error=str(e))
            raise

    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze a research query to extract intent and entities

        Args:
            query: User's research query

        Returns:
            Analysis with intent, entities, and search strategies
        """
        prompt = f"""Analyze the following research query and provide a structured analysis.

Query: "{query}"

Provide your analysis in JSON format with the following structure:
{{
    "intent": "Brief description of what the user wants to research",
    "key_topics": ["topic1", "topic2", "topic3"],
    "entities": {{
        "technologies": [],
        "organizations": [],
        "people": [],
        "dates": [],
        "locations": []
    }},
    "search_strategies": [
        "search query 1",
        "search query 2",
        "search query 3"
    ],
    "research_depth": "quick|standard|comprehensive",
    "time_sensitivity": "current|recent|historical"
}}

Return ONLY the JSON object, no additional text."""

        try:
            response = await self.generate(prompt, temperature=0.3)

            # Extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            # Parse JSON
            analysis = json.loads(response.strip())
            return analysis

        except json.JSONDecodeError as e:
            logger.warning("Failed to parse query analysis", error=str(e))
            # Return a default analysis
            return {
                "intent": query,
                "key_topics": [query],
                "entities": {},
                "search_strategies": [
                    query,
                    f"{query} latest",
                    f"{query} 2025"
                ],
                "research_depth": "standard",
                "time_sensitivity": "recent"
            }

    async def summarize_content(
        self,
        content: str,
        max_length: int = 500,
        focus: Optional[str] = None
    ) -> str:
        """Summarize content

        Args:
            content: Content to summarize
            max_length: Maximum length of summary in words
            focus: Optional focus area for summarization

        Returns:
            Summary text
        """
        focus_instruction = f"Focus particularly on: {focus}" if focus else ""

        prompt = f"""Summarize the following content in approximately {max_length} words.
{focus_instruction}

Content:
{content[:8000]}  # Limit content to avoid token limits

Provide a clear, concise summary that captures the key points and main ideas."""

        try:
            summary = await self.generate(prompt, temperature=0.3)
            return summary.strip()
        except Exception as e:
            logger.error("Content summarization failed", error=str(e))
            return "Failed to generate summary."

    async def synthesize_research(
        self,
        summaries: List[Dict[str, str]],
        query: str
    ) -> Dict[str, Any]:
        """Synthesize multiple content summaries into a coherent research report

        Args:
            summaries: List of content summaries with source info
            query: Original research query

        Returns:
            Synthesized research findings
        """
        # Prepare summaries text
        summaries_text = "\n\n".join([
            f"Source {i+1} ({s.get('url', 'Unknown')}):\n{s.get('summary', '')}"
            for i, s in enumerate(summaries)
        ])

        prompt = f"""You are synthesizing research findings for the query: "{query}"

Based on the following summaries from multiple sources, create a comprehensive research synthesis.

{summaries_text}

Provide your synthesis in JSON format with the following structure:
{{
    "executive_summary": "200-300 word executive summary",
    "key_findings": [
        {{"finding": "Key finding 1", "confidence": 0.9, "sources": [1, 2]}},
        {{"finding": "Key finding 2", "confidence": 0.8, "sources": [3, 4]}}
    ],
    "themes": [
        {{"theme": "Major theme 1", "description": "Description", "sources": [1, 2, 3]}}
    ],
    "contradictions": [
        {{"point": "Contradictory point", "viewpoints": ["View 1", "View 2"], "sources": [1, 3]}}
    ],
    "knowledge_gaps": ["Gap 1", "Gap 2"],
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "further_research": ["Topic 1", "Topic 2"]
}}

Return ONLY the JSON object."""

        try:
            response = await self.generate(prompt, temperature=0.4, max_tokens=3000)

            # Extract and parse JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            synthesis = json.loads(response.strip())
            return synthesis

        except json.JSONDecodeError as e:
            logger.warning("Failed to parse synthesis", error=str(e))
            # Return a basic synthesis
            return {
                "executive_summary": "Research synthesis could not be generated.",
                "key_findings": [],
                "themes": [],
                "contradictions": [],
                "knowledge_gaps": [],
                "recommendations": [],
                "further_research": []
            }

    async def stream_generate(
        self,
        prompt: str,
        system: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream generated text from Ollama

        Args:
            prompt: The prompt to generate from
            system: Optional system prompt

        Yields:
            Generated text chunks
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True
        }

        if system:
            payload["system"] = system

        try:
            async with self.session.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error("Ollama streaming failed", error=str(e))
            raise