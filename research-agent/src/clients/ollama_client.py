"""Ollama LLM client for Research Agent"""

import json
import asyncio
import re
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
        # Create persistent session immediately
        self.session = httpx.AsyncClient(timeout=self.timeout)
        self._context_managed = False

    async def __aenter__(self):
        """Async context manager entry"""
        # Session already created in __init__, just mark as context managed
        self._context_managed = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Only close if we're in context manager mode
        # Keep session open for direct usage
        if self._context_managed:
            self._context_managed = False
            # Don't close the session, keep it persistent

    async def close(self):
        """Close the persistent session"""
        if self.session:
            await self.session.aclose()
            self.session = None

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
            # Session should always exist now, but add safety check
            self.session = httpx.AsyncClient(timeout=self.timeout)

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
            # Session should always exist now, but add safety check
            self.session = httpx.AsyncClient(timeout=self.timeout)

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

    async def reformat_executive_summary(self, raw_summary: str) -> str:
        """Reformat an executive summary into HTML paragraphs

        Args:
            raw_summary: Raw executive summary text

        Returns:
            HTML formatted text with paragraph tags
        """
        prompt = f"""Convert the following text into exactly 3-4 HTML paragraphs. Output ONLY the HTML <p> tags with the content, nothing else.

Text:
{raw_summary}

Output format (ONLY output tags like these, no other text):
<p>First part of the text...</p>
<p>Second part of the text...</p>
<p>Third part of the text...</p>"""

        system = "You are an HTML formatter. Output ONLY valid HTML paragraph tags. Never include any commentary, thinking, or wrapper text. Start your response with <p> and end with </p>."

        try:
            response = await self.generate(prompt, system=system, temperature=0.1, max_tokens=3000)

            # Clean up the response
            response = response.strip()

            # Remove any HTML document wrapper if present
            if '<!DOCTYPE' in response or '<html' in response:
                # Extract just the paragraph content
                import re
                p_tags = re.findall(r'<p>.*?</p>', response, re.DOTALL)
                if p_tags:
                    response = '\n'.join(p_tags)

            # Remove markdown code blocks if present
            if response.startswith("```"):
                lines = response.split('\n')
                # Find where code block ends
                end_index = len(lines)
                for i in range(1, len(lines)):
                    if lines[i].strip().startswith("```"):
                        end_index = i
                        break
                response = '\n'.join(lines[1:end_index])

            # Verify we have <p> tags
            if '<p>' not in response:
                # Fallback: Create HTML paragraphs from plain text
                paragraphs = []
                if '\n\n' in response:
                    # Use existing paragraph breaks
                    for para in response.split('\n\n'):
                        if para.strip():
                            paragraphs.append(f'<p>{para.strip()}</p>')
                else:
                    # Try to create paragraphs from sentences
                    sentences = response.split('. ')
                    if len(sentences) > 6:
                        para_size = len(sentences) // 3
                        for i in range(0, len(sentences), para_size):
                            para = '. '.join(sentences[i:i+para_size])
                            if para and not para.endswith('.'):
                                para += '.'
                            paragraphs.append(f'<p>{para.strip()}</p>')
                    else:
                        # Just wrap the whole thing
                        paragraphs.append(f'<p>{response}</p>')
                response = '\n'.join(paragraphs)

            return response

        except Exception as e:
            logger.warning("Failed to reformat executive summary", error=str(e))
            # Return original wrapped in a paragraph tag
            return f'<p>{raw_summary}</p>'

    def sanitize_json_response(self, response: str) -> str:
        """Sanitize JSON response from LLM to fix common issues

        Args:
            response: Raw JSON string from LLM

        Returns:
            Sanitized JSON string
        """
        try:
            # Remove invalid escape sequences
            # Only keep valid JSON escape sequences
            response = re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', '', response)

            # Fix newlines and tabs that might break JSON parsing
            # Replace actual newlines in strings with escaped ones
            response = re.sub(r'(?<!")(\n|\r\n)(?!")', ' ', response)

            # Remove any trailing commas before closing brackets/braces
            response = re.sub(r',\s*([}\]])', r'\1', response)

            # Fix double quotes inside string values (not keys)
            # This is a simple approach - may need refinement
            response = re.sub(r'(?<=[:{,\[])\s*"([^"]*)"([^"]*)"', r'"\1\2"', response)

            return response
        except Exception as e:
            logger.warning("Failed to sanitize JSON response", error=str(e))
            return response

    def validate_synthesis(self, synthesis: Dict[str, Any]) -> bool:
        """Validate synthesis structure and content

        Args:
            synthesis: Synthesis dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        # Check for required fields
        if not synthesis:
            return False

        # Validate executive summary
        exec_summary = synthesis.get("executive_summary", "")
        if not exec_summary or len(str(exec_summary)) < 100:
            logger.warning("Executive summary too short or missing")
            return False

        # Validate key findings
        key_findings = synthesis.get("key_findings", [])
        if not key_findings or len(key_findings) < 3:
            logger.warning("Insufficient key findings")
            return False

        # Check that findings have required fields
        for finding in key_findings:
            if not finding.get("finding") or not finding.get("headline"):
                return False

        return True

    def _get_simpler_synthesis_prompt(self, summaries: List[Dict[str, str]], query: str, attempt: int) -> str:
        """Generate a simpler prompt for retry attempts

        Args:
            summaries: List of source summaries
            query: Research query
            attempt: Current attempt number (0-based)

        Returns:
            Simpler prompt string
        """
        # Use fewer summaries for simpler processing
        summaries_text = "\n\n".join([
            f"Source {i+1}: {s.get('summary', '')[:300]}"
            for i, s in enumerate(summaries[:5])  # Use only first 5 summaries
        ])

        if attempt == 1:
            # Second attempt - simpler JSON structure
            return f"""Synthesize research about "{query}" from these sources:

{summaries_text}

Return a JSON object with:
{{
    "executive_summary": "A comprehensive 200-300 word summary of the research findings",
    "key_findings": [
        {{
            "headline": "Brief headline",
            "finding": "1-2 sentence explanation",
            "category": "primary",
            "impact_score": 0.8,
            "confidence": 0.8,
            "supporting_sources": [1],
            "statistics": {{}},
            "keywords": []
        }}
        // Generate 4-6 findings
    ],
    "themes": [
        {{"theme": "Main theme", "description": "Brief description", "sources": [1, 2]}}
    ],
    "contradictions": [],
    "knowledge_gaps": [],
    "recommendations": [],
    "further_research": []
}}

Keep the JSON simple and valid. Avoid complex nested structures."""

        else:
            # Third attempt - minimal structure
            return f"""Create a research summary for "{query}".

Based on: {summaries_text[:500]}

Return simple JSON:
{{
    "executive_summary": "Summary paragraph here",
    "key_findings": [
        {{"headline": "Finding 1", "finding": "Description", "category": "primary", "impact_score": 0.7, "confidence": 0.7, "supporting_sources": [1], "statistics": {{}}, "keywords": []}},
        {{"headline": "Finding 2", "finding": "Description", "category": "secondary", "impact_score": 0.6, "confidence": 0.6, "supporting_sources": [1], "statistics": {{}}, "keywords": []}}
    ],
    "themes": [],
    "contradictions": [],
    "knowledge_gaps": [],
    "recommendations": [],
    "further_research": []
}}"""

    def generate_fallback_synthesis(self, summaries: List[Dict[str, str]], query: str) -> Dict[str, Any]:
        """Generate a fallback synthesis when LLM fails

        Args:
            summaries: List of source summaries
            query: Original research query

        Returns:
            Basic but valid synthesis structure
        """
        # Create a basic executive summary from the first few summaries
        exec_summary_parts = []
        for i, summary in enumerate(summaries[:3]):
            if summary.get("summary"):
                exec_summary_parts.append(summary["summary"][:200])

        executive_summary = " ".join(exec_summary_parts) if exec_summary_parts else f"Research findings for: {query}"

        # Extract key findings from summaries
        key_findings = []
        for i, summary in enumerate(summaries[:6]):
            if summary.get("summary"):
                # Extract first sentence as finding
                first_sentence = summary["summary"].split('.')[0]
                if first_sentence:
                    key_findings.append({
                        "headline": f"Finding from Source {i+1}",
                        "finding": first_sentence + ".",
                        "category": "primary" if i < 3 else "secondary",
                        "impact_score": 0.7,
                        "confidence": 0.6,
                        "supporting_sources": [i + 1],
                        "statistics": {},
                        "keywords": []
                    })

        # Ensure we have at least some findings
        if not key_findings:
            key_findings = [{
                "headline": "Research Conducted",
                "finding": f"Analysis completed for query: {query}",
                "category": "primary",
                "impact_score": 0.5,
                "confidence": 0.5,
                "supporting_sources": [1],
                "statistics": {},
                "keywords": []
            }]

        # Create basic themes from source titles/URLs
        themes = []
        seen_themes = set()
        for summary in summaries[:5]:
            if summary.get("title"):
                theme = summary["title"][:50]
                if theme not in seen_themes:
                    themes.append({
                        "theme": theme,
                        "description": summary.get("summary", "")[:100],
                        "sources": [summaries.index(summary) + 1]
                    })
                    seen_themes.add(theme)

        return {
            "executive_summary": executive_summary,
            "key_findings": key_findings,
            "themes": themes,
            "contradictions": [],
            "knowledge_gaps": ["Unable to perform comprehensive analysis due to processing limitations"],
            "recommendations": ["Further research recommended with alternative approaches"],
            "further_research": [query],
            "pull_quote": f"Research findings for: {query}",
            "detailed_analysis": {
                "sections": [
                    {
                        "title": "Overview",
                        "content": executive_summary,
                        "sources": list(range(1, min(4, len(summaries) + 1)))
                    }
                ]
            }
        }

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
    "executive_summary": {{
        "lead_paragraph": "2-3 sentence compelling opening that captures the essence of the research",
        "body_paragraphs": [
            "First main paragraph (3-4 sentences) covering primary findings",
            "Second paragraph (3-4 sentences) covering secondary aspects",
            "Third paragraph (3-4 sentences) covering implications or future directions"
        ],
        "pull_quote": "One powerful sentence that captures the key insight"
    }},
    "key_findings": [
        {{
            "headline": "Brief 10-15 word headline capturing the essence",
            "finding": "1-2 sentence detailed explanation of the finding with specifics",
            "category": "primary|secondary|emerging|consideration",
            "impact_score": 0.85,
            "confidence": 0.9,
            "supporting_sources": [1, 2],
            "statistics": {{"key": "value", "metric": "number"}},
            "keywords": ["keyword1", "keyword2"]
        }},
        // Generate 6-10 diverse findings across all categories
        // Ensure at least 2-3 primary findings
        // Include emerging trends and considerations
    ],
    "detailed_analysis": {{
        "sections": [
            {{
                "title": "Overview and Background",
                "content": "Comprehensive overview in 2-3 paragraphs",
                "sources": [1, 2]
            }},
            {{
                "title": "Key Technologies and Methods",
                "content": "Main technologies and approaches in 2-3 paragraphs",
                "sources": [1, 2, 3]
            }},
            {{
                "title": "Current State and Developments",
                "content": "Recent developments and current status in 2-3 paragraphs",
                "sources": [2, 3]
            }},
            {{
                "title": "Challenges and Limitations",
                "content": "Main challenges and limitations in 2-3 paragraphs",
                "sources": [1, 3]
            }},
            {{
                "title": "Future Outlook",
                "content": "Future predictions and trends in 2-3 paragraphs",
                "sources": [1, 2, 3]
            }}
        ]
    }},
    "themes": [
        {{"theme": "Major theme 1", "description": "Description", "sources": [1, 2, 3]}}
    ],
    "contradictions": [
        {{"point": "Contradictory point", "viewpoints": ["View 1", "View 2"], "sources": [1, 3]}}
    ],
    "knowledge_gaps": ["Gap 1", "Gap 2"],
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "further_research": ["Topic 1", "Topic 2"],
    "suggested_media_keywords": ["visual concept 1", "diagram type", "chart topic"]
}}

IMPORTANT:
- The lead_paragraph should be engaging and journalistic
- Each body paragraph should focus on a distinct aspect
- Paragraphs should be complete and self-contained
- The pull_quote should be memorable and impactful
- Generate 6-10 key_findings with diverse categories (primary, secondary, emerging, consideration)
- Each finding needs a concise headline (10-15 words) and detailed explanation (1-2 sentences)
- Include statistics where available as key-value pairs
- Category definitions:
  * primary: Core, well-established findings with strong evidence
  * secondary: Important but less central findings
  * emerging: New or developing insights with growing evidence
  * consideration: Important caveats, warnings, or limitations
- Impact scores (0-1) represent the potential significance of the finding

Return ONLY the JSON object."""

        # Try up to 3 times with different strategies
        for attempt in range(3):
            try:
                # Adjust temperature for retries
                temperature = 0.4 + (attempt * 0.1)  # 0.4, 0.5, 0.6

                response = await self.generate(prompt, temperature=temperature, max_tokens=4000)

                # Extract and clean JSON
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:]
                if response.startswith("```"):
                    response = response[3:]
                if response.endswith("```"):
                    response = response[:-3]

                # Sanitize the response to fix common JSON issues
                sanitized_response = self.sanitize_json_response(response.strip())

                try:
                    synthesis = json.loads(sanitized_response)
                except json.JSONDecodeError as json_error:
                    # If first attempt fails, try without sanitization
                    if attempt == 0:
                        logger.warning(f"JSON parse failed on attempt {attempt + 1}, retrying", error=str(json_error))
                        synthesis = json.loads(response.strip())
                    else:
                        raise json_error

                # Flatten executive_summary if it's in the new structured format
                if isinstance(synthesis.get("executive_summary"), dict):
                    exec_summary = synthesis["executive_summary"]
                    # Combine paragraphs into formatted text
                    paragraphs = [exec_summary.get("lead_paragraph", "")]
                    paragraphs.extend(exec_summary.get("body_paragraphs", []))
                    synthesis["executive_summary"] = "\n\n".join(p for p in paragraphs if p)
                    synthesis["pull_quote"] = exec_summary.get("pull_quote", "")

                # Validate the synthesis
                if self.validate_synthesis(synthesis):
                    logger.info(f"Synthesis generated successfully on attempt {attempt + 1}")

                    # Ensure detailed_analysis exists with proper structure
                    if not synthesis.get("detailed_analysis") or not synthesis["detailed_analysis"].get("sections"):
                        # Generate fallback sections from themes if available
                        sections = []
                        if synthesis.get("themes"):
                            for theme in synthesis["themes"][:5]:  # Take up to 5 themes
                                sections.append({
                                    "title": theme.get("theme", "Analysis Section"),
                                    "content": theme.get("description", "Detailed analysis content."),
                                    "sources": theme.get("sources", [])
                                })
                        else:
                            # Create default sections
                            sections = [
                                {
                                    "title": "Overview and Background",
                                    "content": "This research provides comprehensive insights into the topic based on analysis of multiple sources.",
                                    "sources": [1, 2]
                                },
                                {
                                    "title": "Key Findings",
                                    "content": "The primary findings indicate significant developments in the field with notable implications.",
                                    "sources": [1, 2, 3]
                                },
                                {
                                    "title": "Current State",
                                    "content": "The current landscape shows rapid evolution with multiple stakeholders contributing to advancement.",
                                    "sources": [2, 3]
                                },
                                {
                                    "title": "Future Outlook",
                                    "content": "Looking ahead, several trends suggest continued growth and innovation in this area.",
                                    "sources": [1, 2, 3]
                                }
                            ]

                        synthesis["detailed_analysis"] = {"sections": sections}

                    return synthesis
                else:
                    logger.warning(f"Synthesis validation failed on attempt {attempt + 1}")
                    if attempt < 2:
                        # Try with a simpler prompt on retry
                        prompt = self._get_simpler_synthesis_prompt(summaries, query, attempt)
                        continue
                    else:
                        # Last attempt - use fallback
                        logger.info("Using fallback synthesis generation")
                        return self.generate_fallback_synthesis(summaries, query)

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse synthesis on attempt {attempt + 1}", error=str(e))
                if attempt < 2:
                    # Try with simpler prompt
                    prompt = self._get_simpler_synthesis_prompt(summaries, query, attempt)
                    continue
                else:
                    # Final attempt failed - use fallback
                    logger.info("All synthesis attempts failed, using fallback")
                    return self.generate_fallback_synthesis(summaries, query)
            except Exception as e:
                logger.error(f"Unexpected error in synthesis attempt {attempt + 1}", error=str(e))
                if attempt < 2:
                    continue
                else:
                    return self.generate_fallback_synthesis(summaries, query)

        # Should not reach here, but just in case
        return self.generate_fallback_synthesis(summaries, query)

    async def generate_analysis_outline(
        self,
        summaries: List[Dict[str, str]],
        query: str
    ) -> List[str]:
        """Generate outline of main sections for detailed analysis

        Args:
            summaries: List of content summaries
            query: Research query

        Returns:
            List of section titles
        """
        summaries_text = "\n\n".join([
            f"Source {i+1}: {s.get('summary', '')[:500]}"
            for i, s in enumerate(summaries[:10])  # Use first 10 for outline
        ])

        prompt = f"""Based on this research about "{query}", create an outline for a detailed analysis report.

Research summaries:
{summaries_text}

Generate 5-8 main section titles that comprehensively cover the topic.
Provide ONLY the section titles, one per line, no numbering or bullets.

Examples of good section titles:
- Technical Innovations and Breakthroughs
- Market Impact and Economic Implications
- Current Implementation Status
- Challenges and Limitations
- Future Outlook and Predictions
- Regulatory and Policy Considerations

Section titles:"""

        try:
            response = await self.generate(prompt, temperature=0.5, max_tokens=500)
            sections = [line.strip() for line in response.strip().split('\n') if line.strip()]
            return sections[:8]  # Limit to 8 sections max
        except Exception as e:
            logger.warning("Failed to generate outline", error=str(e))
            # Return default sections
            return [
                "Overview and Background",
                "Key Developments and Findings",
                "Technical Analysis",
                "Challenges and Considerations",
                "Future Implications"
            ]

    async def generate_section_content(
        self,
        section_title: str,
        summaries: List[Dict[str, str]],
        query: str,
        section_index: int
    ) -> str:
        """Generate detailed content for a specific section

        Args:
            section_title: Title of the section
            summaries: All research summaries
            query: Research query
            section_index: Index of this section

        Returns:
            Section content (2-3 paragraphs)
        """
        # Pass all summaries for comprehensive analysis
        summaries_text = "\n\n".join([
            f"Source [{i+1}] ({s.get('url', 'Unknown')}):\n{s.get('summary', '')}"
            for i, s in enumerate(summaries)
        ])

        prompt = f"""Write a detailed analysis section titled "{section_title}" for research about "{query}".

Research data from all sources:
{summaries_text}

Requirements:
1. Write 2-3 comprehensive paragraphs (300-500 words total) using **markdown formatting**
2. Include specific details, data points, and examples from the sources
3. Reference source numbers like [1], [2] when citing information
4. Focus specifically on aspects related to "{section_title}"
5. Make the content informative and analytical, not just descriptive

**Formatting Guidelines:**
- Use **bold** for key terms, important concepts, and critical findings
- Use *italics* for emphasis, technical terms, or quotes
- Use bullet points for lists of features, benefits, or key points
- Use ### for sub-headings if the content naturally breaks into distinct topics
- Use > for important callouts or quotes from sources
- Maintain professional, magazine-style writing

Return the content in **markdown format** for better readability and visual hierarchy.

Section content:"""

        try:
            response = await self.generate(prompt, temperature=0.6, max_tokens=1000)
            return response.strip()
        except Exception as e:
            logger.warning(f"Failed to generate section content for {section_title}", error=str(e))
            return f"Analysis of {section_title} based on the research findings."

    async def extract_quotes_and_stats(
        self,
        section_content: str,
        section_title: str,
        summaries: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Extract relevant quotes and statistics from sources for a section

        Args:
            section_content: The generated section content
            section_title: Title of the section
            summaries: Original source summaries

        Returns:
            Dictionary with quotes and statistics
        """
        summaries_text = "\n\n".join([
            f"Source [{i+1}]:\n{s.get('summary', '')}"
            for i, s in enumerate(summaries[:10])  # Focus on most relevant
        ])

        prompt = f"""Extract quotes and statistics relevant to "{section_title}" from these sources:

{summaries_text}

Find:
1. 1-2 direct quotes that support the section content (if available)
2. Key statistics or data points mentioned

Format as JSON:
{{
    "quotes": [
        {{"text": "quote text", "source_id": 1, "author": "Author Name or Source"}}
    ],
    "statistics": {{"metric_name": "value", "percentage": "85%"}}
}}

If no relevant quotes or stats found, return empty arrays/objects.
Return ONLY the JSON:"""

        try:
            response = await self.generate(prompt, temperature=0.3, max_tokens=500)
            # Extract JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            result = json.loads(response.strip())
            return result
        except Exception as e:
            logger.warning(f"Failed to extract quotes/stats for {section_title}", error=str(e))
            return {"quotes": [], "statistics": {}}

    async def generate_subsections(
        self,
        section_title: str,
        section_content: str
    ) -> List[Dict[str, str]]:
        """Generate subsections if the section would benefit from them

        Args:
            section_title: Title of the main section
            section_content: Content of the main section

        Returns:
            List of subsections with subtitle and content
        """
        prompt = f"""Does this section need subsections for better organization?

Section Title: {section_title}
Section Content: {section_content[:500]}...

If yes, create 1-2 subsection titles and brief content (1-2 paragraphs each) using **markdown formatting**.
If no subsections needed, respond with "NO_SUBSECTIONS".

**Formatting Guidelines for Subsections:**
- Use **bold** for key terms and important concepts
- Use *italics* for emphasis and technical terms
- Use bullet points for lists when appropriate
- Maintain professional, magazine-style writing

Format if subsections needed:
SUBSECTION 1: [Title]
[Markdown-formatted content]

SUBSECTION 2: [Title]
[Markdown-formatted content]"""

        try:
            response = await self.generate(prompt, temperature=0.5, max_tokens=600)

            if "NO_SUBSECTIONS" in response:
                return []

            subsections = []
            parts = response.split("SUBSECTION")
            for part in parts[1:]:  # Skip first empty part
                if ":" in part:
                    lines = part.strip().split('\n')
                    title = lines[0].split(':', 1)[1].strip()
                    content = '\n'.join(lines[1:]).strip()
                    if title and content:
                        subsections.append({
                            "subtitle": title,
                            "content": content
                        })

            return subsections[:2]  # Max 2 subsections
        except Exception as e:
            logger.warning(f"Failed to generate subsections for {section_title}", error=str(e))
            return []

    async def generate_detailed_analysis_multistep(
        self,
        summaries: List[Dict[str, str]],
        query: str,
        progress_callback=None
    ) -> Dict[str, Any]:
        """Generate detailed analysis using multi-step prompting

        Args:
            summaries: List of content summaries
            query: Research query
            progress_callback: Optional callback for progress updates

        Returns:
            Detailed analysis with sections, quotes, and statistics
        """
        try:
            # Step 1: Generate outline
            if progress_callback:
                await progress_callback(75, "Generating analysis outline")

            section_titles = await self.generate_analysis_outline(summaries, query)
            logger.info(f"Generated {len(section_titles)} sections for analysis")

            # Step 2: Generate content for each section
            sections = []
            for i, title in enumerate(section_titles):
                if progress_callback:
                    progress = 75 + (10 * (i + 1) / len(section_titles))
                    await progress_callback(progress, f"Writing section: {title}")

                # Generate section content
                content = await self.generate_section_content(title, summaries, query, i)

                # Extract source references from content
                source_refs = []
                for j in range(1, min(21, len(summaries) + 1)):
                    if f"[{j}]" in content:
                        source_refs.append(j)

                # Step 3: Extract quotes and statistics for this section
                quotes_stats = await self.extract_quotes_and_stats(content, title, summaries)

                # Step 4: Generate subsections if needed (only for longer sections)
                subsections = []
                if len(content) > 800:  # Only for substantial sections
                    subsections = await self.generate_subsections(title, content)

                section = {
                    "title": title,
                    "content": content,
                    "quotes": quotes_stats.get("quotes", []),
                    "statistics": quotes_stats.get("statistics", {}),
                    "sources": source_refs[:5],  # Limit to 5 source references
                    "subsections": subsections
                }

                sections.append(section)

            if progress_callback:
                await progress_callback(90, "Finalizing analysis structure")

            return {
                "sections": sections
            }

        except Exception as e:
            logger.error("Failed to generate detailed analysis", error=str(e))
            # Return fallback structure
            return {
                "sections": [
                    {
                        "title": "Overview",
                        "content": "Comprehensive analysis of the research findings.",
                        "sources": [1, 2]
                    },
                    {
                        "title": "Key Findings",
                        "content": "The main discoveries and insights from the research.",
                        "sources": [1, 2, 3]
                    }
                ]
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
            # Session should always exist now, but add safety check
            self.session = httpx.AsyncClient(timeout=self.timeout)

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