"""Abstract base class for all data sources."""

from abc import ABC, abstractmethod
from pipeline.models import RawArticle


class BaseSource(ABC):
    """Base class that all data source collectors must implement."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable source name."""
        ...

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Source category: 'rss', 'news_api', 'gdelt', 'government'."""
        ...

    @abstractmethod
    def fetch(self) -> list[RawArticle]:
        """Fetch raw articles from this source. Returns list of RawArticle."""
        ...

    def is_relevant(self, text: str) -> bool:
        """Check if article text is relevant to Iran-US/Israel conflict."""
        from config import CONFLICT_KEYWORDS
        text_lower = text.lower()
        return any(kw in text_lower for kw in CONFLICT_KEYWORDS)
