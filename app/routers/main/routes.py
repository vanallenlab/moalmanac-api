import datetime
import fastapi
import sqlalchemy
import typing
import uuid

from app import models
from . import handlers

router = fastapi.APIRouter()


def get_session_factory(request: fastapi.Request):
    return request.app.state.session_factory


def create_response(
        data,
        session,
        message="",
        received=None,
        request_url=None,
        status_code=200,
):
    """
    """
    if received is None:
        received = generate_datetime_now()

    timestamp_returned = generate_datetime_now()
    elapsed = timestamp_returned - received
    meta = {
        "message": message,
        "request_url": request_url if request_url else None,
        "status": "success" if 200 <= status_code < 300 else "error",
        "status_code": status_code,
        "timestamp_elapsed": round(elapsed.total_seconds(), 6),
        "timestamp_received": f"{received.isoformat()}Z" if received else None,
        "timestamp_returned": f"{timestamp_returned.isoformat()}Z",
        "trace_id": str(uuid.uuid4()),
        "data_length": len(data) if hasattr(data, '__len__') else 1,
    }
    return {
        "meta": meta,
        "service": get_service_metadata(session=session),
        "data": data
    }


def get_service_metadata(session) -> dict:
    handler = handlers.About()
    statement = handler.construct_base_query(model=models.About)
    result = handler.execute_query(session=session, statement=statement)
    serialized = handler.serialize_instances(instances=result)
    return serialized[0]


def generate_datetime_now():
    return datetime.datetime.now(datetime.timezone.utc)


@router.get("/about", tags=["Service Info"])
def get_about(
        request: fastapi.Request,
        session_factory=fastapi.Depends(get_session_factory)
):
    """
    Gets service information from the About table.
    """
    with session_factory() as session:
        result = get_service_metadata(session=session)
        return create_response(
            data=result,
            message="About metadata retrieved successfully",
            received=generate_datetime_now(),
            request_url=str(request.url),
            session=session,
            status_code=200
        )


@router.get("/agents", tags=["Entities"])
def get_agents(
        request: fastapi.Request,
        agent_name: str = fastapi.Query(default=None),
        session_factory=fastapi.Depends(get_session_factory)
):
    """

    """
    received = generate_datetime_now()
    handler = handlers.Agents()
    statement = handler.construct_base_query(model=models.Agents)
    if agent_name:
        statement = statement.where(models.Agents.name == agent_name)

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)

    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

        return create_response(
            data=serialized,
            message=f"Agents retrieved successfully",
            received=received,
            request_url=str(request.url),
            session=session,
            status_code=200
        )


@router.get("/biomarkers", tags=["Entities"])
def get_biomarkers(
        request: fastapi.Request,
        biomarker_name: str = fastapi.Query(default=None),
        session_factory=fastapi.Depends(get_session_factory)
):
    received = generate_datetime_now()
    handler = handlers.Biomarkers()
    statement = handler.construct_base_query(model=models.Biomarkers)
    if biomarker_name:
        statement = statement.where(models.Biomarkers.name == biomarker_name)
        message_subject = f"Biomarker id {biomarker_name}"
    else:
        message_subject = "Biomarkers"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)

    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

        return create_response(
            data=serialized,
            message=f"{message_subject} retrieved successfully",
            received=received,
            request_url=str(request.url),
            session=session,
            status_code=200
        )


@router.get("/codings", tags=["Entities"])
def get_codings(
        request: fastapi.Request,
        coding_id: str = fastapi.Query(default=None),
        session_factory=fastapi.Depends(get_session_factory)
):
    received = generate_datetime_now()
    handler = handlers.Codings()
    statement = handler.construct_base_query(model=models.Codings)
    if coding_id:
        statement = statement.where(models.Codings.id == coding_id)
        message_subject = f"Coding id {coding_id}"
    else:
        message_subject = "Codings"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)

    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

        return create_response(
            data=serialized,
            message=f"{message_subject} retrieved successfully",
            received=received,
            request_url=str(request.url),
            session=session,
            status_code=200
        )


@router.get("/contributions", tags=["Entities"])
def get_contributions(
        request: fastapi.Request,
        contribution_id: str = fastapi.Query(default=None),
        session_factory=fastapi.Depends(get_session_factory)
):
    received = generate_datetime_now()
    handler = handlers.Contributions()
    statement = handler.construct_base_query(model=models.Contributions)
    if contribution_id:
        statement = statement.where(models.Contributions.id == contribution_id)
        message_subject = f"Contribution id {contribution_id}"
    else:
        message_subject = "Contributions"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)

    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

        return create_response(
            data=serialized,
            message=f"{message_subject} retrieved successfully",
            received=received,
            request_url=str(request.url),
            session=session,
            status_code=200
        )


@router.get("/diseases", tags=["Entities"])
def get_diseases(
        request: fastapi.Request,
        disease_name: str = fastapi.Query(default=None),
        session_factory=fastapi.Depends(get_session_factory)
):
    """

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
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)

    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        session=session,
        status_code=200
    )


@router.get("/documents", tags=["Entities"])
def get_documents(
        request: fastapi.Request,
        document_id: str = fastapi.Query(default=None),
        session_factory=fastapi.Depends(get_session_factory)
):
    """

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
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)

    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        session=session,
        status_code=200
    )


@router.get("/genes", tags=["Entities"])
def get_genes(
        request: fastapi.Request,
        gene_name: str = fastapi.Query(default=None),
        session_factory=fastapi.Depends(get_session_factory)
):
    """

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
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)

    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        session=session,
        status_code=200
    )


@router.get("/indications", tags=["Entities"])
def get_indications(
        request: fastapi.Request,
        indication_id: str = fastapi.Query(default=None),
        session_factory=fastapi.Depends(get_session_factory)
):
    """

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
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)

    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        session=session,
        status_code=200
    )


@router.get("/mappings", tags=["Entities"])
def get_mappings(
        request: fastapi.Request,
        mapping_id: str = fastapi.Query(default=None),
        session_factory=fastapi.Depends(get_session_factory)
):
    """
    Hmm... this serializes by dropping the primary coding since it is used within codings...
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
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)

    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result, pop_primary_coding=False)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        session=session,
        status_code=200
    )


@router.get("/organizations", tags=["Entities"])
def get_organizations(
        request: fastapi.Request,
        organization_id: str = fastapi.Query(default=None),
        session_factory=fastapi.Depends(get_session_factory)
):
    """

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
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)

    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        session=session,
        status_code=200
    )


@router.get("/propositions", tags=["Entities"])
def get_propositions(
        request: fastapi.Request,
        proposition_id: str = fastapi.Query(default=None),
        session_factory=fastapi.Depends(get_session_factory)
):
    """

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
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)

    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        session=session,
        status_code=200
    )


@router.get("/statements", tags=["Entities"])
def get_statements(
        request: fastapi.Request,
        statement_id: str = fastapi.Query(default=None),
        session_factory=fastapi.Depends(get_session_factory)
):
    """
    Gets all statement records from the database. If a statement_id is provided, return only that record.

    Args:
        statement_id (int): The id of the statement to retrieve. If None, return all statements.

    Returns:

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
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    # statement = handler.apply_joinedload(statement=statement)
    # statement = handler.apply_filters(statement=statement, parameters=parameters)

    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        session=session,
        status_code=200
    )


@router.get("/strengths", tags=["Entities"])
def get_strengths(
        request: fastapi.Request,
        strength_name: str = fastapi.Query(default=None),
        session_factory=fastapi.Depends(get_session_factory)
):
    """

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
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)

    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        session=session,
        status_code=200
    )


@router.get("/therapies", tags=["Entities"])
def get_therapies(
        request: fastapi.Request,
        therapy_name: str = fastapi.Query(default=None),
        session_factory=fastapi.Depends(get_session_factory)
):
    """

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
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)

    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        session=session,
        status_code=200
    )


@router.get("/therapygroups", tags=["Entities"])
def get_therapy_groups(
        request: fastapi.Request,
        therapy_group_id: str = fastapi.Query(default=None),
        session_factory=fastapi.Depends(get_session_factory)
):
    """

    """
    received = generate_datetime_now()
    handler = handlers.TherapyGroups()
    statement = handler.construct_base_query(model=models.TherapyGroups)
    if therapy_group_id:
        statement = statement.where(models.TherapyGroups.id == therapy_group_id)
        message_subject = f"Therapy group id {therapy_group_id}"
    else:
        message_subject = "Therapy groups"

    parameters = handler.get_parameters(arguments=request.query_params)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)

    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        received=received,
        request_url=str(request.url),
        session=session,
        status_code=200
    )
