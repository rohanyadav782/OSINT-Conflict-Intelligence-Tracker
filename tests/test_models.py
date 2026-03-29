"""Tests for Pydantic data models."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pipeline.models import Event, RawArticle


def test_event_severity_clamping():
    """Severity score should be clamped to 0-10."""
    event = Event(
        event_datetime_utc="2026-03-28T00:00:00+00:00",
        source_name="test", source_url="http://test.com/1",
        source_type="rss", claim_text="Test event",
        severity_score=15.0,
    )
    assert event.severity_score == 10.0

    event2 = Event(
        event_datetime_utc="2026-03-28T00:00:00+00:00",
        source_name="test", source_url="http://test.com/2",
        source_type="rss", claim_text="Test event",
        severity_score=-5.0,
    )
    assert event2.severity_score == 0.0


def test_event_confidence_clamping():
    """Confidence score should be clamped to 0-1."""
    event = Event(
        event_datetime_utc="2026-03-28T00:00:00+00:00",
        source_name="test", source_url="http://test.com/3",
        source_type="rss", claim_text="Test event",
        confidence_score=1.5,
    )
    assert event.confidence_score == 1.0


def test_event_defaults():
    """Event should have sensible defaults."""
    event = Event(
        event_datetime_utc="2026-03-28T00:00:00+00:00",
        source_name="test", source_url="http://test.com/4",
        source_type="rss", claim_text="Test event",
    )
    assert event.event_type == "unknown"
    assert event.verification_status == "unverified"
    assert event.conflict_flag == 0


def test_raw_article_required_fields():
    """RawArticle should require title, url, source_name, source_type."""
    article = RawArticle(
        title="Test", url="http://test.com",
        source_name="Test Source", source_type="rss",
    )
    assert article.title == "Test"
    assert article.description == ""


def test_raw_article_missing_required():
    """RawArticle should reject missing required fields."""
    with pytest.raises(Exception):
        RawArticle(title="Test")  # missing url, source_name, source_type
