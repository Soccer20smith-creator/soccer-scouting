"""
Step 2: Generate tactical scouting visuals for a target team.

Usage:
    python scripts/04_tactical_report.py
    python scripts/04_tactical_report.py --team "Chelsea"
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
from src.metrics import (  # noqa: E402
    final_third_entries,
    get_shots,
    league_ppda_ranking,
    ppda_summary,
    xg_season_totals,
    xg_summary,
    zone_summary,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build tactical scouting report.")
    parser.add_argument("--team", type=str, default=DEFAULT_TEAM)
    return parser.parse_args()


def team_slug(team: str) -> str:
    return team.lower().replace(" ", "_")


def plot_shot_map(shots: pd.DataFrame, team: str, output_path: Path) -> None:
    pitch = Pitch(
        pitch_type="statsbomb",
        line_zorder=2,
        pitch_color="#22312b",
        line_color="#c7d5cc",
    )
    fig, ax = pitch.draw(figsize=(12, 8))

    goal_shots = shots[shots["is_goal"] == 1]
    other_shots = shots[shots["is_goal"] == 0]

    pitch.hexbin(
        other_shots["location_x"],
        other_shots["location_y"],
        ax=ax,
        gridsize=(18, 12),
        cmap="YlOrRd",
        alpha=0.45,
        zorder=2,
        mincnt=1,
    )
    pitch.scatter(
        other_shots["location_x"],
        other_shots["location_y"],
        ax=ax,
        s=18,
        c="white",
        edgecolors="none",
        alpha=0.35,
        zorder=3,
        label="Shot",
    )
    if not goal_shots.empty:
        pitch.scatter(
            goal_shots["location_x"],
            goal_shots["location_y"],
            ax=ax,
            s=160,
            marker="*",
            c="#4fd1c5",
            edgecolors="white",
            linewidth=0.8,
            zorder=4,
            label="Goal",
        )

    ax.set_title(f"{team} Shot Map — Premier League 2015/16", fontsize=14, color="white", pad=16)
    legend = ax.legend(loc="upper right", frameon=False)
    for text in legend.get_texts():
        text.set_color("white")
    fig.patch.set_facecolor("#1a1a1a")
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def plot_zone_bars(zone_df: pd.DataFrame, team: str, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    colors = ["#034694", "#6cabdd", "#4fd1c5"]

    axes[0].bar(zone_df["zone"], zone_df["shots"], color=colors)
    axes[0].set_title("Shots by Zone")
    axes[0].set_ylabel("Shots")

    axes[1].bar(zone_df["zone"], zone_df["total_xg"], color=colors)
    axes[1].set_title("xG by Zone")
    axes[1].set_ylabel("Expected Goals")

    fig.suptitle(f"{team} Attack Zones", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def write_text_report(
    output_path: Path,
    team: str,
    xg_totals: dict,
    xg_breakdown: pd.DataFrame,
    zone_df: pd.DataFrame,
    entries_df: pd.DataFrame,
    ppda: dict,
    ppda_rank: pd.DataFrame,
) -> None:
    team_rank = ppda_rank[ppda_rank["team"] == team].iloc[0]
    strongest_zone = zone_df.sort_values("total_xg", ascending=False).iloc[0]
    top_entry_zone = entries_df.sort_values("entries", ascending=False).iloc[0]

    lines = [
        f"# {team} — Tactical Scouting Summary",
        "",
        "## Season xG Profile",
        f"- Shots: {xg_totals['shots']}",
        f"- Goals: {xg_totals['goals']}",
        f"- Total xG: {xg_totals['total_xg']}",
        f"- xG Difference (Goals - xG): {xg_totals['xg_difference']}",
        f"- Average xG per shot: {xg_totals['avg_xg_per_shot']}",
        "",
        "## Shot Context",
    ]

    for _, row in xg_breakdown.iterrows():
        context = row["shot_context"] if pd.notna(row["shot_context"]) else "Unknown"
        lines.append(
            f"- {context}: {int(row['shots'])} shots, {row['total_xg']:.2f} xG, {int(row['goals'])} goals"
        )

    lines.extend(
        [
            "",
            "## Pressing (PPDA)",
            f"- {team} PPDA: {ppda['ppda']} (lower = more aggressive press)",
            f"- League rank: {int(team_rank['press_rank'])} of {len(ppda_rank)}",
            "",
            "## Attack Zones",
            f"- Strongest shooting zone: {strongest_zone['zone']} ({strongest_zone['total_xg']:.2f} xG)",
            f"- Most final-third entries from: {top_entry_zone['zone']} ({int(top_entry_zone['entries'])} entries)",
            "",
            "## Coaching Notes",
            "- Shot map highlights where they finish attacks; larger/darker markers = higher xG chances.",
            "- Zone split shows whether they bias chances down the left, centrally, or down the right.",
            "- PPDA helps you plan build-up: low PPDA teams disrupt possession early; high PPDA teams defend deeper.",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    engine = get_engine()
    output_dir = PROJECT_ROOT / "outputs" / team_slug(args.team)
    output_dir.mkdir(parents=True, exist_ok=True)

    shots = get_shots(engine, args.team)
    xg_totals = xg_season_totals(engine, args.team)
    xg_breakdown = xg_summary(engine, args.team)
    zone_df = zone_summary(engine, args.team)
    entries_df = final_third_entries(engine, args.team)
    ppda = ppda_summary(engine, args.team)
    ppda_rank = league_ppda_ranking(engine)

    shot_map_path = output_dir / "shot_map.png"
    zone_chart_path = output_dir / "attack_zones.png"
    report_path = output_dir / "tactical_summary.md"

    plot_shot_map(shots, args.team, shot_map_path)
    plot_zone_bars(zone_df, args.team, zone_chart_path)
    write_text_report(
        report_path,
        args.team,
        xg_totals,
        xg_breakdown,
        zone_df,
        entries_df,
        ppda,
        ppda_rank,
    )

    print(f"Tactical report generated for {args.team}")
    print(f"  Shot map: {shot_map_path}")
    print(f"  Zone chart: {zone_chart_path}")
    print(f"  Written summary: {report_path}")
    print()
    print("Season xG totals:")
    for key, value in xg_totals.items():
        print(f"  {key}: {value}")
    print()
    print(f"PPDA: {ppda['ppda']} (rank {int(ppda_rank[ppda_rank['team'] == args.team].iloc[0]['press_rank'])} in league)")


if __name__ == "__main__":
    main()