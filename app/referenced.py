"""
Mapping between moalmanac-db referenced JSON records and the SQLite tables in
app.models.

One `TableSpec` per referenced table lists its JSON keys in file order and says how
each key is stored: as a column of the entity table (the column name is the JSON
key), as an ordered association table (array-valued foreign keys), or, for
biomarkers, as rows of `biomarker_extensions`. The same specs drive both directions,
so loading (`records_to_rows`) and dumping (`load_referenced`) stay symmetric.
"""

import dataclasses
import datetime
import typing

import sqlalchemy
import sqlalchemy.orm

from app import models


@dataclasses.dataclass(frozen=True)
class ListField:
    """
    An array-valued foreign key stored in an association table.

    Attributes:
        association (type[models.Base]): The association model.
        owner (str): The association attribute holding the owner record's id.
        target (str): The association attribute holding the array item.
    """

    association: type[models.Base]
    owner: str
    target: str


@dataclasses.dataclass(frozen=True)
class TableSpec:
    """
    How one referenced table maps onto the database.

    Attributes:
        model (type[models.Base]): The entity model.
        keys (tuple[str, ...]): The record's JSON keys, in file order.
        lists (dict[str, ListField]): JSON keys stored in association tables.
        omit (dict[str, typing.Callable[[dict], bool]]): JSON keys left out of a
            record when the predicate, called with the record, returns True.
        extensions (bool): Whether the record has an `extensions` array stored in
            `biomarker_extensions`.
    """

    model: type[models.Base]
    keys: tuple[str, ...]
    lists: dict[str, ListField] = dataclasses.field(default_factory=dict)
    omit: dict[str, typing.Callable[[dict], bool]] = dataclasses.field(
        default_factory=dict,
    )
    extensions: bool = False

    @property
    def columns(self) -> dict[str, sqlalchemy.Column]:
        """
        Maps each JSON key stored as a column to its column.

        Returns:
            dict[str, sqlalchemy.Column]: Columns of the entity table, keyed by JSON key.
        """
        table = self.model.__table__
        return {key: table.c[key] for key in self.keys if key in table.c}


def _is_none(key: str) -> typing.Callable[[dict], bool]:
    """
    Builds an `omit` predicate for optional keys that are absent rather than null.

    Args:
        key (str): The JSON key.

    Returns:
        typing.Callable[[dict], bool]: True when the record's value for key is None.
    """
    return lambda record: record[key] is None


def _is_not_hse(record: dict) -> bool:
    """
    Whether an indication is from any organization other than HSE, whose records
    are the only ones carrying reimbursement keys.

    Args:
        record (dict): An indication record.

    Returns:
        bool: True unless the id begins with "ind:hse:".
    """
    return not record["id"].startswith("ind:hse:")


def _mappings(association: type[models.Base], owner: str) -> ListField:
    """
    Builds the ListField for a `mappings` array.

    Args:
        association (type[models.Base]): The association model.
        owner (str): The association attribute holding the owner record's id.

    Returns:
        ListField: The mappings list field.
    """
    return ListField(association=association, owner=owner, target="mapping_id")


# Insertion order satisfies foreign keys, so the loader can follow it directly.
TABLES: dict[str, TableSpec] = {
    "agents": TableSpec(
        model=models.Agents,
        keys=(
            "id",
            "type",
            "agentType",
            "name",
            "description",
            "last_updated",
            "url",
        ),
        omit={"last_updated": _is_none("last_updated"), "url": _is_none("url")},
    ),
    "urls": TableSpec(
        model=models.URLs,
        keys=("id", "url"),
    ),
    "codings": TableSpec(
        model=models.Codings,
        keys=("id", "code", "name", "system", "systemVersion", "iris"),
        omit={"name": _is_none("name"), "systemVersion": _is_none("systemVersion")},
    ),
    "mappings": TableSpec(
        model=models.Mappings,
        keys=("id", "primary_coding_id", "coding_id", "relation"),
    ),
    "sequence_references": TableSpec(
        model=models.SequenceReferences,
        keys=(
            "id",
            "type",
            "name",
            "aliases",
            "description",
            "moleculeType",
            "refgetAccession",
            "residueAlphabet",
        ),
    ),
    "sequence_locations": TableSpec(
        model=models.SequenceLocations,
        keys=(
            "id",
            "type",
            "name",
            "aliases",
            "description",
            "digest",
            "sequenceReference",
            "start",
            "end",
            "sequence",
        ),
    ),
    "alleles": TableSpec(
        model=models.Alleles,
        keys=(
            "id",
            "type",
            "name",
            "aliases",
            "description",
            "digest",
            "hgvs.g",
            "hgvs.c",
            "hgvs.c_short",
            "hgvs.p",
            "hgvs.p_short",
            "location",
            "state_type",
            "state_sequence",
            "state_length",
            "state_repeat_subunit_length",
        ),
    ),
    "copy_changes": TableSpec(
        model=models.CopyChanges,
        keys=("id", "name"),
    ),
    "function_consequences": TableSpec(
        model=models.FunctionConsequences,
        keys=("id", "name", "primary_coding_id"),
    ),
    "genes": TableSpec(
        model=models.Genes,
        keys=(
            "id",
            "conceptType",
            "name",
            "primary_coding_id",
            "mappings",
            "cds_start",
            "location",
            "location_sortable",
            "protein_product",
            "protein_product_exons",
            "transcript",
            "transcript_exons",
        ),
        lists={
            "mappings": _mappings(models.AssociationGenesAndMappings, "gene_id"),
            "protein_product_exons": ListField(
                association=models.AssociationGenesAndProteinProductExons,
                owner="gene_id",
                target="sequence_location_id",
            ),
            "transcript_exons": ListField(
                association=models.AssociationGenesAndTranscriptExons,
                owner="gene_id",
                target="sequence_location_id",
            ),
        },
    ),
    "biomarkers": TableSpec(
        model=models.Biomarkers,
        keys=(
            "id",
            "type",
            "name",
            "allele",
            "copyChange",
            "function",
            "genes",
            "location",
            "biomarker_type",
            "extensions",
        ),
        lists={
            "genes": ListField(
                association=models.AssociationBiomarkersAndGenes,
                owner="biomarker_id",
                target="gene_id",
            ),
            "location": ListField(
                association=models.AssociationBiomarkersAndSequenceLocations,
                owner="biomarker_id",
                target="sequence_location_id",
            ),
        },
        extensions=True,
    ),
    "biomarker_criteria": TableSpec(
        model=models.BiomarkerCriteria,
        keys=("id", "subject", "present"),
    ),
    "diseases": TableSpec(
        model=models.Diseases,
        keys=(
            "id",
            "conceptType",
            "name",
            "primary_coding_id",
            "mappings",
            "solid_tumor",
        ),
        lists={
            "mappings": _mappings(models.AssociationDiseasesAndMappings, "disease_id"),
        },
    ),
    "therapies": TableSpec(
        model=models.Therapies,
        keys=(
            "id",
            "conceptType",
            "name",
            "primary_coding_id",
            "mappings",
            "therapy_strategy",
            "therapy_type",
        ),
        lists={
            "mappings": _mappings(models.AssociationMappingsAndTherapies, "therapy_id"),
        },
    ),
    "therapy_groups": TableSpec(
        model=models.TherapyGroups,
        keys=("id", "membershipOperator", "therapies"),
        lists={
            "therapies": ListField(
                association=models.AssociationTherapiesAndTherapyGroups,
                owner="therapy_group_id",
                target="therapy_id",
            ),
        },
    ),
    "contributions": TableSpec(
        model=models.Contributions,
        keys=("id", "type", "agent_id", "description", "date"),
    ),
    "documents": TableSpec(
        model=models.Documents,
        keys=(
            "id",
            "type",
            "documentType",
            "name",
            "title",
            "aliases",
            "description",
            "urls",
            "doi",
            "pmid",
            "agent_id",
            "company",
            "drug_name_brand",
            "drug_name_generic",
            "first_publication_date",
            "identification_number",
            "publication_date",
            "status",
        ),
        lists={
            "urls": ListField(
                association=models.AssociationDocumentsAndURLs,
                owner="document_id",
                target="url_id",
            ),
        },
    ),
    "indications": TableSpec(
        model=models.Indications,
        keys=(
            "id",
            "type",
            "description",
            "contributions",
            "reportedIn",
            "status",
            "statement_description",
            "raw_biomarkers",
            "raw_cancer_types",
            "raw_therapeutics",
            "superseded_by",
            "reimbursement_scheme",
            "reimbursement_comment",
        ),
        lists={
            "contributions": ListField(
                association=models.AssociationContributionsAndIndications,
                owner="indication_id",
                target="contribution_id",
            ),
            "reportedIn": ListField(
                association=models.AssociationDocumentsAndIndications,
                owner="indication_id",
                target="document_id",
            ),
            "superseded_by": ListField(
                association=models.AssociationIndicationsAndSupersededBy,
                owner="indication_id",
                target="superseded_by_id",
            ),
        },
        omit={
            "reimbursement_scheme": _is_not_hse,
            "reimbursement_comment": _is_not_hse,
        },
    ),
    "propositions": TableSpec(
        model=models.Propositions,
        keys=(
            "id",
            "type",
            "predicate",
            "biomarker_criteria",
            "conditionQualifier_id",
            "therapy_id",
            "therapy_group_id",
        ),
        lists={
            "biomarker_criteria": ListField(
                association=models.AssociationBiomarkerCriteriaAndPropositions,
                owner="proposition_id",
                target="biomarker_criterion_id",
            ),
        },
    ),
    "strengths": TableSpec(
        model=models.Strengths,
        keys=("id", "conceptType", "name", "primary_coding_id", "mappings"),
        lists={
            "mappings": _mappings(
                models.AssociationMappingsAndStrengths,
                "strength_id",
            ),
        },
    ),
    "statements": TableSpec(
        model=models.Statements,
        keys=(
            "id",
            "type",
            "description",
            "contributions",
            "reportedIn",
            "proposition_id",
            "direction",
            "strength_id",
            "status",
            "indication_id",
        ),
        lists={
            "contributions": ListField(
                association=models.AssociationContributionsAndStatements,
                owner="statement_id",
                target="contribution_id",
            ),
            "reportedIn": ListField(
                association=models.AssociationDocumentsAndStatements,
                owner="statement_id",
                target="document_id",
            ),
        },
    ),
}

ABOUT_KEYS = ("github", "name", "license", "release", "url", "last_updated")


def _from_json(column: sqlalchemy.Column, value: typing.Any) -> typing.Any:
    """
    Converts a JSON value to the Python value stored in column.

    Args:
        column (sqlalchemy.Column): The destination column.
        value (typing.Any): The JSON value.

    Returns:
        typing.Any: A datetime.date for date columns, otherwise value unchanged.

    Raises:
        ValueError: If a date column's value is not an ISO 8601 (YYYY-MM-DD) string.
    """
    if value is not None and isinstance(column.type, sqlalchemy.Date):
        return datetime.date.fromisoformat(value)
    return value


def _to_json(value: typing.Any) -> typing.Any:
    """
    Converts a stored column value back to its JSON value.

    Args:
        value (typing.Any): The value read from the database.

    Returns:
        typing.Any: An ISO 8601 string for dates, otherwise value unchanged.
    """
    if isinstance(value, datetime.date):
        return value.isoformat()
    return value


def about_to_row(record: dict) -> dict:
    """
    Converts the referenced about record to an About row.

    Args:
        record (dict): The record from referenced/about.json.

    Returns:
        dict: Column values for models.About, with the fixed id 0.
    """
    table = models.About.__table__
    row = {key: _from_json(table.c[key], record[key]) for key in ABOUT_KEYS}
    row["id"] = 0
    return row


def records_to_rows(
    name: str,
    records: list[dict],
) -> tuple[list[dict], dict[type[models.Base], list[dict]]]:
    """
    Converts referenced records into rows for the entity table and its association
    (and extension) tables.

    Args:
        name (str): The referenced table name, a key of TABLES.
        records (list[dict]): The records from referenced/<name>.json, in file order.

    Returns:
        tuple[list[dict], dict[type[models.Base], list[dict]]]: Entity rows in file
        order, and rows for each association or extension model.

    Raises:
        KeyError: If a record has a key the spec does not know, or lacks one it
            requires.
    """
    spec = TABLES[name]
    columns = spec.columns
    known = set(spec.keys)
    rows = []
    children: dict[type[models.Base], list[dict]] = {
        field.association: [] for field in spec.lists.values()
    }
    if spec.extensions:
        children[models.BiomarkerExtensions] = []

    for record in records:
        unknown = set(record) - known
        if unknown:
            raise KeyError(f"{name} {record.get('id')}: unknown keys {sorted(unknown)}")
        missing = known - set(record) - set(spec.omit)
        if missing:
            raise KeyError(f"{name} {record.get('id')}: missing keys {sorted(missing)}")

        rows.append(
            {
                column.key: _from_json(column, record.get(key))
                for key, column in columns.items()
            },
        )
        for key, field in spec.lists.items():
            children[field.association].extend(
                {field.owner: record["id"], field.target: value, "position": position}
                for position, value in enumerate(record[key])
            )
        if spec.extensions:
            children[models.BiomarkerExtensions].extend(
                {
                    "biomarker_id": record["id"],
                    "position": position,
                    "name": extension["name"],
                    "value": extension["value"],
                    "description": extension.get("description"),
                }
                for position, extension in enumerate(record["extensions"])
            )
    return rows, children


def _load_lists(
    session: sqlalchemy.orm.Session,
    field: ListField,
) -> dict[str, list[str]]:
    """
    Reads an association table into ordered lists keyed by owner id.

    Args:
        session (sqlalchemy.orm.Session): The database session.
        field (ListField): The array-valued field.

    Returns:
        dict[str, list[str]]: Item ids for each owner, in array order.
    """
    owner = getattr(field.association, field.owner)
    target = getattr(field.association, field.target)
    statement = sqlalchemy.select(owner, target).order_by(
        owner,
        field.association.position,
    )
    lists: dict[str, list[str]] = {}
    for owner_id, target_id in session.execute(statement):
        lists.setdefault(owner_id, []).append(target_id)
    return lists


def _load_extensions(session: sqlalchemy.orm.Session) -> dict[str, list[dict]]:
    """
    Reads biomarker_extensions into ordered extension lists keyed by biomarker id.

    Args:
        session (sqlalchemy.orm.Session): The database session.

    Returns:
        dict[str, list[dict]]: Extensions for each biomarker, in array order.
    """
    model = models.BiomarkerExtensions
    statement = sqlalchemy.select(model).order_by(model.biomarker_id, model.position)
    extensions: dict[str, list[dict]] = {}
    for row in session.scalars(statement):
        extension = {"name": row.name, "value": row.value}
        if row.description is not None:
            extension["description"] = row.description
        extensions.setdefault(row.biomarker_id, []).append(extension)
    return extensions


def load_table(session: sqlalchemy.orm.Session, name: str) -> list[dict]:
    """
    Rebuilds one referenced table from the database.

    Records come back in insertion (rowid) order, which is file order, with keys in
    file order and optional keys omitted as in the source.

    Args:
        session (sqlalchemy.orm.Session): The database session.
        name (str): The referenced table name, a key of TABLES.

    Returns:
        list[dict]: The table's records, equal to referenced/<name>.json.
    """
    spec = TABLES[name]
    columns = spec.columns
    lists = {key: _load_lists(session, field) for key, field in spec.lists.items()}
    extensions = _load_extensions(session) if spec.extensions else {}

    table = spec.model.__table__
    statement = sqlalchemy.select(table).order_by(sqlalchemy.literal_column("rowid"))
    records = []
    for row in session.execute(statement):
        mapping = row._mapping
        record_id = mapping[table.c.id]
        record = {}
        for key in spec.keys:
            if key in columns:
                record[key] = _to_json(mapping[columns[key]])
            elif key in lists:
                record[key] = lists[key].get(record_id, [])
            else:
                record[key] = extensions.get(record_id, [])
        for key, predicate in spec.omit.items():
            if predicate(record):
                del record[key]
        records.append(record)
    return records


def load_about(session: sqlalchemy.orm.Session) -> dict:
    """
    Rebuilds the referenced about record from the database.

    Args:
        session (sqlalchemy.orm.Session): The database session.

    Returns:
        dict: The about record, equal to referenced/about.json.
    """
    about = session.get(models.About, 0)
    return {key: _to_json(getattr(about, key)) for key in ABOUT_KEYS}


def load_referenced(session: sqlalchemy.orm.Session) -> dict[str, list[dict] | dict]:
    """
    Rebuilds every referenced table from the database.

    Args:
        session (sqlalchemy.orm.Session): The database session.

    Returns:
        dict[str, list[dict] | dict]: Records for each table in TABLES, plus the
        `about` record, each equal to the matching referenced/*.json file.
    """
    referenced: dict[str, list[dict] | dict] = {"about": load_about(session)}
    for name in TABLES:
        referenced[name] = load_table(session, name)
    return referenced
