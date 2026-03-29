"""Tests for the enrichment module."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pipeline.enrichment import compute_severity, compute_confidence, geocode_location
from pipeline.models import Event


def _make_event(**kwargs):
    defaults = dict(
        event_datetime_utc="2026-03-28T00:00:00+00:00",
        source_name="test", source_url="http://test.com/enrich",
        source_type="rss", claim_text="Test",
    )
    defaults.update(kwargs)
    return Event(**defaults)


def test_severity_military_high():
    event = _make_event(event_type="military_action", actor_1="IDF")
    score = compute_severity(event, "bombing attack killed soldiers destroyed base")
    assert score > 5.0


def test_severity_diplomatic_low():
    event = _make_event(event_type="diplomatic", actor_1="United Nations")
    score = compute_severity(event, "peace talks continued between diplomats")
    assert score < 5.0


def test_severity_in_range():
    event = _make_event(event_type="nuclear")
    score = compute_severity(event, "uranium enrichment detected by IAEA")
    assert 0.0 <= score <= 10.0


def test_confidence_wire_service():
    event = _make_event(source_name="Reuters")
    score = compute_confidence(event)
    assert score >= 0.7


def test_confidence_state_media():
    event = _make_event(source_name="IRNA")
    score = compute_confidence(event)
    assert score <= 0.7  # Bias-adjusted


def test_geocode_known_location():
    lat, lon = geocode_location("Tehran")
    assert lat is not None
    assert abs(lat - 35.69) < 0.1


def test_geocode_unknown_location():
    lat, lon = geocode_location("Unknown City XYZ")
    assert lat is None
    assert lon is None
