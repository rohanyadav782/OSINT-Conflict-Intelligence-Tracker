"""RSS feed collector for multiple news sources."""

import feedparser
from datetime import datetime, timezone
from dateutil import parser as dateparser
from pipeline.sources.base_source import BaseSource
from pipeline.models import RawArticle
from config import RSS_FEEDS


class RSSSource(BaseSource):
    """Collects articles from configured RSS feeds."""

    source_type = "rss"

    def __init__(self, feed_name: str = None, feed_url: str = None):
        self._feed_name = feed_name
        self._feed_url = feed_url

    @property
    def source_name(self):
        return self._feed_name or "RSS"

    def fetch(self) -> list[RawArticle]:
        articles = []
        if self._feed_name and self._feed_url:
            feeds = {self._feed_name: self._feed_url}
        else:
            feeds = RSS_FEEDS

        for name, url in feeds.items():
            try:
                articles.extend(self._fetch_feed(name, url))
            except Exception as e:
                print(f"[RSS] Error fetching {name}: {e}")
        return articles

    def _fetch_feed(self, name: str, url: str) -> list[RawArticle]:
        """Parse a single RSS feed and return relevant articles."""
        articles = []
        feed = feedparser.parse(url)

        for entry in feed.entries:
            title = entry.get("title", "")
            description = entry.get("summary", entry.get("description", ""))
            link = entry.get("link", "")
            combined_text = f"{title} {description}"

            if not self.is_relevant(combined_text):
                continue

            pub_date = self._parse_date(entry)

            articles.append(RawArticle(
                title=title,
                description=description,
                url=link,
                source_name=name,
                source_type="rss",
                published_at=pub_date,
                raw_metadata={
                    "feed_url": url,
                    "author": entry.get("author", ""),
                    "tags": [t.get("term", "") for t in entry.get("tags", [])],
                }
            ))

        print(f"[RSS] {name}: {len(articles)} relevant articles")
        return articles

    def _parse_date(self, entry) -> str:
        """Extract and normalize publication date from feed entry."""
        for field in ["published", "updated", "created"]:
            raw = entry.get(field)
            if raw:
                try:
                    dt = dateparser.parse(raw)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt.astimezone(timezone.utc).isoformat()
                except (ValueError, TypeError):
                    continue
        return datetime.now(timezone.utc).isoformat()
