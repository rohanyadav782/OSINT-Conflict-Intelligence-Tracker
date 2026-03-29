"""GDELT API collector for structured conflict event data."""

import requests
from datetime import datetime, timezone
from pipeline.sources.base_source import BaseSource
from pipeline.models import RawArticle
from config import GDELT_API_URL, SEARCH_QUERIES


class GDELTSource(BaseSource):
    """Collects articles from GDELT Project API (no API key needed)."""

    source_name = "GDELT"
    source_type = "gdelt"

    def fetch(self) -> list[RawArticle]:
        articles = []
        seen_urls = set()

        for query in SEARCH_QUERIES[:5]:  # limit queries to avoid rate limiting
            try:
                batch = self._search(query, seen_urls)
                articles.extend(batch)
            except Exception as e:
                print(f"[GDELT] Error querying '{query}': {e}")

        print(f"[GDELT] Total: {len(articles)} articles")
        return articles

    def _search(self, query: str, seen_urls: set) -> list[RawArticle]:
        """Search GDELT for a single query."""
        params = {
            "query": query,
            "mode": "artlist",
            "maxrecords": "50",
            "format": "json",
            "sort": "datedesc",
        }

        resp = requests.get(GDELT_API_URL, params=params, timeout=30)
        resp.raise_for_status()

        data = resp.json()
        raw_articles = data.get("articles", [])
        articles = []

        for item in raw_articles:
            url = item.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            title = item.get("title", "")
            if not self.is_relevant(title):
                continue

            # Parse GDELT datetime format
            seendate = item.get("seendate", "")
            pub_date = self._parse_gdelt_date(seendate)

            articles.append(RawArticle(
                title=title,
                description=title,  # GDELT artlist doesn't include description
                url=url,
                source_name=item.get("domain", "GDELT"),
                source_type="gdelt",
                published_at=pub_date,
                raw_metadata={
                    "gdelt_domain": item.get("domain", ""),
                    "language": item.get("language", ""),
                    "source_country": item.get("sourcecountry", ""),
                    "tone": item.get("tone", ""),
                    "socialimage": item.get("socialimage", ""),
                }
            ))

        return articles

    def _parse_gdelt_date(self, seendate: str) -> str:
        """Parse GDELT's date format (YYYYMMDDTHHmmSS)."""
        if not seendate:
            return datetime.now(timezone.utc).isoformat()
        try:
            dt = datetime.strptime(seendate, "%Y%m%dT%H%M%S")
            dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            return datetime.now(timezone.utc).isoformat()
