"""Time-series aggregation and trend analysis."""
from __future__ import annotations

import pandas as pd
from pipeline.db import get_events_dataframe
from config import DB_PATH


def get_daily_trends(db_path=DB_PATH) -> pd.DataFrame:
    """Aggregate events by day with key metrics."""
    df = get_events_dataframe(db_path)
    if df.empty:
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["event_datetime_utc"], format="ISO8601", utc=True).dt.date
    daily = df.groupby("date").agg(
        event_count=("event_id", "count"),
        avg_severity=("severity_score", "mean"),
        max_severity=("severity_score", "max"),
        avg_confidence=("confidence_score", "mean"),
        unique_sources=("source_name", "nunique"),
    ).reset_index()

    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date")

    # Rolling averages
    if len(daily) > 1:
        daily["severity_7d_avg"] = daily["avg_severity"].rolling(7, min_periods=1).mean()
        daily["count_7d_avg"] = daily["event_count"].rolling(7, min_periods=1).mean()
    else:
        daily["severity_7d_avg"] = daily["avg_severity"]
        daily["count_7d_avg"] = daily["event_count"].astype(float)

    return daily


def get_domain_trends(db_path=DB_PATH) -> pd.DataFrame:
    """Event counts by domain over time."""
    df = get_events_dataframe(db_path)
    if df.empty:
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["event_datetime_utc"], format="ISO8601", utc=True).dt.date
    return df.groupby(["date", "domain"]).size().reset_index(name="count")


def get_actor_frequency(db_path=DB_PATH, top_n: int = 15) -> pd.DataFrame:
    """Top actors by mention frequency."""
    df = get_events_dataframe(db_path)
    if df.empty:
        return pd.DataFrame()

    actors = []
    for col in ["actor_1", "actor_2"]:
        actor_counts = df[col].dropna().value_counts()
        actors.append(actor_counts)

    if not actors:
        return pd.DataFrame()

    combined = pd.concat(actors).groupby(level=0).sum().sort_values(ascending=False)
    return combined.head(top_n).reset_index(name="count").rename(columns={"index": "actor"})


def get_event_type_distribution(db_path=DB_PATH) -> pd.DataFrame:
    """Distribution of event types."""
    df = get_events_dataframe(db_path)
    if df.empty:
        return pd.DataFrame()

    return df["event_type"].value_counts().reset_index(name="count").rename(
        columns={"index": "event_type"}
    )


def get_country_distribution(db_path=DB_PATH) -> pd.DataFrame:
    """Distribution of events by country."""
    df = get_events_dataframe(db_path)
    if df.empty:
        return pd.DataFrame()

    return df["country"].value_counts().reset_index(name="count").rename(
        columns={"index": "country"}
    )


def get_severity_by_domain(db_path=DB_PATH) -> pd.DataFrame:
    """Average severity by domain."""
    df = get_events_dataframe(db_path)
    if df.empty:
        return pd.DataFrame()

    return df.groupby("domain").agg(
        avg_severity=("severity_score", "mean"),
        max_severity=("severity_score", "max"),
        event_count=("event_id", "count"),
    ).reset_index().sort_values("avg_severity", ascending=False)
