"""Tactical metrics for opposition scouting."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

DEFENSIVE_ACTIONS = (
    "Pressure",
    "Foul Committed",
    "Tackle",
    "Interception",
    "Block",
)

SET_PIECE_PATTERNS = (
    "From Corner",
    "From Free Kick",
    "From Throw In",
    "From Penalty",
    "From Goal Kick",
)


def load_team_events(engine: Engine, team: str) -> pd.DataFrame:
    query = text(
        """
        SELECT *
        FROM events
        WHERE team_name = :team
        """
    )
    return pd.read_sql(query, engine, params={"team": team})


def load_match_events(engine: Engine, match_ids: list[int]) -> pd.DataFrame:
    if not match_ids:
        return pd.DataFrame()
    placeholders = ", ".join(str(match_id) for match_id in match_ids)
    query = f"SELECT * FROM events WHERE match_id IN ({placeholders})"
    return pd.read_sql(query, engine)


def get_team_match_ids(engine: Engine, team: str) -> list[int]:
    query = text(
        """
        SELECT match_id
        FROM matches
        WHERE home_team_name = :team OR away_team_name = :team
        ORDER BY match_date
        """
    )
    frame = pd.read_sql(query, engine, params={"team": team})
    return frame["match_id"].tolist()


def get_shots(engine: Engine, team: str, open_play_only: bool = False) -> pd.DataFrame:
    query = text(
        """
        SELECT
            event_id,
            match_id,
            player_name,
            minute,
            location_x,
            location_y,
            shot_xg,
            shot_outcome,
            shot_body_part,
            shot_type,
            play_pattern,
            is_goal
        FROM events
        WHERE team_name = :team
          AND is_shot = 1
          AND location_x IS NOT NULL
          AND location_y IS NOT NULL
        """
    )
    shots = pd.read_sql(query, engine, params={"team": team})
    if open_play_only:
        shots = shots[~shots["play_pattern"].isin(SET_PIECE_PATTERNS)]
    return shots


def xg_summary(engine: Engine, team: str) -> pd.DataFrame:
    shots = get_shots(engine, team)
    if shots.empty:
        return pd.DataFrame()

    grouped = shots.groupby("shot_type", dropna=False).agg(
        shots=("event_id", "count"),
        goals=("is_goal", "sum"),
        total_xg=("shot_xg", "sum"),
    )
    grouped["avg_xg_per_shot"] = grouped["total_xg"] / grouped["shots"]
    grouped["xg_per_goal"] = grouped["total_xg"] / grouped["goals"].replace(0, pd.NA)
    grouped = grouped.reset_index().rename(columns={"shot_type": "shot_context"})
    return grouped.sort_values("shots", ascending=False)


def xg_season_totals(engine: Engine, team: str) -> dict[str, float | int]:
    shots = get_shots(engine, team)
    goals = int(shots["is_goal"].sum())
    total_xg = float(shots["shot_xg"].fillna(0).sum())
    return {
        "shots": len(shots),
        "goals": goals,
        "total_xg": round(total_xg, 2),
        "xg_difference": round(goals - total_xg, 2),
        "avg_xg_per_shot": round(total_xg / len(shots), 3) if len(shots) else 0.0,
    }


def pitch_zone(y: float) -> str:
    if y < 80 / 3:
        return "Left"
    if y > (80 / 3) * 2:
        return "Right"
    return "Central"


def zone_summary(engine: Engine, team: str) -> pd.DataFrame:
    shots = get_shots(engine, team)
    if shots.empty:
        return pd.DataFrame()

    shots["zone"] = shots["location_y"].apply(pitch_zone)
    summary = (
        shots.groupby("zone")
        .agg(
            shots=("event_id", "count"),
            goals=("is_goal", "sum"),
            total_xg=("shot_xg", "sum"),
        )
        .reset_index()
    )
    summary["shot_share_pct"] = (summary["shots"] / summary["shots"].sum() * 100).round(1)
    order = ["Left", "Central", "Right"]
    summary["zone"] = pd.Categorical(summary["zone"], categories=order, ordered=True)
    return summary.sort_values("zone")


def final_third_entries(engine: Engine, team: str) -> pd.DataFrame:
    query = text(
        """
        SELECT location_x, location_y, event_type
        FROM events
        WHERE team_name = :team
          AND event_type IN ('Pass', 'Carry')
          AND location_x IS NOT NULL
          AND location_y IS NOT NULL
          AND (
            (event_type = 'Pass' AND end_location_x >= 80)
            OR (event_type = 'Carry' AND end_location_x >= 80)
          )
        """
    )
    entries = pd.read_sql(query, engine, params={"team": team})
    if entries.empty:
        return pd.DataFrame()

    entries["zone"] = entries["location_y"].apply(pitch_zone)
    summary = entries.groupby("zone").size().reset_index(name="entries")
    summary["entry_share_pct"] = (summary["entries"] / summary["entries"].sum() * 100).round(1)
    order = ["Left", "Central", "Right"]
    summary["zone"] = pd.Categorical(summary["zone"], categories=order, ordered=True)
    return summary.sort_values("zone")


def ppda_for_match(match_events: pd.DataFrame, team: str) -> float | None:
    team_actions = match_events[
        (match_events["team_name"] == team)
        & (match_events["event_type"].isin(DEFENSIVE_ACTIONS))
    ]
    opponent_passes = match_events[
        (match_events["team_name"] != team) & (match_events["event_type"] == "Pass")
    ]

    if team_actions.empty:
        return None
    return len(opponent_passes) / len(team_actions)


def _load_ppda_events(engine: Engine, match_ids: list[int] | None = None) -> pd.DataFrame:
    type_list = ", ".join(f"'{event_type}'" for event_type in (*DEFENSIVE_ACTIONS, "Pass"))
    if match_ids:
        placeholders = ", ".join(str(match_id) for match_id in match_ids)
        query = f"""
            SELECT match_id, team_name, event_type
            FROM events
            WHERE match_id IN ({placeholders})
              AND event_type IN ({type_list})
        """
    else:
        query = f"""
            SELECT match_id, team_name, event_type
            FROM events
            WHERE event_type IN ({type_list})
        """
    return pd.read_sql(query, engine)


def ppda_summary(engine: Engine, team: str) -> dict[str, float]:
    match_ids = get_team_match_ids(engine, team)
    if not match_ids:
        return {"ppda": 0.0, "matches": 0}

    events = _load_ppda_events(engine, match_ids)
    values: list[float] = []

    for match_id in match_ids:
        match_events = events[events["match_id"] == match_id]
        value = ppda_for_match(match_events, team)
        if value is not None:
            values.append(value)

    if not values:
        return {"ppda": 0.0, "matches": 0}

    return {
        "ppda": round(sum(values) / len(values), 2),
        "matches": len(values),
    }


def league_ppda_ranking(engine: Engine) -> pd.DataFrame:
    teams = pd.read_sql("SELECT DISTINCT team_name FROM events ORDER BY team_name", engine)
    events = _load_ppda_events(engine)
    rows = []

    for team in teams["team_name"]:
        match_ids = get_team_match_ids(engine, team)
        values: list[float] = []
        for match_id in match_ids:
            match_events = events[events["match_id"] == match_id]
            value = ppda_for_match(match_events, team)
            if value is not None:
                values.append(value)
        rows.append(
            {
                "team": team,
                "ppda": round(sum(values) / len(values), 2) if values else 0.0,
                "matches": len(values),
            }
        )

    frame = pd.DataFrame(rows).sort_values("ppda")
    frame["press_rank"] = range(1, len(frame) + 1)
    return frame.reset_index(drop=True)