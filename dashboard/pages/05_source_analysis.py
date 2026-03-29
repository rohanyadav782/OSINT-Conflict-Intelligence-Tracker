"""Source Analysis page — provenance, reliability, and bias tracking."""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
import plotly.express as px
from pipeline.db import get_events_dataframe, get_source_reliability


def show():
    st.header("Source Analysis")
    st.caption("Source reliability, provenance tracking, and coverage analysis")

    df = get_events_dataframe()
    if df.empty:
        st.warning("No data available.")
        return

    # Source reliability table
    st.subheader("Source Reliability Scores")
    reliability = get_source_reliability()
    if reliability:
        rel_df = pd.DataFrame(reliability)
        display_cols = ["source_name", "total_reports", "reliability_score"]
        available_cols = [c for c in display_cols if c in rel_df.columns]
        st.dataframe(
            rel_df[available_cols].style.format({
                "reliability_score": "{:.3f}",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Run analysis pipeline to compute reliability scores")

    st.divider()

    # Source volume chart
    st.subheader("Events by Source")
    source_counts = df["source_name"].value_counts().head(20)
    fig = px.bar(
        x=source_counts.values, y=source_counts.index,
        orientation="h", labels={"x": "Event Count", "y": "Source"},
        title="Top Sources by Volume",
    )
    fig.update_layout(height=500, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Source type distribution
    st.subheader("Source Type Coverage")
    col1, col2 = st.columns(2)

    with col1:
        type_counts = df["source_type"].value_counts()
        fig = px.pie(
            names=type_counts.index, values=type_counts.values,
            title="Events by Source Type", hole=0.4,
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Average severity by source
        source_severity = df.groupby("source_name").agg(
            avg_severity=("severity_score", "mean"),
            event_count=("event_id", "count"),
        ).reset_index().sort_values("avg_severity", ascending=False).head(10)

        st.markdown("**Average Severity by Source** (top 10)")
        st.dataframe(
            source_severity.style.format({"avg_severity": "{:.2f}"}),
            use_container_width=True,
            hide_index=True,
        )

    # Provenance note
    st.divider()
    st.caption(
        "**Provenance:** All events link back to their original source URL. "
        "Source reliability scores are computed based on corroboration rates. "
        "State-affiliated media sources (e.g., IRNA, Press TV) are flagged with "
        "adjusted confidence scores to account for potential editorial bias."
    )
