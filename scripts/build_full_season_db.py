"""
Build the full Premier League 2015/16 database for cloud deployment.

Usage:
    python scripts/build_full_season_db.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.bootstrap import database_ready, ensure_database  # noqa: E402


def main() -> None:
    if database_ready():
        print("Database already exists and looks complete.")
        return

    print("Downloading full Premier League 2015/16 season from StatsBomb...")
    ensure_database()
    print("Done. Database is ready for Streamlit Cloud deployment.")


if __name__ == "__main__":
    main()
