"""
The SQLite database mirrors moalmanac-db/schemas/referenced: rebuilding each table
from the database gives back referenced/<table>.json exactly (record order, list
order, values, and which keys are present; dict key order is not compared).
"""

import jsonschema
import pytest
import sqlalchemy
import sqlalchemy.orm
from referencing import Registry

from app import referenced
from tests.conftest import REFERENCED_ROOT, SCHEMA_ROOT, load_json

TABLE_NAMES = ["about", *referenced.TABLES]


@pytest.fixture(scope="module")
def rebuilt(session: sqlalchemy.orm.Session) -> dict:
    """
    Rebuilds every referenced table from the test database.

    Args:
        session (sqlalchemy.orm.Session): A session on the test database.

    Returns:
        dict: Records for each table, keyed by table name.
    """
    return referenced.load_referenced(session)


def validator(name: str, registry: Registry) -> jsonschema.Draft202012Validator:
    """
    Builds a validator for one referenced schema, asserting `format` keywords.

    Args:
        name (str): The table name.
        registry (Registry): The schema registry.

    Returns:
        jsonschema.Draft202012Validator: A validator for schemas/referenced/<name>.schema.json.
    """
    schema = load_json(SCHEMA_ROOT / "referenced" / f"{name}.schema.json")
    return jsonschema.Draft202012Validator(
        schema,
        registry=registry,
        format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER,
    )


def test_every_referenced_file_is_loaded():
    """
    Ensures every referenced/*.json file has a table spec, so new upstream tables
    are not silently skipped.
    """
    files = {path.stem for path in REFERENCED_ROOT.glob("*.json")}
    assert files == set(TABLE_NAMES)


def test_foreign_keys_are_enforced_and_satisfied(session: sqlalchemy.orm.Session):
    """
    Ensures SQLite foreign key enforcement is on and no row violates a foreign key.
    """
    assert session.execute(sqlalchemy.text("PRAGMA foreign_keys")).scalar() == 1
    violations = session.execute(sqlalchemy.text("PRAGMA foreign_key_check")).all()
    assert violations == []


@pytest.mark.parametrize("name", TABLE_NAMES)
def test_table_round_trips(name: str, rebuilt: dict):
    """
    Ensures a table rebuilt from the database equals its referenced JSON file.
    """
    expected = load_json(REFERENCED_ROOT / f"{name}.json")
    actual = rebuilt[name]
    if isinstance(expected, dict):
        assert actual == expected
        return

    assert [record["id"] for record in actual] == [record["id"] for record in expected]
    mismatched = [
        record["id"]
        for record, expected_record in zip(actual, expected)
        if record != expected_record
    ]
    assert not mismatched, (
        f"{len(mismatched)} {name} records differ, e.g. {mismatched[:3]}"
    )


@pytest.mark.parametrize("name", TABLE_NAMES)
def test_table_matches_referenced_schema(name: str, rebuilt: dict, registry: Registry):
    """
    Ensures every record rebuilt from the database validates against its
    referenced schema.
    """
    check = validator(name, registry)
    records = rebuilt[name]
    if isinstance(records, dict):
        records = [records]
    failures = []
    for record in records:
        error = jsonschema.exceptions.best_match(check.iter_errors(record))
        if error is not None:
            failures.append(f"{record.get('id')}: {error.message[:200]}")
    assert not failures, f"{len(failures)} invalid {name} records, e.g. {failures[:3]}"
