"""Matplotlib figures for the scouting dashboard."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure
from mplsoccer import Pitch


def create_shot_map_fig(shots: pd.DataFrame, team: str) -> Figure:
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
    fig.tight_layout()
    return fig


def create_zone_fig(zone_df: pd.DataFrame, team: str) -> Figure:
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
    return fig


def create_corner_delivery_fig(deliveries: pd.DataFrame, team: str) -> Figure:
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
    fig.tight_layout()
    return fig


def create_set_piece_balance_fig(
    attack_df: pd.DataFrame,
    defense_df: pd.DataFrame,
    team: str,
) -> Figure:
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
    return fig


def create_delivery_zones_fig(zones: pd.DataFrame, team: str) -> Figure:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(zones["target_zone"], zones["count"], color=["#034694", "#6cabdd", "#4fd1c5"])
    ax.set_title(f"{team} — Corner Delivery Zones")
    ax.set_ylabel("Deliveries")
    fig.tight_layout()
    return fig