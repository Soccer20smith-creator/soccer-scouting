"""Ensure the SQLite database exists before running the dashboard."""

from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from sqlalchemy import create_engine, text

from config import (
    DATA_DIR,
    DB_PATH,
    DEFAULT_COMPETITION_ID,
    DEFAULT_SEASON_ID,
    PROJECT_ROOT,
    STATSBOMB_BASE_URL,
)

MIN_EVENT_ROWS = 10_000


def database_ready() -> bool:
    if not DB_PATH.exists():
        return False

    engine = create_engine(f"sqlite:///{DB_PATH}")
    with engine.connect() as connection:
        count = connection.execute(text("SELECT COUNT(*) FROM events")).scalar()
    return bool(count and count >= MIN_EVENT_ROWS)


def _fetch_json(url: str) -> list | dict:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.json()


def _save_json(path: Path, payload: list | dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle)


def _download_season(competition_id: int, season_id: int) -> list[dict]:
    competitions_path = DATA_DIR / "competitions.json"
    if not competitions_path.exists():
        _save_json(competitions_path, _fetch_json(f"{STATSBOMB_BASE_URL}/competitions.json"))

    matches_path = DATA_DIR / "matches" / str(competition_id) / f"{season_id}.json"
    if not matches_path.exists():
        matches = _fetch_json(f"{STATSBOMB_BASE_URL}/matches/{competition_id}/{season_id}.json")
        _save_json(matches_path, matches)

    with matches_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _download_events(matches: list[dict]) -> None:
    for match in matches:
        match_id = match["match_id"]
        path = DATA_DIR / "events" / f"{match_id}.json"
        if path.exists():
            continue
        _save_json(path, _fetch_json(f"{STATSBOMB_BASE_URL}/events/{match_id}.json"))
        time.sleep(0.05)


def _flatten_location(location: list | None, index: int) -> float | None:
    if not location or len(location) <= index:
        return None
    return float(location[index])


def _event_rows(match_id: int, events: list[dict]) -> list[dict]:
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
                "location_x": _flatten_location(location, 0),
                "location_y": _flatten_location(location, 1),
                "end_location_x": _flatten_location(end_location, 0),
                "end_location_y": _flatten_location(end_location, 1),
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


def _load_schema(engine) -> None:
    schema_path = PROJECT_ROOT / "sql" / "schema.sql"
    with schema_path.open(encoding="utf-8") as handle:
        with engine.begin() as connection:
            for statement in handle.read().split(";"):
                cleaned = statement.strip()
                if cleaned:
                    connection.execute(text(cleaned))


def _load_database(competition_id: int, season_id: int, matches: list[dict]) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}")
    _load_schema(engine)

    with (DATA_DIR / "competitions.json").open(encoding="utf-8") as handle:
        competitions = json.load(handle)

    competition_rows = [
        row
        for row in competitions
        if row["competition_id"] == competition_id and row["season_id"] == season_id
    ]
    pd.DataFrame(competition_rows).to_sql("competitions", engine, if_exists="replace", index=False)

    match_rows = []
    for match in matches:
        match_rows.append(
            {
                "match_id": match["match_id"],
                "competition_id": competition_id,
                "season_id": season_id,
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

    all_events: list[dict] = []
    for event_file in sorted((DATA_DIR / "events").glob("*.json")):
        with event_file.open(encoding="utf-8") as handle:
            events = json.load(handle)
        all_events.extend(_event_rows(int(event_file.stem), events))

    pd.DataFrame(all_events).to_sql("events", engine, if_exists="replace", index=False)


def ensure_database(
    *,
    competition_id: int = DEFAULT_COMPETITION_ID,
    season_id: int = DEFAULT_SEASON_ID,
    team: str | None = None,
) -> None:
    """Download StatsBomb data and load SQLite if the database is missing."""
    if database_ready():
        return

    matches = _download_season(competition_id, season_id)
    if team:
        team_lower = team.lower()
        matches = [
            match
            for match in matches
            if team_lower
            in (
                match["home_team"]["home_team_name"].lower(),
                match["away_team"]["away_team_name"].lower(),
            )
        ]

    _download_events(matches)
    _load_database(competition_id, season_id, matches)


def ensure_database_via_scripts(*, team: str | None = None) -> None:
    """Fallback that reuses the CLI scripts."""
    if database_ready():
        return

    download_cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "01_download_data.py")]
    load_cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "02_load_database.py")]
    if team:
        download_cmd.extend(["--team", team])
        load_cmd.extend(["--team", team])

    subprocess.run(download_cmd, check=True, cwd=PROJECT_ROOT)
    subprocess.run(load_cmd, check=True, cwd=PROJECT_ROOT)
