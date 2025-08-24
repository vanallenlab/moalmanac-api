import configparser
import os
import sqlalchemy
import typing
from sqlalchemy.orm import sessionmaker


def get_database(
    session: sessionmaker[sqlalchemy.orm.Session],
) -> typing.Generator[sqlalchemy.orm.Session, None, None]:
    """
    Yields a sqlalchemy.orm.Session created from the provided sessionmaker.

    Args:
        session (sessionmaker[sqlalchemy.orm.Session]): The sessionmaker instance for creating database sessions.

    Returns:
        sqlalchemy.orm.Session: The database session object.

    Raises:
        ...
    """
    database = session()
    try:
        yield database  # type: ignore
    except Exception:
        database.rollback()
        raise
    finally:
        database.close()


def init_db(
    config_path: str,
) -> tuple[sqlalchemy.Engine, sessionmaker[sqlalchemy.orm.Session]]:
    """
    Initializes the sqlite database connection and session.

    This function reads the configuration file for the app from a specific file (`config_path`),
    creates an SQLAlchemy engine, and configures a session for database interactions.

    Args:
        config_path (str): The path to the database configuration file.

    Returns:
        tuple[sqlalchemy.engine.Engine, sessionmaker[sqlalchemy.orm.Session]]: A tuple containing the SQLAlchemy engine and configured session.

    Raises:
        FileNotFoundError: If the specified configuration file does not exist.
        KeyError: If the database path is not found within the configuration file.
    """
    config = read_config_ini(path=config_path)
    try:
        path = os.path.abspath(config["database"]["path"])
    except KeyError as error:
        raise KeyError(
            "Database path not found within configuration file."
        ) from error
    engine = sqlalchemy.create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
        poolclass=sqlalchemy.pool.NullPool,
        pool_pre_ping=True,
        future=True,
    )
    session_factory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        future=True,
    )
    return engine, session_factory


def read_config_ini(path: str) -> configparser.ConfigParser:
    """
    Reads a configuration file in INI format.

    Args:
        path (str): The path to the database configuration file.

    Returns:
        config (configparser.ConfigParser): A ConfigParser object containing the configuration data.

    Raises:
        FileNotFoundError: If the specified configuration file does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found at {path}")
    config = configparser.ConfigParser()
    config.read(path)
    return config
