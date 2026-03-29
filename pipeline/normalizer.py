"""Normalize raw articles into structured Event objects."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pipeline.models import RawArticle, Event
from config import (
    EVENT_TYPE_KEYWORDS, EVENT_TYPE_TO_DOMAIN, KNOWN_ACTORS,
    CONFLICT_KEYWORDS,
)


def normalize(article: RawArticle) -> Event:
    """Convert a RawArticle into a structured Event."""
    text = f"{article.title} {article.description} {article.full_text}"

    # Classify event type
    event_type = classify_event_type(text)
    domain = EVENT_TYPE_TO_DOMAIN.get(event_type, "unknown")

    # Extract actors
    actor_1, actor_2 = extract_actors(text)

    # Extract country
    country = extract_country(text)

    # Extract location
    location_text = extract_location(text)

    # Parse datetime
    event_dt = article.published_at or datetime.now(timezone.utc).isoformat()

    # Build claim text (title + first sentence of description)
    claim_text = article.title
    if article.description:
        # Add first 300 chars of description
        claim_text = f"{article.title}. {article.description[:300]}"

    # Build tags
    tags = extract_tags(text)

    return Event(
        event_datetime_utc=event_dt,
        source_name=article.source_name,
        source_url=article.url,
        source_type=article.source_type,
        claim_text=claim_text,
        country=country,
        location_text=location_text,
        actor_1=actor_1,
        actor_2=actor_2,
        event_type=event_type,
        domain=domain,
        tags=json.dumps(tags),
        raw_text=text[:5000],
        last_updated_at=datetime.now(timezone.utc).isoformat(),
    )


def classify_event_type(text: str) -> str:
    """Classify event type based on keyword matching. Returns highest-scoring type."""
    text_lower = text.lower()
    scores = {}

    for etype, keywords in EVENT_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            scores[etype] = score

    if not scores:
        return "unknown"
    return max(scores, key=scores.get)


def extract_actors(text: str) -> tuple[str | None, str | None]:
    """Extract the two most prominent actors from text using known actors list."""
    found = []
    for keyword, canonical in KNOWN_ACTORS.items():
        if keyword.lower() in text.lower():
            if canonical not in found:
                found.append(canonical)

    # Prioritize state actors and military entities
    if len(found) == 0:
        return None, None
    elif len(found) == 1:
        return found[0], None
    else:
        return found[0], found[1]


def extract_country(text: str) -> str | None:
    """Extract primary country from text."""
    country_map = {
        "iran": "IR", "tehran": "IR", "iranian": "IR",
        "israel": "IL", "tel aviv": "IL", "jerusalem": "IL", "israeli": "IL",
        "united states": "US", "washington": "US", "american": "US",
        "lebanon": "LB", "beirut": "LB", "lebanese": "LB",
        "syria": "SY", "damascus": "SY", "syrian": "SY",
        "iraq": "IQ", "baghdad": "IQ", "iraqi": "IQ",
        "yemen": "YE", "sanaa": "YE", "yemeni": "YE",
        "gaza": "PS", "palestinian": "PS",
    }
    text_lower = text.lower()
    for keyword, code in country_map.items():
        if keyword in text_lower:
            return code
    return None


def extract_location(text: str) -> str | None:
    """Extract location mentions from text."""
    locations = [
        "Tehran", "Tel Aviv", "Jerusalem", "Gaza", "Beirut", "Damascus",
        "Baghdad", "Sanaa", "Strait of Hormuz", "Red Sea", "Golan Heights",
        "West Bank", "Rafah", "Isfahan", "Natanz", "Dimona", "Haifa",
        "Erbil", "Aleppo", "Homs", "Persian Gulf", "Gulf of Oman",
        "Bandar Abbas", "Chabahar", "Parchin", "Fordow", "Arak",
    ]
    found = [loc for loc in locations if loc.lower() in text.lower()]
    if found:
        return ", ".join(found[:3])
    return None


def extract_tags(text: str) -> list[str]:
    """Extract relevant tags/keywords from text."""
    tag_keywords = [
        "nuclear", "missile", "drone", "sanctions", "ceasefire",
        "proxy", "militia", "navy", "air force", "cyber",
        "JCPOA", "enrichment", "ballistic", "cruise missile",
        "humanitarian", "refugees", "casualties", "escalation",
        "de-escalation", "negotiations", "intelligence",
    ]
    text_lower = text.lower()
    return [tag for tag in tag_keywords if tag.lower() in text_lower]
