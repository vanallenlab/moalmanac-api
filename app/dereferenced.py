"""
Builds the in-memory cache of dereferenced records served by the API.

The API's SQLite tables mirror moalmanac-db/schemas/referenced (see app.referenced).
Endpoints instead serve records shaped like moalmanac-db/schemas/dereferenced, with
foreign keys resolved to embedded objects. Rather than reimplementing that
resolution, this module rebuilds the referenced tables from SQLite
(`app.referenced.load_referenced`) and runs them through the moalmanac-db
submodule's own `utils.dereference`, so the submodule stays the single source of
truth for the output shape.

`build_cache` is called once, at startup (see app.main.create_app), and its result
is stored on `app.state.dereferenced`. It is a plain read-only dict and is never
written to disk or mutated afterward.
"""

import copy
import pathlib
import sys
import typing

import sqlalchemy.orm

from app import referenced

_MOALMANAC_DB_ROOT = (
    pathlib
    .Path(__file__)
    .resolve()
    .parents[1]
    / "moalmanac-db"
)
if str(_MOALMANAC_DB_ROOT) not in sys.path:
    sys.path.insert(0, str(_MOALMANAC_DB_ROOT))

from utils import dereference

# Every table `dereference.Database` needs to resolve foreign keys, keyed by the
# same names as app.referenced.TABLES. `urls` has no entry in _CONCEPT_DIRS (it is
# only ever embedded inside documents), but Database still requires it.
_TABLE_CLASSES: dict[str, type] = {
    "agents": dereference.Agents,
    "alleles": dereference.Alleles,
    "biomarkers": dereference.Biomarkers,
    "biomarker_criteria": dereference.BiomarkerCriteria,
    "codings": dereference.Codings,
    "contributions": dereference.Contributions,
    "copy_changes": dereference.CopyChanges,
    "diseases": dereference.Diseases,
    "documents": dereference.Documents,
    "function_consequences": dereference.FunctionConsequences,
    "genes": dereference.Genes,
    "indications": dereference.Indications,
    "mappings": dereference.Mappings,
    "propositions": dereference.Propositions,
    "sequence_locations": dereference.SequenceLocations,
    "sequence_references": dereference.SequenceReferences,
    "statements": dereference.Statements,
    "strengths": dereference.Strengths,
    "therapies": dereference.Therapies,
    "therapy_groups": dereference.TherapyGroups,
    "urls": dereference.URLs,
}

Cache = dict[str, dict[str, dict[str, typing.Any]]]


def build_cache(session: sqlalchemy.orm.Session) -> Cache:
    """
    Rebuilds every dereferenced entity from the database.

    Rebuilds the referenced tables from SQLite, feeds them into a fresh
    `dereference.Database`, and dereferences each entity in the same order
    `utils.dereference.write_all_concepts` uses. This is the entire dereferencing
    logic; the API does not duplicate any of it.

    Args:
        session (sqlalchemy.orm.Session): The database session to read from.

    Returns:
        Cache: `{entity: {id: record}}` for every entity in
        `utils.dereference._CONCEPT_DIRS`, each record equal to its file in
        moalmanac-db/dereferenced/<entity>/. Dict order (both the outer entities and
        each inner id) matches the referenced source, which callers rely on for
        deterministic, file-order output.
    """
    tables = referenced.load_referenced(session)
    database = dereference.Database(
        **{
            name: table_class(records=copy.deepcopy(tables[name]))
            for name, table_class in _TABLE_CLASSES.items()
        },
    )

    cache: Cache = {}
    for attribute, _output_dir in dereference._CONCEPT_DIRS:
        table = getattr(database, attribute)
        table.dereference(database)
        cache[attribute] = {record["id"]: record for record in table.records}
    return cache
