from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from config import DB_PATH


def get_engine() -> Engine:
    return create_engine(f"sqlite:///{DB_PATH}")