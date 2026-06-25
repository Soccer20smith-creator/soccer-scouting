"""
Step 3: Set-piece scouting report for a target team.

Usage:
    python scripts/05_set_piece_report.py
    python scripts/05_set_piece_report.py --team "Chelsea"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from mplsoccer import Pitch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DEFAULT_TEAM  # noqa: E402
from src.db import get_engine  # noqa: E402
from src.set_pieces import (  # noqa: E402
    CORNER_PATTERN,
    attack_summary,
    defense_summary,
    delivery_players,
    delivery_zone,
    get_deliveries,
    get_set_piece_shots,
    get_set_piece_shots_conceded,
    shot_players,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build set-piece scouting report.")
    parser.add_argument("--team", type=str, default=DEFAULT_TEAM)
    return parser.parse_args()


def team_slug(team: str) -> str:
    return team.lower().replace(" ", "_")


def plot_corner_deliveries(deliveries: pd.DataFrame, team: str, output_path: Path) -> None:
    pitch = Pitch(
        pitch_type="statsbomb",
        pitch_color="#22312b",
        line_color="#c7d5cc",
        line_zorder=2,
    )
    fig, ax = pitch.draw(figsize=(12, 8))

    pitch.scatter(
        deliveries["end_location_x"],
        deliveries["end_location_y"],
        ax=ax,
        s=70,
        c="#6cabdd",
        edgecolors="white",
        linewidth=0.5,
        alpha=0.8,
        zorder=3,
    )
    pitch.scatter(
        [120, 120, 0, 0],
        [0, 80, 0, 80],
        ax=ax,
        s=120,
        marker="s",
        c="#034694",
        edgecolors="white",
        linewidth=0.8,
        zorder=4,
        label="Corner take-off",
    )

    ax.set_title(
        f"{team} Corner Delivery Targets — Premier League 2015/16",
        fontsize=14,
        color="white",
        pad=16,
    )
    legend = ax.legend(loc="upper right", frameon=False)
    for text in legend.get_texts():
        text.set_color("white")
    fig.patch.set_facecolor("#1a1a1a")
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def plot_attacking_vs_defending(
    attack_df: pd.DataFrame,
    defense_df: pd.DataFrame,
    team: str,
    output_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    colors = ["#034694", "#6cabdd"]

    attack_plot = attack_df[attack_df["context"].isin(["Corners (shots)", "Free kicks (shots)"])]
    axes[0].bar(attack_plot["context"], attack_plot["total_xg"], color=colors)
    axes[0].set_title(f"{team} — xG Created from Set Pieces")
    axes[0].set_ylabel("Expected Goals")
    axes[0].tick_params(axis="x", rotation=15)

    defense_plot = defense_df[defense_df["context"].isin(["Corners conceded", "Free kicks conceded"])]
    axes[1].bar(defense_plot["context"], defense_plot["total_xg"], color=["#e74c3c", "#f39c12"])
    axes[1].set_title(f"{team} — xG Conceded from Set Pieces")
    axes[1].set_ylabel("Expected Goals")
    axes[1].tick_params(axis="x", rotation=15)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_delivery_zones(zones: pd.DataFrame, team: str, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(zones["target_zone"], zones["count"], color=["#034694", "#6cabdd", "#4fd1c5"])
    ax.set_title(f"{team} — Corner Delivery Zones")
    ax.set_ylabel("Deliveries")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_report(
    output_path: Path,
    team: str,
    attack_df: pd.DataFrame,
    defense_df: pd.DataFrame,
    corner_takers: pd.DataFrame,
    corner_shooters: pd.DataFrame,
    zone_df: pd.DataFrame,
) -> None:
    corners = attack_df[attack_df["context"] == "Corners (shots)"].iloc[0]
    free_kicks = attack_df[attack_df["context"] == "Free kicks (shots)"].iloc[0]
    conceded_all = defense_df[defense_df["context"] == "All set pieces conceded"].iloc[0]
    top_taker = corner_takers.iloc[0] if not corner_takers.empty else None
    top_zone = zone_df.sort_values("count", ascending=False).iloc[0] if not zone_df.empty else None

    lines = [
        f"# {team} — Set-Piece Scouting Report",
        "",
        "## Attacking Set Pieces",
        f"- Corners taken: {int(corners['deliveries'])}",
        f"- Shots from corners: {int(corners['shots'])} ({corners['total_xg']:.2f} xG, {int(corners['goals'])} goals)",
        f"- Free-kick shots: {int(free_kicks['shots'])} ({free_kicks['total_xg']:.2f} xG, {int(free_kicks['goals'])} goals)",
        "",
        "## Defensive Vulnerability",
        f"- Set-piece shots conceded: {int(conceded_all['shots'])}",
        f"- Set-piece xG conceded: {conceded_all['total_xg']:.2f}",
        f"- Set-piece goals conceded: {int(conceded_all['goals'])}",
        "",
    ]

    if top_taker is not None:
        lines.append(f"## Primary Corner Taker: {top_taker['player_name']} ({int(top_taker['deliveries'])} corners)")
        lines.append("")

    if top_zone is not None:
        lines.append(f"## Preferred Delivery Zone: {top_zone['target_zone']} ({int(top_zone['count'])} deliveries)")
        lines.append("")

    lines.append("## Threat Players from Corners")
    if corner_shooters.empty:
        lines.append("- No corner-shot attempts recorded.")
    else:
        for _, row in corner_shooters.head(5).iterrows():
            lines.append(
                f"- {row['player_name']}: {int(row['shots'])} shots, {row['total_xg']:.2f} xG, {int(row['goals'])} goals"
            )

    lines.extend(
        [
            "",
            "## Coaching Recommendations",
            "- Mark the primary corner taker and study delivery zone tendencies (near/far post).",
            "- Organize zonal/man marking for the top shot-winners listed above.",
            "- If xG conceded from corners is high, prioritize goalkeeper positioning and near-post clears.",
            "- Compare open-play xG (Step 2) with set-piece xG to decide whether to press aggressively at restarts.",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    engine = get_engine()
    output_dir = PROJECT_ROOT / "outputs" / team_slug(args.team)
    output_dir.mkdir(parents=True, exist_ok=True)

    corner_deliveries = get_deliveries(engine, args.team, "Corner")
    attack_df = attack_summary(engine, args.team)
    defense_df = defense_summary(engine, args.team)
    corner_takers = delivery_players(engine, args.team, "Corner")
    corner_shooters = shot_players(engine, args.team, CORNER_PATTERN)
    zone_df = delivery_zone(corner_deliveries, "end_location_x", "end_location_y")

    delivery_map_path = output_dir / "corner_delivery_map.png"
    balance_chart_path = output_dir / "set_piece_balance.png"
    zone_chart_path = output_dir / "corner_delivery_zones.png"
    report_path = output_dir / "set_piece_report.md"

    plot_corner_deliveries(corner_deliveries, args.team, delivery_map_path)
    plot_attacking_vs_defending(attack_df, defense_df, args.team, balance_chart_path)
    plot_delivery_zones(zone_df, args.team, zone_chart_path)
    write_report(
        report_path,
        args.team,
        attack_df,
        defense_df,
        corner_takers,
        corner_shooters,
        zone_df,
    )

    conceded = get_set_piece_shots_conceded(engine, args.team)
    corner_shots = get_set_piece_shots(engine, args.team, CORNER_PATTERN)

    print(f"Set-piece report generated for {args.team}")
    print(f"  Corner delivery map: {delivery_map_path}")
    print(f"  Attack vs defense chart: {balance_chart_path}")
    print(f"  Delivery zones chart: {zone_chart_path}")
    print(f"  Written report: {report_path}")
    print()
    print(f"Corners taken: {len(corner_deliveries)}")
    print(f"Shots from corners: {len(corner_shots)}")
    print(f"Set-piece shots conceded: {len(conceded)}")


if __name__ == "__main__":
    main()