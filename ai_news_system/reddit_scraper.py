"""Reddit scraper using subreddit RSS feeds (public, no auth)."""

from __future__ import annotations

from bs4 import BeautifulSoup
import feedparser

from config import REDDIT_LIMIT, REDDIT_SUBREDDITS


def _clean_html(html_text: str) -> str:
    """Convert HTML snippets from RSS into plain text."""
    soup = BeautifulSoup(html_text or "", "html.parser")
    return soup.get_text(" ", strip=True)


def scrape_subreddit(subreddit: str, limit: int = REDDIT_LIMIT) -> list[dict]:
    """Fetch posts for one subreddit from its RSS feed."""
    url = f"https://www.reddit.com/r/{subreddit}/.rss"
    parsed = feedparser.parse(url)
    posts: list[dict] = []

    for entry in parsed.entries[:limit]:
        posts.append(
            {
                "subreddit": subreddit,
                "title": entry.get("title", ""),
                "post_text": _clean_html(entry.get("summary", "")),
                # RSS doesn't expose these consistently; store defaults.
                "score": 0,
                "comments_count": 0,
                "timestamp": entry.get("published", entry.get("updated", "")),
                "post_url": entry.get("link", ""),
            }
        )
    return posts


def scrape_reddit() -> list[dict]:
    """Fetch posts from configured subreddits."""
    combined: list[dict] = []
    for subreddit in REDDIT_SUBREDDITS:
        combined.extend(scrape_subreddit(subreddit))
    return combined


def run_reddit_scrape() -> list[dict]:
    """Convenience entrypoint callable from other modules."""
    return scrape_reddit()


if __name__ == "__main__":
    data = run_reddit_scrape()
    print(f"Scraped {len(data)} reddit posts.")
