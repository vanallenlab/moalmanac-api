import configparser
import os
import sqlalchemy
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


def init_db(config_path: str) -> tuple[Engine, sessionmaker]:
    """
    Initializes the sqlite database connection and session.

    This function reads the configuration file for the app from a specific file (`config_path`),
    creates an SQLAlchemy engine, and configures a session for database interactions.

    Args:
        config_path (str): The path to the database configuration file.

    Returns:
        tuple[sqqlalchemy.orm.engine, sqlalchemy.orm.Session]: A tuple containing the SQLAlchemy engine
            and configured session.

    Raises:
        FileNotFoundError: If the specified configuration file does not exist.
        KeyError: If the database path is not found within the configuration file.
    """
    config = configparser.ConfigParser()

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at {config_path}")

    config.read(config_path)

    try:
        path = config['database']['path']
    except KeyError:
        raise KeyError("Database path not found within configuration file.")

    path = os.path.abspath(path)

    engine = sqlalchemy.create_engine(f"sqlite:///{path}")
    session = sessionmaker(bind=engine)
    return engine, session
