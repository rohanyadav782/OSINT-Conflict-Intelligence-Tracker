"""Event Feed page — filterable table with export."""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
from pipeline.db import get_events_dataframe
from dashboard.components.tables import render_event_table


def show():
    st.header("Event Feed")
    st.caption("Browse, filter, and export conflict events")

    df = get_events_dataframe()
    if df.empty:
        st.warning("No data available. Run the pipeline first.")
        return

    # No filters — show all data
    filtered = df

    # Summary stats
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Events", f"{len(filtered)}")
    col2.metric("Avg Severity", f"{filtered['severity_score'].mean():.1f}")
    col3.metric("Avg Confidence", f"{filtered['confidence_score'].mean():.2f}")

    # Quick filter tabs
    tab1, tab2, tab3 = st.tabs(["All Events", "Confirmed Only", "High Severity"])

    with tab1:
        render_event_table(filtered)

    with tab2:
        confirmed = filtered[filtered["verification_status"] == "confirmed"]
        if confirmed.empty:
            st.info("No confirmed events yet. Events are confirmed when corroborated by multiple sources.")
        else:
            render_event_table(confirmed, key="confirmed")

    with tab3:
        high_sev = filtered[filtered["severity_score"] >= 7.0]
        if high_sev.empty:
            st.info("No events with severity >= 7.0 in current filter")
        else:
            render_event_table(high_sev, key="high_sev")

    # Export
    st.divider()
    csv = filtered.to_csv(index=False)
    st.download_button(
        label="Export Filtered Data as CSV",
        data=csv,
        file_name="conflict_events_export.csv",
        mime="text/csv",
    )

    # Event detail expander
    st.divider()
    st.subheader("Event Detail View")
    if not filtered.empty:
        event_options = filtered["claim_text"].str[:80].tolist()
        selected_idx = st.selectbox(
            "Select an event to view details",
            range(len(event_options)),
            format_func=lambda i: event_options[i],
        )

        if selected_idx is not None:
            event = filtered.iloc[selected_idx]
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Full Claim:**")
                st.write(event["claim_text"])
                st.markdown(f"**Source:** [{event['source_name']}]({event['source_url']})")
                st.markdown(f"**Source Type:** {event['source_type']}")
                st.markdown(f"**Date:** {event['event_datetime_utc']}")

            with col2:
                st.markdown(f"**Event Type:** {event['event_type']}")
                st.markdown(f"**Domain:** {event['domain']}")
                st.markdown(f"**Country:** {event.get('country', 'N/A')}")
                st.markdown(f"**Location:** {event.get('location_text', 'N/A')}")
                st.markdown(f"**Actor 1:** {event.get('actor_1', 'N/A')}")
                st.markdown(f"**Actor 2:** {event.get('actor_2', 'N/A')}")
                st.markdown(f"**Severity:** {event['severity_score']:.1f} / 10")
                st.markdown(f"**Confidence:** {event['confidence_score']:.2f}")
                st.markdown(f"**Status:** {event['verification_status']}")
