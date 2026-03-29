"""Quick script to print data from the conflict_tracker database."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from pipeline.db import get_connection
from config import DB_PATH


conn = get_connection(DB_PATH)

# ── 1. All Tables & Row Counts ─────────────────────────────────────────────
print("\n" + "="*60)
print("TABLES & ROW COUNTS")
print("="*60)
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {t['name']}").fetchone()[0]
    print(f"  {t['name']:<25} {count} rows")

# ── 2. Latest 5 Events ─────────────────────────────────────────────────────
print("\n" + "="*60)
print("LATEST 5 EVENTS")
print("="*60)
events = conn.execute("""
    SELECT event_id, event_datetime_utc, source_name, event_type,
           severity_score, confidence_score, actor_1, actor_2, country, claim_text
    FROM events
    ORDER BY event_datetime_utc DESC
    LIMIT 5
""").fetchall()
for e in events:
    print(f"\n  ID        : {e['event_id']}")
    print(f"  Date      : {e['event_datetime_utc']}")
    print(f"  Source    : {e['source_name']}")
    print(f"  Type      : {e['event_type']}")
    print(f"  Severity  : {e['severity_score']}  |  Confidence: {e['confidence_score']}")
    print(f"  Actors    : {e['actor_1']} vs {e['actor_2']}")
    print(f"  Country   : {e['country']}")
    print(f"  Claim     : {e['claim_text'][:120]}...")

# ── 3. Escalation Index ────────────────────────────────────────────────────
print("\n" + "="*60)
print("ESCALATION INDEX (last 7 days)")
print("="*60)
rows = conn.execute("""
    SELECT date_utc, event_count, avg_severity, escalation_score,
           dominant_domain, anomaly_flag
    FROM escalation_index
    ORDER BY date_utc DESC
    LIMIT 7
""").fetchall()
if rows:
    print(f"  {'Date':<12} {'Events':<8} {'Avg Sev':<10} {'Esc Score':<12} {'Domain':<15} {'Anomaly'}")
    print("  " + "-"*65)
    for r in rows:
        anomaly = "⚠ YES" if r['anomaly_flag'] else "No"
        print(f"  {r['date_utc']:<12} {r['event_count']:<8} {r['avg_severity']:<10.2f} {r['escalation_score']:<12.4f} {r['dominant_domain']:<15} {anomaly}")
else:
    print("  No escalation data yet. Run: python run_pipeline.py")

# ── 4. Source Reliability ──────────────────────────────────────────────────
print("\n" + "="*60)
print("SOURCE RELIABILITY SCORES")
print("="*60)
sources = conn.execute("""
    SELECT source_name, total_reports, reliability_score
    FROM source_reliability
    ORDER BY reliability_score DESC
""").fetchall()
if sources:
    print(f"  {'Source':<25} {'Reports':<10} {'Reliability'}")
    print("  " + "-"*45)
    for s in sources:
        print(f"  {s['source_name']:<25} {s['total_reports']:<10} {s['reliability_score']:.3f}")
else:
    print("  No reliability data yet. Run analysis pipeline first.")

# ── 5. Event Type Breakdown ────────────────────────────────────────────────
print("\n" + "="*60)
print("EVENT TYPE BREAKDOWN")
print("="*60)
types = conn.execute("""
    SELECT event_type, COUNT(*) as count,
           ROUND(AVG(severity_score), 2) as avg_severity
    FROM events
    GROUP BY event_type
    ORDER BY count DESC
""").fetchall()
if types:
    print(f"  {'Event Type':<20} {'Count':<8} {'Avg Severity'}")
    print("  " + "-"*40)
    for t in types:
        print(f"  {t['event_type']:<20} {t['count']:<8} {t['avg_severity']}")
else:
    print("  No events yet.")

# ── 6. Top Actors ──────────────────────────────────────────────────────────
print("\n" + "="*60)
print("TOP ACTORS (by mention)")
print("="*60)
actors = conn.execute("""
    SELECT actor, SUM(cnt) as total FROM (
        SELECT actor_1 as actor, COUNT(*) as cnt FROM events
        WHERE actor_1 IS NOT NULL GROUP BY actor_1
        UNION ALL
        SELECT actor_2 as actor, COUNT(*) as cnt FROM events
        WHERE actor_2 IS NOT NULL GROUP BY actor_2
    )
    GROUP BY actor
    ORDER BY total DESC
    LIMIT 10
""").fetchall()
if actors:
    for a in actors:
        print(f"  {a['actor']:<30} {a['total']} mentions")
else:
    print("  No actor data yet.")

conn.close()
print("\n" + "="*60 + "\n")
