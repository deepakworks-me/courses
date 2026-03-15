"""Scheduler that runs scraping + analysis every 60 minutes."""

from __future__ import annotations

import time

import schedule

from database import (
    fetch_recent_content,
    init_db,
    insert_news_articles,
    insert_reddit_posts,
    insert_trending_topics,
)
from news_scraper import scrape_news
from nlp_analysis import detect_trending_topics
from reddit_scraper import scrape_reddit


def pipeline_run() -> None:
    """Single pipeline run: scrape, persist, detect trends."""
    print("[Pipeline] Starting scrape...")
    news_articles = scrape_news()
    reddit_posts = scrape_reddit()

    inserted_news = insert_news_articles(news_articles)
    inserted_reddit = insert_reddit_posts(reddit_posts)
    print(f"[Pipeline] Inserted {inserted_news} news rows and {inserted_reddit} reddit rows.")

    rows = fetch_recent_content(limit=2000)
    trends = detect_trending_topics(rows)
    if trends:
        insert_trending_topics(trends)
    print(f"[Pipeline] Detected {len(trends)} trending topics.")


def run_scheduler() -> None:
    """Initialize DB, run once, then schedule hourly runs."""
    init_db()
    pipeline_run()

    schedule.every(60).minutes.do(pipeline_run)
    print("[Scheduler] Running every 60 minutes...")

    while True:
        schedule.run_pending()
        time.sleep(2)


if __name__ == "__main__":
    run_scheduler()
