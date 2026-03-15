"""NLP pipeline for keyword extraction, entities, clustering, and sentiment."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from typing import Iterable

import spacy
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from config import N_CLUSTERS, SPACY_MODEL, TOP_K_KEYWORDS, TREND_WINDOW_HOURS


POSITIVE_WORDS = {"good", "great", "success", "benefit", "positive", "improve", "win"}
NEGATIVE_WORDS = {"bad", "crisis", "war", "risk", "negative", "fail", "loss"}


@dataclass
class NLPResult:
    keywords: list[tuple[str, int]]
    entities: list[tuple[str, int]]
    sentiment_distribution: dict[str, int]
    cluster_top_terms: dict[int, list[str]]


def load_spacy_model() -> spacy.language.Language:
    """Load spaCy model, fallback to blank model if unavailable."""
    try:
        return spacy.load(SPACY_MODEL)
    except Exception:
        nlp = spacy.blank("en")
        if "sentencizer" not in nlp.pipe_names:
            nlp.add_pipe("sentencizer")
        return nlp


def simple_sentiment(text: str) -> str:
    """Lightweight rule-based sentiment (positive/neutral/negative)."""
    tokens = [token.lower() for token in text.split()]
    pos = sum(1 for t in tokens if t in POSITIVE_WORDS)
    neg = sum(1 for t in tokens if t in NEGATIVE_WORDS)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def analyze_content(rows: Iterable[dict | object]) -> NLPResult:
    """Run NLP analysis over rows from the database."""
    nlp = load_spacy_model()

    keyword_counter: Counter[str] = Counter()
    entity_counter: Counter[str] = Counter()
    sentiments: Counter[str] = Counter()
    texts: list[str] = []

    for row in rows:
        title = row["title"]
        body = row["body"] or ""
        full_text = f"{title}. {body}".strip()
        if not full_text:
            continue

        doc = nlp(full_text)
        texts.append(full_text)

        for token in doc:
            if token.is_stop or token.is_punct or not token.is_alpha:
                continue
            lemma = token.lemma_.lower() if token.lemma_ else token.text.lower()
            if len(lemma) > 2:
                keyword_counter[lemma] += 1

        for ent in doc.ents:
            if ent.label_ in {"PERSON", "ORG", "GPE", "LOC"}:
                entity_counter[ent.text] += 1

        sentiments[simple_sentiment(full_text)] += 1

    cluster_terms = cluster_topics(texts)
    return NLPResult(
        keywords=keyword_counter.most_common(TOP_K_KEYWORDS),
        entities=entity_counter.most_common(TOP_K_KEYWORDS),
        sentiment_distribution=dict(sentiments),
        cluster_top_terms=cluster_terms,
    )


def cluster_topics(texts: list[str]) -> dict[int, list[str]]:
    """Cluster texts into topical groups using TF-IDF + KMeans."""
    if len(texts) < 3:
        return {}

    vectorizer = TfidfVectorizer(max_features=1500, stop_words="english")
    matrix = vectorizer.fit_transform(texts)
    n_clusters = min(N_CLUSTERS, len(texts))
    if n_clusters < 2:
        return {}

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    model.fit(matrix)

    terms = vectorizer.get_feature_names_out()
    order_centroids = model.cluster_centers_.argsort()[:, ::-1]
    cluster_summary: dict[int, list[str]] = {}
    for cluster_idx in range(n_clusters):
        top_terms = [terms[i] for i in order_centroids[cluster_idx, :8]]
        cluster_summary[cluster_idx] = top_terms
    return cluster_summary


def detect_trending_topics(rows: Iterable[dict | object]) -> list[dict]:
    """Compare recent keyword usage against historical baseline and score trends."""
    now = datetime.now(timezone.utc)
    recent_start = now - timedelta(hours=1)
    baseline_start = now - timedelta(hours=TREND_WINDOW_HOURS)

    recent_counter: Counter[str] = Counter()
    baseline_counter: Counter[str] = Counter()
    nlp = load_spacy_model()

    for row in rows:
        title = row["title"]
        body = row["body"] or ""
        text = f"{title}. {body}".strip()
        if not text:
            continue

        scraped_at = row["scraped_at"]
        try:
            timestamp = datetime.fromisoformat(scraped_at.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        except Exception:
            continue

        doc = nlp(text)
        keywords = [
            (t.lemma_.lower() if t.lemma_ else t.text.lower())
            for t in doc
            if t.is_alpha and not t.is_stop and len(t.text) > 2
        ]

        if timestamp >= recent_start:
            recent_counter.update(keywords)
        if baseline_start <= timestamp < recent_start:
            baseline_counter.update(keywords)

    trends: list[dict] = []
    for keyword, recent_count in recent_counter.items():
        baseline_count = baseline_counter.get(keyword, 0)
        trend_score = recent_count / (baseline_count + 1)
        if recent_count >= 2 and trend_score >= 1.5:
            trends.append(
                {
                    "topic": keyword,
                    "score": round(trend_score, 3),
                    "period_start": recent_start.isoformat(),
                    "period_end": now.isoformat(),
                    "metadata": json.dumps(
                        {
                            "recent_count": recent_count,
                            "baseline_count": baseline_count,
                        }
                    ),
                }
            )

    trends.sort(key=lambda x: x["score"], reverse=True)
    return trends[:TOP_K_KEYWORDS]
