"""Pattern detection: actor networks, event clustering, co-occurrence analysis."""
from __future__ import annotations

import json
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from pipeline.db import get_events_dataframe
from config import DB_PATH


def get_actor_cooccurrence(db_path=DB_PATH) -> pd.DataFrame:
    """Build actor co-occurrence matrix from (actor_1, actor_2) pairs."""
    df = get_events_dataframe(db_path)
    if df.empty:
        return pd.DataFrame()

    pairs = df[["actor_1", "actor_2"]].dropna(subset=["actor_1", "actor_2"])
    if pairs.empty:
        return pd.DataFrame()

    cooc = pairs.groupby(["actor_1", "actor_2"]).size().reset_index(name="count")
    return cooc.sort_values("count", ascending=False)


def get_actor_network(db_path=DB_PATH) -> dict:
    """Build an actor interaction network for visualization."""
    cooc = get_actor_cooccurrence(db_path)
    if cooc.empty:
        return {"nodes": [], "edges": []}

    # Build nodes
    actors = set(cooc["actor_1"].tolist() + cooc["actor_2"].tolist())
    nodes = [{"id": a, "label": a} for a in actors]

    # Build edges
    edges = []
    for _, row in cooc.iterrows():
        edges.append({
            "source": row["actor_1"],
            "target": row["actor_2"],
            "weight": int(row["count"]),
        })

    return {"nodes": nodes, "edges": edges}


def cluster_events(db_path=DB_PATH, eps: float = 0.5, min_samples: int = 2) -> pd.DataFrame:
    """Cluster events by text similarity to find related storylines."""
    df = get_events_dataframe(db_path)
    if df.empty or len(df) < min_samples:
        return df

    # TF-IDF vectorization
    try:
        vectorizer = TfidfVectorizer(
            stop_words="english", max_features=3000, min_df=1
        )
        tfidf_matrix = vectorizer.fit_transform(df["claim_text"].fillna(""))

        # DBSCAN clustering
        clustering = DBSCAN(
            eps=eps, min_samples=min_samples, metric="cosine"
        ).fit(tfidf_matrix)

        df["cluster"] = clustering.labels_

        n_clusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
        print(f"[Patterns] Found {n_clusters} event clusters")

    except Exception as e:
        print(f"[Patterns] Clustering error: {e}")
        df["cluster"] = -1

    return df


def get_storylines(db_path=DB_PATH) -> list[dict]:
    """Identify major storylines (groups of related events)."""
    df = cluster_events(db_path)
    if df.empty or "cluster" not in df.columns:
        return []

    storylines = []
    for cluster_id in sorted(df["cluster"].unique()):
        if cluster_id == -1:
            continue  # Skip noise

        cluster_events_df = df[df["cluster"] == cluster_id]
        if len(cluster_events_df) < 2:
            continue

        # Summarize the storyline
        storylines.append({
            "cluster_id": int(cluster_id),
            "event_count": len(cluster_events_df),
            "avg_severity": round(cluster_events_df["severity_score"].mean(), 2),
            "dominant_type": cluster_events_df["event_type"].mode().iloc[0] if not cluster_events_df["event_type"].mode().empty else "unknown",
            "actors": list(set(
                cluster_events_df["actor_1"].dropna().tolist()
                + cluster_events_df["actor_2"].dropna().tolist()
            ))[:5],
            "date_range": f"{cluster_events_df['event_datetime_utc'].min()[:10]} to {cluster_events_df['event_datetime_utc'].max()[:10]}",
            "sample_claims": cluster_events_df["claim_text"].head(3).tolist(),
        })

    return sorted(storylines, key=lambda x: x["event_count"], reverse=True)


def detect_escalation_patterns(db_path=DB_PATH) -> list[dict]:
    """Detect specific escalation patterns in the data."""
    df = get_events_dataframe(db_path)
    if df.empty:
        return []

    df["date"] = pd.to_datetime(df["event_datetime_utc"], format="ISO8601", utc=True).dt.date
    patterns = []

    # Pattern 1: Military action spike
    daily_military = df[df["event_type"] == "military_action"].groupby("date").size()
    if not daily_military.empty:
        mean_military = daily_military.mean()
        for date, count in daily_military.items():
            if count > mean_military * 2 and count > 3:
                patterns.append({
                    "type": "military_spike",
                    "date": str(date),
                    "description": f"Military action spike: {count} events (avg: {mean_military:.1f})",
                    "severity": "high",
                })

    # Pattern 2: Multi-domain escalation (events across 3+ domains in one day)
    daily_domains = df.groupby("date")["domain"].nunique()
    for date, n_domains in daily_domains.items():
        if n_domains >= 3:
            patterns.append({
                "type": "multi_domain",
                "date": str(date),
                "description": f"Multi-domain activity: {n_domains} domains active",
                "severity": "moderate",
            })

    # Pattern 3: High severity clustering (3+ events with severity > 7 on same day)
    daily_high = df[df["severity_score"] > 7].groupby("date").size()
    for date, count in daily_high.items():
        if count >= 3:
            patterns.append({
                "type": "severity_cluster",
                "date": str(date),
                "description": f"High-severity cluster: {count} events above 7.0",
                "severity": "high",
            })

    return sorted(patterns, key=lambda x: x["date"], reverse=True)
