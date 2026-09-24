"""
Each entity endpoint's `data` equals the records in
moalmanac-db/dereferenced/<entity>/*.json exactly, and every record it returns
validates against schemas/dereferenced/<entity>.schema.json. This is the plan's
definition of done for the migration.
"""

import fastapi.testclient
import jsonschema
import pytest
from referencing import Registry

from tests.conftest import SCHEMA_ROOT, extension_value, load_dereferenced, load_json

# Entities whose endpoint only returns records with one of these status values.
ALLOWED_STATUSES = {
    "documents": {"Active"},
    "indications": {"Approved", "Accelerated"},
    "statements": {"Active"},
}

# path -> (dereferenced entity name, primary query parameter)
ENDPOINTS = {
    "/agents": ("agents", None),
    "/alleles": ("alleles", None),
    "/biomarker_criteria": ("biomarker_criteria", None),
    "/biomarkers": ("biomarkers", None),
    "/codings": ("codings", None),
    "/contributions": ("contributions", None),
    "/copy_changes": ("copy_changes", None),
    "/diseases": ("diseases", None),
    "/documents": ("documents", None),
    "/function_consequences": ("function_consequences", None),
    "/genes": ("genes", None),
    "/indications": ("indications", None),
    "/mappings": ("mappings", None),
    "/propositions": ("propositions", None),
    "/sequence_locations": ("sequence_locations", None),
    "/sequence_references": ("sequence_references", None),
    "/statements": ("statements", None),
    "/strengths": ("strengths", None),
    "/therapies": ("therapies", None),
    "/therapy_groups": ("therapy_groups", None),
}


def validator(entity: str, registry: Registry) -> jsonschema.Draft202012Validator:
    """
    Builds a validator for one dereferenced schema, asserting `format` keywords.

    Args:
        entity (str): The entity name.
        registry (Registry): The schema registry.

    Returns:
        jsonschema.Draft202012Validator: A validator for schemas/dereferenced/<entity>.schema.json.
    """
    schema = load_json(SCHEMA_ROOT / "dereferenced" / f"{entity}.schema.json")
    return jsonschema.Draft202012Validator(
        schema,
        registry=registry,
        format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER,
    )


def test_every_dereferenced_directory_has_an_endpoint():
    """
    Ensures every moalmanac-db/dereferenced/<entity>/ directory has a matching
    endpoint, so a new upstream entity is not silently left unserved.
    """
    from tests.conftest import DEREFERENCED_ROOT

    directories = {path.name for path in DEREFERENCED_ROOT.iterdir() if path.is_dir()}
    endpoints = {entity for entity, _ in ENDPOINTS.values()}
    assert directories == endpoints


@pytest.mark.parametrize("path", sorted(ENDPOINTS))
def test_endpoint_matches_dereferenced_files(
    path: str,
    client: fastapi.testclient.TestClient,
):
    """
    Ensures an endpoint's unfiltered `data` equals moalmanac-db's dereferenced
    files for that entity, keyed by id (so record and list order are checked, but
    not dict key order). For entities in ALLOWED_STATUSES, only records with an
    allowed status are expected, since those endpoints filter the rest out.
    """
    entity, _ = ENDPOINTS[path]
    expected = load_dereferenced(entity)

    allowed_statuses = ALLOWED_STATUSES.get(entity)
    if allowed_statuses is not None:
        expected = {
            record_id: record
            for record_id, record in expected.items()
            if extension_value(record, "status") in allowed_statuses
        }

    response = client.get(path)
    assert response.status_code == 200
    records = response.json()["data"]

    actual = {record["id"]: record for record in records}
    assert set(actual) == set(expected)
    mismatched = [
        record_id
        for record_id, record in actual.items()
        if record != expected[record_id]
    ]
    assert not mismatched, (
        f"{len(mismatched)} {entity} records differ, e.g. {mismatched[:3]}"
    )


@pytest.mark.parametrize("path", sorted(ENDPOINTS))
def test_endpoint_matches_dereferenced_schema(
    path: str,
    client: fastapi.testclient.TestClient,
    registry: Registry,
):
    """
    Ensures every record an endpoint returns validates against its dereferenced schema.
    """
    entity, _ = ENDPOINTS[path]
    check = validator(entity, registry)

    response = client.get(path)
    records = response.json()["data"]

    failures = []
    for record in records:
        error = jsonschema.exceptions.best_match(check.iter_errors(record))
        if error is not None:
            failures.append(f"{record.get('id')}: {error.message[:200]}")
    assert not failures, (
        f"{len(failures)} invalid {entity} records, e.g. {failures[:3]}"
    )


def test_about_matches_referenced_about(client: fastapi.testclient.TestClient):
    """
    Ensures /about equals moalmanac-db's referenced/about.json.
    """
    from tests.conftest import REFERENCED_ROOT

    expected = load_json(REFERENCED_ROOT / "about.json")
    response = client.get("/about")
    assert response.status_code == 200
    assert response.json()["data"] == expected


def test_search_matches_propositions_plus_aggregates(
    client: fastapi.testclient.TestClient,
):
    """
    Ensures /search, with include_empty=true, returns every dereferenced
    proposition plus an `aggregates` key, and nothing else changed.
    """
    expected = load_dereferenced("propositions")

    response = client.get("/search", params={"include_empty": "true"})
    assert response.status_code == 200
    records = response.json()["data"]

    actual = {record["id"]: record for record in records}
    assert set(actual) == set(expected)
    for record_id, record in actual.items():
        assert "aggregates" in record
        without_aggregates = {k: v for k, v in record.items() if k != "aggregates"}
        assert without_aggregates == expected[record_id]
