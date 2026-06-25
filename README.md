# Soccer Scouting Platform

Opposition scouting and set-piece analysis built on [StatsBomb Open Data](https://github.com/statsbomb/open-data).

## Step 1 — Data foundation (current)

1. Download raw JSON from StatsBomb
2. Load matches and events into SQLite
3. Explore the database

## Setup

```bash
cd soccer-scouting
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run Step 1

Default opposition target: **Chelsea** (Premier League 2015/2016).

Start with a small sample while learning:

```bash
python scripts/01_download_data.py --team "Chelsea" --max-matches 5
python scripts/02_load_database.py --team "Chelsea"
python scripts/03_explore_data.py --team "Chelsea"
```

Download Chelsea's full season (38 matches) when ready:

```bash
python scripts/01_download_data.py --team "Chelsea"
python scripts/02_load_database.py --team "Chelsea"
```

## Step 2 — Tactical metrics (current)

Generate Chelsea's shot map, xG profile, PPDA, and attack zones:

```bash
python scripts/02_load_database.py --team "Chelsea"
python scripts/04_tactical_report.py --team "Chelsea"
```

Outputs are saved to `outputs/chelsea/`.

## Step 3 — Set-piece analysis

Generate corner maps, delivery zones, and defensive vulnerability notes:

```bash
python scripts/02_load_database.py --team "Chelsea"
python scripts/05_set_piece_report.py --team "Chelsea"
```

Outputs are saved to `outputs/chelsea/`.

## Step 4 — Interactive dashboard

Launch the scouting dashboard:

```bash
streamlit run app.py
```

Features:
- Team selector (all 20 Premier League teams in the dataset)
- Tactical analysis page (shot map, xG, PPDA)
- Set-piece page (corners, vulnerabilities)
- Downloadable opposition brief (Markdown)

## Publish your portfolio

See **[PUBLISHING.md](PUBLISHING.md)** for step-by-step instructions to deploy on:

| Platform | What you publish |
|----------|------------------|
| **GitHub** | Full codebase |
| **Kaggle** | `kaggle/soccer_scouting_analysis.ipynb` |
| **Streamlit Cloud** | Live dashboard (`app.py`) |

Quick start for cloud deploy:

```bash
# Optional: pre-build full-season DB for faster Streamlit cold starts
python scripts/build_full_season_db.py
streamlit run app.py
```

The dashboard auto-downloads StatsBomb data on first launch if the database is missing.

## Project roadmap

- [x] Step 1: Data download + SQLite pipeline
- [x] Step 2: Team-level tactical metrics (shots, xG zones, PPDA)
- [x] Step 3: Set-piece analysis module
- [x] Step 4: Streamlit scouting report dashboard