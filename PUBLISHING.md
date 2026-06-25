# Publishing Guide

Publish the Soccer Scouting Platform in three places: **GitHub** (code), **Kaggle** (notebook), and **Streamlit Cloud** (live dashboard).

---

## 1. GitHub

### One-time setup

```powershell
cd C:\Users\Soccer20Smith\soccer-scouting
git init
git add .
git commit -m "Initial commit: soccer scouting platform"
```

Create a new repository on GitHub (public, no README). Then:

```powershell
git branch -M main
git remote add origin https://github.com/Soccer20smith-creator/soccer-scouting.git
git push -u origin main
```

### What gets committed

| Included | Excluded (`.gitignore`) |
|----------|-------------------------|
| Source code, scripts, SQL schema | `.venv/` |
| Kaggle notebook + metadata | `data/raw/` (download at runtime) |
| README, tutorial, publishing docs | `database/*.db` |
| Streamlit config | `outputs/` |

Raw StatsBomb JSON is **not** committed. The app downloads it when needed.

### Optional: faster Streamlit cold starts

After building the full-season database locally:

```powershell
python scripts/build_full_season_db.py
```

You can commit `database/scouting.db` for faster Streamlit deploys (remove that line from `.gitignore` first). The file may be large (~100MB+ for a full PL season).

---

## 2. Kaggle

### Upload via web UI (easiest)

1. Sign in at [kaggle.com](https://www.kaggle.com)
2. **Code** → **New Notebook** → **File** → **Upload Notebook**
3. Upload `kaggle/soccer_scouting_analysis.ipynb`
4. **Settings** → turn **Internet** **On**
5. **Run All**, then **Save Version** → **Save & Run All (Commit)**
6. **Share** → set visibility to **Public**
7. Pin the notebook on your Kaggle profile

### Upload via Kaggle CLI (optional)

```powershell
pip install kaggle
```

Create an API token: Kaggle → **Account** → **Create New Token**. Save as:

`C:\Users\Soccer20Smith\.kaggle\kaggle.json`

Edit `kaggle/kernel-metadata.json` and replace `YOUR_KAGGLE_USERNAME`.

```powershell
cd kaggle
kaggle kernels push -p .
```

### StatsBomb attribution

When publishing, include:

- Text: *Data sourced from StatsBomb Open Data*
- Link: https://github.com/statsbomb/open-data
- Logo: https://statsbomb.com/media-pack/

### Optional derived dataset

Export PPDA/xG tables from the notebook and upload as a separate Kaggle dataset using `kaggle/dataset-metadata.json` as a template. Attribute StatsBomb as the **source data**, not as the dataset author.

---

## 3. Streamlit Community Cloud

### Prerequisites

- GitHub repo pushed (see section 1)
- [Streamlit Community Cloud](https://share.streamlit.io/) account (sign in with GitHub)

### Deploy

1. Go to https://share.streamlit.io/
2. **New app**
3. Repository: `Soccer20smith-creator/soccer-scouting`
4. Branch: `main`
5. Main file path: `app.py`
6. **Deploy**

### First launch behavior

On first run, the app downloads StatsBomb data and builds SQLite automatically (`src/bootstrap.py`). Expect **5–10 minutes** on the first load.

For faster loads, pre-build the database locally and commit `database/scouting.db` (see GitHub section above).

### Add the live link to README

After deploy, add to `README.md`:

```markdown
## Live demo

[Open the scouting dashboard](https://YOUR_APP.streamlit.app/)
```

---

## Portfolio checklist

- [ ] GitHub repo public with README screenshots
- [ ] Kaggle notebook public with StatsBomb attribution
- [ ] Streamlit app deployed with live URL in README
- [ ] Kaggle + Streamlit + GitHub links on LinkedIn/resume

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Kaggle notebook fails on download | Enable **Internet** in notebook settings |
| Streamlit timeout on first load | Pre-build DB locally and commit it, or redeploy and wait |
| `kaggle` command not found | `pip install kaggle` and add token to `~/.kaggle/kaggle.json` |
| Git push rejected | Create the GitHub repo first, then add remote |
