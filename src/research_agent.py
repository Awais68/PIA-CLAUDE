"""Research Agent - Multi-topic research with Gemini image generation."""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import google.generativeai as genai
from anthropic import Anthropic
from playwright.async_api import async_playwright

from src.config import RESEARCH, GEMINI_API_KEY
from src.utils import log_action

logger = logging.getLogger(__name__)

class ResearchAgent:
    """Multi-topic research orchestrator with Gemini image generation."""

    def __init__(self):
        """Initialize research agent."""
        self.client = Anthropic()
        self.research_dir = RESEARCH
        self.research_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir = self.research_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

        # Configure Gemini
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel("gemini-pro-vision")
        else:
            logger.warning("GEMINI_API_KEY not set - image generation disabled")
            self.gemini_model = None

    async def scrape_news(self, topic: str) -> dict:
        """Scrape news and data for a topic using Playwright.

        Args:
            topic: Stock ticker, crypto ticker, or search term

        Returns:
            Dict with headlines, data, sentiment keywords
        """
        results = {
            "topic": topic,
            "headlines": [],
            "data": {},
            "sentiment_keywords": [],
            "sources": []
        }

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # Try multiple sources
                sources = [
                    f"https://news.google.com/search?q={topic}",
                    f"https://finance.yahoo.com/quote/{topic.upper()}",
                ]

                for url in sources:
                    try:
                        await page.goto(url, timeout=10000, wait_until="domcontentloaded")
                        await page.wait_for_timeout(2000)

                        # Extract headlines
                        headlines = await page.eval_on_selector_all(
                            "h2, h3, a[data-testid]",
                            "elements => elements.map(e => e.innerText).filter(t => t.length > 10)"
                        )
                        results["headlines"].extend(headlines[:5])

                        # Extract any price data
                        prices = await page.eval_on_selector_all(
                            "[data-symbol], .price, .fin-streamer",
                            "elements => elements.map(e => e.innerText)"
                        )
                        if prices:
                            results["data"]["prices"] = prices[:3]

                        results["sources"].append(url)

                    except Exception as e:
                        logger.debug(f"Failed to scrape {url}: {e}")

                await browser.close()

        except Exception as e:
            logger.error(f"Playwright scraping failed for {topic}: {e}")

        return results

    def research_topic(self, topic: str, context: str = "") -> dict:
        """Research a single topic using Claude.

        Args:
            topic: Topic to research (stock, crypto, keyword)
            context: Additional context

        Returns:
            Dict with summary, key_data, sentiment
        """
        prompt = f"""Research and summarize {topic} ({context}):

1. Provide a 2-3 paragraph summary
2. Include key data (price, volume, change if applicable)
3. Assess sentiment (Bullish/Bearish/Neutral)
4. List top 3 key points

Format as:
**Summary**: [2-3 paragraphs]
**Key Data**: [bullet points]
**Sentiment**: [Bullish/Bearish/Neutral]
**Key Points**: [top 3]"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = message.content[0].text.strip()

            return {
                "topic": topic,
                "summary": content,
                "generated": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to research {topic}: {e}")
            return {
                "topic": topic,
                "summary": f"Unable to research {topic}. Error: {e}",
                "error": str(e)
            }

    def generate_infographic(self, topic: str, research_data: dict) -> Optional[str]:
        """Generate an infographic image using Gemini.

        Args:
            topic: Topic for the image
            research_data: Research data to visualize

        Returns:
            Path to saved image file or None
        """
        if not self.gemini_model:
            logger.warning(f"Gemini not configured - skipping image generation for {topic}")
            return None

        try:
            prompt = f"""Create a text-based infographic about {topic}:

Summary: {research_data.get('summary', '')}

Generate a creative ASCII art or text visualization showing:
1. Topic name prominently
2. Key metrics or data points
3. Sentiment indicator (up/down/stable)
4. Date generated

Make it visually interesting and informative."""

            response = self.gemini_model.generate_content(prompt)
            image_text = response.text

            # Save as text-based image
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_file = self.images_dir / f"{topic}_{now}.txt"
            image_file.write_text(image_text)

            log_action("research_agent", f"Generated infographic for {topic}", result="success")
            return str(image_file)

        except Exception as e:
            logger.error(f"Failed to generate infographic for {topic}: {e}")
            return None

    def research_topics(self, topics: list[str], context: str = "") -> dict:
        """Research multiple topics and generate report.

        Args:
            topics: List of topics to research
            context: Additional context for research

        Returns:
            Dict with research results for all topics
        """
        results = {
            "topics": topics,
            "generated": datetime.now().isoformat(),
            "research": []
        }

        for topic in topics:
            logger.info(f"Researching {topic}...")

            # Research the topic
            research = self.research_topic(topic, context)

            # Generate infographic
            image_path = self.generate_infographic(topic, research)
            research["image"] = image_path

            results["research"].append(research)

        return results

    def save_report(self, research_results: dict, scheduled: bool = False) -> str:
        """Save research report to Research/ folder.

        Args:
            research_results: Results from research_topics()
            scheduled: Whether this is a scheduled report

        Returns:
            Path to saved report file
        """
        topics = research_results.get("topics", [])
        topic_str = "_".join(topics)[:50]  # Limit filename length
        now = datetime.now().strftime("%Y%m%d_%H%M%S")

        report_file = self.research_dir / f"RESEARCH_{now}_{topic_str}.md"

        # Build markdown content
        content = f"""---
type: research_report
topics: {json.dumps(topics)}
generated: {datetime.now().isoformat()}
scheduled: {str(scheduled)}
---

# Research Report: {', '.join(topics)}

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""

        for research in research_results.get("research", []):
            topic = research.get("topic", "Unknown")
            summary = research.get("summary", "No summary available")
            image = research.get("image", None)

            content += f"\n## {topic}\n\n"
            content += f"{summary}\n"

            if image:
                image_name = Path(image).name
                content += f"\n**Visualization**: ![{topic}](images/{image_name})\n"

            content += "\n---\n"

        report_file.write_text(content)
        log_action("research_agent", f"Saved report for {topic_str}", result="success")

        return str(report_file)

    async def async_research(self, topics: list[str], context: str = "") -> dict:
        """Async research with web scraping + Claude analysis.

        Args:
            topics: Topics to research
            context: Additional context

        Returns:
            Research results
        """
        results = {
            "topics": topics,
            "generated": datetime.now().isoformat(),
            "research": []
        }

        # Scrape data for each topic concurrently
        scrape_tasks = [self.scrape_news(topic) for topic in topics]
        scrape_results = await asyncio.gather(*scrape_tasks)

        # Analyze with Claude
        for topic, scrape_data in zip(topics, scrape_results):
            context_str = f"Headlines: {', '.join(scrape_data.get('headlines', [])[:3])}"
            research = self.research_topic(topic, context_str)
            research["scrape_data"] = scrape_data

            # Generate image
            image_path = self.generate_infographic(topic, research)
            research["image"] = image_path

            results["research"].append(research)

        return results


def main():
    """CLI entry point for research agent."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Research Agent")
    parser.add_argument("--topics", required=True, help="Comma-separated topics (e.g., 'BTC,AAPL')")
    parser.add_argument("--context", default="", help="Additional context")
    parser.add_argument("--schedule", default="", help="Schedule pattern (e.g., 'daily 09:00')")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without saving")

    args = parser.parse_args()

    topics = [t.strip() for t in args.topics.split(",")]
    agent = ResearchAgent()

    print(f"Researching: {', '.join(topics)}")

    # Run research
    results = agent.research_topics(topics, args.context)

    # Save report (unless dry-run)
    if not args.dry_run:
        report_path = agent.save_report(results, scheduled=bool(args.schedule))
        print(f"Report saved to: {report_path}")
    else:
        print(json.dumps(results, indent=2))

    if args.schedule:
        print(f"Scheduled: {args.schedule}")


if __name__ == "__main__":
    main()
