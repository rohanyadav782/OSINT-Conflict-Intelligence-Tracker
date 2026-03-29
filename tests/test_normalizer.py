"""Tests for the normalization module."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.normalizer import classify_event_type, extract_actors, extract_country, extract_location
from pipeline.models import RawArticle
from pipeline.normalizer import normalize


def test_classify_military():
    assert classify_event_type("Iran launched missile strike against Israeli targets") == "military_action"


def test_classify_nuclear():
    assert classify_event_type("IAEA inspectors found uranium enrichment beyond limits") == "nuclear"


def test_classify_diplomatic():
    assert classify_event_type("Peace talks summit between envoys reached agreement") == "diplomatic"


def test_classify_unknown():
    assert classify_event_type("Weather forecast for tomorrow") == "unknown"


def test_extract_actors_iran_israel():
    a1, a2 = extract_actors("Iran launched attacks against Israel")
    assert a1 is not None
    assert a2 is not None


def test_extract_country():
    assert extract_country("Tehran announced new military drills") == "IR"
    assert extract_country("Israeli forces deployed near Gaza") == "IL"


def test_extract_location():
    loc = extract_location("Explosions reported near Tehran and Isfahan")
    assert "Tehran" in loc
    assert "Isfahan" in loc


def test_normalize_article():
    article = RawArticle(
        title="Iran strikes Israeli military base",
        description="IRGC claimed responsibility for missile attack",
        url="http://test.com/article1",
        source_name="Test News",
        source_type="rss",
        published_at="2026-03-28T12:00:00+00:00",
    )
    event = normalize(article)
    assert event.event_type == "military_action"
    assert event.domain == "military"
    assert event.country is not None
    assert event.source_url == "http://test.com/article1"
