#!/usr/bin/env python3
"""CLI entry point for running the data ingestion pipeline."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline.orchestrator import run_pipeline


if __name__ == "__main__":
    skip_ner = "--skip-ner" in sys.argv
    if skip_ner:
        print("Skipping NER enrichment (use without --skip-ner for full pipeline)")
    run_pipeline(skip_ner=skip_ner)
