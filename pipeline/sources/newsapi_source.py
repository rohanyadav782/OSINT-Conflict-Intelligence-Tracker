"""NewsAPI collector for news articles."""

import requests
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser
from pipeline.sources.base_source import BaseSource
from pipeline.models import RawArticle
from config import NEWSAPI_URL, NEWSAPI_KEY


class NewsAPISource(BaseSource):
    """Collects articles from NewsAPI.org (requires free API key)."""

    source_name = "NewsAPI"
    source_type = "news_api"

    def fetch(self) -> list[RawArticle]:
        if not NEWSAPI_KEY:
            print("[NewsAPI] No API key configured — skipping")
            return []

        articles = []
        seen_urls = set()

        queries = [
            'Iran AND (Israel OR "United States" OR military OR nuclear)',
            "IRGC OR Hezbollah OR Houthi",
            "Iran sanctions OR Iran nuclear deal",
        ]

        for query in queries:
            try:
                batch = self._search(query, seen_urls)
                articles.extend(batch)
            except Exception as e:
                print(f"[NewsAPI] Error querying '{query}': {e}")

        print(f"[NewsAPI] Total: {len(articles)} articles")
        return articles

    def _search(self, query: str, seen_urls: set) -> list[RawArticle]:
        """Search NewsAPI for a single query."""
        from_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

        params = {
            "q": query,
            "from": from_date,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 50,
            "apiKey": NEWSAPI_KEY,
        }

        resp = requests.get(NEWSAPI_URL, params=params, timeout=30)
        resp.raise_for_status()

        data = resp.json()
        raw_articles = data.get("articles", [])
        articles = []

        for item in raw_articles:
            url = item.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            title = item.get("title", "") or ""
            description = item.get("description", "") or ""

            if not self.is_relevant(f"{title} {description}"):
                continue

            pub_date = item.get("publishedAt", "")
            if pub_date:
                try:
                    dt = dateparser.parse(pub_date)
                    pub_date = dt.astimezone(timezone.utc).isoformat()
                except (ValueError, TypeError):
                    pub_date = datetime.now(timezone.utc).isoformat()
            else:
                pub_date = datetime.now(timezone.utc).isoformat()

            source_info = item.get("source", {})

            articles.append(RawArticle(
                title=title,
                description=description,
                full_text=item.get("content", "") or "",
                url=url,
                source_name=source_info.get("name", "NewsAPI"),
                source_type="news_api",
                published_at=pub_date,
                author=item.get("author"),
                image_url=item.get("urlToImage"),
                raw_metadata={
                    "newsapi_source_id": source_info.get("id", ""),
                }
            ))

        return articles
