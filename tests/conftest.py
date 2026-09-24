import json
import pathlib
import typing

import fastapi.testclient
import pytest
import sqlalchemy.orm
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from app import database, populate_database
from app.main import create_app

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MOALMANAC_DB_ROOT = REPO_ROOT / "moalmanac-db"
REFERENCED_ROOT = MOALMANAC_DB_ROOT / "referenced"
DEREFERENCED_ROOT = MOALMANAC_DB_ROOT / "dereferenced"
SCHEMA_ROOT = MOALMANAC_DB_ROOT / "schemas"


def load_json(path: pathlib.Path) -> dict[str, typing.Any]:
    """
    Loads JSON data from a file path.

    Args:
        path (pathlib.Path): The path to the JSON file.

    Returns:
        dict[str, typing.Any]: The deserialized JSON object.
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


@pytest.fixture(scope="session")
def app(config_path: str) -> fastapi.FastAPI:
    """
    Builds the FastAPI application against the test database.

    Args:
        config_path (str): The path to the test config file.

    Returns:
        fastapi.FastAPI: The application, with its dereferenced cache built.
    """
    return create_app(config_path=config_path)


@pytest.fixture(scope="session")
def client(app: fastapi.FastAPI) -> fastapi.testclient.TestClient:
    """
    A test client for the application.

    Args:
        app (fastapi.FastAPI): The application under test.

    Returns:
        fastapi.testclient.TestClient: A client that issues requests against `app`
        in-process, with no network involved.
    """
    return fastapi.testclient.TestClient(app)


def load_dereferenced(entity: str) -> dict[str, dict]:
    """
    Loads every record for one entity from moalmanac-db/dereferenced, keyed by id.

    Args:
        entity (str): The entity's directory name under moalmanac-db/dereferenced.

    Returns:
        dict[str, dict]: The entity's records, keyed by `id`, in the same order
        `app.dereferenced.build_cache` returns them in (filesystem glob order is
        irrelevant; callers sort or key-compare rather than relying on this order).
    """
    records = {}
    for path in sorted((DEREFERENCED_ROOT / entity).glob("*.json")):
        record = load_json(path)
        records[record["id"]] = record
    return records


def extension_value(record: dict, name: str) -> typing.Any:
    """
    Looks up one named value in a dereferenced record's `extensions` list.

    Args:
        record (dict): A dereferenced record with an `extensions` list.
        name (str): The extension's `name`.

    Raises:
        StopIteration: If no extension with that name is present.

    Returns:
        typing.Any: The matching extension's `value`.
    """
    return next(e["value"] for e in record["extensions"] if e["name"] == name)
