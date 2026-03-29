# OSINT Conflict Tracker: Iran-US/Israel

A lightweight open-source intelligence (OSINT) system for tracking, analyzing, and visualizing conflict events in the Iran-US/Israel theatre. Built for analysts under time pressure.

## Quick Start

```bash
# 1. Install dependencies
python3 -m pip install -r requirements.txt

# 2. (Optional) Set NewsAPI key for additional sources
export NEWSAPI_KEY=your_key_here

# 3. Run data pipeline
python3 run_pipeline.py              # Full pipeline with NER
python3 run_pipeline.py --skip-ner   # Faster, skip NER model download

# 4. Launch dashboard
python3 run_dashboard.py
# Or directly: streamlit run dashboard/app.py
```

## Architecture

```
Data Sources (RSS, GDELT, NewsAPI)
        |
        v
  [Collection Layer]
   pipeline/sources/
        |
        v
  [Normalization] --> [Deduplication] --> [Enrichment]
   normalizer.py       dedup.py          enrichment.py
        |                                    |
        v                                    v
  [SQLite Database]  <--  [Analysis Layer]
   data/                  analysis/
        |
        v
  [Streamlit Dashboard]
   dashboard/
```

## Data Sources

| Category | Sources | API Key Required |
|----------|---------|-----------------|
| RSS Feeds | Al Jazeera, BBC Middle East, Times of Israel, IRNA | No |
| News APIs | GDELT Project | No |
| News APIs | NewsAPI.org | Yes (free tier) |

## Data Schema

Each event contains:
- `event_datetime_utc` - ISO 8601 timestamp
- `source_name`, `source_url`, `source_type` - Full provenance
- `claim_text` - What was reported
- `country`, `location_text`, `latitude`, `longitude` - Geographic data
- `actor_1`, `actor_2` - Identified actors
- `event_type` - military_action, diplomatic, sanctions, cyber, nuclear, rhetoric, humanitarian
- `domain` - military, political, economic, cyber, nuclear, humanitarian
- `severity_score` (0-10) - Composite severity rating
- `confidence_score` (0-1) - Source reliability and verification
- `verification_status` - confirmed, unverified, disputed, denied
- `tags` - Relevant keywords

## Analysis Features

### Severity Scoring (0-10)
Weighted composite: 35% event type + 25% keyword intensity + 20% actor significance + 20% fatality factor

### Confidence Scoring (0-1)
Base by source type, adjusted for corroboration (+0.1 per independent source), recency, and conflict between reports (-0.2)

### Escalation Detection
Daily index combining normalized event count (40%), average severity (30%), high-severity ratio (20%), and domain diversity (10%). Z-score anomaly detection flags days > 2 SD above 30-day rolling mean.

### Deduplication
Two-pass: exact URL match, then TF-IDF cosine similarity (threshold 0.85) within 48-hour windows. Near-duplicates become corroborating sources.

## Dashboard Pages

1. **Executive Summary** - Key metrics, escalation trend, alerts, high-severity events
2. **Event Feed** - Filterable table, tabs (all/confirmed/high-severity), CSV export, detail view
3. **Trends** - Time series, actor frequency, event type distribution, domain trends
4. **Map View** - Geographic scatter map, location/country breakdowns
5. **Source Analysis** - Reliability scores, volume by source, bias indicators
6. **Drill-Down** - Storyline clustering, actor co-occurrence matrix, event detail with corroboration

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| SQLite | Zero-config, single file, portable, sufficient scale |
| TF-IDF dedup | Fast, interpretable, no GPU required |
| Keyword classifier | Deterministic, transparent, no training data needed |
| Z-score anomaly | Interpretable, works immediately, no training period |
| Static geocoding | Avoids rate-limited API calls, sufficient for known locations |
| RSS over scraping | Structured data, stable, no CSS selector fragility |

## Fact vs Inference Separation

- **Fact**: `claim_text` preserves the original source claim verbatim
- **Inference**: `event_type`, `severity_score`, `confidence_score` are system-generated classifications
- **Unknown**: Events default to `verification_status = "unverified"` until corroborated
- Conflicting reports are flagged with `conflict_flag = True`

## Project Structure

```
War-upadte tracker/
+-- config.py              # Central configuration
+-- run_pipeline.py         # Data ingestion CLI
+-- run_dashboard.py        # Dashboard launcher
+-- pipeline/               # Data collection and processing
|   +-- models.py           # Pydantic schemas
|   +-- db.py               # SQLite CRUD
|   +-- normalizer.py       # Raw -> structured
|   +-- dedup.py            # Deduplication engine
|   +-- enrichment.py       # NER, scoring, geocoding
|   +-- orchestrator.py     # Pipeline coordinator
|   +-- sources/            # Data source collectors
+-- analysis/               # Analytical modules
|   +-- escalation.py       # Escalation index
|   +-- trends.py           # Time-series analysis
|   +-- patterns.py         # Clustering, actor networks
|   +-- confidence.py       # Source reliability
+-- dashboard/              # Streamlit presentation
|   +-- app.py              # Main app
|   +-- pages/              # 6 dashboard pages
|   +-- components/         # Reusable UI components
+-- docs/                   # Documentation pack
+-- data/                   # SQLite database
+-- tests/                  # Test suite
```

## AI Usage Declaration

This project was built with assistance from Claude (Anthropic). Claude was used for:
- Code generation and architecture design
- Implementation of data pipeline, analysis algorithms, and dashboard
- Documentation writing

All analytical decisions (scoring algorithms, thresholds, source reliability methodology) were designed with explicit rationale and are fully documented. No data was fabricated; all events come from real open sources.
