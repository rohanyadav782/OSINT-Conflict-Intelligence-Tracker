"""Pipeline orchestrator: collect -> normalize -> dedup -> enrich -> store."""

import sys
from datetime import datetime, timezone
from pipeline.db import init_db, insert_event
from pipeline.sources.rss_source import RSSSource
from pipeline.sources.gdelt_source import GDELTSource
from pipeline.sources.newsapi_source import NewsAPISource
from pipeline.normalizer import normalize
from pipeline.dedup import is_duplicate, assign_cluster_id
from pipeline.enrichment import enrich_event


def run_pipeline(skip_ner: bool = False):
    """Execute the full data ingestion pipeline."""
    print("=" * 60)
    print(f"Pipeline started at {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # Initialize database
    init_db()
    print("[DB] Database initialized")

    # Step 1: Collect from all sources
    print("\n--- STEP 1: Collecting data ---")
    sources = [
        RSSSource(),
        GDELTSource(),
        NewsAPISource(),
    ]

    all_articles = []
    for source in sources:
        try:
            articles = source.fetch()
            all_articles.extend(articles)
        except Exception as e:
            print(f"[ERROR] Source {source.source_name} failed: {e}")

    print(f"\nTotal raw articles collected: {len(all_articles)}")

    if not all_articles:
        print("[WARN] No articles collected. Check network and source availability.")
        return

    # Step 2: Normalize
    print("\n--- STEP 2: Normalizing ---")
    events = []
    for article in all_articles:
        try:
            event = normalize(article)
            events.append(event)
        except Exception as e:
            print(f"[NORM] Error normalizing {article.url}: {e}")

    print(f"Normalized: {len(events)} events")

    # Step 3: Deduplicate and store
    print("\n--- STEP 3: Dedup & Store ---")
    stored = 0
    duplicates = 0
    errors = 0

    for event in events:
        try:
            # Check for duplicates
            is_dup, match_id = is_duplicate(event)
            if is_dup:
                duplicates += 1
                continue

            # Assign cluster ID
            event.dedup_cluster_id = assign_cluster_id(event)

            # Step 4: Enrich (NER, scoring, geocoding)
            if not skip_ner:
                event = enrich_event(event)

            # Store in database
            event_dict = event.model_dump()
            event_id = insert_event(event_dict)
            if event_id:
                stored += 1
            else:
                duplicates += 1

        except Exception as e:
            errors += 1
            print(f"[STORE] Error: {e}")

    print(f"\nResults: {stored} stored, {duplicates} duplicates, {errors} errors")
    print(f"Pipeline completed at {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    return {"stored": stored, "duplicates": duplicates, "errors": errors}
