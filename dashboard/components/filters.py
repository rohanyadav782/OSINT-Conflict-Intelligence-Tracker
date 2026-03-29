"""Reusable inline filters for the dashboard."""
from __future__ import annotations

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


def apply_filters(df: pd.DataFrame, key_prefix: str = "") -> pd.DataFrame:
    """Apply inline filters using an expander and return filtered DataFrame."""
    if df.empty:
        return df

    with st.expander("Filters", expanded=False):
        col1, col2, col3, col4 = st.columns(4)

        # Event type
        with col1:
            if "event_type" in df.columns:
                event_types = sorted(df["event_type"].dropna().unique())
                selected_types = st.multiselect(
                    "Event Type", event_types, default=event_types,
                    key=f"{key_prefix}_etype"
                )
                if selected_types:
                    df = df[df["event_type"].isin(selected_types)]

        # Domain
        with col2:
            if "domain" in df.columns:
                domains = sorted(df["domain"].dropna().unique())
                selected_domains = st.multiselect(
                    "Domain", domains, default=domains,
                    key=f"{key_prefix}_domain"
                )
                if selected_domains:
                    df = df[df["domain"].isin(selected_domains)]

        # Country
        with col3:
            if "country" in df.columns:
                countries = sorted(df["country"].dropna().unique())
                selected_countries = st.multiselect(
                    "Country", countries, default=countries,
                    key=f"{key_prefix}_country"
                )
                if selected_countries:
                    df = df[df["country"].isin(selected_countries)]

        # Source type
        with col4:
            if "source_type" in df.columns:
                source_types = sorted(df["source_type"].dropna().unique())
                selected_sources = st.multiselect(
                    "Source Type", source_types, default=source_types,
                    key=f"{key_prefix}_stype"
                )
                if selected_sources:
                    df = df[df["source_type"].isin(selected_sources)]

    return df
