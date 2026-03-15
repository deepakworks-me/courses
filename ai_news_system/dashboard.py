"""Console dashboard + charts for AI News Intelligence System."""

from __future__ import annotations

import json

import matplotlib.pyplot as plt
import pandas as pd

from config import CHARTS_DIR
from database import fetch_recent_content, get_connection
from nlp_analysis import analyze_content


def _plot_trending_keywords(keywords: list[tuple[str, int]]) -> str:
    if not keywords:
        return ""
    labels, values = zip(*keywords[:10])
    plt.figure(figsize=(10, 5))
    plt.bar(labels, values)
    plt.xticks(rotation=45, ha="right")
    plt.title("Trending Keywords")
    plt.tight_layout()
    path = CHARTS_DIR / "trending_keywords.png"
    plt.savefig(path)
    plt.close()
    return str(path)


def _plot_sentiment_distribution(sentiments: dict[str, int]) -> str:
    if not sentiments:
        return ""
    labels = list(sentiments.keys())
    values = list(sentiments.values())
    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct="%1.1f%%")
    plt.title("Sentiment Distribution")
    path = CHARTS_DIR / "sentiment_distribution.png"
    plt.savefig(path)
    plt.close()
    return str(path)


def _plot_news_volume_per_source() -> str:
    with get_connection() as conn:
        df = pd.read_sql_query(
            "SELECT source, COUNT(*) AS total FROM news_articles GROUP BY source ORDER BY total DESC",
            conn,
        )
    if df.empty:
        return ""

    plt.figure(figsize=(8, 4))
    plt.bar(df["source"], df["total"])
    plt.title("News Volume per Source")
    plt.ylabel("Articles")
    plt.tight_layout()
    path = CHARTS_DIR / "news_volume_per_source.png"
    plt.savefig(path)
    plt.close()
    return str(path)


def _latest_headlines(limit: int = 8) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT title, source, publish_date FROM news_articles ORDER BY scraped_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [f"[{row['source']}] {row['title']} ({row['publish_date']})" for row in rows]


def _top_trending_topics(limit: int = 10) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT topic, score, metadata FROM trending_topics ORDER BY created_at DESC, score DESC LIMIT ?",
            (limit,),
        ).fetchall()
    topics = []
    for row in rows:
        meta = json.loads(row["metadata"]) if row["metadata"] else {}
        topics.append(
            f"{row['topic']} (score={row['score']}, recent={meta.get('recent_count', 'n/a')}, baseline={meta.get('baseline_count', 'n/a')})"
        )
    return topics


def render_dashboard() -> None:
    """Print key metrics and generate chart images."""
    rows = fetch_recent_content(limit=1000)
    analysis = analyze_content(rows)

    keyword_chart = _plot_trending_keywords(analysis.keywords)
    sentiment_chart = _plot_sentiment_distribution(analysis.sentiment_distribution)
    source_chart = _plot_news_volume_per_source()

    print("\n=== AI News Intelligence Dashboard ===")
    print("\nTop trending topics:")
    for topic in _top_trending_topics():
        print(f" - {topic}")

    print("\nLatest headlines:")
    for headline in _latest_headlines():
        print(f" - {headline}")

    print("\nMost discussed entities (people, companies, countries):")
    for entity, count in analysis.entities[:15]:
        print(f" - {entity}: {count}")

    print("\nClustered topics:")
    for cluster_id, terms in analysis.cluster_top_terms.items():
        print(f" - Cluster {cluster_id}: {', '.join(terms)}")

    print("\nCharts generated:")
    for chart in [keyword_chart, sentiment_chart, source_chart]:
        if chart:
            print(f" - {chart}")


if __name__ == "__main__":
    render_dashboard()
