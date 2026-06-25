from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from config import DB_PATH


def get_engine() -> Engine:
    db_path = DB_PATH.resolve().as_posix()
    return create_engine(f"sqlite:///{db_path}")