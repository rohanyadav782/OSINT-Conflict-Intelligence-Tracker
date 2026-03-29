"""Plotly chart builders for the dashboard."""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def escalation_timeline(esc_df: pd.DataFrame) -> go.Figure:
    """Escalation score over time with anomaly highlights."""
    if esc_df.empty:
        return go.Figure().update_layout(title="No escalation data")

    fig = go.Figure()

    # Main line
    fig.add_trace(go.Scatter(
        x=esc_df["date_utc"],
        y=esc_df["escalation_score"],
        mode="lines+markers",
        name="Escalation Score",
        line=dict(color="#1f77b4", width=2),
    ))

    # Anomaly points
    anomalies = esc_df[esc_df["anomaly_flag"] == 1]
    if not anomalies.empty:
        fig.add_trace(go.Scatter(
            x=anomalies["date_utc"],
            y=anomalies["escalation_score"],
            mode="markers",
            name="Anomaly",
            marker=dict(color="red", size=12, symbol="triangle-up"),
        ))

    fig.update_layout(
        title="Escalation Index Over Time",
        xaxis_title="Date",
        yaxis_title="Escalation Score",
        height=400,
        template="plotly_white",
    )
    return fig


def domain_breakdown(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of event counts by domain."""
    if df.empty or "domain" not in df.columns:
        return go.Figure()

    domain_counts = df["domain"].value_counts()

    colors = {
        "military": "#d62728", "political": "#1f77b4", "economic": "#ff7f0e",
        "cyber": "#9467bd", "nuclear": "#e377c2", "humanitarian": "#2ca02c",
        "unknown": "#7f7f7f",
    }

    fig = go.Figure(go.Bar(
        x=domain_counts.values,
        y=domain_counts.index,
        orientation="h",
        marker_color=[colors.get(d, "#7f7f7f") for d in domain_counts.index],
    ))

    fig.update_layout(
        title="Events by Domain",
        xaxis_title="Count",
        height=300,
        template="plotly_white",
    )
    return fig


def severity_timeline(df: pd.DataFrame) -> go.Figure:
    """Event count and severity over time."""
    if df.empty or "event_datetime_utc" not in df.columns:
        return go.Figure()

    df = df.copy()
    df["date"] = pd.to_datetime(df["event_datetime_utc"], format="ISO8601", utc=True).dt.date
    daily = df.groupby("date").agg(
        count=("event_id", "count"),
        avg_severity=("severity_score", "mean"),
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily["date"], y=daily["count"],
        name="Event Count", marker_color="#1f77b4", opacity=0.6,
    ))
    fig.add_trace(go.Scatter(
        x=daily["date"], y=daily["avg_severity"],
        name="Avg Severity", yaxis="y2",
        line=dict(color="#d62728", width=2),
    ))

    fig.update_layout(
        title="Daily Event Count & Average Severity",
        yaxis=dict(title="Event Count"),
        yaxis2=dict(title="Avg Severity", overlaying="y", side="right", range=[0, 10]),
        height=400,
        template="plotly_white",
    )
    return fig


def event_map(df: pd.DataFrame) -> go.Figure:
    """Scatter map of events by location."""
    if df.empty:
        return go.Figure()

    map_df = df.dropna(subset=["latitude", "longitude"])
    if map_df.empty:
        return go.Figure().update_layout(title="No geocoded events")

    domain_colors = {
        "military": "red", "political": "blue", "economic": "orange",
        "cyber": "purple", "nuclear": "pink", "humanitarian": "green",
        "unknown": "gray",
    }

    fig = px.scatter_mapbox(
        map_df,
        lat="latitude",
        lon="longitude",
        color="domain",
        size="severity_score",
        hover_name="claim_text",
        hover_data=["source_name", "event_type", "severity_score", "confidence_score"],
        color_discrete_map=domain_colors,
        size_max=15,
        zoom=3,
        center={"lat": 32, "lon": 48},
        mapbox_style="open-street-map",
    )

    fig.update_layout(
        title="Conflict Events Map",
        height=600,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


def actor_bar_chart(actor_df: pd.DataFrame) -> go.Figure:
    """Top actors bar chart."""
    if actor_df.empty:
        return go.Figure()

    fig = go.Figure(go.Bar(
        x=actor_df["count"],
        y=actor_df["actor"],
        orientation="h",
        marker_color="#1f77b4",
    ))

    fig.update_layout(
        title="Top Actors by Mention Frequency",
        xaxis_title="Mentions",
        height=400,
        template="plotly_white",
        yaxis=dict(autorange="reversed"),
    )
    return fig


def event_type_pie(df: pd.DataFrame) -> go.Figure:
    """Pie chart of event type distribution."""
    if df.empty:
        return go.Figure()

    type_counts = df["event_type"].value_counts()

    fig = go.Figure(go.Pie(
        labels=type_counts.index,
        values=type_counts.values,
        hole=0.4,
    ))

    fig.update_layout(
        title="Event Type Distribution",
        height=350,
        template="plotly_white",
    )
    return fig
