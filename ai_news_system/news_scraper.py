"""RSS news scraper that enriches feed entries with article body text."""

from __future__ import annotations

from typing import List

import feedparser
import requests
from bs4 import BeautifulSoup

from config import RSS_FEEDS


def extract_article_text(url: str, timeout: int = 15) -> str:
    """Download a web page and return paragraph text."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        return "\n".join(p for p in paragraphs if p)
    except Exception:
        return ""


def scrape_news() -> List[dict]:
    """Scrape all configured RSS feeds and return normalized records."""
    results: list[dict] = []

    for source, feed_url in RSS_FEEDS.items():
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries:
            article_url = entry.get("link", "")
            text = extract_article_text(article_url) if article_url else ""

            author = entry.get("author") or entry.get("dc_creator") or "Unknown"

            results.append(
                {
                    "title": entry.get("title", ""),
                    "article_text": text,
                    "author": author,
                    "source": source,
                    "publish_date": entry.get("published", entry.get("updated", "")),
                    "article_url": article_url,
                }
            )
    return results


def run_news_scrape() -> list[dict]:
    """Convenience entrypoint callable from other modules."""
    return scrape_news()


if __name__ == "__main__":
    data = run_news_scrape()
    print(f"Scraped {len(data)} news articles.")
