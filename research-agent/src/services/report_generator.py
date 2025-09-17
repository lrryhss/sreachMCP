"""Report generation service"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

from structlog import get_logger

logger = get_logger()


class ReportGenerator:
    """Generates research reports in various formats"""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize report generator

        Args:
            template_dir: Directory containing templates
        """
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent / "templates"

        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def generate_html_report(self, research_results: Dict[str, Any]) -> str:
        """Generate HTML report

        Args:
            research_results: Research results from orchestrator

        Returns:
            HTML report string
        """
        try:
            template = self.env.get_template("report.html")

            # Prepare template context
            context = self._prepare_context(research_results)

            # Render template
            html = template.render(**context)

            logger.info("HTML report generated", task_id=research_results.get("task_id"))
            return html

        except Exception as e:
            logger.error("HTML report generation failed", error=str(e))
            # Return a basic error report
            return self._generate_error_report(research_results, str(e))

    def generate_json_report(self, research_results: Dict[str, Any]) -> str:
        """Generate JSON report

        Args:
            research_results: Research results

        Returns:
            JSON string
        """
        try:
            # Clean up for JSON serialization
            clean_results = self._clean_for_json(research_results)
            return json.dumps(clean_results, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("JSON report generation failed", error=str(e))
            return json.dumps({"error": str(e)})

    def generate_markdown_report(self, research_results: Dict[str, Any]) -> str:
        """Generate Markdown report

        Args:
            research_results: Research results

        Returns:
            Markdown string
        """
        try:
            context = self._prepare_context(research_results)
            synthesis = context.get("synthesis", {})

            markdown = f"""# Research Report: {context['query']}

**Generated**: {context['generated_at']}
**Task ID**: {context['task_id']}
**Sources Analyzed**: {context['sources_count']}

## Executive Summary

{synthesis.get('executive_summary', 'No summary available.')}

## Key Findings

"""
            # Add key findings
            for finding in synthesis.get("key_findings", []):
                confidence = finding.get("confidence", 0) * 100
                markdown += f"- **{finding['finding']}** (Confidence: {confidence:.0f}%)\n"

            markdown += "\n## Detailed Analysis\n\n"

            # Add themes
            themes = synthesis.get("themes", [])
            if themes:
                markdown += "### Major Themes\n\n"
                for theme in themes:
                    markdown += f"**{theme['theme']}**\n{theme.get('description', '')}\n\n"

            # Add contradictions if any
            contradictions = synthesis.get("contradictions", [])
            if contradictions:
                markdown += "### Contradictions Found\n\n"
                for contradiction in contradictions:
                    markdown += f"- **{contradiction['point']}**\n"
                    for viewpoint in contradiction.get("viewpoints", []):
                        markdown += f"  - {viewpoint}\n"
                    markdown += "\n"

            # Add sources
            markdown += "## Sources\n\n"
            for i, source in enumerate(context.get("sources", []), 1):
                markdown += f"{i}. [{source.get('title', 'Untitled')}]({source['url']})\n"
                markdown += f"   {source.get('summary', '')[:200]}...\n\n"

            # Add recommendations
            recommendations = synthesis.get("recommendations", [])
            if recommendations:
                markdown += "## Recommendations\n\n"
                for rec in recommendations:
                    markdown += f"- {rec}\n"

            # Add further research
            further = synthesis.get("further_research", [])
            if further:
                markdown += "\n## Topics for Further Research\n\n"
                for topic in further:
                    markdown += f"- {topic}\n"

            return markdown

        except Exception as e:
            logger.error("Markdown report generation failed", error=str(e))
            return f"# Error Generating Report\n\nError: {str(e)}"

    def _prepare_context(self, research_results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare template context from research results

        Args:
            research_results: Raw research results

        Returns:
            Template context dictionary
        """
        synthesis = research_results.get("synthesis", {})
        sources = research_results.get("sources", [])
        metadata = research_results.get("metadata", {})

        # Calculate statistics
        total_words = sum(s.get("word_count", 0) for s in sources)
        avg_confidence = 0
        if synthesis.get("key_findings"):
            confidences = [f.get("confidence", 0) for f in synthesis["key_findings"]]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        context = {
            "task_id": research_results.get("task_id", ""),
            "query": research_results.get("query", ""),
            "status": research_results.get("status", ""),
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "synthesis": synthesis,
            "sources": sources,
            "sources_count": len(sources),
            "metadata": metadata,
            "statistics": {
                "total_words_analyzed": total_words,
                "average_confidence": avg_confidence,
                "search_strategies_used": len(metadata.get("search_strategies", [])),
                "urls_found": metadata.get("total_urls_found", 0),
                "content_fetched": metadata.get("content_fetched", 0)
            }
        }

        return context

    def _clean_for_json(self, data: Any) -> Any:
        """Clean data for JSON serialization

        Args:
            data: Data to clean

        Returns:
            Cleaned data
        """
        if isinstance(data, dict):
            return {k: self._clean_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_for_json(item) for item in data]
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            return str(data)

    def _generate_error_report(self, research_results: Dict[str, Any], error: str) -> str:
        """Generate basic error report

        Args:
            research_results: Partial research results
            error: Error message

        Returns:
            HTML error report
        """
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Research Report - Error</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
        }}
        .error {{
            background: #fee;
            border: 1px solid #fcc;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        h1 {{
            color: #c00;
        }}
        .details {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        pre {{
            background: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <h1>Research Report Generation Error</h1>
    <div class="error">
        <h2>Error Details</h2>
        <p>{error}</p>
    </div>
    <div class="details">
        <h3>Research Query</h3>
        <p>{research_results.get('query', 'N/A')}</p>
        <h3>Task ID</h3>
        <p>{research_results.get('task_id', 'N/A')}</p>
        <h3>Status</h3>
        <p>{research_results.get('status', 'N/A')}</p>
    </div>
</body>
</html>
"""