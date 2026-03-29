"""Styled dataframe renderers for the dashboard."""
from __future__ import annotations

import streamlit as st
import pandas as pd


def render_event_table(df: pd.DataFrame, key: str = "events"):
    """Render a styled event table with key columns."""
    if df.empty:
        st.info("No events to display.")
        return

    display_cols = [
        "event_datetime_utc", "source_name", "claim_text",
        "event_type", "domain", "country",
        "actor_1", "actor_2", "severity_score",
        "confidence_score", "verification_status",
    ]
    available = [c for c in display_cols if c in df.columns]
    display_df = df[available].copy()

    # Truncate claim text
    if "claim_text" in display_df.columns:
        display_df["claim_text"] = display_df["claim_text"].str[:120] + "..."

    # Format datetime
    if "event_datetime_utc" in display_df.columns:
        display_df["event_datetime_utc"] = pd.to_datetime(
            display_df["event_datetime_utc"], format="ISO8601", utc=True
        ).dt.strftime("%Y-%m-%d %H:%M")
        display_df = display_df.rename(columns={"event_datetime_utc": "datetime"})

    st.dataframe(
        display_df,
        use_container_width=True,
        height=min(400, 35 * len(display_df) + 38),
        hide_index=True,
    )


def render_high_severity_table(df: pd.DataFrame, threshold: float = 7.0):
    """Render top high-severity events."""
    if df.empty:
        st.info("No high-severity events.")
        return

    high = df[df["severity_score"] >= threshold].nlargest(10, "severity_score")
    if high.empty:
        st.info(f"No events with severity >= {threshold}")
        return

    for _, row in high.iterrows():
        severity = row["severity_score"]
        color = "red" if severity >= 8 else "orange" if severity >= 6 else "blue"
        st.markdown(
            f":{color}[**{severity:.1f}**] {row['claim_text'][:150]}  \n"
            f"*{row['source_name']} | {row.get('event_type', '')} | "
            f"{row.get('country', '')}*"
        )


def render_metric_row(metrics: list[dict]):
    """Render a row of metric cards."""
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        col.metric(
            label=m["label"],
            value=m["value"],
            delta=m.get("delta"),
            delta_color=m.get("delta_color", "normal"),
        )
