"""Enrichment module: NER, severity scoring, confidence scoring, geocoding."""
from __future__ import annotations

import re
from pipeline.models import Event
from config import (
    SEVERITY_BASE, HIGH_INTENSITY_KEYWORDS, SOURCE_RELIABILITY,
    KNOWN_ACTORS, EVENT_TYPE_KEYWORDS,
)

# Lazy-loaded NER pipeline (avoid loading transformer on import)
_ner_pipeline = None


def get_ner_pipeline():
    """Lazy-load the NER pipeline to avoid slow startup."""
    global _ner_pipeline
    if _ner_pipeline is None:
        try:
            from transformers import pipeline
            _ner_pipeline = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple",
            )
            print("[NER] Model loaded successfully")
        except Exception as e:
            print(f"[NER] Failed to load model: {e}")
            _ner_pipeline = "unavailable"
    return _ner_pipeline if _ner_pipeline != "unavailable" else None


def enrich_event(event: Event) -> Event:
    """Apply all enrichment steps to an event."""
    text = event.raw_text or event.claim_text

    # NER-based enrichment (optional — falls back to keyword extraction)
    event = enrich_with_ner(event, text)

    # Severity scoring
    event.severity_score = compute_severity(event, text)

    # Confidence scoring
    event.confidence_score = compute_confidence(event)

    # Geocoding (lightweight — use location lookup table instead of API)
    if event.location_text and not event.latitude:
        lat, lon = geocode_location(event.location_text)
        event.latitude = lat
        event.longitude = lon

    return event


def enrich_with_ner(event: Event, text: str) -> Event:
    """Use NER to extract entities if transformer is available."""
    ner = get_ner_pipeline()
    if ner is None:
        return event

    try:
        # Truncate text for NER (model has max input length)
        ner_text = text[:512]
        entities = ner(ner_text)

        orgs = []
        locs = []
        persons = []

        for ent in entities:
            label = ent["entity_group"]
            word = ent["word"].strip()
            if len(word) < 2:
                continue

            if label == "ORG":
                # Map to known actors if possible
                for keyword, canonical in KNOWN_ACTORS.items():
                    if keyword.lower() in word.lower():
                        word = canonical
                        break
                orgs.append(word)
            elif label == "LOC":
                locs.append(word)
            elif label == "PER":
                persons.append(word)

        # Update actors if NER found better matches
        if orgs and not event.actor_1:
            event.actor_1 = orgs[0]
            if len(orgs) > 1 and not event.actor_2:
                event.actor_2 = orgs[1]

        # Update location if NER found locations
        if locs and not event.location_text:
            event.location_text = ", ".join(locs[:3])

    except Exception as e:
        print(f"[NER] Error processing text: {e}")

    return event


def compute_severity(event: Event, text: str) -> float:
    """
    Composite severity score (0-10):
    - 35% event type base severity
    - 25% keyword intensity
    - 20% actor significance
    - 20% fatality factor
    """
    # Event type base
    type_score = SEVERITY_BASE.get(event.event_type, 5.0)

    # Keyword intensity
    text_lower = text.lower()
    intensity_count = sum(1 for kw in HIGH_INTENSITY_KEYWORDS if kw in text_lower)
    keyword_score = min(10.0, intensity_count * 2.0)

    # Actor significance
    actor_scores = {
        "IDF": 8, "IRGC": 8, "US Military": 8, "US CENTCOM": 8,
        "Iran Military": 8, "IAF": 8, "US Navy": 7,
        "Hezbollah": 7, "Hamas": 7, "Houthis": 6,
        "Mossad": 7, "IRGC Quds Force": 8, "Shin Bet": 7,
        "Iran Leadership": 7, "Israel Leadership": 7, "US Leadership": 7,
        "IAEA": 5, "United Nations": 4, "European Union": 4,
    }
    actor_score = max(
        actor_scores.get(event.actor_1 or "", 5),
        actor_scores.get(event.actor_2 or "", 3),
    )

    # Fatality factor
    fatality_score = 0.0
    if event.fatalities and event.fatalities > 0:
        import math
        fatality_score = min(10.0, math.log10(event.fatalities + 1) * 3)

    severity = (
        0.35 * type_score
        + 0.25 * keyword_score
        + 0.20 * actor_score
        + 0.20 * fatality_score
    )
    return round(max(0.0, min(10.0, severity)), 2)


def compute_confidence(event: Event) -> float:
    """
    Confidence score (0-1) based on source reliability and verification signals.
    """
    # Base by source type
    base = SOURCE_RELIABILITY.get(event.source_type, 0.5)

    # Wire services and well-known outlets get a boost
    high_reliability_sources = [
        "reuters", "associated press", "ap news", "bbc", "afp",
    ]
    source_lower = event.source_name.lower()
    if any(s in source_lower for s in high_reliability_sources):
        base = max(base, 0.8)

    # Government and state media get a bias adjustment
    state_media = ["irna", "isna", "press tv", "fars news"]
    if any(s in source_lower for s in state_media):
        base = min(base, 0.6)  # Lower ceiling due to potential bias

    # Penalty for conflicting reports
    if event.conflict_flag:
        base -= 0.2

    return round(max(0.0, min(1.0, base)), 2)


# Static geocoding lookup (avoids rate-limited API calls)
LOCATION_COORDS = {
    "Tehran": (35.6892, 51.3890),
    "Tel Aviv": (32.0853, 34.7818),
    "Jerusalem": (31.7683, 35.2137),
    "Gaza": (31.5017, 34.4668),
    "Beirut": (33.8938, 35.5018),
    "Damascus": (33.5138, 36.2765),
    "Baghdad": (33.3152, 44.3661),
    "Sanaa": (15.3694, 44.1910),
    "Strait of Hormuz": (26.5667, 56.2500),
    "Red Sea": (20.0000, 38.0000),
    "Golan Heights": (33.0000, 35.7500),
    "West Bank": (31.9500, 35.2500),
    "Rafah": (31.2750, 34.2500),
    "Isfahan": (32.6546, 51.6680),
    "Natanz": (33.5100, 51.9200),
    "Dimona": (31.0700, 35.0300),
    "Haifa": (32.7940, 34.9896),
    "Erbil": (36.1912, 44.0119),
    "Aleppo": (36.2021, 37.1343),
    "Homs": (34.7300, 36.7100),
    "Persian Gulf": (26.0000, 52.0000),
    "Gulf of Oman": (24.5000, 58.5000),
    "Bandar Abbas": (27.1865, 56.2808),
    "Chabahar": (25.2919, 60.6430),
    "Parchin": (35.5200, 51.7700),
    "Fordow": (34.7100, 51.2600),
    "Arak": (34.0917, 49.6892),
}


def geocode_location(location_text: str) -> tuple[float | None, float | None]:
    """Look up coordinates from the static table. Returns (lat, lon) or (None, None)."""
    if not location_text:
        return None, None

    for loc_name, (lat, lon) in LOCATION_COORDS.items():
        if loc_name.lower() in location_text.lower():
            return lat, lon

    return None, None
