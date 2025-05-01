import datetime
import flask
import sqlalchemy
import uuid

from app import models
from . import main_bp
from . import handlers


def create_response(data, message="", received=None, request_url=None, status_code=200):
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
    service = get_about(return_as_response=False)
    response = {
        "meta": meta,
        "service": service,
        "data": data
    }
    return flask.jsonify(response), status_code


def generate_datetime_now():
    return datetime.datetime.now(datetime.timezone.utc)


@main_bp.route('/tables', methods=['GET'])
def list_tables():
    inspector = sqlalchemy.inspect(models.engine)
    tables = inspector.get_table_names()
    return create_response(tables, "Tables retrieved successfully")


@main_bp.route('/about', methods=['GET'])
def get_about(return_as_response=True):
    """
    Gets service information from the About table.
    """
    handler = handlers.About()
    statement = handler.construct_base_query(model=models.About)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)
        serialized = serialized[0]
    if return_as_response:
        return create_response(
            request_url=flask.request.url,
            received=generate_datetime_now(),
            data=serialized,
            message="About metadata retrieved successfully",
            status_code=200
        )
    else:
        return serialized


@main_bp.route('/agents', defaults={'agent_name': None}, methods=['GET'])
@main_bp.route('/agents/<agent_name>', methods=['GET'])
def get_agents(agent_name=None):
    """

    """
    received = generate_datetime_now()
    handler = handlers.Agents()
    statement = handler.construct_base_query(model=models.Agents)
    if agent_name:
        statement = statement.where(models.Agents.name == agent_name)

    parameters = handler.get_parameters(arguments=flask.request.args)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        request_url=flask.request.url,
        received=received,
        data=serialized,
        message=f"Agents retrieved successfully",
        status_code=200
    )


@main_bp.route('/biomarkers', defaults={'biomarker_name': None}, methods=['GET'])
@main_bp.route('/biomarkers/<biomarker_name>', methods=['GET'])
def get_biomarkers(biomarker_name=None):
    """

    """
    received = generate_datetime_now()
    handler = handlers.Biomarkers()
    statement = handler.construct_base_query(model=models.Biomarkers)
    if biomarker_name:
        statement = statement.where(models.Biomarkers.name == biomarker_name)
        message_subject = f"Biomarker id {biomarker_name}"
    else:
        message_subject = "Biomarkers"

    parameters = handler.get_parameters(arguments=flask.request.args)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        request_url=flask.request.url,
        received=received,
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        status_code=200
    )


@main_bp.route('/codings', defaults={'coding_id': None}, methods=['GET'])
@main_bp.route('/codings/<coding_id>', methods=['GET'])
def get_codings(coding_id=None):
    """

    """
    received = generate_datetime_now()
    handler = handlers.Codings()
    statement = handler.construct_base_query(model=models.Codings)
    if coding_id:
        statement = statement.where(models.Codings.id == coding_id)
        message_subject = f"Coding id {coding_id}"
    else:
        message_subject = "Codings"

    parameters = handler.get_parameters(arguments=flask.request.args)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        request_url=flask.request.url,
        received=received,
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        status_code=200
    )


@main_bp.route('/contributions', defaults={'contribution_id': None}, methods=['GET'])
@main_bp.route('/contributions/<contribution_id>', methods=['GET'])
def get_contributions(contribution_id=None):
    """

    """
    received = generate_datetime_now()
    handler = handlers.Contributions()
    statement = handler.construct_base_query(model=models.Contributions)
    if contribution_id:
        statement = statement.where(models.Contributions.id == contribution_id)
        message_subject = f"Contribution id {contribution_id}"
    else:
        message_subject = "Contributions"

    parameters = handler.get_parameters(arguments=flask.request.args)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        request_url=flask.request.url,
        received=received,
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        status_code=200
    )


@main_bp.route('/diseases', defaults={'disease_name': None}, methods=['GET'])
@main_bp.route('/diseases/<disease_name>', methods=['GET'])
def get_diseases(disease_name=None):
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

    parameters = handler.get_parameters(arguments=flask.request.args)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        request_url=flask.request.url,
        received=received,
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        status_code=200
    )


@main_bp.route('/documents', defaults={'document_id': None}, methods=['GET'])
@main_bp.route('/documents/<document_id>', methods=['GET'])
def get_documents(document_id=None):
    """

    """
    received = generate_datetime_now()
    handler = handlers.Documents()
    statement = handler.construct_base_query(model=models.Documents)
    if document_id:
        statement = statement.where(models.Documents.name == document_id)
        message_subject = f"Document id {document_id}"
    else:
        message_subject = "Documents"

    parameters = handler.get_parameters(arguments=flask.request.args)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        request_url=flask.request.url,
        received=received,
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        status_code=200
    )


@main_bp.route('/genes', defaults={'gene_name': None}, methods=['GET'])
@main_bp.route('/genes/<gene_name>', methods=['GET'])
def get_genes(gene_name=None):
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

    parameters = handler.get_parameters(arguments=flask.request.args)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        request_url=flask.request.url,
        received=received,
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        status_code=200
    )


@main_bp.route('/indications', defaults={'indication_id': None}, methods=['GET'])
@main_bp.route('/indications/<indication_id>', methods=['GET'])
def get_indications(indication_id=None):
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

    parameters = handler.get_parameters(arguments=flask.request.args)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        request_url=flask.request.url,
        received=received,
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        status_code=200
    )


@main_bp.route('/mappings', defaults={'mapping_id': None}, methods=['GET'])
@main_bp.route('/mappings/<mapping_id>', methods=['GET'])
def get_mappings(mapping_id=None):
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

    parameters = handler.get_parameters(arguments=flask.request.args)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        request_url=flask.request.url,
        received=received,
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        status_code=200
    )


@main_bp.route('/organizations', defaults={'organization_name': None}, methods=['GET'])
@main_bp.route('/organizations/<organization_name>', methods=['GET'])
def get_organizations(organization_name=None):
    """

    """
    received = generate_datetime_now()
    handler = handlers.Organizations()
    statement = handler.construct_base_query(model=models.Organizations)
    if organization_name:
        statement = statement.where(models.Organizations == organization_name)
        message_subject = f"Organization {organization_name}"
    else:
        message_subject = "Mappings"

    parameters = handler.get_parameters(arguments=flask.request.args)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        request_url=flask.request.url,
        received=received,
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        status_code=200
    )


@main_bp.route('/propositions', defaults={'proposition_id': None}, methods=['GET'])
@main_bp.route('/propositions/<proposition_id>', methods=['GET'])
def get_propositions(proposition_id=None):
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

    parameters = handler.get_parameters(arguments=flask.request.args)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        request_url=flask.request.url,
        received=received,
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        status_code=200
    )


@main_bp.route('/statements', defaults={'statement_id': None}, methods=['GET'])
@main_bp.route('/statements/<statement_id>', methods=['GET'])
def get_statements(statement_id=None):
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

    parameters = handler.get_parameters(arguments=flask.request.args)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    # statement = handler.apply_joinedload(statement=statement)
    # statement = handler.apply_filters(statement=statement, parameters=parameters)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        request_url=flask.request.url,
        received=received,
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        status_code=200
    )


@main_bp.route('/strengths', defaults={'strength_name': None}, methods=['GET'])
@main_bp.route('/strengths/<strength_name>', methods=['GET'])
def get_strengths(strength_name=None):
    """

    """
    received = generate_datetime_now()
    handler = handlers.Strengths()
    statement = handler.construct_base_query(model=models.Strengths)
    if strength_name:
        statement = statement.where(models.Strength.name == strength_name)
        message_subject = f"Strength name {strength_name}"
    else:
        message_subject = "Strengths"

    parameters = handler.get_parameters(arguments=flask.request.args)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        request_url=flask.request.url,
        received=received,
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        status_code=200
    )


@main_bp.route('/therapies', defaults={'therapy_id': None}, methods=['GET'])
@main_bp.route('/therapies/<therapy_id>', methods=['GET'])
def get_therapies(therapy_id=None):
    """

    """
    received = generate_datetime_now()
    handler = handlers.Therapies()
    statement = handler.construct_base_query(model=models.Therapies)
    if therapy_id:
        statement = statement.where(models.Therapies.id == therapy_id)
        message_subject = f"Therapy id {therapy_id}"
    else:
        message_subject = "Therapies"

    parameters = handler.get_parameters(arguments=flask.request.args)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        request_url=flask.request.url,
        received=received,
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        status_code=200
    )


@main_bp.route('/therapygroups', defaults={'therapy_group_id': None}, methods=['GET'])
@main_bp.route('/therapygroups/<therapy_group_id>', methods=['GET'])
def get_therapy_groups(therapy_group_id=None):
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

    parameters = handler.get_parameters(arguments=flask.request.args)
    statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)

    return create_response(
        request_url=flask.request.url,
        received=received,
        data=serialized,
        message=f"{message_subject} retrieved successfully",
        status_code=200
    )
