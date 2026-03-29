"""Escalation index computation and anomaly detection."""
from __future__ import annotations

import numpy as np
import pandas as pd
from pipeline.db import get_events_dataframe, upsert_escalation, get_connection
from config import DB_PATH


def compute_escalation_index(db_path=DB_PATH):
    """Compute daily escalation index and detect anomalies."""
    df = get_events_dataframe(db_path)
    if df.empty:
        print("[Escalation] No events to analyze")
        return

    df["date"] = pd.to_datetime(df["event_datetime_utc"], format="ISO8601", utc=True).dt.date

    daily = df.groupby("date").agg(
        event_count=("event_id", "count"),
        avg_severity=("severity_score", "mean"),
        max_severity=("severity_score", "max"),
        domains=("domain", lambda x: x.nunique()),
        high_severity=("severity_score", lambda x: (x > 7).sum()),
    ).reset_index()

    # Compute 30-day rolling average for normalization
    if len(daily) > 1:
        rolling_avg = daily["event_count"].rolling(window=30, min_periods=1).mean()
    else:
        rolling_avg = daily["event_count"].astype(float)

    total_domains = df["domain"].nunique() or 1

    for i, row in daily.iterrows():
        norm_event_count = row["event_count"] / max(rolling_avg.iloc[i], 1)
        high_severity_ratio = row["high_severity"] / max(row["event_count"], 1)
        domain_diversity = row["domains"] / total_domains

        escalation_score = (
            0.4 * min(norm_event_count, 3.0) / 3.0  # normalize to 0-1 range
            + 0.3 * row["avg_severity"] / 10.0
            + 0.2 * high_severity_ratio
            + 0.1 * domain_diversity
        )
        escalation_score = round(escalation_score, 4)

        # Find dominant domain for the day
        day_events = df[df["date"] == row["date"]]
        dominant_domain = day_events["domain"].mode()
        dominant_domain = dominant_domain.iloc[0] if not dominant_domain.empty else "unknown"

        upsert_escalation({
            "date_utc": str(row["date"]),
            "event_count": int(row["event_count"]),
            "avg_severity": round(row["avg_severity"], 2),
            "max_severity": round(row["max_severity"], 2),
            "escalation_score": escalation_score,
            "dominant_domain": dominant_domain,
            "anomaly_flag": 0,
        }, db_path)

    # Anomaly detection: z-score on escalation_score
    detect_anomalies(db_path)

    print(f"[Escalation] Computed index for {len(daily)} days")


def detect_anomalies(db_path=DB_PATH):
    """Flag days where escalation score is > 2 SD above 30-day rolling mean."""
    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT date_utc, escalation_score FROM escalation_index ORDER BY date_utc"
    ).fetchall()

    if len(rows) < 3:
        conn.close()
        return

    scores = np.array([r["escalation_score"] for r in rows])
    dates = [r["date_utc"] for r in rows]

    # Rolling z-score with 30-day window
    window = min(30, len(scores))
    for i in range(len(scores)):
        start = max(0, i - window)
        window_scores = scores[start:i + 1]
        if len(window_scores) < 2:
            continue

        mean = np.mean(window_scores)
        std = np.std(window_scores)
        if std == 0:
            continue

        z_score = (scores[i] - mean) / std
        anomaly = 1 if z_score > 2.0 else 0

        conn.execute(
            "UPDATE escalation_index SET anomaly_flag = ? WHERE date_utc = ?",
            (anomaly, dates[i])
        )

    conn.commit()
    conn.close()


def get_escalation_summary(db_path=DB_PATH) -> dict:
    """Get current escalation status summary."""
    conn = get_connection(db_path)

    latest = conn.execute(
        "SELECT * FROM escalation_index ORDER BY date_utc DESC LIMIT 1"
    ).fetchone()

    anomaly_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM escalation_index WHERE anomaly_flag = 1"
    ).fetchone()["cnt"]

    avg_score = conn.execute(
        "SELECT AVG(escalation_score) as avg FROM escalation_index"
    ).fetchone()["avg"]

    conn.close()

    if not latest:
        return {"status": "no_data"}

    score = latest["escalation_score"]
    if score > 0.7:
        level = "HIGH"
    elif score > 0.4:
        level = "MODERATE"
    else:
        level = "LOW"

    return {
        "current_score": score,
        "level": level,
        "date": latest["date_utc"],
        "event_count": latest["event_count"],
        "avg_severity": latest["avg_severity"],
        "anomaly_count": anomaly_count,
        "overall_avg": round(avg_score, 4) if avg_score else 0,
        "is_anomaly": bool(latest["anomaly_flag"]),
    }
