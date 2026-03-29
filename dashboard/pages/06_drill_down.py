"""Drill-Down page — detailed event analysis and storylines."""
from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st
import pandas as pd
import json
from pipeline.db import get_events_dataframe
from analysis.patterns import get_storylines, get_actor_cooccurrence


def show():
    st.header("Drill-Down Analysis")
    st.caption("Event clusters, storylines, and actor relationships")

    df = get_events_dataframe()
    if df.empty:
        st.warning("No data available.")
        return

    # Storylines
    st.subheader("Identified Storylines")
    st.caption("Groups of related events detected via text similarity clustering")

    storylines = get_storylines()
    if storylines:
        for i, story in enumerate(storylines[:10]):
            with st.expander(
                f"Storyline {i+1}: {story['dominant_type']} — "
                f"{story['event_count']} events (Avg severity: {story['avg_severity']})"
            ):
                st.markdown(f"**Date range:** {story['date_range']}")
                st.markdown(f"**Actors involved:** {', '.join(story['actors'])}")
                st.markdown("**Sample events:**")
                for claim in story["sample_claims"]:
                    st.markdown(f"- {claim[:200]}")
    else:
        st.info("Not enough events to detect storylines (need 2+ related events)")

    st.divider()

    # Actor co-occurrence
    st.subheader("Actor Relationships")
    cooc = get_actor_cooccurrence()
    if not cooc.empty:
        st.dataframe(
            cooc.head(20).rename(columns={
                "actor_1": "Actor 1", "actor_2": "Actor 2", "count": "Co-occurrences"
            }),
            use_container_width=True,
            hide_index=True,
        )

        # Network visualization as a simple matrix
        import plotly.express as px
        top_actors = set(cooc.head(15)["actor_1"].tolist() + cooc.head(15)["actor_2"].tolist())
        matrix = cooc[cooc["actor_1"].isin(top_actors) & cooc["actor_2"].isin(top_actors)]
        if not matrix.empty:
            pivot = matrix.pivot_table(
                index="actor_1", columns="actor_2", values="count", fill_value=0
            )
            fig = px.imshow(
                pivot, title="Actor Co-occurrence Matrix",
                color_continuous_scale="Blues",
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No actor co-occurrence data available")

    st.divider()

    # Individual event drill-down
    st.subheader("Event Detail Lookup")
    event_ids = df["event_id"].tolist()
    if event_ids:
        selected_id = st.selectbox(
            "Select Event ID",
            event_ids,
            format_func=lambda eid: f"#{eid}: {df[df['event_id']==eid]['claim_text'].iloc[0][:80]}",
        )

        if selected_id:
            event = df[df["event_id"] == selected_id].iloc[0]

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Event Details")
                st.markdown(f"**Claim:** {event['claim_text']}")
                st.markdown(f"**Source:** [{event['source_name']}]({event['source_url']})")
                st.markdown(f"**Type:** {event['source_type']}")
                st.markdown(f"**Date:** {event['event_datetime_utc']}")
                st.markdown(f"**Location:** {event.get('location_text', 'N/A')}")

            with col2:
                st.markdown("### Classification")
                st.markdown(f"**Event Type:** {event['event_type']}")
                st.markdown(f"**Domain:** {event['domain']}")
                st.markdown(f"**Severity:** {event['severity_score']:.1f} / 10")
                st.markdown(f"**Confidence:** {event['confidence_score']:.2f}")
                st.markdown(f"**Status:** {event['verification_status']}")
                st.markdown(f"**Actor 1:** {event.get('actor_1', 'N/A')}")
                st.markdown(f"**Actor 2:** {event.get('actor_2', 'N/A')}")

                # Tags
                try:
                    tags = json.loads(event.get("tags", "[]"))
                    if tags:
                        st.markdown(f"**Tags:** {', '.join(tags)}")
                except (json.JSONDecodeError, TypeError):
                    pass

            # Related events (same cluster)
            cluster_id = event.get("dedup_cluster_id")
            if cluster_id and pd.notna(cluster_id):
                related = df[
                    (df["dedup_cluster_id"] == cluster_id) &
                    (df["event_id"] != selected_id)
                ]
                if not related.empty:
                    st.markdown("### Related Events (same cluster)")
                    for _, rel in related.iterrows():
                        st.markdown(f"- #{rel['event_id']}: {rel['claim_text'][:120]}")
