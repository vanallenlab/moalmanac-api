import datetime
import fastapi
import sqlalchemy
import time
import typing
import uuid

from app import database
from app import models
from . import handlers

router = fastapi.APIRouter()


def generate_datetime_now() -> datetime.datetime:
    """
    Generates current datetime in UTC timezone.
    """
    return datetime.datetime.now(datetime.timezone.utc)


def get_session_factory(
    request: fastapi.Request,
) -> sqlalchemy.orm.sessionmaker[sqlalchemy.orm.Session]:
    """ """
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
    Dependency that provides a database session.
    """
    yield from database.get_database(session=session_factory)


def create_response(
    *,
    data,
    message: str = "",
    received: datetime.datetime | None = None,
    request_url: str | None = None,
    status_code: int = 200,
    service: dict | None = None,
) -> dict:
    """ """
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
        "trace_id": str(uuid.uuid4())
        
    }
    return {
        "meta": meta,
        "service": service,
        "data": data,
    }


def get_service_metadata(database: sqlalchemy.orm.Session) -> dict:
    handler = handlers.About()
    statement = handler.construct_base_query(model=models.About)
    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)
    return serialized[0]


_service_cache: dict[str, tuple[float, dict]] = {}
def get_service_metadata_cached(database: sqlalchemy.orm.Session, ttl: int = 300) -> dict:
    now = time.time()
    hit = _service_cache.get("about")
    if hit and now - hit[0] < ttl:
        return hit[1]
    
    value = get_service_metadata(database=database)
    _service_cache["about"] = (now, value)
    return value


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
    Retrieves Agents table from database.
    """
    received = generate_datetime_now()
    handler = handlers.Agents()
    statement = handler.construct_base_query(model=models.Agents)
    if agent_name:
        statement = statement.where(models.Agents.name == agent_name)

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(
        statement=statement, parameters=parameters
    )

    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)

    service = get_service_metadata_cached(database=database)

    return create_response(
        data=serialized,
        message=f"Agents retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/biomarkers", tags=["Entities"])
def get_biomarkers(
    request: fastapi.Request,
    biomarker_name: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Biomarkers table from database.
    """
    received = generate_datetime_now()
    handler = handlers.Biomarkers()
    statement = handler.construct_base_query(model=models.Biomarkers)
    if biomarker_name:
        statement = statement.where(models.Biomarkers.name == biomarker_name)
        message_subject = f"Biomarker id {biomarker_name}"
    else:
        message_subject = "Biomarkers"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(
        statement=statement, parameters=parameters
    )

    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)

    service = get_service_metadata_cached(database=database)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/codings", tags=["Entities"])
def get_codings(
    request: fastapi.Request,
    coding_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Codings table from the database. Codings are representations of a concept from another website.
    """
    received = generate_datetime_now()
    handler = handlers.Codings()
    statement = handler.construct_base_query(model=models.Codings)
    if coding_id:
        statement = statement.where(models.Codings.id == coding_id)
        message_subject = f"Coding id {coding_id}"
    else:
        message_subject = "Codings"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(
        statement=statement, parameters=parameters
    )

    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)

    service = get_service_metadata_cached(database=database)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/contributions", tags=["Entities"])
def get_contributions(
    request: fastapi.Request,
    contribution_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Contributions table from the database.
    """
    received = generate_datetime_now()
    handler = handlers.Contributions()
    statement = handler.construct_base_query(model=models.Contributions)
    if contribution_id:
        statement = statement.where(models.Contributions.id == contribution_id)
        message_subject = f"Contribution id {contribution_id}"
    else:
        message_subject = "Contributions"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(
        statement=statement, parameters=parameters
    )

    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)

    service = get_service_metadata_cached(database=database)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/diseases", tags=["Entities"])
def get_diseases(
    request: fastapi.Request,
    disease_name: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Diseases table from the database.
    """
    received = generate_datetime_now()
    handler = handlers.Diseases()
    statement = handler.construct_base_query(model=models.Diseases)
    if disease_name:
        statement = statement.where(models.Diseases.name == disease_name)
        message_subject = f"Disease name {disease_name}"
    else:
        message_subject = "Diseases"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(
        statement=statement, parameters=parameters
    )

    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)

    service = get_service_metadata_cached(database=database)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/documents", tags=["Entities"])
def get_documents(
    request: fastapi.Request,
    document_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Documents table from the database.
    """
    received = generate_datetime_now()
    handler = handlers.Documents()
    statement = handler.construct_base_query(model=models.Documents)
    if document_id:
        statement = statement.where(models.Documents.id == document_id)
        message_subject = f"Document id {document_id}"
    else:
        message_subject = "Documents"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(
        statement=statement, parameters=parameters
    )

    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)

    service = get_service_metadata_cached(database=database)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/genes", tags=["Entities"])
def get_genes(
    request: fastapi.Request,
    gene_name: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Genes table from the database.
    """
    received = generate_datetime_now()
    handler = handlers.Genes()
    statement = handler.construct_base_query(model=models.Genes)
    if gene_name:
        statement = statement.where(models.Genes.name == gene_name)
        message_subject = f"Gene name {gene_name}"
    else:
        message_subject = "Genes"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(
        statement=statement, parameters=parameters
    )

    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)

    service = get_service_metadata_cached(database=database)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/indications", tags=["Entities"])
def get_indications(
    request: fastapi.Request,
    indication_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Indications (Regulatory approvals) table from the database.
    """
    received = generate_datetime_now()
    handler = handlers.Indications()
    statement = handler.construct_base_query(model=models.Indications)
    if indication_id:
        statement = statement.where(models.Indications.id == indication_id)
        message_subject = f"Indication id {indication_id}"
    else:
        message_subject = "Indications"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(
        statement=statement, parameters=parameters
    )

    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)

    service = get_service_metadata_cached(database=database)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/mappings", tags=["Entities"])
def get_mappings(
    request: fastapi.Request,
    mapping_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Mappings table from the database. Mappings are relationships between two Codings.
    """
    received = generate_datetime_now()
    handler = handlers.Mappings()
    statement = handler.construct_base_query(model=models.Mappings)
    if mapping_id:
        statement = statement.where(models.Mappings.id == mapping_id)
        message_subject = f"Mapping id {mapping_id}"
    else:
        message_subject = "Mappings"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(
        statement=statement, parameters=parameters
    )

    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)

    service = get_service_metadata_cached(database=database)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/organizations", tags=["Entities"])
def get_organizations(
    request: fastapi.Request,
    organization_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves Organization table from the database.
    """
    received = generate_datetime_now()
    handler = handlers.Organizations()
    statement = handler.construct_base_query(model=models.Organizations)
    if organization_id:
        statement = statement.where(models.Organizations.id == organization_id)
        message_subject = f"Organization {organization_id}"
    else:
        message_subject = "Organizations"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(
        statement=statement, parameters=parameters
    )

    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)

    service = get_service_metadata_cached(database=database)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/propositions", tags=["Entities"])
def get_propositions(
    request: fastapi.Request,
    proposition_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Retrieves the Propositions table from the database.
    """
    received = generate_datetime_now()
    handler = handlers.Propositions()
    statement = handler.construct_base_query(model=models.Propositions)
    if proposition_id:
        statement = statement.where(models.Propositions.id == proposition_id)
        message_subject = f"Proposition id {proposition_id}"
    else:
        message_subject = "Propositions"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(
        statement=statement, parameters=parameters
    )

    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)

    service = get_service_metadata_cached(database=database)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/statements", tags=["Entities"])
def get_statements(
    request: fastapi.Request,
    statement_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Gets the Statements table from the database. This endpoint essentially fetches the entire database, and will take
    several seconds to complete.
    """
    received = generate_datetime_now()
    handler = handlers.Statements()
    statement = handler.construct_base_query(model=models.Statements)
    if statement_id:
        statement = statement.where(models.Statements.id == statement_id)
        message_subject = f"Statement id {statement_id}"
    else:
        message_subject = "Statements"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(
        statement=statement, parameters=parameters
    )
    # statement = handler.apply_joinedload(statement=statement)
    # statement = handler.apply_filters(statement=statement, parameters=parameters)

    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)

    service = get_service_metadata_cached(database=database)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/strengths", tags=["Entities"])
def get_strengths(
    request: fastapi.Request,
    strength_name: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Gets the Strengths table from the database.
    """
    received = generate_datetime_now()
    handler = handlers.Strengths()
    statement = handler.construct_base_query(model=models.Strengths)
    if strength_name:
        statement = statement.where(models.Strengths.name == strength_name)
        message_subject = f"Strength name {strength_name}"
    else:
        message_subject = "Strengths"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(
        statement=statement, parameters=parameters
    )

    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)

    service = get_service_metadata_cached(database=database)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/therapies", tags=["Entities"])
def get_therapies(
    request: fastapi.Request,
    therapy_name: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Get the Therapies table from the database.
    """
    received = generate_datetime_now()
    handler = handlers.Therapies()
    statement = handler.construct_base_query(model=models.Therapies)
    if therapy_name:
        statement = statement.where(models.Therapies.name == therapy_name)
        message_subject = f"Therapy name {therapy_name}"
    else:
        message_subject = "Therapies"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(
        statement=statement, parameters=parameters
    )

    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)

    service = get_service_metadata_cached(database=database)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )


@router.get("/therapygroups", tags=["Entities"])
def get_therapy_groups(
    request: fastapi.Request,
    therapy_group_id: str = fastapi.Query(default=None),
    database: sqlalchemy.orm.Session = fastapi.Depends(get_db),
):
    """
    Gets the Therapy Groups table from the database.
    """
    received = generate_datetime_now()
    handler = handlers.TherapyGroups()
    statement = handler.construct_base_query(model=models.TherapyGroups)
    if therapy_group_id:
        statement = statement.where(
            models.TherapyGroups.id == therapy_group_id
        )
        message_subject = f"Therapy group id {therapy_group_id}"
    else:
        message_subject = "Therapy groups"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(
        statement=statement, parameters=parameters
    )

    result = handler.execute_query(session=database, statement=statement)
    serialized = handler.serialize_instances(instances=result)

    service = get_service_metadata_cached(database=database)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        status_code=200,
        service=service,
    )
