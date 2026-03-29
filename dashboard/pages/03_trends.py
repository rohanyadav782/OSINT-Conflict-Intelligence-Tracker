"""Trends page — time series, actor charts, domain analysis."""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
from pipeline.db import get_events_dataframe
from analysis.trends import (
    get_daily_trends, get_actor_frequency, get_event_type_distribution,
    get_severity_by_domain, get_domain_trends,
)
from dashboard.components.charts import severity_timeline, actor_bar_chart, event_type_pie


def show():
    st.header("Trend Analysis")
    st.caption("Temporal patterns, actor frequency, and domain breakdown")

    df = get_events_dataframe()
    if df.empty:
        st.warning("No data available.")
        return

    # Event count + severity timeline
    st.plotly_chart(severity_timeline(df), use_container_width=True)

    st.divider()

    # Two columns: actor frequency + event type pie
    col1, col2 = st.columns(2)

    with col1:
        actor_df = get_actor_frequency()
        st.plotly_chart(actor_bar_chart(actor_df), use_container_width=True)

    with col2:
        st.plotly_chart(event_type_pie(df), use_container_width=True)

    st.divider()

    # Severity by domain
    st.subheader("Severity by Domain")
    sev_domain = get_severity_by_domain()
    if not sev_domain.empty:
        st.dataframe(
            sev_domain.style.format({
                "avg_severity": "{:.2f}",
                "max_severity": "{:.1f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

    # Daily trends table
    st.subheader("Daily Summary")
    daily = get_daily_trends()
    if not daily.empty:
        st.dataframe(
            daily.style.format({
                "avg_severity": "{:.2f}",
                "max_severity": "{:.1f}",
                "avg_confidence": "{:.2f}",
                "severity_7d_avg": "{:.2f}",
                "count_7d_avg": "{:.1f}",
            }),
            use_container_width=True,
            hide_index=True,
        )
