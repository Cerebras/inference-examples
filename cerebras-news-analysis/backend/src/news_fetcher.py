import feedparser
from loguru import logger
from urllib.parse import quote_plus

from . import config

def fetch_google_news(topic: str) -> list:
    """Fetches news from the Google News RSS feed for a specific topic."""
    logger.info(f"Fetching news for topic: {topic}")
    query = f'{topic} when:1h'
    encoded_query = quote_plus(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl={config.NEWS_LANG}&gl={config.NEWS_COUNTRY}&ceid={config.NEWS_COUNTRY}_{config.NEWS_LANG}"
    feed = feedparser.parse(rss_url)
    if feed.bozo:
        logger.warning(f"Error parsing RSS feed: {feed.bozo_exception}")
        return []
    return feed.entries
