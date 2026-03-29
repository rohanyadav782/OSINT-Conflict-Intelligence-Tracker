#!/usr/bin/env python3
"""Launch the Streamlit dashboard."""

import subprocess
import sys
import os

if __name__ == "__main__":
    dashboard_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "dashboard", "app.py"
    )
    subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path])
