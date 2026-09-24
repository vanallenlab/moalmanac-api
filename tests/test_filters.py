"""
Targeted integration tests for query parameter filters: each request goes
through the full stack (FastAPI routing, handlers, a real database session, and
the dereferenced cache), returns 200, returns at least one record, and every
returned record actually matches the filter. These are not exhaustive;
test_endpoints.py's unfiltered comparison against moalmanac-db is the primary
correctness check.
"""

import fastapi.testclient
import pytest

from tests.conftest import extension_value


@pytest.mark.parametrize(
    ("path", "params", "check"),
    [
        (
            "/agents",
            {"agent_type": "organization"},
            lambda r: all(a["agentType"] == "organization" for a in r),
        ),
        (
            "/biomarkers",
            {"biomarker_type": "Somatic variant"},
            lambda r: all(
                extension_value(b, "biomarker_type") == "Somatic variant" for b in r
            ),
        ),
        (
            "/contributions",
            {"agent": "Van Allen lab"},
            lambda r: all(c["contributor"]["name"] == "Van Allen lab" for c in r),
        ),
        (
            "/diseases",
            {"disease_name": "Melanoma"},
            lambda r: all(d["name"] == "Melanoma" for d in r),
        ),
        (
            "/documents",
            {},
            lambda r: all(extension_value(d, "status") == "Active" for d in r),
        ),
        (
            "/indications",
            {},
            lambda r: all(
                extension_value(i, "status") in ("Approved", "Accelerated") for i in r
            ),
        ),
        (
            "/statements",
            {},
            lambda r: all(extension_value(s, "status") == "Active" for s in r),
        ),
        (
            "/documents",
            {"agent": "Food and Drug Administration"},
            lambda r: all(
                extension_value(d, "agent")["name"] == "Food and Drug Administration"
                for d in r
            ),
        ),
        (
            "/documents",
            {"agent_id": "agent:org:fda"},
            lambda r: all(
                extension_value(d, "agent")["id"] == "agent:org:fda" for d in r
            ),
        ),
        (
            "/genes",
            {"gene_name": "BRAF"},
            lambda r: all(g["name"] == "BRAF" for g in r),
        ),
        (
            "/indications",
            {"agent": "Food and Drug Administration"},
            lambda r: all(
                all(
                    extension_value(doc, "agent")["name"]
                    == "Food and Drug Administration"
                    for doc in i["reportedIn"]
                )
                for i in r
            ),
        ),
        (
            "/propositions",
            {"gene": "BRAF"},
            lambda r: all(
                any(
                    gene["name"] == "BRAF"
                    for bmkr in extension_value(p, "biomarkers")
                    for gene in _biomarker_genes(bmkr["subject"])
                )
                for p in r
            ),
        ),
        (
            "/propositions",
            {"disease": "Melanoma"},
            lambda r: all(p["conditionQualifier"]["name"] == "Melanoma" for p in r),
        ),
        (
            "/propositions",
            {"therapy_type": "Targeted therapy"},
            lambda r: all(
                _flatten_therapy_types(p["objectTherapeutic"]) == {"Targeted therapy"}
                or "Targeted therapy" in _flatten_therapy_types(p["objectTherapeutic"])
                for p in r
            ),
        ),
        (
            "/statements",
            {"gene": "BRAF"},
            lambda r: len(r) > 0,
        ),
        (
            "/statements",
            {"document": "doc:fda:verzenio"},
            lambda r: all(
                any(doc["id"] == "doc:fda:verzenio" for doc in s["reportedIn"])
                for s in r
            ),
        ),
        (
            "/statements",
            {"indication": "ind:fda:verzenio:0"},
            lambda r: all(
                extension_value(s, "indication")["id"] == "ind:fda:verzenio:0"
                for s in r
            ),
        ),
        (
            "/therapies",
            {"therapy": "Abemaciclib"},
            lambda r: all(t["name"] == "Abemaciclib" for t in r),
        ),
        (
            "/therapies",
            {"therapy_type": "Targeted therapy"},
            lambda r: all(
                extension_value(t, "therapy_type") == "Targeted therapy" for t in r
            ),
        ),
    ],
)
def test_filter_returns_matching_records(
    path: str,
    params: dict,
    check,
    client: fastapi.testclient.TestClient,
):
    """
    Ensures a filtered request succeeds, returns at least one record, and every
    returned record satisfies the filter.
    """
    response = client.get(path, params=params)
    assert response.status_code == 200
    records = response.json()["data"]
    assert len(records) > 0
    assert check(records), (
        f"{path}?{params}: a returned record did not match the filter"
    )


def _biomarker_genes(subject: dict) -> list[dict]:
    """
    Extracts the gene records embedded in a biomarker's FeatureContextConstraint or
    AdjacencyConstraint constraints.

    Args:
        subject (dict): A dereferenced biomarker (a proposition's biomarker
            criterion subject).

    Returns:
        list[dict]: The gene records referenced by the biomarker's constraints.
    """
    genes = []
    for constraint in subject.get("constraints", []):
        if "featureContext" in constraint:
            genes.append(constraint["featureContext"])
        # A Gene fusion/Rearrangement/Translocation's AdjacencyConstraint embeds
        # each known gene directly in `adjoinedElements` (not under a
        # `featureContext` key); an unknown gene is {"type": "UnspecifiedElement"}.
        if "adjoinedElements" in constraint:
            genes.extend(
                element
                for element in constraint["adjoinedElements"]
                if element.get("conceptType") == "Gene"
            )
    return genes


def _flatten_therapy_types(object_therapeutic: dict) -> set[str]:
    """
    Collects every `therapy_type` extension value from a proposition's
    objectTherapeutic, whether it is a single therapy or a therapy group.

    Args:
        object_therapeutic (dict): A dereferenced therapy or therapy group.

    Returns:
        set[str]: The therapy_type values found.
    """
    therapies = object_therapeutic.get("therapies", [object_therapeutic])
    types = set()
    for therapy in therapies:
        for extension in therapy.get("extensions", []):
            if extension["name"] == "therapy_type":
                types.add(extension["value"])
    return types


def test_search_include_empty_false_drops_zero_statement_propositions(
    client: fastapi.testclient.TestClient,
):
    """
    Ensures /search without include_empty drops propositions with no statements,
    and every returned proposition has a positive statement_count.
    """
    response = client.get("/search")
    assert response.status_code == 200
    records = response.json()["data"]
    assert len(records) > 0
    assert all(record["aggregates"]["statement_count"] > 0 for record in records)


def test_search_by_document_narrows_aggregates_not_selection(
    client: fastapi.testclient.TestClient,
):
    """
    Ensures /search?document=... narrows the statement counts in `aggregates`
    without changing which propositions are selected.
    """
    baseline = client.get("/search", params={"include_empty": "true"}).json()["data"]
    filtered = client.get(
        "/search",
        params={"include_empty": "true", "document": "doc:fda:verzenio"},
    ).json()["data"]

    assert {r["id"] for r in baseline} == {r["id"] for r in filtered}

    total_count = sum(r["aggregates"]["statement_count"] for r in filtered)
    assert total_count > 0
    assert any(
        by_document["id"] == "doc:fda:verzenio"
        for record in filtered
        for by_document in record["aggregates"]["by_document"]
    )


@pytest.mark.parametrize(
    "path, id_param, record_id",
    [
        ("/biomarkers", "biomarker_id", "bmkr:12"),
        ("/diseases", "disease_id", "dis:oncotree:ALL"),
        ("/genes", "gene_id", "gene:hgnc:76"),
        ("/therapies", "therapy_id", "tx:ncit:C62528"),
    ],
)
def test_id_parameter_returns_single_record(
    path: str,
    id_param: str,
    record_id: str,
    client: fastapi.testclient.TestClient,
):
    """
    Ensures each entity's `<entity>_id` parameter returns exactly the matching
    record, and an unknown id returns no records.
    """
    response = client.get(path, params={id_param: record_id})
    assert response.status_code == 200
    records = response.json()["data"]
    assert [record["id"] for record in records] == [record_id]

    response = client.get(path, params={id_param: "not-an-id"})
    assert response.status_code == 200
    assert response.json()["data"] == []


@pytest.mark.parametrize(
    "path, id_param, deprecated_statuses",
    [
        ("/documents", "document_id", {"Deprecated"}),
        ("/indications", "indication_id", {"Superseded", "Withdrawn"}),
        ("/statements", "statement_id", {"Superseded", "Deprecated"}),
    ],
)
def test_include_deprecated_returns_deprecated_records(
    path: str,
    id_param: str,
    deprecated_statuses: set[str],
    client: fastapi.testclient.TestClient,
):
    """
    Ensures deprecated records (e.g. Deprecated documents, Superseded and
    Withdrawn indications, Superseded and Deprecated statements) are excluded by
    default and returned when include_deprecated=true, including when requested
    by id.
    """
    default = client.get(path).json()["data"]
    everything = client.get(
        path, params={"include_deprecated": "true"},
    ).json()["data"]
    assert len(everything) > len(default)
    assert not any(
        extension_value(record, "status") in deprecated_statuses
        for record in default
    )

    deprecated = [
        record
        for record in everything
        if extension_value(record, "status") in deprecated_statuses
    ]
    assert deprecated
    deprecated_id = deprecated[0]["id"]

    response = client.get(path, params={id_param: deprecated_id})
    assert response.json()["data"] == []
    response = client.get(
        path,
        params={id_param: deprecated_id, "include_deprecated": "true"},
    )
    assert [record["id"] for record in response.json()["data"]] == [deprecated_id]
