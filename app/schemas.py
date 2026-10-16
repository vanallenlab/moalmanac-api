"""
OpenAPI response schemas, built from moalmanac-db's JSON Schemas.

The API returns moalmanac-db's dereferenced records unchanged, so its response
schemas are moalmanac-db's own `schemas/dereferenced/*.schema.json` (plus
`schemas/referenced/about.schema.json` for service metadata), copied into the
OpenAPI document's `components/schemas`. moalmanac-db stays the single source of
truth: updating the submodule updates the API documentation.

These schemas only document responses. Routes do not set `response_model`, so
nothing is validated or re-serialized at request time.

The db schemas reference each other with relative file `$ref`s
(`genes.schema.json#/$defs/Gene`) and local `$defs` (`#/$defs/Gene`), resolved
through each schema's `$id`. Swagger UI resolves `$ref`s against the OpenAPI
document instead, so each schema's `$defs` become components of their own and
every `$ref` is rewritten to point at `#/components/schemas/...`.

Each record schema's example is a real record from moalmanac-db's `dereferenced/`
directory (see `EXAMPLE_IDS`). Any other string field with a `pattern` gets a
placeholder from the pattern's literal prefix (e.g. `coding:string`), because
Swagger UI otherwise generates a random string matching the regex.
"""

import copy
import json
import pathlib
import re
import typing

DB_DIRECTORY = pathlib.Path(__file__).parent.parent / "moalmanac-db"
DEREFERENCED_DIRECTORY = DB_DIRECTORY / "dereferenced"
SCHEMAS_DIRECTORY = DB_DIRECTORY / "schemas"
COMPONENTS_PREFIX = "#/components/schemas/"

# The record used as each entity's example, keyed by its `dereferenced/` directory.
# Together they follow one statement: FDA approval of dabrafenib for BRAF p.V600E
# melanoma. If an id no longer exists, the directory's first record is used.
EXAMPLE_IDS = {
    "agents": "agent:org:fda",
    "alleles": "ga4gh:VA.j4XnsLZcdzDIYa5pvvXM7t1wn9OITr0L",
    "biomarker_criteria": "bmkr.criterion:16",
    "biomarkers": "bmkr:16",
    "codings": "coding:hgnc:1097",
    "contributions": "ctrb:fda:2013-05-29:0",
    "diseases": "dis:ncit:C3224",
    "documents": "doc:fda:tafinlar",
    "genes": "gene:hgnc:1097",
    "indications": "ind:fda:tafinlar:0",
    "mappings": "map:hgnc:1097::ncbi:673",
    "propositions": "prop:vtxr:88",
    "sequence_locations": "ga4gh:SL.t-3DrWALhgLdXHsupI-e-M00aL3HgK3y",
    "sequence_references": "ga4gh:SQ.cQvw4UsHHRRlogxbWCB8W-mKD4AraM9y",
    "statements": "stmt:fda:tafinlar:0:0",
    "strengths": "str:ncit:C25425",
    "therapies": "tx:ncit:C82386",
    "therapy_groups": "txgrp:18",
}

# Hand-written, matching `create_response` in app/routers/main/routes.py.
META_SCHEMA = {
    "title": "Meta",
    "description": "Information about the request and response.",
    "type": "object",
    "required": [
        "data_length",
        "message",
        "request_url",
        "status",
        "status_code",
        "timestamp_elapsed",
        "timestamp_received",
        "timestamp_returned",
        "trace_id",
    ],
    "properties": {
        "data_length": {
            "type": "integer",
            "description": "Number of records in `data`, or 1 for a single object.",
        },
        "message": {
            "type": "string",
            "description": "Human-readable status message.",
        },
        "request_url": {
            "type": ["string", "null"],
            "description": "The full URL of the request.",
        },
        "status": {"type": "string", "enum": ["success", "error"]},
        "status_code": {"type": "integer", "examples": [200]},
        "timestamp_elapsed": {
            "type": "number",
            "description": "Seconds between receiving the request and returning it.",
        },
        "timestamp_received": {
            "type": "string",
            "format": "date-time",
            "description": "When the request was received, in UTC.",
            "examples": ["2026-10-16T14:03:12.123456Z"],
        },
        "timestamp_returned": {
            "type": "string",
            "format": "date-time",
            "description": "When the response was returned, in UTC.",
            "examples": ["2026-10-16T14:03:12.123456Z"],
        },
        "trace_id": {
            "type": "string",
            "format": "uuid",
            "description": "Unique id for this response.",
        },
    },
    "additionalProperties": False,
}

CONTRIBUTION_RECORDS_EXTENSION_SCHEMA = {
    "type": "object",
    "required": ["name", "value", "description"],
    "properties": {
        "name": {"const": "records"},
        "value": {
            "type": "array",
            "description": "Indications and statements this contribution was made to.",
            "items": {
                "type": "object",
                "required": ["id", "type", "name", "description"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string", "enum": ["Indication", "Statement"]},
                    "name": {"type": ["string", "null"]},
                    "description": {"type": ["string", "null"]},
                },
                "additionalProperties": False,
            },
        },
        "description": {"type": "string"},
    },
    "additionalProperties": False,
}

SEARCH_AGGREGATES_SCHEMA = {
    "title": "Search aggregates",
    "description": (
        "Counts of Active statements made about this proposition, narrowed by the "
        "`document`, `indication`, and `agent_id` filters."
    ),
    "type": "object",
    "required": [
        "statement_count",
        "by_direction",
        "by_document",
        "by_agent",
        "by_strength",
    ],
    "properties": {
        "statement_count": {"type": "integer"},
        "by_direction": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["direction", "count"],
                "properties": {
                    "direction": {"type": ["string", "null"]},
                    "count": {"type": "integer"},
                },
                "additionalProperties": False,
            },
        },
        **{
            key: {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "count"],
                    "properties": {
                        "id": {"type": "string", "description": description},
                        "count": {"type": "integer"},
                    },
                    "additionalProperties": False,
                },
            }
            for key, description in (
                ("by_document", "Document id."),
                ("by_agent", "Agent id."),
                ("by_strength", "Strength id."),
            )
        },
    },
    "additionalProperties": False,
}


def add_pattern_examples(node: typing.Any) -> typing.Any:
    """
    Gives every string schema with a `pattern` and no examples a placeholder
    example, in place.

    Args:
        node (typing.Any): A schema, or any value within one.

    Returns:
        typing.Any: `node`, with placeholder examples added.
    """
    if isinstance(node, list):
        for item in node:
            add_pattern_examples(node=item)
    elif isinstance(node, dict):
        pattern = node.get("pattern")
        if (
            isinstance(pattern, str)
            and node.get("type", "string") == "string"
            and "examples" not in node
        ):
            example = pattern_example(pattern=pattern)
            if example is not None:
                node["examples"] = [example]
        for value in node.values():
            add_pattern_examples(node=value)
    return node


def build_components() -> dict[str, dict]:
    """
    Builds the OpenAPI component schemas for every API response.

    Returns:
        dict[str, dict]: Component schemas keyed by name: one per db schema
            (named by its `title`, e.g. `Agent`), one per `$defs` entry (e.g.
            `Indication.FDAIndication`), plus `Meta` and the API-specific
            `SearchResult` and `ContributionResult`.
    """
    paths = [
        *sorted((SCHEMAS_DIRECTORY / "dereferenced").glob("*.schema.json")),
        SCHEMAS_DIRECTORY / "referenced" / "about.schema.json",
    ]
    loaded = {path.name: json.loads(path.read_text()) for path in paths}
    titles = {filename: schema["title"] for filename, schema in loaded.items()}

    components: dict[str, dict] = {}
    for filename, schema in loaded.items():
        title = titles[filename]
        schema = copy.deepcopy(schema)
        schema.pop("$schema", None)
        schema.pop("$id", None)
        definitions = schema.pop("$defs", {})
        example = load_example(filename=filename)
        if example is not None:
            schema["examples"] = [example]
        components[title] = rewrite_references(
            node=schema,
            filename=filename,
            titles=titles,
        )
        for name, definition in definitions.items():
            component_name = definition_component_name(title=title, name=name)
            if component_name in components:
                raise ValueError(f"Duplicate component name {component_name}.")
            components[component_name] = rewrite_references(
                node=definition,
                filename=filename,
                titles=titles,
            )

    search_result = copy.deepcopy(components["Proposition"])
    search_result["title"] = "SearchResult"
    search_result["examples"] = [search_result_example(components=components)]
    search_result["description"] = (
        "A Proposition with aggregated information about the statements made about it."
    )
    search_result["properties"]["aggregates"] = SEARCH_AGGREGATES_SCHEMA
    search_result.setdefault("required", []).append("aggregates")
    components["SearchResult"] = search_result

    contribution_result = copy.deepcopy(components["Contribution"])
    contribution_result["title"] = "ContributionResult"
    contribution_result["description"] = (
        "A Contribution, with a `records` extension when requested with "
        "`include_records=true`."
    )
    contribution_result["properties"]["extensions"] = {
        "type": "array",
        "items": CONTRIBUTION_RECORDS_EXTENSION_SCHEMA,
    }
    components["ContributionResult"] = contribution_result

    components["Meta"] = META_SCHEMA
    add_pattern_examples(node=components)
    return components


def definition_component_name(title: str, name: str) -> str:
    """
    Names the component for one `$defs` entry of a db schema.

    OpenAPI component names may only contain letters, digits, `.`, `-`, and `_`,
    so `name` is converted to PascalCase.

    Args:
        title (str): The title of the schema the definition belongs to, e.g.
            "Indication".
        name (str): The `$defs` key, e.g. "FDA Indication".

    Returns:
        str: The component name, e.g. "Indication.FDAIndication".
    """
    words = re.split(r"[^A-Za-z0-9]+", name)
    return f"{title}." + "".join(word[:1].upper() + word[1:] for word in words)


def envelope(data: dict, path: str, message: str) -> dict:
    """
    Wraps a `data` schema in the standard response envelope of meta, service, and
    data.

    Args:
        data (dict): The schema for the `data` key.
        path (str): The endpoint's path, for the example `meta`, e.g. "/agents".
        message (str): The endpoint's `meta.message`, for the example `meta`.

    Returns:
        dict: The envelope schema.
    """
    return {
        "type": "object",
        "required": ["meta", "service", "data"],
        "properties": {
            "meta": {
                "$ref": f"{COMPONENTS_PREFIX}Meta",
                "examples": [meta_example(path=path, message=message)],
            },
            "service": {
                "$ref": f"{COMPONENTS_PREFIX}About",
                "description": "Service and database release metadata.",
            },
            "data": data,
        },
        "additionalProperties": False,
    }


def list_response(
    component: str,
    path: str,
    subject: str,
) -> dict[int | str, dict[str, typing.Any]]:
    """
    Builds a route's `responses` for an endpoint returning a list of records.

    Args:
        component (str): The component name of one record, e.g. "Agent".
        path (str): The endpoint's path, e.g. "/agents".
        subject (str): The subject of the endpoint's `meta.message`, e.g. "Agents".

    Returns:
        dict[int | str, dict[str, typing.Any]]: The value for the route's
            `responses` argument.
    """
    return {
        200: {
            "description": f"Matching {component} records.",
            "content": {
                "application/json": {
                    "schema": envelope(
                        data={
                            "type": "array",
                            "items": {"$ref": f"{COMPONENTS_PREFIX}{component}"},
                        },
                        path=path,
                        message=f"{subject} retrieved successfully",
                    ),
                },
            },
        },
    }


def load_example(filename: str) -> dict | None:
    """
    Loads the moalmanac-db record used as the example for one db schema.

    Args:
        filename (str): The schema's filename, e.g. "agents.schema.json".

    Returns:
        dict | None: The record named in `EXAMPLE_IDS`, or the directory's first
            record if that id no longer exists, or None if the schema has no
            record directory (e.g. `extension.schema.json`).
    """
    if filename == "about.schema.json":
        return json.loads((DB_DIRECTORY / "referenced" / "about.json").read_text())

    directory = DEREFERENCED_DIRECTORY / filename.removesuffix(".schema.json")
    if not directory.is_dir():
        return None

    record_id = EXAMPLE_IDS.get(directory.name, "")
    path = directory / f"{record_id.replace(':', '_')}.json"
    if not path.is_file():
        records = sorted(directory.glob("*.json"))
        if not records:
            return None
        path = records[0]
    return json.loads(path.read_text())


def meta_example(path: str, message: str) -> dict:
    """
    Builds an example `meta` block for one endpoint.

    Args:
        path (str): The endpoint's path, e.g. "/agents".
        message (str): The endpoint's `meta.message`.

    Returns:
        dict: An example `meta` block describing a one-record response.
    """
    return {
        "data_length": 1,
        "message": message,
        "request_url": f"https://api.moalmanac.org{path}",
        "status": "success",
        "status_code": 200,
        "timestamp_elapsed": 0.012345,
        "timestamp_received": "2026-10-16T14:03:12.123456Z",
        "timestamp_returned": "2026-10-16T14:03:12.135801Z",
        "trace_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    }


def object_response(
    component: str,
    path: str,
    subject: str,
) -> dict[int | str, dict[str, typing.Any]]:
    """
    Builds a route's `responses` for an endpoint returning a single object.

    Args:
        component (str): The component name of the object, e.g. "About".
        path (str): The endpoint's path, e.g. "/about".
        subject (str): The subject of the endpoint's `meta.message`, e.g.
            "About metadata".

    Returns:
        dict[int | str, dict[str, typing.Any]]: The value for the route's
            `responses` argument.
    """
    return {
        200: {
            "description": f"The {component} record.",
            "content": {
                "application/json": {
                    "schema": envelope(
                        data={"$ref": f"{COMPONENTS_PREFIX}{component}"},
                        path=path,
                        message=f"{subject} retrieved successfully",
                    ),
                },
            },
        },
    }


def pattern_example(pattern: str) -> str | None:
    """
    Builds a placeholder example from the literal prefix of a regex pattern.

    Args:
        pattern (str): The regex, e.g. "^bmkr\\.criterion:\\d+$".

    Returns:
        str | None: The literal prefix followed by "string", e.g.
            "bmkr.criterion:string", or None if the pattern has no literal prefix.
    """
    if not pattern.startswith("^"):
        return None

    prefix = ""
    characters = iter(pattern[1:])
    for character in characters:
        if character == "\\":
            escaped = next(characters, "")
            if escaped.isalnum() or not escaped:
                break
            prefix += escaped
        elif character in ".[](){}*+?|$^":
            break
        else:
            prefix += character
    return f"{prefix}string" if prefix else None


def rewrite_references(
    node: typing.Any,
    filename: str,
    titles: dict[str, str],
) -> typing.Any:
    """
    Rewrites every `$ref` in a db schema to point into `#/components/schemas`.

    Args:
        node (typing.Any): A schema, or any value within one.
        filename (str): The file the schema came from, which local `#/$defs/...`
            references resolve against.
        titles (dict[str, str]): Schema titles keyed by filename.

    Returns:
        typing.Any: `node`, with `$ref`s rewritten in place.

    Raises:
        ValueError: If a `$ref` is not of a form used by moalmanac-db's schemas.
    """
    if isinstance(node, list):
        for item in node:
            rewrite_references(node=item, filename=filename, titles=titles)
    elif isinstance(node, dict):
        reference = node.get("$ref")
        if isinstance(reference, str):
            target, _, fragment = reference.partition("#")
            target = target or filename
            if target not in titles:
                raise ValueError(f"Unknown $ref target {reference!r} in {filename}.")
            target_title = titles[target]
            if fragment == "":
                node["$ref"] = f"{COMPONENTS_PREFIX}{target_title}"
            elif fragment.startswith("/$defs/"):
                name = fragment.removeprefix("/$defs/")
                node["$ref"] = COMPONENTS_PREFIX + definition_component_name(
                    title=target_title,
                    name=name,
                )
            else:
                raise ValueError(f"Unsupported $ref {reference!r} in {filename}.")
        for key, value in node.items():
            if key != "$ref":
                rewrite_references(node=value, filename=filename, titles=titles)
    return node


def search_result_example(components: dict[str, dict]) -> dict:
    """
    Builds the SearchResult example: the example Proposition, with aggregates
    counting only the example Statement, which is made about that proposition.

    Args:
        components (dict[str, dict]): Component schemas built so far, including
            examples for `Proposition` and `Statement`.

    Returns:
        dict: An illustrative `/search` result.
    """
    proposition = components["Proposition"]["examples"][0]
    statement = components["Statement"]["examples"][0]
    return {
        **proposition,
        "aggregates": {
            "statement_count": 1,
            "by_direction": [{"direction": statement["direction"], "count": 1}],
            "by_document": [
                {"id": document["id"], "count": 1}
                for document in statement["reportedIn"]
            ],
            "by_agent": [{"id": EXAMPLE_IDS["agents"], "count": 1}],
            "by_strength": [{"id": statement["strength"]["id"], "count": 1}],
        },
    }
