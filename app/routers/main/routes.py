import datetime
import time
import typing
import uuid

import fastapi
import sqlalchemy

from app import database, referenced

from . import handlers

router = fastapi.APIRouter()


def generate_datetime_now() -> datetime.datetime:
    """
    Returns the current datetime in UTC.

    Returns:
        datetime.datetime: The current UTC datetime.
    """
    return datetime.datetime.now(datetime.timezone.utc)


def get_session_factory(
    request: fastapi.Request,
) -> sqlalchemy.orm.sessionmaker[sqlalchemy.orm.Session]:
    """
    Returns the SQLAlchemy session factory attached to the application state.

    Args:
        request (fastapi.Request): The current FastAPI request, used to access
            application state.

    Returns:
        sqlalchemy.orm.sessionmaker[sqlalchemy.orm.Session]: The configured session
        factory for the application.
    """
    return typing.cast(
        sqlalchemy.orm.sessionmaker[sqlalchemy.orm.Session],
        request.app.state.session_factory,
    )


def get_db(
    session_factory: sqlalchemy.orm.sessionmaker[
        sqlalchemy.orm.Session
    ] = fastapi.Depends(get_session_factory),
) -> typing.Generator[sqlalchemy.orm.Session, None, None]:
    """
    FastAPI dependency that yields a database session.

    Args:
        session_factory (sqlalchemy.orm.sessionmaker[sqlalchemy.orm.Session]):
            The session factory resolved via FastAPI dependency injection.

    Returns:
        typing.Generator[sqlalchemy.orm.Session, None, None]: A generator that
        yields a single database session and closes it on exit.
    """
    yield from database.get_database(session=session_factory)


def create_response(
    *,
    data: typing.Any,
    message: str = "",
    received: datetime.datetime | None = None,
    request_url: str | None = None,
    status_code: int = 200,
    service: dict | None = None,
) -> dict:
    """
    Builds the standard API response envelope of meta, service, and data.

    Computes the elapsed time from `received` until now, derives a status string
    from the HTTP status code, and assigns a fresh trace id.

    Args:
        data (typing.Any): The payload to return under the `data` key.
        message (str): A human-readable status message.
        received (datetime.datetime | None): The time the request was received;
            defaults to now in UTC.
        request_url (str | None): The full URL of the originating request.
        status_code (int): The HTTP status code (default: 200).
        service (dict | None): Service metadata to attach under the `service` key.

    Returns:
        dict: A dictionary with `meta`, `service`, and `data` keys.
    """
    if received is None:
        received = generate_datetime_now()

    returned = generate_datetime_now()
    elapsed = returned - received

    meta = {
        "data_length": len(data) if hasattr(data, "__len__") else 1,
        "message": message,
        "request_url": request_url,
        "status": "success" if 200 <= status_code < 300 else "error",
        "status_code": status_code,
        "timestamp_elapsed": round(elapsed.total_seconds(), 6),
        "timestamp_received": f"{received.isoformat()}Z" if received else None,
        "timestamp_returned": f"{returned.isoformat()}Z",
        "trace_id": str(uuid.uuid4()),
    }
    return {
        "meta": meta,
        "service": service,
        "data": data,
    }


def get_service_metadata(database: sqlalchemy.orm.Session) -> dict:
    """
    Retrieves the About record from the database.

    Args:
        database (sqlalchemy.orm.Session): The database session to query against.

    Returns:
        dict: The About record, matching moalmanac-db's referenced/about.json.
    """
    return referenced.load_about(session=database)


_service_cache: dict[str, tuple[float, dict]] = {}


def get_service_metadata_cached(
    database: sqlalchemy.orm.Session,
    ttl: int = 300,
) -> dict:
    """
    Returns the About metadata using a process-local cache with a TTL.

    On a miss or expiry, queries the database and refreshes the cached value.

    Args:
        database (sqlalchemy.orm.Session): The database session to query against.
        ttl (int): The cache time-to-live in seconds (default: 300).

    Returns:
        dict: The About record.
    """
    now = time.time()
    hit = _service_cache.get("about")
    if hit and now - hit[0] < ttl:
        return hit[1]

    value = get_service_metadata(database=database)
    _service_cache["about"] = (now, value)
    return value


def list_entities(
    *,
    request: fastapi.Request,
    database: sqlalchemy.orm.Session,
    handler: type[handlers.BaseHandler],
    received: datetime.datetime,
    message_subject: str,
    primary_filter: sqlalchemy.ColumnElement | None = None,
) -> dict:
    """
    Runs the common list-endpoint pipeline for one entity: filter, join, query,
    and look up the matching records in the dereferenced cache.

    Args:
        request (fastapi.Request): The current request, used for query parameters,
            the request URL, and the application's dereferenced cache.
        database (sqlalchemy.orm.Session): The database session to query against.
        handler (type[handlers.BaseHandler]): The entity's handler class.
        received (datetime.datetime): When the request was received.
        message_subject (str): The subject noun for the response message, e.g.
            "Agents" or "Agent name BRAF".
        primary_filter (sqlalchemy.ColumnElement | None): An optional exact-match
            condition from the route's own declared query parameter (e.g.
            `models.Agents.id == agent_id`).

    Returns:
        dict: The response envelope from `create_response`.
    """
    statement = handler.construct_base_query()
    if primary_filter is not None:
        statement = statement.where(primary_filter)

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, _joined_tables = handler.perform_joins(
        statement=statement,
        parameters=parameters,
    )

    ids = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize(ids=ids, cache=request.app.state.dereferenced)

    service = get_service_metadata_cached(database=database)
    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/about", tags=["Service Info"])
def get_about(
    request: fastapi.Request,
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves service metadata from the About table in the database.
    """
    received = generate_datetime_now()
    service = get_service_metadata_cached(database=database)
    return create_response(
        data=service,
        message="About metadata retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/agents", tags=["Entities"])
def get_agents(
    request: fastapi.Request,
    agent_name: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Agents from the database. Filters by agent_name, agent_id, and
    agent_type.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.Agents,
        received=generate_datetime_now(),
        message_subject=f"Agent name {agent_name}" if agent_name else "Agents",
        primary_filter=(
            handlers.Agents.model.name == agent_name if agent_name else None
        ),
    )


@router.get("/alleles", tags=["Entities"])
def get_alleles(
    request: fastapi.Request,
    allele_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Alleles from the database.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.Alleles,
        received=generate_datetime_now(),
        message_subject=f"Allele id {allele_id}" if allele_id else "Alleles",
        primary_filter=(handlers.Alleles.model.id == allele_id if allele_id else None),
    )


@router.get("/biomarkers", tags=["Entities"])
def get_biomarkers(
    request: fastapi.Request,
    biomarker_name: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Biomarkers from the database. Filters by biomarker_name,
    biomarker_type, and gene.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.Biomarkers,
        received=generate_datetime_now(),
        message_subject=(
            f"Biomarker name {biomarker_name}" if biomarker_name else "Biomarkers"
        ),
        primary_filter=(
            handlers.Biomarkers.model.name == biomarker_name if biomarker_name else None
        ),
    )


@router.get("/biomarker_criteria", tags=["Entities"])
def get_biomarker_criteria(
    request: fastapi.Request,
    biomarker_criterion_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Biomarker Criteria from the database.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.BiomarkerCriteria,
        received=generate_datetime_now(),
        message_subject=(
            f"Biomarker criterion id {biomarker_criterion_id}"
            if biomarker_criterion_id
            else "Biomarker criteria"
        ),
        primary_filter=(
            handlers.BiomarkerCriteria.model.id == biomarker_criterion_id
            if biomarker_criterion_id
            else None
        ),
    )


@router.get("/codings", tags=["Entities"])
def get_codings(
    request: fastapi.Request,
    coding_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Codings from the database. Codings are representations of a concept
    from another website.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.Codings,
        received=generate_datetime_now(),
        message_subject=f"Coding id {coding_id}" if coding_id else "Codings",
        primary_filter=(handlers.Codings.model.id == coding_id if coding_id else None),
    )


@router.get("/contributions", tags=["Entities"])
def get_contributions(
    request: fastapi.Request,
    contribution_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Contributions from the database. Filters by contribution_id, agent,
    and agent_id.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.Contributions,
        received=generate_datetime_now(),
        message_subject=(
            f"Contribution id {contribution_id}" if contribution_id else "Contributions"
        ),
        primary_filter=(
            handlers.Contributions.model.id == contribution_id
            if contribution_id
            else None
        ),
    )


@router.get("/copy_changes", tags=["Entities"])
def get_copy_changes(
    request: fastapi.Request,
    copy_change_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Copy Changes from the database.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.CopyChanges,
        received=generate_datetime_now(),
        message_subject=(
            f"Copy change id {copy_change_id}" if copy_change_id else "Copy changes"
        ),
        primary_filter=(
            handlers.CopyChanges.model.id == copy_change_id if copy_change_id else None
        ),
    )


@router.get("/diseases", tags=["Entities"])
def get_diseases(
    request: fastapi.Request,
    disease_name: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Diseases from the database.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.Diseases,
        received=generate_datetime_now(),
        message_subject=f"Disease name {disease_name}" if disease_name else "Diseases",
        primary_filter=(
            handlers.Diseases.model.name == disease_name if disease_name else None
        ),
    )


@router.get("/documents", tags=["Entities"])
def get_documents(
    request: fastapi.Request,
    document_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Documents from the database. Filters by document_id, agent, and
    agent_id. Only Active documents are returned.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.Documents,
        received=generate_datetime_now(),
        message_subject=f"Document id {document_id}" if document_id else "Documents",
        primary_filter=(
            handlers.Documents.model.id == document_id if document_id else None
        ),
    )


@router.get("/function_consequences", tags=["Entities"])
def get_function_consequences(
    request: fastapi.Request,
    function_consequence_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Function Consequences from the database.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.FunctionConsequences,
        received=generate_datetime_now(),
        message_subject=(
            f"Function consequence id {function_consequence_id}"
            if function_consequence_id
            else "Function consequences"
        ),
        primary_filter=(
            handlers.FunctionConsequences.model.id == function_consequence_id
            if function_consequence_id
            else None
        ),
    )


@router.get("/genes", tags=["Entities"])
def get_genes(
    request: fastapi.Request,
    gene_name: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Genes from the database.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.Genes,
        received=generate_datetime_now(),
        message_subject=f"Gene name {gene_name}" if gene_name else "Genes",
        primary_filter=(handlers.Genes.model.name == gene_name if gene_name else None),
    )


@router.get("/indications", tags=["Entities"])
def get_indications(
    request: fastapi.Request,
    indication_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Indications (regulatory approvals) from the database. Filters by
    indication_id, document, agent, and agent_id. Only Approved and Accelerated
    indications are returned.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.Indications,
        received=generate_datetime_now(),
        message_subject=(
            f"Indication id {indication_id}" if indication_id else "Indications"
        ),
        primary_filter=(
            handlers.Indications.model.id == indication_id if indication_id else None
        ),
    )


@router.get("/mappings", tags=["Entities"])
def get_mappings(
    request: fastapi.Request,
    mapping_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Mappings from the database. Mappings are relationships between two Codings.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.Mappings,
        received=generate_datetime_now(),
        message_subject=f"Mapping id {mapping_id}" if mapping_id else "Mappings",
        primary_filter=(
            handlers.Mappings.model.id == mapping_id if mapping_id else None
        ),
    )


@router.get("/propositions", tags=["Entities"])
def get_propositions(
    request: fastapi.Request,
    proposition_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Propositions from the database. Filters by proposition_id,
    biomarker, biomarker_type, gene, disease, therapy, and therapy_type.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.Propositions,
        received=generate_datetime_now(),
        message_subject=(
            f"Proposition id {proposition_id}" if proposition_id else "Propositions"
        ),
        primary_filter=(
            handlers.Propositions.model.id == proposition_id if proposition_id else None
        ),
    )


@router.get("/search", tags=["Search"])
def get_search(
    request: fastapi.Request,
    proposition_id: str | None = fastapi.Query(default=None),
    include_empty: bool = fastapi.Query(default=False),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Searches Propositions, with aggregated Statement information attached to each.
    Which propositions are returned is filtered the same way as /propositions
    (proposition_id, biomarker, biomarker_type, gene, disease, therapy,
    therapy_type). document, indication, and agent_id instead narrow each
    proposition's Statement aggregates, without changing which propositions are
    returned; those aggregates only count Active statements. include_empty=true
    also returns propositions with zero matching statements.
    """
    received = generate_datetime_now()
    handler = handlers.Searches
    statement = handler.construct_base_query()
    if proposition_id:
        statement = statement.where(handler.model.id == proposition_id)
        message_subject = (
            f"Search results by Proposition where proposition id {proposition_id}"
        )
    else:
        message_subject = "Search results by Proposition"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, _joined_tables = handler.perform_joins(
        statement=statement,
        parameters=parameters,
    )

    ids = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize(
        ids=ids,
        cache=request.app.state.dereferenced,
        session=database,
        parameters=parameters,
    )
    if not include_empty:
        serialized = [
            proposition
            for proposition in serialized
            if proposition["aggregates"]["statement_count"] > 0
        ]
    suffix = "" if not include_empty else " (including zero-statement propositions)"

    service = get_service_metadata_cached(database=database)
    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully{suffix}",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/sequence_locations", tags=["Entities"])
def get_sequence_locations(
    request: fastapi.Request,
    sequence_location_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Sequence Locations from the database.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.SequenceLocations,
        received=generate_datetime_now(),
        message_subject=(
            f"Sequence location id {sequence_location_id}"
            if sequence_location_id
            else "Sequence locations"
        ),
        primary_filter=(
            handlers.SequenceLocations.model.id == sequence_location_id
            if sequence_location_id
            else None
        ),
    )


@router.get("/sequence_references", tags=["Entities"])
def get_sequence_references(
    request: fastapi.Request,
    sequence_reference_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Sequence References from the database.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.SequenceReferences,
        received=generate_datetime_now(),
        message_subject=(
            f"Sequence reference id {sequence_reference_id}"
            if sequence_reference_id
            else "Sequence references"
        ),
        primary_filter=(
            handlers.SequenceReferences.model.id == sequence_reference_id
            if sequence_reference_id
            else None
        ),
    )


@router.get("/statements", tags=["Entities"])
def get_statements(
    request: fastapi.Request,
    statement_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Statements from the database. This endpoint essentially fetches the
    entire database, and will take several seconds to complete. Filters by
    statement_id, proposition_id, biomarker, biomarker_type, gene, disease,
    therapy, therapy_type, document, agent, agent_id, indication, and
    contribution. Only Active statements are returned.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.Statements,
        received=generate_datetime_now(),
        message_subject=f"Statement id {statement_id}"
        if statement_id
        else "Statements",
        primary_filter=(
            handlers.Statements.model.id == statement_id if statement_id else None
        ),
    )


@router.get("/strengths", tags=["Entities"])
def get_strengths(
    request: fastapi.Request,
    strength_name: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Strengths from the database.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.Strengths,
        received=generate_datetime_now(),
        message_subject=(
            f"Strength name {strength_name}" if strength_name else "Strengths"
        ),
        primary_filter=(
            handlers.Strengths.model.name == strength_name if strength_name else None
        ),
    )


@router.get("/therapies", tags=["Entities"])
def get_therapies(
    request: fastapi.Request,
    therapy_name: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Therapies from the database. Filters by therapy_name and
    therapy_type.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.Therapies,
        received=generate_datetime_now(),
        message_subject=f"Therapy name {therapy_name}" if therapy_name else "Therapies",
        primary_filter=(
            handlers.Therapies.model.name == therapy_name if therapy_name else None
        ),
    )


@router.get("/therapy_groups", tags=["Entities"])
def get_therapy_groups(
    request: fastapi.Request,
    therapy_group_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Therapy Groups from the database.
    """
    return list_entities(
        request=request,
        database=database,
        handler=handlers.TherapyGroups,
        received=generate_datetime_now(),
        message_subject=(
            f"Therapy group id {therapy_group_id}"
            if therapy_group_id
            else "Therapy groups"
        ),
        primary_filter=(
            handlers.TherapyGroups.model.id == therapy_group_id
            if therapy_group_id
            else None
        ),
    )
