"""Pydantic models for data validation and schema enforcement."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class RawArticle(BaseModel):
    """Raw article as fetched from a source before normalization."""
    title: str
    description: str = ""
    full_text: str = ""
    url: str
    source_name: str
    source_type: str  # 'rss', 'news_api', 'gdelt', 'government', 'think_tank'
    published_at: Optional[str] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    raw_metadata: dict = Field(default_factory=dict)


class Event(BaseModel):
    """Normalized conflict event matching the required schema."""
    event_datetime_utc: str
    source_name: str
    source_url: str
    source_type: str
    claim_text: str
    country: Optional[str] = None
    location_text: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    actor_1: Optional[str] = None
    actor_2: Optional[str] = None
    event_type: str = "unknown"
    domain: str = "unknown"
    severity_score: float = 5.0
    confidence_score: float = 0.5
    verification_status: str = "unverified"
    tags: str = "[]"  # JSON array as string
    conflict_flag: int = 0
    raw_text: str = ""
    cameo_code: Optional[str] = None
    fatalities: Optional[int] = None
    last_updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    dedup_cluster_id: Optional[int] = None

    @field_validator("severity_score")
    @classmethod
    def clamp_severity(cls, v: float) -> float:
        return max(0.0, min(10.0, v))

    @field_validator("confidence_score")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class EventSource(BaseModel):
    """A corroborating source for an existing event."""
    event_id: int
    source_name: str
    source_url: str
    source_type: str
    claim_text: str = ""
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
