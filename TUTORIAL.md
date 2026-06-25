# Soccer Scouting Platform — Self-Completion Tutorial

This guide explains **what was built**, **what is already done on your machine**, and **what you still need to do** to call the project portfolio-ready.

---

## Is the project complete?

### Already built (on your PC)

| Step | Status | Location |
|------|--------|----------|
| 1 — Data pipeline | Done | `scripts/01–03`, `sql/schema.sql`, `database/scouting.db` |
| 2 — Tactical metrics | Done | `src/metrics.py`, `scripts/04_tactical_report.py` |
| 3 — Set-piece analysis | Done | `src/set_pieces.py`, `scripts/05_set_piece_report.py` |
| 4 — Dashboard | Done | `app.py`, `src/plots.py`, `src/brief.py` |

Chelsea's full 2015/16 season is downloaded, loaded, and report outputs exist in `outputs/chelsea/`.

### You still need to do (portfolio polish)

- [ ] Run every step yourself and confirm outputs
- [ ] Replace `Chelsea` with another team to prove the pipeline is reusable
- [ ] Push code to GitHub (public repo)
- [ ] Add screenshots to README
- [ ] Deploy dashboard to Streamlit Community Cloud (optional but impressive)
- [ ] Write a 1-paragraph project summary for your resume/LinkedIn

The **code** is complete. The **portfolio presentation** is what you finish yourself.

---

## Project structure (what each folder does)

```
soccer-scouting/
├── app.py                 # Step 4: Streamlit dashboard
├── config.py              # Paths, default team, competition IDs
├── requirements.txt       # Python packages
├── scripts/
│   ├── 01_download_data.py   # Pull JSON from StatsBomb GitHub
│   ├── 02_load_database.py   # Flatten JSON → SQLite tables
│   ├── 03_explore_data.py    # Quick sanity-check queries
│   ├── 04_tactical_report.py # Step 2 charts + markdown
│   └── 05_set_piece_report.py# Step 3 charts + markdown
├── sql/schema.sql         # Database table definitions
├── src/
│   ├── db.py              # SQLite connection helper
│   ├── metrics.py         # xG, PPDA, zone metrics
│   ├── set_pieces.py      # Corner/free-kick analysis
│   ├── plots.py           # Matplotlib figures for dashboard
│   └── brief.py           # Exportable opposition brief
├── data/raw/              # Downloaded JSON (not committed to git)
├── database/              # scouting.db (not committed to git)
└── outputs/               # Generated PNG/MD reports
```

---

## Prerequisites

- Python 3.10+ installed
- PowerShell or terminal
- Internet access (to download StatsBomb data)

---

## Part A — Run the existing project (30–45 min)

### 1. Open the project

```powershell
cd C:\Users\Soccer20Smith\soccer-scouting
.venv\Scripts\activate
```

If `.venv` does not exist yet:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Step 1 — Download and load data

Start small (5 matches) to learn, then scale up.

```powershell
# Small sample
python scripts/01_download_data.py --team "Chelsea" --max-matches 5
python scripts/02_load_database.py --team "Chelsea"
python scripts/03_explore_data.py --team "Chelsea"
```

```powershell
# Full Chelsea season (38 matches) — already done on your machine
python scripts/01_download_data.py --team "Chelsea"
python scripts/02_load_database.py --team "Chelsea"
```

**What to verify:** You should see match counts, event counts, and a table of Chelsea fixtures.

**What you learned:** Raw JSON → structured SQLite tables (`matches`, `events`, `competitions`).

### 3. Step 2 — Tactical report

```powershell
python scripts/04_tactical_report.py --team "Chelsea"
```

**Check outputs:**

- `outputs/chelsea/shot_map.png`
- `outputs/chelsea/attack_zones.png`
- `outputs/chelsea/tactical_summary.md`

**What you learned:** xG, PPDA, and zone metrics turned into coach-facing visuals.

### 4. Step 3 — Set-piece report

```powershell
python scripts/05_set_piece_report.py --team "Chelsea"
```

**Check outputs:**

- `outputs/chelsea/corner_delivery_map.png`
- `outputs/chelsea/set_piece_balance.png`
- `outputs/chelsea/set_piece_report.md`

**What you learned:** Corners and free kicks are a separate, scoutable game phase.

### 5. Step 4 — Dashboard

```powershell
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

**Try this:**

1. Select a different team (e.g., Leicester City)
2. Visit all four sidebar pages
3. Download the opposition brief from the last page

---

## Part B — Understand each step (how you would build it yourself)

### Step 1: Data foundation

**Goal:** Get data into a queryable database.

1. **Download** — StatsBomb hosts free JSON at GitHub. `01_download_data.py` fetches:
   - `competitions.json` (available leagues/seasons)
   - `matches/{competition_id}/{season_id}.json`
   - `events/{match_id}.json`

2. **Schema** — `sql/schema.sql` defines three core tables:
   - `competitions` — league + season metadata
   - `matches` — fixtures and scores
   - `events` — every pass, shot, pressure, etc.

3. **Load** — `02_load_database.py` flattens nested JSON into flat columns (e.g., `shot_xg`, `location_x`, `pass_type`).

**Exercise:** Open `database/scouting.db` in [DB Browser for SQLite](https://sqlitebrowser.org/) and run:

```sql
SELECT player_name, shot_xg, shot_outcome
FROM events
WHERE team_name = 'Chelsea' AND is_shot = 1
ORDER BY shot_xg DESC
LIMIT 10;
```

---

### Step 2: Tactical metrics

**Goal:** Answer "How does this team play?"

| Metric | Question it answers | Where it lives |
|--------|---------------------|----------------|
| xG | How good were their chances? | `src/metrics.py` → `xg_season_totals()` |
| PPDA | How aggressively do they press? | `src/metrics.py` → `ppda_summary()` |
| Zone split | Where do they attack/shoot? | `src/metrics.py` → `zone_summary()` |
| Shot map | Visual shot locations | `src/plots.py` → `create_shot_map_fig()` |

**PPDA formula (simplified):**

```
PPDA = Opponent passes ÷ Your defensive actions
```

Lower PPDA = more intense press.

**Exercise:** Change `DEFAULT_TEAM` in `config.py` to `"Arsenal"`, re-run Steps 1–2, and compare PPDA values.

---

### Step 3: Set-piece analysis

**Goal:** Answer "How do we defend their restarts?"

Key filters:

- Corner deliveries: `pass_type = 'Corner'`
- Set-piece shots: `play_pattern IN ('From Corner', 'From Free Kick')`
- Conceded shots: same filters, but `team_name != your opponent`

**Exercise:** In `05_set_piece_report.py` output, find Chelsea's primary corner taker and top aerial threats. Write 3 bullet points a coach would use in a pre-match meeting.

---

### Step 4: Dashboard

**Goal:** Package everything for non-technical users.

`app.py` uses Streamlit patterns:

- `@st.cache_data` — cache slow database queries
- `st.sidebar.selectbox` — team picker
- `st.pyplot(fig)` — display matplotlib charts
- `st.download_button` — export opposition brief

**Exercise:** Add a fifth sidebar page called "Match Log" that shows the selected team's fixtures in a table (`matches` table filtered by team).

---

## Part C — Prove reusability (recommended)

Pick a second team and run the full pipeline without help:

```powershell
python scripts/01_download_data.py --team "Leicester City"
python scripts/02_load_database.py --team "Leicester City"
python scripts/04_tactical_report.py --team "Leicester City"
python scripts/05_set_piece_report.py --team "Leicester City"
streamlit run app.py
```

If all outputs generate correctly, you understand the project — not just the Chelsea-specific results.

---

## Part D — Publish to GitHub

### 1. Initialize git (inside project folder)

```powershell
cd C:\Users\Soccer20Smith\soccer-scouting
git init
git add .
git commit -m "Add soccer scouting platform with tactical and set-piece analysis"
```

`.gitignore` already excludes large data (`data/raw/`, `database/`, `outputs/`).

### 2. Create a GitHub repo

1. Go to github.com → New repository → name it `soccer-scouting`
2. Do **not** add a README (you already have one)

### 3. Push

```powershell
git remote add origin https://github.com/YOUR_USERNAME/soccer-scouting.git
git branch -M main
git push -u origin main
```

### 4. Add a note to README for recruiters

Explain that data is downloaded locally via `01_download_data.py` (so the repo stays lightweight).

---

## Part E — Deploy dashboard (optional)

1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Deploy `app.py` from `soccer-scouting`
5. Add `requirements.txt` (already exists)

**Note:** Cloud deploy needs the database. Options:

- Commit a small pre-built `database/scouting.db` (Chelsea-only, ~few MB), OR
- Add a "Setup" script in README that runs download + load on first launch

For portfolio, committing a small SQLite file for one team is the easiest path.

---

## Part F — Resume / interview talking points

When asked about this project, use this structure:

1. **Problem:** "I built an opposition scouting tool for pre-match analysis."
2. **Data:** "I used StatsBomb open event data — 136K+ events — stored in SQLite."
3. **Analysis:** "I calculated xG, PPDA, zone tendencies, and set-piece patterns."
4. **Delivery:** "I shipped a Streamlit dashboard with downloadable coaching briefs."
5. **Insight example:** "Chelsea conceded 20 set-piece goals vs 7 scored from corners — a clear defensive vulnerability."

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Activate venv: `.venv\Scripts\activate` then `pip install -r requirements.txt` |
| No data in dashboard | Run `01_download_data.py` then `02_load_database.py` first |
| Streamlit won't start | Try `python -m streamlit run app.py` |
| Wrong team / empty outputs | Check exact team name spelling (case-sensitive in some scripts) |
| Slow PPDA calculation | Normal on first load; dashboard caches results after that |

---

## Suggested learning schedule

| Day | Task | Time |
|-----|------|------|
| 1 | Run Steps 1–2, explore SQLite | 2 hrs |
| 2 | Run Step 3, read `set_pieces.py` | 2 hrs |
| 3 | Run dashboard, download brief | 1 hr |
| 4 | Second team (Leicester), compare | 2 hrs |
| 5 | GitHub + README screenshots | 2 hrs |
| 6 | Deploy to Streamlit Cloud (optional) | 1 hr |

---

## What to build next (stretch goals)

- Add per-match filtering in the dashboard
- Compare two teams side-by-side
- Add expected threat (xT) for passes
- Pull a recent season when StatsBomb adds more free PL data

---

*You have a working project. Completing it yourself means running it, understanding each file, publishing it, and being able to explain your decisions in an interview.*