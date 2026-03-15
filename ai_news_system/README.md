# AI News Intelligence System

A complete Python pipeline that scrapes global news + Reddit discussions, stores data in SQLite, analyzes text with NLP, detects trends, and renders a dashboard.

## Install

```bash
pip install requests beautifulsoup4 feedparser pandas spacy scikit-learn schedule matplotlib
python -m spacy download en_core_web_sm
```

## Run

1. Run the automated scheduler (scrape + trend detection every 60 min):

```bash
cd ai_news_system
python scheduler.py
```

2. Render dashboard output + charts:

```bash
cd ai_news_system
python dashboard.py
```

Charts are saved in `ai_news_system/charts/`.
