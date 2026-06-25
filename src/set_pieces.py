"""Set-piece analysis for opposition scouting."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.metrics import SET_PIECE_PATTERNS, get_team_match_ids

CORNER_PATTERN = "From Corner"
FREE_KICK_PATTERN = "From Free Kick"


def get_deliveries(engine: Engine, team: str, pass_type: str) -> pd.DataFrame:
    query = text(
        """
        SELECT
            event_id,
            match_id,
            player_name,
            pass_type,
            end_location_x,
            end_location_y,
            pass_length,
            play_pattern
        FROM events
        WHERE team_name = :team
          AND event_type = 'Pass'
          AND pass_type = :pass_type
          AND end_location_x IS NOT NULL
          AND end_location_y IS NOT NULL
        """
    )
    return pd.read_sql(query, engine, params={"team": team, "pass_type": pass_type})


def get_set_piece_shots(
    engine: Engine,
    team: str,
    play_pattern: str | None = None,
) -> pd.DataFrame:
    query = text(
        """
        SELECT
            event_id,
            match_id,
            player_name,
            minute,
            play_pattern,
            shot_xg,
            shot_outcome,
            is_goal,
            location_x,
            location_y
        FROM events
        WHERE team_name = :team
          AND is_shot = 1
          AND play_pattern IN ('From Corner', 'From Free Kick')
        """
    )
    shots = pd.read_sql(query, engine, params={"team": team})
    if play_pattern:
        shots = shots[shots["play_pattern"] == play_pattern]
    return shots


def get_set_piece_shots_conceded(engine: Engine, team: str) -> pd.DataFrame:
    match_ids = get_team_match_ids(engine, team)
    if not match_ids:
        return pd.DataFrame()

    placeholders = ", ".join(str(match_id) for match_id in match_ids)
    query = f"""
        SELECT
            event_id,
            match_id,
            team_name AS opponent,
            player_name,
            minute,
            play_pattern,
            shot_xg,
            shot_outcome,
            is_goal,
            location_x,
            location_y
        FROM events
        WHERE match_id IN ({placeholders})
          AND team_name != '{team.replace("'", "''")}'
          AND is_shot = 1
          AND play_pattern IN ('From Corner', 'From Free Kick')
    """
    return pd.read_sql(query, engine)


def summarize_shots(shots: pd.DataFrame, label: str) -> dict:
    if shots.empty:
        return {
            "context": label,
            "shots": 0,
            "goals": 0,
            "total_xg": 0.0,
            "conversion_pct": 0.0,
        }

    goals = int(shots["is_goal"].sum())
    total_xg = float(shots["shot_xg"].fillna(0).sum())
    shot_count = len(shots)
    return {
        "context": label,
        "shots": shot_count,
        "goals": goals,
        "total_xg": round(total_xg, 2),
        "conversion_pct": round(goals / shot_count * 100, 1) if shot_count else 0.0,
    }


def attack_summary(engine: Engine, team: str) -> pd.DataFrame:
    corner_shots = get_set_piece_shots(engine, team, CORNER_PATTERN)
    free_kick_shots = get_set_piece_shots(engine, team, FREE_KICK_PATTERN)
    corner_deliveries = get_deliveries(engine, team, "Corner")
    free_kick_deliveries = get_deliveries(engine, team, "Free Kick")

    rows = [
        {
            **summarize_shots(corner_shots, "Corners (shots)"),
            "deliveries": len(corner_deliveries),
        },
        {
            **summarize_shots(free_kick_shots, "Free kicks (shots)"),
            "deliveries": len(free_kick_deliveries),
        },
    ]
    return pd.DataFrame(rows)


def defense_summary(engine: Engine, team: str) -> pd.DataFrame:
    conceded = get_set_piece_shots_conceded(engine, team)
    corner_shots = conceded[conceded["play_pattern"] == CORNER_PATTERN]
    free_kick_shots = conceded[conceded["play_pattern"] == FREE_KICK_PATTERN]

    rows = [
        summarize_shots(corner_shots, "Corners conceded"),
        summarize_shots(free_kick_shots, "Free kicks conceded"),
        summarize_shots(conceded, "All set pieces conceded"),
    ]
    return pd.DataFrame(rows)


def delivery_players(engine: Engine, team: str, pass_type: str) -> pd.DataFrame:
    deliveries = get_deliveries(engine, team, pass_type)
    if deliveries.empty:
        return pd.DataFrame()

    summary = (
        deliveries.groupby("player_name")
        .size()
        .reset_index(name="deliveries")
        .sort_values("deliveries", ascending=False)
    )
    return summary


def shot_players(engine: Engine, team: str, play_pattern: str) -> pd.DataFrame:
    shots = get_set_piece_shots(engine, team, play_pattern)
    if shots.empty:
        return pd.DataFrame()

    summary = (
        shots.groupby("player_name")
        .agg(shots=("event_id", "count"), goals=("is_goal", "sum"), total_xg=("shot_xg", "sum"))
        .reset_index()
        .sort_values("shots", ascending=False)
    )
    return summary


def delivery_zone(shots_or_deliveries: pd.DataFrame, x_col: str, y_col: str) -> pd.DataFrame:
    frame = shots_or_deliveries.copy()
    if frame.empty:
        return pd.DataFrame()

    def zone(row: pd.Series) -> str:
        y = row[y_col]
        if y < 80 / 3:
            return "Near Post"
        if y > (80 / 3) * 2:
            return "Far Post"
        return "Penalty Spot"

    frame["target_zone"] = frame.apply(zone, axis=1)
    summary = (
        frame.groupby("target_zone")
        .size()
        .reset_index(name="count")
    )
    order = ["Near Post", "Penalty Spot", "Far Post"]
    summary["target_zone"] = pd.Categorical(summary["target_zone"], categories=order, ordered=True)
    return summary.sort_values("target_zone")