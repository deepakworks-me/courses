"""Central configuration for the AI News Intelligence System."""

from pathlib import Path

# RSS feed endpoints
RSS_FEEDS = {
    "BBC": "http://feeds.bbci.co.uk/news/rss.xml",
    "CNN": "http://rss.cnn.com/rss/edition.rss",
    "Reuters": "http://feeds.reuters.com/reuters/topNews",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
}

# Reddit settings (using public JSON endpoint)
REDDIT_SUBREDDITS = ["news", "worldnews", "technology"]
REDDIT_LIMIT = 50
REDDIT_USER_AGENT = "AINewsIntelligenceSystem/1.0"

# Local storage
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "ai_news.db"
CHARTS_DIR = BASE_DIR / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

# NLP / analytics settings
SPACY_MODEL = "en_core_web_sm"
TOP_K_KEYWORDS = 20
N_CLUSTERS = 5
TREND_WINDOW_HOURS = 24

# Scheduler
SCRAPE_INTERVAL_MINUTES = 60
