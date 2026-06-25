"""
Step 4: Interactive opposition scouting dashboard.

Run:
    streamlit run app.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from config import DEFAULT_TEAM
from src.bootstrap import database_ready, ensure_database
from src.brief import build_opposition_brief
from src.db import get_engine
from src.metrics import (
    final_third_entries,
    get_shots,
    league_ppda_ranking,
    ppda_summary,
    xg_season_totals,
    xg_summary,
    zone_summary,
)
from src.plots import (
    create_corner_delivery_fig,
    create_delivery_zones_fig,
    create_set_piece_balance_fig,
    create_shot_map_fig,
    create_zone_fig,
)
from src.set_pieces import (
    CORNER_PATTERN,
    attack_summary,
    defense_summary,
    delivery_players,
    delivery_zone,
    get_deliveries,
    shot_players,
)

st.set_page_config(
    page_title="Soccer Scouting Platform",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; }
    div[data-testid="stMetric"] {
        background: #0f1b2d;
        border: 1px solid #1e3a5f;
        border-radius: 10px;
        padding: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_teams() -> list[str]:
    engine = get_engine()
    teams = pd.read_sql(
        "SELECT DISTINCT team_name FROM events ORDER BY team_name",
        engine,
    )
    return teams["team_name"].tolist()


@st.cache_data(show_spinner=False)
def load_ppda_ranking() -> pd.DataFrame:
    return league_ppda_ranking(get_engine())


@st.cache_data(show_spinner=False)
def load_team_data(team: str) -> dict:
    engine = get_engine()
    corner_deliveries = get_deliveries(engine, team, "Corner")
    return {
        "shots": get_shots(engine, team),
        "xg_totals": xg_season_totals(engine, team),
        "xg_breakdown": xg_summary(engine, team),
        "zone_df": zone_summary(engine, team),
        "entries_df": final_third_entries(engine, team),
        "ppda": ppda_summary(engine, team),
        "attack_df": attack_summary(engine, team),
        "defense_df": defense_summary(engine, team),
        "corner_deliveries": corner_deliveries,
        "corner_takers": delivery_players(engine, team, "Corner"),
        "corner_shooters": shot_players(engine, team, CORNER_PATTERN),
        "delivery_zones": delivery_zone(
            corner_deliveries,
            "end_location_x",
            "end_location_y",
        ),
    }


@st.cache_data(show_spinner=False)
def load_brief(team: str) -> str:
    return build_opposition_brief(team, get_engine())


def show_fig(fig) -> None:
    st.pyplot(fig)
    plt.close(fig)


def render_overview(team: str, data: dict) -> None:
    xg = data["xg_totals"]
    ppda = data["ppda"]
    ppda_rank = data["ppda_rank"]
    rank_row = ppda_rank[ppda_rank["team"] == team].iloc[0]
    conceded = data["defense_df"][data["defense_df"]["context"] == "All set pieces conceded"].iloc[0]

    st.subheader("Season Overview")
    cols = st.columns(5)
    cols[0].metric("Shots", xg["shots"])
    cols[1].metric("Goals", xg["goals"])
    cols[2].metric("Total xG", xg["total_xg"])
    cols[3].metric("PPDA", ppda["ppda"], help="Lower = more aggressive press")
    cols[4].metric("Press Rank", f"{int(rank_row['press_rank'])} / {len(ppda_rank)}")

    st.info(
        f"**{team}** scored {xg['goals']} goals from {xg['total_xg']:.2f} xG "
        f"({xg['xg_difference']:+.2f} difference). "
        f"They conceded **{int(conceded['goals'])}** set-piece goals — a key weakness to target."
    )


def render_tactical(team: str, data: dict) -> None:
    st.subheader("Tactical Profile")

    col_left, col_right = st.columns([1.3, 1])
    with col_left:
        show_fig(create_shot_map_fig(data["shots"], team))
    with col_right:
        show_fig(create_zone_fig(data["zone_df"], team))

    st.markdown("### xG Breakdown")
    st.dataframe(data["xg_breakdown"], use_container_width=True, hide_index=True)

    st.markdown("### PPDA League Ranking")
    st.dataframe(
        data["ppda_rank"].head(10),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Final-Third Entries by Zone")
    st.dataframe(data["entries_df"], use_container_width=True, hide_index=True)


def render_set_pieces(team: str, data: dict) -> None:
    st.subheader("Set-Piece Analysis")

    col_left, col_right = st.columns(2)
    with col_left:
        show_fig(create_corner_delivery_fig(data["corner_deliveries"], team))
    with col_right:
        show_fig(create_set_piece_balance_fig(data["attack_df"], data["defense_df"], team))

    show_fig(create_delivery_zones_fig(data["delivery_zones"], team))

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("#### Attacking Summary")
        st.dataframe(data["attack_df"], use_container_width=True, hide_index=True)
    with col_b:
        st.markdown("#### Defensive Summary")
        st.dataframe(data["defense_df"], use_container_width=True, hide_index=True)
    with col_c:
        st.markdown("#### Corner Takers")
        st.dataframe(data["corner_takers"].head(8), use_container_width=True, hide_index=True)

    st.markdown("#### Threat Players from Corners")
    st.dataframe(data["corner_shooters"], use_container_width=True, hide_index=True)


def render_brief(team: str, data: dict) -> None:
    st.subheader("Opposition Brief")
    st.caption("Export this brief for coaching staff or include it in your portfolio.")

    brief_text = data["brief"]
    st.markdown(brief_text)

    file_name = f"{team.lower().replace(' ', '_')}_opposition_brief.md"
    st.download_button(
        label="Download Opposition Brief",
        data=brief_text,
        file_name=file_name,
        mime="text/markdown",
    )


def main() -> None:
    if not database_ready():
        st.warning(
            "First launch: downloading StatsBomb data and building the database. "
            "This takes about 5–10 minutes on Streamlit Cloud."
        )
        with st.spinner("Building database from StatsBomb Open Data..."):
            ensure_database()

    teams = load_teams()
    default_index = teams.index(DEFAULT_TEAM) if DEFAULT_TEAM in teams else 0

    st.sidebar.title("Soccer Scouting")
    st.sidebar.caption("Premier League 2015/16 | StatsBomb Open Data")

    team = st.sidebar.selectbox("Opposition team", teams, index=default_index)
    page = st.sidebar.radio(
        "Navigate",
        ["Overview", "Tactical Analysis", "Set Pieces", "Opposition Brief"],
    )

    st.title("Opposition Scouting Dashboard")
    st.markdown(f"### Target: **{team}**")

    with st.spinner(f"Loading {team} data..."):
        data = load_team_data(team)
        data["ppda_rank"] = load_ppda_ranking()

    if page == "Overview":
        render_overview(team, data)
    elif page == "Tactical Analysis":
        render_tactical(team, data)
    elif page == "Set Pieces":
        render_set_pieces(team, data)
    else:
        data["brief"] = load_brief(team)
        render_brief(team, data)

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**Portfolio project**  \n"
        "Steps 1–4: Data pipeline → Tactical metrics → Set pieces → Dashboard"
    )


if __name__ == "__main__":
    main()