"""
Quick sanity check after Step 1 — prints summary stats from SQLite.

Usage:
    python scripts/03_explore_data.py
    python scripts/03_explore_data.py --team "Barcelona"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DB_PATH, DEFAULT_TEAM  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Explore loaded scouting database.")
    parser.add_argument("--team", type=str, default=DEFAULT_TEAM)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    engine = create_engine(f"sqlite:///{DB_PATH}")

    print("=== Competition ===")
    print(pd.read_sql("SELECT * FROM competitions", engine).to_string(index=False))
    print()

    team_filter = "WHERE home_team_name = :team OR away_team_name = :team"
    matches = pd.read_sql(
        text(f"SELECT match_id, match_date, home_team_name, away_team_name, home_score, away_score FROM matches {team_filter} ORDER BY match_date"),
        engine,
        params={"team": args.team},
    )
    print(f"=== {args.team} Matches ({len(matches)}) ===")
    print(matches.to_string(index=False))
    print()

    event_summary = pd.read_sql(
        text(
            """
            SELECT event_type, COUNT(*) AS event_count
            FROM events
            WHERE team_name = :team
            GROUP BY event_type
            ORDER BY event_count DESC
            LIMIT 10
            """
        ),
        engine,
        params={"team": args.team},
    )
    print(f"=== Top Event Types for {args.team} ===")
    print(event_summary.to_string(index=False))


if __name__ == "__main__":
    main()