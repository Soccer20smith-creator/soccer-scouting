"""
Step 1: Download StatsBomb open data for a competition season.

Usage:
    python scripts/01_download_data.py
    python scripts/01_download_data.py --competition-id 11 --season-id 90
    python scripts/01_download_data.py --team "Barcelona" --max-matches 5
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import (  # noqa: E402
    DATA_DIR,
    DEFAULT_COMPETITION_ID,
    DEFAULT_SEASON_ID,
    STATSBOMB_BASE_URL,
)


def fetch_json(url: str) -> list | dict:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.json()


def save_json(path: Path, payload: list | dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle)


def download_competitions() -> list[dict]:
    path = DATA_DIR / "competitions.json"
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)

    print("Downloading competitions index...")
    competitions = fetch_json(f"{STATSBOMB_BASE_URL}/competitions.json")
    save_json(path, competitions)
    return competitions


def download_matches(competition_id: int, season_id: int) -> list[dict]:
    path = DATA_DIR / "matches" / str(competition_id) / f"{season_id}.json"
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)

    print(f"Downloading matches for competition {competition_id}, season {season_id}...")
    matches = fetch_json(
        f"{STATSBOMB_BASE_URL}/matches/{competition_id}/{season_id}.json"
    )
    save_json(path, matches)
    return matches


def filter_matches_by_team(matches: list[dict], team_name: str) -> list[dict]:
    team_lower = team_name.lower()
    return [
        match
        for match in matches
        if team_lower
        in (
            match["home_team"]["home_team_name"].lower(),
            match["away_team"]["away_team_name"].lower(),
        )
    ]


def download_events(match_id: int) -> None:
    path = DATA_DIR / "events" / f"{match_id}.json"
    if path.exists():
        return

    events = fetch_json(f"{STATSBOMB_BASE_URL}/events/{match_id}.json")
    save_json(path, events)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download StatsBomb open data.")
    parser.add_argument("--competition-id", type=int, default=DEFAULT_COMPETITION_ID)
    parser.add_argument("--season-id", type=int, default=DEFAULT_SEASON_ID)
    parser.add_argument(
        "--team",
        type=str,
        default=None,
        help="Only download events for matches involving this team.",
    )
    parser.add_argument(
        "--max-matches",
        type=int,
        default=None,
        help="Cap the number of event files downloaded (useful while learning).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    competitions = download_competitions()
    matches = download_matches(args.competition_id, args.season_id)

    season_label = next(
        (
            f"{row['competition_name']} {row['season_name']}"
            for row in competitions
            if row["competition_id"] == args.competition_id
            and row["season_id"] == args.season_id
        ),
        f"competition {args.competition_id} season {args.season_id}",
    )

    selected_matches = matches
    if args.team:
        selected_matches = filter_matches_by_team(matches, args.team)
        print(f"Filtered to {len(selected_matches)} matches for '{args.team}'.")

    if args.max_matches is not None:
        selected_matches = selected_matches[: args.max_matches]

    print(f"Downloading event files for {len(selected_matches)} matches...")
    for index, match in enumerate(selected_matches, start=1):
        match_id = match["match_id"]
        home = match["home_team"]["home_team_name"]
        away = match["away_team"]["away_team_name"]
        print(f"  [{index}/{len(selected_matches)}] {home} vs {away} ({match_id})")
        download_events(match_id)
        time.sleep(0.05)

    print()
    print("Download complete.")
    print(f"  Season: {season_label}")
    print(f"  Matches indexed: {len(matches)}")
    print(f"  Event files saved: {len(selected_matches)}")
    print(f"  Data folder: {DATA_DIR}")


if __name__ == "__main__":
    main()