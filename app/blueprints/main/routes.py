import datetime
import flask
import sqlalchemy
import uuid

from app import models
from . import main_bp
from . import handlers

TABLE_MAP = {
    'about': models.About,
    'agents': models.Agents,
    'biomarkers': models.Biomarkers,
    'codings': models.Codings,
    'contributions': models.Contributions,
    'diseases': models.Diseases,
    'documents': models.Documents,
    'genes': models.Genes,
    'indication': models.Indications,
    'mappings': models.Mappings,
    'organization': models.Organizations,
    'propositions': models.Propositions,
    'statements': models.Statements,
    'strengths': models.Strengths,
    'therapies': models.Therapies,
    'therapy_groups': models.TherapyGroups,
    'therapy_strategies': models.TherapyStrategies
}


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


@main_bp.route('/contributions', defaults={'agent': None}, methods=['GET'])
@main_bp.route('/contributions/<agent>', methods=['GET'])
def get_contributions(agent=None):
    """
    Should have the option to dereference the agents table
    And filter by date and agent name
    :param agent:
    :param dereferenced:
    :return:
    """
    session = flask.current_app.config['SESSION']()
    try:
        query = (
            session
            .query(models.Contributions)
        )

        query_parameters = flask.request.args.to_dict()
        if 'dereferenced' in query_parameters:
            dereference = False if query_parameters['dereferenced'].lower() == 'false' else True
        else:
            dereference = True

        if dereference:
            query = (
                query
                .join(models.Agents, models.Agents.id == models.Contributions.agent_id)
                .options(
                    sqlalchemy.orm.joinedload(models.Contributions.agents)
                )
            )
        if agent:
            filter_criteria = [{'filter': 'agent', 'values': agent}]
            query = apply_filters(
                filter_criteria=filter_criteria,
                query=query
            )

        results = query.all()
        result = []
        for contribution in results:
            data = serialize_instance(instance=contribution)
            if dereference:
                data['agent'] = serialize_instance(instance=contribution.agents)
                data.pop('agent_id', None)
            data['date'] = convert_date_to_iso(data['date'])
            result.append(data)
        return create_response(
            data=result,
            message="Contributions retrieved successfully",
            status_code=200
        )
    finally:
        session.close()


@main_bp.route('/tables', methods=['GET'])
def list_tables():
    inspector = sqlalchemy.inspect(models.engine)
    tables = inspector.get_table_names()
    return create_response(tables, "Tables retrieved successfully")


@main_bp.route('/rows', methods=['GET'])
def get_row_count():
    """
    This is in progress
    :return:
    """
    table_name = flask.request.args.get('table')
    if not table_name:
        return create_response(
            data={},
            message=f"Table {table_name} not found",
            status_code=404
        )

    session = flask.current_app.config['SESSION']()
    try:
        table_class = TABLE_MAP.get(table_name)
        if not table_class:
            return create_response(
                data={},
                message=f"Table {table_name} not found",
                status_code=404
            )

        count = session.query(sqlalchemy.func.count(table_class.id)).scalar()
        return create_response(
            data=count,
            message=f"Row count for {table_name} retrieved successfully",
            status_code=200
        )
    finally:
        session.close()


@main_bp.route('/documents', methods=['GET'])
def get_documents():
    session = flask.current_app.config['SESSION']()
    try:
        # Subqueries to join other tables
        indication_count_subquery = (
            session
            .query(
                models.Indications.document_id,
                sqlalchemy.func.count(models.Indications.id).label('indication_count')
            )
            .group_by(models.Indications.document_id)
            .subquery()
        )

        #statement_count_subquery = (
        #    session
        #    .query(
        #        models.Statements.document_id,
        #        sqlalchemy.func.count(models.Statement.id).label('statement_count')
        #    )
        #    .group_by(models.Statement.document_id)
        #    .subquery()
        #)

        # Base query
        query = (
            session
            .query(
                models.Documents,
                indication_count_subquery.c.indication_count,
                #statement_count_subquery.c.statement_count
            )
            #.outerjoin(
            #statement_count_subquery,
            #    models.Documents.id == statement_count_subquery.c.document_id
            #)
            .outerjoin(
                indication_count_subquery,
                models.Documents.id == indication_count_subquery.c.document_id
            )
        )

        # Get and apply filters
        filter_criteria = []
        for field in ['organization', 'drug_name_brand', 'drug_name_generic']:
            filter_field = {'filter': field, 'values': flask.request.args.getlist(field)}
            filter_criteria.append(filter_field)

        query = apply_filters(
            filter_criteria=filter_criteria,
            query=query
        )

        # Execute query and return all results
        results = query.all()
        result = []
        for document, indication_count in results:
            #for document, indication_count, statement_count in results:
            data = serialize_instance(document)
            data.pop('_sa_instance_state', None)
            data['indication_count'] = indication_count or 0
            #data['statement_count'] = statement_count or 0
            result.append(data)

        return create_response(
            data=result,
            message=f"Documents successfully retrieved",
            status_code=200
        )
    finally:
        session.close()


@main_bp.route('/genes', defaults={'gene': None}, methods=['GET'])
@main_bp.route('/genes/<gene>', methods=['GET'])
def get_genes(gene=None):
    session = flask.current_app.config['SESSION']()
    try:
        query = (
            session
            .query(models.Genes)
        )
        if gene:
            query = query.filter(models.Genes.gene == gene)

        results = query.all()
        result = []
        for gene in results:
            data = serialize_instance(gene)
            data['primaryCoding'] = serialize_instance(instance=gene.primary_coding)
            mappings = []
            for mapping in gene.mappings:
                mappings.append(serialize_instance(instance=mapping))
            data['mappings'] = mappings
            data = move_keys_to_extensions(
                dictionary=data,
                keys=['location', 'location_sortable']
            )
            print(data)
            data['conceptType'] = data['concept_type']
            data = reorder_dictionary(dictionary=data, key_order=models.Genes.field_order)
            print(data)
            result.append(data)

        return create_response(
            data=result,
            message="Genes retrieved successfully",
            status_code=200
        )
    finally:
        session.close()


@main_bp.route('/terms', defaults={'table': None}, methods=['GET'])
@main_bp.route('/terms/<table>', methods=['GET'])
def get_terms(table=None):
    session = flask.current_app.config['SESSION']()
    try:
        query = (
            session
            .query(models.Terms)
        )
        if table:
            query = query.filter(models.Terms.table == table)

        results = query.all()
        result = []
        for term in results:
            data = serialize_instance(term)
            result.append(data)
        return create_response(
            data=result,
            message="Terms retrieved successfully",
            status_code=200
        )
    finally:
        session.close()


@main_bp.route('/termcounts', methods=['GET'])
def get_term_counts():
    session = flask.current_app.config['SESSION']()
    try:
        query = (
            session
            .query(models.TermCounts)
        )
        results = query.all()
        result = []
        for table in results:
            data = serialize_instance(table)
            result.append(data)
        return create_response(
            data=result,
            message="Term counts retrieved successfully",
            status_code=200
        )
    finally:
        session.close()


@main_bp.route('/therapy', defaults={'therapy_name': None}, methods=['GET'])
@main_bp.route('/therapy/<therapy_name>', methods=['GET'])
def get_therapy(therapy_name=None):
    """
    This should list all therapies with the statement count associated with each
    Providing a specific therapy name should list all statements involving the therapy
    :param therapy_name:
    :return:
    """
    session = flask.current_app.config['SESSION']()
    try:
        query = (
            session
            .query(models.Statements)
            .join(models.Indications, models.Statements.indication_id == models.Indications.id)
            #.join(models.Implication, models.Statement.implication == models.Implication.id)
            #.join(models.Therapy, models.Implication.therapies)

            .all()
        )

        if therapy_name:
            query = query.filter(models.Statements.id == statement_id)

        result = []
        for statement in statements:
            data = statement.__dict__
            data.pop('_sa_instance_state', None)
            result.append(data)
        return create_response(
            data=result,
            message=f"Statements for therapy {therapy_name} retrieved successfully",
            status_code=200
        )
    finally:
        session.close()


@main_bp.route('/unique', methods=['GET'])
def get_unique_values():
    table_name = flask.request.args.get('table')
    column_name = flask.request.args.get('column')

    if not table_name or not column_name:
        return create_response(
            data={},
            message="Table name and column name are required",
            status_code=400
        )

    session = flask.current_app.config['SESSION']()
    try:
        table_class = TABLE_MAP.get(table_name)
        if not table_class:
            return create_response(
                data={},
                message=f"Table {table_name} not found",
                status_code=404
            )

        if not hasattr(table_class, column_name):
            return create_response(
                data={},
                message=f"Column '{column_name}' not found in table '{table_name}'",
                status_code=404
            )

        values = session.query(getattr(table_class, column_name)).distinct().all()
        data = [value[0] for value in values]
        return create_response(
            data=data,
            message=f"Unique values for column '{column_name}' in table '{table_name}' retrieved successfully ",
            status_code=200
        )
    finally:
        session.close()

"""
def get_statement_query(session, parameters=None):
    query = (
        session
        .query(models.Statements)
    )

    if parameters is None:
        parameters = {}
    else:
        # the .join statements are needed to filter the data on any other of these fields
        CodingFromGene = sqlalchemy.orm.aliased(models.Codings)
        CodingFromDisease = sqlalchemy.orm.aliased(models.Codings)
        CodingFromTherapy = sqlalchemy.orm.aliased(models.Codings)

        MappingFromGene = sqlalchemy.orm.aliased(models.Mappings)
        MappingFromDisease = sqlalchemy.orm.aliased(models.Mappings)
        MappingFromTherapy = sqlalchemy.orm.aliased(models.Mappings)

        OrganizationFromDocument = sqlalchemy.orm.aliased(models.Organizations)

        DocumentFromStatement = sqlalchemy.orm.aliased(models.Documents)
        DocumentFromIndication = sqlalchemy.orm.aliased(models.Documents)

        query = (
            query
            .join(models.Indications, models.Statements.indication_id == models.Indications.id)
            .join(models.Propositions, models.Statements.proposition_id == models.Propositions.id)
            # Need to join all of the tables...
            .join(models.Codings, models.Mappings.primary_coding)
            # Biomarkers
            .join(models.Biomarkers, models.Propositions.biomarkers)
            .join(models.Genes, models.Biomarkers.genes)
            .join(MappingFromGene, models.Genes.mappings)
            .join(CodingFromGene, models.Genes.primary_coding)
            # Cancer type
            .join(models.Diseases, models.Propositions.condition_qualifier)
            .join(MappingFromDisease, models.Diseases.mappings)
            .join(CodingFromDisease, models.Diseases.primary_coding)
            # Therapy group
            .join(models.TherapyGroups, models.Propositions.therapy_group)
            .join(models.Therapies, models.TherapyGroups.therapies)
            # Therapy
            .join(models.Therapies, models.Propositions.therapy)
            .join(MappingFromTherapy, models.Therapies.mappings)
            .join(CodingFromTherapy, models.Therapies.primary_coding)
            # Documents
            .join(models.Documents, models.Statements.documents)
            .join(models.Organizations, models.Documents.organization)
            # Indication
            .join(models.Indications, models.Statements.indication)
            .join(models.Documents, models.Indications.documents)
            # Strength
            .join(models.Strengths, models.Statements.strength_id == models.Strengths.id)
        )

    dereference = should_dereference(parameters=parameters)
    if not dereference:
        return query
    else:
        # Eager load .joinedload options are needed to serialize the related data,
        # and this reduces the overall number of queries
        eager_load_options = [
            (
                sqlalchemy.orm.joinedload(models.Statements.contributions)
                .joinedload(models.Contributions.agents)
            ),
            (
                sqlalchemy.orm.joinedload(models.Statements.documents)
                .joinedload(models.Documents.organization)
             ),
            (
                sqlalchemy.orm.joinedload(models.Statements.indication)
                .joinedload(models.Indications.documents)
                .joinedload(models.Documents.organization)
            ),
            (
                sqlalchemy.orm.joinedload(models.Statements.proposition)
                .joinedload(models.Propositions.biomarkers)
                .joinedload(models.Biomarkers.genes)
                .joinedload(models.Genes.primary_coding)
            ),
            (
                sqlalchemy.orm.joinedload(models.Statements.proposition)
                .joinedload(models.Propositions.biomarkers)
                .joinedload(models.Biomarkers.genes)
                .joinedload(models.Genes.mappings)
                .joinedload(models.Mappings.primary_coding)
            ),
            (
                sqlalchemy.orm.joinedload(models.Statements.proposition)
                .joinedload(models.Propositions.condition_qualifier)
            ),
            (
                sqlalchemy.orm.joinedload(models.Statements.proposition)
                .joinedload(models.Propositions.condition_qualifier)
                .joinedload(models.Diseases.mappings)
                .joinedload(models.Mappings.primary_coding)
            ),
            (
                sqlalchemy.orm.joinedload(models.Statements.proposition)
                .joinedload(models.Propositions.therapy)
            ),
            (
                sqlalchemy.orm.joinedload(models.Statements.proposition)
                .joinedload(models.Propositions.therapy)
                .joinedload(models.Therapies.mappings)
                .joinedload(models.Mappings.primary_coding)
            ),
            (
                sqlalchemy.orm.joinedload(models.Statements.proposition)
                .joinedload(models.Propositions.therapy_group)
                .joinedload(models.TherapyGroups.therapies)
                .joinedload(models.Therapies.primary_coding)
            ),
            (
                sqlalchemy.orm.joinedload(models.Statements.proposition)
                .joinedload(models.Propositions.therapy_group)
                .joinedload(models.TherapyGroups.therapies)
                .joinedload(models.Therapies.mappings)
                .joinedload(models.Mappings.primary_coding)
            ),
            (
                sqlalchemy.orm.joinedload(models.Statements.proposition)
                .joinedload(models.Propositions.therapy_group)
                .joinedload(models.TherapyGroups.therapies)
                .joinedload(models.Therapies.primary_coding)
            )
        ]

        return query.options(*eager_load_options)
"""
@main_bp.route('/propositions', defaults={'proposition_id': None}, methods=['GET'])
@main_bp.route('/propositions/<proposition_id>', methods=['GET'])
def get_propositions(propositions_id=None):
    """

    """
    # Step 1: Instnatiate the handler for the table
    handler = handlers.Statements()
    statement = handler.construct_base_query(model=models.Propositions)
    if propositions_id:
        statement = statement.where(models.Propositions.id == propositions_id)

    parameters = handler.get_parameters(arguments=flask.request.args)
    #statement, joined_tables = handler.perform_joins(statement=statement, parameters=parameters)
    statement = handler.apply_joinedload(statement=statement)
    statement = handler.apply_filters(statement=statement, parameters=parameters)
    #print(joined_tables)

    session_factory = flask.current_app.config['SESSION_FACTORY']
    with session_factory() as session:
        result = handler.execute_query(session=session, statement=statement)
        serialized = handler.serialize_instances(instances=result)
    return create_response(
        data=serialized,
        message=f"Statements retrieved successfully",
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
        message=f"Statements retrieved successfully",
        status_code=200
    )
