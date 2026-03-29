"""Map View page — geographic visualization of conflict events."""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
from pipeline.db import get_events_dataframe
from dashboard.components.charts import event_map
from dashboard.components.filters import apply_filters


def show():
    st.header("Map View")
    st.caption("Geographic distribution of conflict events")

    df = get_events_dataframe()
    if df.empty:
        st.warning("No data available.")
        return

    # Apply filters
    filtered = apply_filters(df, key_prefix="map")

    # Stats
    geocoded = filtered.dropna(subset=["latitude", "longitude"])
    col1, col2 = st.columns(2)
    col1.metric("Total Events", len(filtered))
    col2.metric("Geocoded Events", len(geocoded))

    # Map
    fig = event_map(filtered)
    st.plotly_chart(fig, use_container_width=True)

    # Location breakdown
    st.divider()
    st.subheader("Events by Location")
    if "location_text" in filtered.columns:
        loc_counts = filtered["location_text"].dropna().value_counts().head(15)
        if not loc_counts.empty:
            import plotly.express as px
            fig = px.bar(
                x=loc_counts.values, y=loc_counts.index,
                orientation="h", labels={"x": "Events", "y": "Location"},
                title="Top Locations by Event Count",
            )
            fig.update_layout(height=400, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

    # Country breakdown
    st.subheader("Events by Country")
    country_counts = filtered["country"].dropna().value_counts()
    if not country_counts.empty:
        country_names = {
            "IR": "Iran", "IL": "Israel", "US": "United States",
            "LB": "Lebanon", "SY": "Syria", "IQ": "Iraq",
            "YE": "Yemen", "PS": "Palestine",
        }
        country_df = pd.DataFrame({
            "Country": [country_names.get(c, c) for c in country_counts.index],
            "Code": country_counts.index,
            "Events": country_counts.values,
        })
        st.dataframe(country_df, use_container_width=True, hide_index=True)
