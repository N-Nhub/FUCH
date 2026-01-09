import feedparser
from datetime import datetime, timedelta

GLOBAL_FEEDS = [
    "https://feeds.reuters.com/reuters/worldNews",
    "https://feeds.reuters.com/reuters/topNews",
    "https://rss.cnn.com/rss/edition_world.rss",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
]

def fetch_news(days=7, max_items=10):
    cutoff = datetime.utcnow() - timedelta(days=days)
    articles = []

    for url in GLOBAL_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            try:
                published = datetime(*entry.published_parsed[:6])
            except:
                continue

            if published < cutoff:
                continue

            articles.append({
                "title": entry.title,
                "summary": entry.summary,
                "link": entry.link,
                "date": published,
                "source": feed.feed.title
            })

    articles.sort(key=lambda x: x["date"], reverse=True)
    return articles[:max_items]
