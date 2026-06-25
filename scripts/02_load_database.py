"""
Step 1: Load downloaded StatsBomb JSON into SQLite.

Usage:
    python scripts/02_load_database.py
    python scripts/02_load_database.py --team "Barcelona"
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DATA_DIR, DB_PATH, DEFAULT_COMPETITION_ID, DEFAULT_SEASON_ID  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load StatsBomb JSON into SQLite.")
    parser.add_argument("--competition-id", type=int, default=DEFAULT_COMPETITION_ID)
    parser.add_argument("--season-id", type=int, default=DEFAULT_SEASON_ID)
    parser.add_argument("--team", type=str, default=None)
    return parser.parse_args()


def load_schema(engine) -> None:
    schema_path = PROJECT_ROOT / "sql" / "schema.sql"
    with schema_path.open(encoding="utf-8") as handle:
        with engine.begin() as connection:
            for statement in handle.read().split(";"):
                cleaned = statement.strip()
                if cleaned:
                    connection.execute(text(cleaned))


def flatten_location(location: list | None, index: int) -> float | None:
    if not location or len(location) <= index:
        return None
    return float(location[index])


def event_rows(match_id: int, events: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for event in events:
        team = event.get("team") or {}
        player = event.get("player") or {}
        event_type = event.get("type") or {}
        shot = event.get("shot") or {}
        pass_data = event.get("pass") or {}

        location = event.get("location")
        end_location = None
        if pass_data:
            end_location = pass_data.get("end_location")
        elif shot:
            end_location = shot.get("end_location")

        pass_length = None
        pass_angle = None
        if location and end_location:
            dx = end_location[0] - location[0]
            dy = end_location[1] - location[1]
            pass_length = math.sqrt(dx**2 + dy**2)
            pass_angle = math.degrees(math.atan2(dy, dx))

        rows.append(
            {
                "event_id": f"{match_id}_{event['index']}",
                "match_id": match_id,
                "team_id": team.get("id"),
                "team_name": team.get("name"),
                "player_id": player.get("id"),
                "player_name": player.get("name"),
                "event_type": event_type.get("name"),
                "event_type_id": event_type.get("id"),
                "possession": event.get("possession"),
                "period": event.get("period"),
                "minute": event.get("minute"),
                "second": event.get("second"),
                "location_x": flatten_location(location, 0),
                "location_y": flatten_location(location, 1),
                "end_location_x": flatten_location(end_location, 0),
                "end_location_y": flatten_location(end_location, 1),
                "is_goal": int(shot.get("outcome", {}).get("name") == "Goal"),
                "is_shot": int(event_type.get("name") == "Shot"),
                "shot_xg": shot.get("statsbomb_xg"),
                "shot_body_part": (shot.get("body_part") or {}).get("name"),
                "shot_type": (shot.get("type") or {}).get("name"),
                "shot_outcome": shot.get("outcome", {}).get("name"),
                "pass_type": (pass_data.get("type") or {}).get("name"),
                "pass_outcome": pass_data.get("outcome", {}).get("name"),
                "pass_length": pass_length,
                "pass_angle": pass_angle,
                "under_pressure": int(bool(event.get("under_pressure"))),
                "play_pattern": (event.get("play_pattern") or {}).get("name"),
            }
        )
    return rows


def main() -> None:
    args = parse_args()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}")

    load_schema(engine)

    with (DATA_DIR / "competitions.json").open(encoding="utf-8") as handle:
        competitions = json.load(handle)

    competition_rows = [
        row
        for row in competitions
        if row["competition_id"] == args.competition_id
        and row["season_id"] == args.season_id
    ]
    pd.DataFrame(competition_rows).to_sql(
        "competitions", engine, if_exists="replace", index=False
    )

    matches_path = DATA_DIR / "matches" / str(args.competition_id) / f"{args.season_id}.json"
    with matches_path.open(encoding="utf-8") as handle:
        matches = json.load(handle)

    match_rows = []
    for match in matches:
        match_rows.append(
            {
                "match_id": match["match_id"],
                "competition_id": args.competition_id,
                "season_id": args.season_id,
                "match_date": match.get("match_date"),
                "kick_off": match.get("kick_off"),
                "home_team_id": match["home_team"]["home_team_id"],
                "home_team_name": match["home_team"]["home_team_name"],
                "away_team_id": match["away_team"]["away_team_id"],
                "away_team_name": match["away_team"]["away_team_name"],
                "home_score": match["home_score"],
                "away_score": match["away_score"],
            }
        )
    pd.DataFrame(match_rows).to_sql("matches", engine, if_exists="replace", index=False)

    event_files = sorted((DATA_DIR / "events").glob("*.json"))
    if args.team:
        team_lower = args.team.lower()
        allowed_match_ids = {
            row["match_id"]
            for row in match_rows
            if team_lower in (row["home_team_name"].lower(), row["away_team_name"].lower())
        }
        event_files = [
            path for path in event_files if int(path.stem) in allowed_match_ids
        ]

    all_events: list[dict] = []
    for event_file in event_files:
        with event_file.open(encoding="utf-8") as handle:
            events = json.load(handle)
        all_events.extend(event_rows(int(event_file.stem), events))

    pd.DataFrame(all_events).to_sql("events", engine, if_exists="replace", index=False)

    with engine.connect() as connection:
        match_count = connection.execute(text("SELECT COUNT(*) FROM matches")).scalar()
        event_count = connection.execute(text("SELECT COUNT(*) FROM events")).scalar()
        team_count = connection.execute(
            text("SELECT COUNT(DISTINCT team_name) FROM events")
        ).scalar()

    print("Database load complete.")
    print(f"  Database: {DB_PATH}")
    print(f"  Matches: {match_count}")
    print(f"  Events: {event_count}")
    print(f"  Teams with event data: {team_count}")


if __name__ == "__main__":
    main()