"""Database helpers for storing scraped and analyzed data."""

import sqlite3
from pathlib import Path
from typing import Iterable

from config import DB_PATH


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Return a sqlite3 connection with row support."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create database tables if they do not already exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                article_text TEXT,
                author TEXT,
                source TEXT,
                publish_date TEXT,
                article_url TEXT UNIQUE,
                scraped_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reddit_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subreddit TEXT,
                title TEXT,
                post_text TEXT,
                score INTEGER,
                comments_count INTEGER,
                timestamp TEXT,
                post_url TEXT UNIQUE,
                scraped_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trending_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                score REAL,
                period_start TEXT,
                period_end TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def insert_news_articles(articles: Iterable[dict]) -> int:
    """Insert or ignore news article records."""
    query = """
        INSERT OR IGNORE INTO news_articles
        (title, article_text, author, source, publish_date, article_url)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    count = 0
    with get_connection() as conn:
        cur = conn.cursor()
        for item in articles:
            cur.execute(
                query,
                (
                    item.get("title"),
                    item.get("article_text"),
                    item.get("author"),
                    item.get("source"),
                    item.get("publish_date"),
                    item.get("article_url"),
                ),
            )
            if cur.rowcount > 0:
                count += 1
        conn.commit()
    return count


def insert_reddit_posts(posts: Iterable[dict]) -> int:
    """Insert or ignore Reddit post records."""
    query = """
        INSERT OR IGNORE INTO reddit_posts
        (subreddit, title, post_text, score, comments_count, timestamp, post_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    count = 0
    with get_connection() as conn:
        cur = conn.cursor()
        for item in posts:
            cur.execute(
                query,
                (
                    item.get("subreddit"),
                    item.get("title"),
                    item.get("post_text"),
                    item.get("score"),
                    item.get("comments_count"),
                    item.get("timestamp"),
                    item.get("post_url"),
                ),
            )
            if cur.rowcount > 0:
                count += 1
        conn.commit()
    return count


def insert_trending_topics(topics: Iterable[dict]) -> None:
    """Store trending topic snapshots."""
    query = """
        INSERT INTO trending_topics (topic, score, period_start, period_end, metadata)
        VALUES (?, ?, ?, ?, ?)
    """
    with get_connection() as conn:
        cur = conn.cursor()
        for topic in topics:
            cur.execute(
                query,
                (
                    topic.get("topic"),
                    topic.get("score"),
                    topic.get("period_start"),
                    topic.get("period_end"),
                    topic.get("metadata"),
                ),
            )
        conn.commit()


def fetch_recent_content(limit: int = 500) -> list[sqlite3.Row]:
    """Return merged recent news + reddit records for NLP analysis."""
    with get_connection() as conn:
        query = """
            SELECT title, article_text AS body, source AS channel, publish_date AS published_at,
                   scraped_at, 'news' AS content_type
            FROM news_articles
            UNION ALL
            SELECT title, post_text AS body, subreddit AS channel, timestamp AS published_at,
                   scraped_at, 'reddit' AS content_type
            FROM reddit_posts
            ORDER BY scraped_at DESC
            LIMIT ?
        """
        return conn.execute(query, (limit,)).fetchall()
