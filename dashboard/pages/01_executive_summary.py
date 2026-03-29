"""Executive Summary page — key metrics, escalation trend, alerts."""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
from pipeline.db import get_events_dataframe, get_escalation_index
from analysis.escalation import get_escalation_summary
from analysis.patterns import detect_escalation_patterns
from dashboard.components.charts import escalation_timeline, domain_breakdown
from dashboard.components.tables import render_metric_row, render_high_severity_table


def show():
    st.header("Executive Summary")
    st.caption("Iran-US/Israel Conflict Intelligence Dashboard")

    df = get_events_dataframe()
    if df.empty:
        st.warning("No data available. Run the pipeline first: `python3 run_pipeline.py`")
        return

    # Parse dates
    df["_dt"] = pd.to_datetime(df["event_datetime_utc"], format="ISO8601", utc=True)

    # Top metrics
    esc = get_escalation_summary()
    total = len(df)
    last_24h = len(df[df["_dt"] >= pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=24)])
    last_7d = len(df[df["_dt"] >= pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=7)])

    # Escalation level color
    level = esc.get("level", "N/A")
    level_emoji = {"HIGH": "🔴", "MODERATE": "🟡", "LOW": "🟢"}.get(level, "⚪")

    render_metric_row([
        {"label": "Total Events", "value": total},
        {"label": "Last 24 Hours", "value": last_24h},
        {"label": "Last 7 Days", "value": last_7d},
        {"label": f"Escalation Level", "value": f"{level_emoji} {level}"},
        {"label": "Anomaly Alerts", "value": esc.get("anomaly_count", 0)},
    ])

    st.divider()

    # Two columns: escalation chart + domain breakdown
    col1, col2 = st.columns([2, 1])

    with col1:
        esc_df = get_escalation_index()
        st.plotly_chart(escalation_timeline(esc_df), use_container_width=True)

    with col2:
        st.plotly_chart(domain_breakdown(df), use_container_width=True)

    st.divider()

    # Alerts & patterns
    st.subheader("Active Alerts & Patterns")
    patterns = detect_escalation_patterns()
    if patterns:
        for p in patterns[:5]:
            sev_color = "red" if p["severity"] == "high" else "orange"
            st.markdown(
                f":{sev_color}[**{p['type'].upper()}**] ({p['date']}) — {p['description']}"
            )
    else:
        st.success("No escalation patterns detected")

    st.divider()

    # High severity events
    st.subheader("Highest Severity Events (last 48h)")
    recent = df[df["_dt"] >= pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=48)]
    render_high_severity_table(recent, threshold=5.0)

    # Confidence disclaimer
    st.divider()
    st.caption(
        "**Methodology note:** Severity scores (0-10) are computed from event type, "
        "keyword intensity, actor significance, and casualty data. Confidence scores (0-1) "
        "reflect source reliability and cross-referencing. All data is from open sources. "
        "Unverified events are clearly marked."
    )
