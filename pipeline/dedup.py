"""Deduplication engine using URL matching and TF-IDF cosine similarity."""
from __future__ import annotations

from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pipeline.models import Event
from pipeline.db import url_exists, get_recent_events, insert_event_source, get_next_cluster_id
from config import DEDUP_FUZZY_THRESHOLD, DEDUP_TFIDF_THRESHOLD, DEDUP_TIME_WINDOW_HOURS
from datetime import datetime, timezone


def is_duplicate(event: Event) -> tuple[bool, int | None]:
    """
    Check if an event is a duplicate of an existing one.
    Returns (is_dup, matching_event_id).
    If it's a near-duplicate, the source is added as a corroborating source.
    """
    # Pass 1: Exact URL match
    if url_exists(event.source_url):
        return True, None

    # Pass 2: Fuzzy semantic match against recent events
    recent = get_recent_events(hours=DEDUP_TIME_WINDOW_HOURS)
    if not recent:
        return False, None

    # Quick pre-filter with rapidfuzz on claim_text
    candidates = []
    for existing in recent:
        score = fuzz.token_sort_ratio(
            event.claim_text[:200], existing["claim_text"][:200]
        )
        if score >= DEDUP_FUZZY_THRESHOLD:
            candidates.append(existing)

    if not candidates:
        return False, None

    # Detailed check with TF-IDF cosine similarity
    texts = [event.claim_text] + [c["claim_text"] for c in candidates]
    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        tfidf_matrix = vectorizer.fit_transform(texts)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]

        for i, sim in enumerate(similarities):
            if sim >= DEDUP_TFIDF_THRESHOLD:
                match = candidates[i]
                # Add as corroborating source
                insert_event_source({
                    "event_id": match["event_id"],
                    "source_name": event.source_name,
                    "source_url": event.source_url,
                    "source_type": event.source_type,
                    "claim_text": event.claim_text,
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                })
                return True, match["event_id"]
    except ValueError:
        # TF-IDF can fail on very short or empty texts
        pass

    return False, None


def assign_cluster_id(event: Event) -> int:
    """Assign a dedup cluster ID to a new event."""
    return get_next_cluster_id()
