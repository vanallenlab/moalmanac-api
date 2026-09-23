import json
import pathlib

import pytest
import sqlalchemy.orm
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from app import database, populate_database

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MOALMANAC_DB_ROOT = REPO_ROOT / "moalmanac-db"
REFERENCED_ROOT = MOALMANAC_DB_ROOT / "referenced"
SCHEMA_ROOT = MOALMANAC_DB_ROOT / "schemas"


def load_json(path: pathlib.Path) -> object:
    """
    Loads JSON data from a file path.

    Args:
        path (pathlib.Path): The path to the JSON file.

    Returns:
        object: The deserialized JSON content.
    """
    return json.loads(path.read_text())


@pytest.fixture(scope="session")
def config_path(tmp_path_factory: pytest.TempPathFactory) -> str:
    """
    Writes a config file pointing at a SQLite file in a temporary directory, and
    populates that database from moalmanac-db/referenced.

    Args:
        tmp_path_factory (pytest.TempPathFactory): Pytest's session temp directory factory.

    Returns:
        str: The path to the config file.
    """
    directory = tmp_path_factory.mktemp("database")
    path = directory / "config.ini"
    path.write_text(f"[database]\npath = {directory / 'moalmanac.sqlite3'}\n")
    populate_database.main(
        referenced_directory=str(REFERENCED_ROOT),
        config_path=str(path),
    )
    return str(path)


@pytest.fixture(scope="session")
def registry() -> Registry:
    """
    Registry of every moalmanac-db schema, keyed by `$id`, so relative `$ref`s
    resolve locally.

    Returns:
        Registry: The schema registry.
    """
    resources = []
    for tree in ("referenced", "dereferenced"):
        for path in sorted((SCHEMA_ROOT / tree).glob("*.schema.json")):
            schema = load_json(path)
            resources.append((schema["$id"], Resource(schema, DRAFT202012)))
    return Registry().with_resources(resources)


@pytest.fixture(scope="session")
def session(config_path: str) -> sqlalchemy.orm.Session:
    """
    Opens a session on the populated test database.

    Args:
        config_path (str): The path to the test config file.

    Yields:
        sqlalchemy.orm.Session: A session on the test database.
    """
    engine, session_factory = database.init_db(config_path=config_path)
    with session_factory() as session:
        yield session
    engine.dispose()
