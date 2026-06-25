from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
DB_PATH = PROJECT_ROOT / "database" / "scouting.db"

STATSBOMB_BASE_URL = (
    "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
)

# Default dataset: Premier League 2015/2016 (Chelsea — full season in open data)
DEFAULT_COMPETITION_ID = 2
DEFAULT_SEASON_ID = 27
DEFAULT_TEAM = "Chelsea"