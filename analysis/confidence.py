"""Source reliability and cross-referencing analysis."""
from __future__ import annotations

import pandas as pd
from pipeline.db import get_connection, get_events_dataframe
from config import DB_PATH, SOURCE_RELIABILITY


def compute_source_reliability(db_path=DB_PATH):
    """Compute and store source reliability scores based on cross-referencing."""
    conn = get_connection(db_path)

    # Count total and corroborated events per source
    sources = conn.execute("""
        SELECT source_name,
               COUNT(*) as total_reports,
               SUM(CASE WHEN verification_status = 'confirmed' THEN 1 ELSE 0 END) as confirmed
        FROM events
        GROUP BY source_name
    """).fetchall()

    for src in sources:
        name = src["source_name"]
        total = src["total_reports"]
        confirmed = src["confirmed"]

        # Check how many of this source's events have corroborating sources
        corroborated = conn.execute("""
            SELECT COUNT(DISTINCT e.event_id) as cnt
            FROM events e
            JOIN event_sources es ON e.event_id = es.event_id
            WHERE e.source_name = ?
        """, (name,)).fetchone()["cnt"]

        # Reliability = base + corroboration_ratio
        base = 0.5
        if total > 0:
            corr_ratio = corroborated / total
            base = min(1.0, 0.5 + corr_ratio * 0.3)

        conn.execute("""
            INSERT INTO source_reliability (source_name, total_reports, confirmed_reports,
                                            reliability_score, last_evaluated)
            VALUES (?, ?, ?, ?, datetime('now'))
            ON CONFLICT(source_name) DO UPDATE SET
                total_reports = ?,
                confirmed_reports = ?,
                reliability_score = ?,
                last_evaluated = datetime('now')
        """, (name, total, confirmed, round(base, 3),
              total, confirmed, round(base, 3)))

    conn.commit()
    conn.close()
    print("[Confidence] Source reliability scores updated")


def get_source_agreement_matrix(db_path=DB_PATH) -> pd.DataFrame:
    """Build a matrix showing how often sources agree on events."""
    conn = get_connection(db_path)
    df = pd.read_sql_query("""
        SELECT e.source_name as primary_source,
               es.source_name as corroborating_source,
               COUNT(*) as agreement_count
        FROM events e
        JOIN event_sources es ON e.event_id = es.event_id
        GROUP BY e.source_name, es.source_name
    """, conn)
    conn.close()
    if df.empty:
        return pd.DataFrame()
    return df.pivot_table(
        index="primary_source", columns="corroborating_source",
        values="agreement_count", fill_value=0
    )
