import datetime
import flask
import sqlalchemy
#from sqlalchemy.orm import joinedload

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


def apply_filters(filter_criteria, query):
    filter_map = {
        'agent': lambda value: models.Agents.name == value,
        'biomarker_type': lambda value: models.Biomarkers.biomarker_type == value,
        'biomarker': lambda value: models.Biomarkers.name == value,
        'gene': lambda value: models.Genes.name == value,
        'cancer_type': lambda value: models.Diseases.name == value,
        #'oncotree_code': lambda value: models.Context.oncotree_code == value,
        #'oncotree_term': lambda value: models.Context.oncotree_term == value,
        'organization': lambda value: models.Organizations.name == value,
        #'drug_name_brand': lambda value: models.Documents.drug_name_brand == value,
        #'drug_name_generic': lambda value: models.Documents.drug_name_generic == value,
        'therapy_name': lambda value: models.Therapies.name == value,
        'therapy_type': lambda value: models.Therapies.therapy_type == value
    }

    and_filters = []
    or_filters = []

    for criteria in filter_criteria:
        filter_name = criteria.get('filter')
        filter_values = criteria.get('values')
        if (filter_name in filter_map) and filter_values:
            # ^ This may be problematic for filter names that do not match
            # Queries across different categories will be combined with an AND operator
            # Queries across the same category will be combined with an OR operator

            processed_values = []
            for value in filter_values:
                formatted_value = value
                # formatted_value = value.replace(' ', '%20')
                # Add additional formatting, such as checking against aliase, here
                processed_values.append(formatted_value)

            if len(processed_values) > 1:
                # Create an OR condition if multiple of the same filter are passed
                filter_conditions = [filter_map[filter_name](value) for value in processed_values]
                or_filters.append(sqlalchemy.or_(*filter_conditions))
            else:
                # Otherwise, filter for a single value
                filter_condition = filter_map[filter_name](processed_values[0])
                and_filters.append(filter_condition)

    if and_filters:
        query = query.filter(sqlalchemy.and_(*and_filters))
    if or_filters:
        query = query.filter(sqlalchemy.or_(*or_filters))

    return query


def convert_date_to_iso(value: datetime.date) -> str:
    """
    Converts a datetime.date value to an ISO 8601 format string.
    
    Args:
        value: The datetime.date value to convert.
    
    Returns:
        str: The ISO 8601 format string if the value is a date, otherwise the original value.
    """
    if isinstance(value, datetime.date):
        return value.isoformat()
    else:
        raise ValueError(f"Input value not of type datetime.date: {value}")


def create_response(data, message="", status=200):
    """Wrapper function to create a response with metadata."""
    response = {
        "status_code": status,
        "message": message,
        "count": data if isinstance(data, int) else len(data),
        "data": data,
    }
    return flask.jsonify(response), status


def move_keys_to_extensions(dictionary: dict, keys: list[str]) -> dict:
    if 'extensions' not in dictionary:
        dictionary['extensions'] = []
    for key in keys:
        extension = [{'name': key, 'value': dictionary[key]}]
        dictionary['extensions'].append(extension)
        dictionary.pop(key, None)
    return dictionary


def reorder_dictionary(dictionary: dict, key_order: list[str]) -> dict:
    """
    Reorders the keys in a dictionary based on a given list of keys.

    Args:
        dictionary (dict): The original dictionary to reorder.
        key_order (list[str]): A list of keys specifying the desired order.

    Returns:
        reoredered (dict): A new dictionary with keys reordered.
    """
    reordered = {key: dictionary[key] for key in key_order if key in dictionary}
    return reordered


@main_bp.route('/about', methods=['GET'])
def get_about():
    session = flask.current_app.config['SESSION']()
    try:
        about = session.query(models.About).filter_by(id=0).first()
        if about:
            data = about.__dict__
            data.pop('_sa_instance_state', None)
            data.pop('id', None)

            data['last_updated'] = convert_date_to_iso(data['last_updated'])

            return create_response(
                data=[data],
                message="About metadata retrieved successfully",
                status=200
            )
        else:
            return create_response(
                data={},
                message="No database metadata found",
                status=404
            )
    except Exception as e:
        print(f"Error occurred: {e}")
        return create_response(
            data={"error": {e}},
            message="An error occurred while retrieving about metadata",
            status=500
        )
    finally:
        session.close()


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
            status=200
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
            status=404
        )

    session = flask.current_app.config['SESSION']()
    try:
        table_class = TABLE_MAP.get(table_name)
        if not table_class:
            return create_response(
                data={},
                message=f"Table {table_name} not found",
                status=404
            )

        count = session.query(sqlalchemy.func.count(table_class.id)).scalar()
        return create_response(
            data=count,
            message=f"Row count for {table_name} retrieved successfully",
            status=200
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
            status=200
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
            status=200
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
            status=200
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
            status=200
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
            status=200
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
            status=400
        )

    session = flask.current_app.config['SESSION']()
    try:
        table_class = TABLE_MAP.get(table_name)
        if not table_class:
            return create_response(
                data={},
                message=f"Table {table_name} not found",
                status=404
            )

        if not hasattr(table_class, column_name):
            return create_response(
                data={},
                message=f"Column '{column_name}' not found in table '{table_name}'",
                status=404
            )

        values = session.query(getattr(table_class, column_name)).distinct().all()
        data = [value[0] for value in values]
        return create_response(
            data=data,
            message=f"Unique values for column '{column_name}' in table '{table_name}' retrieved successfully ",
            status=200
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


def serialize_statement_instance(query_results, dereference=True) -> dict:
    result = []
    for statement in query_results:
        data = serialize_instance(statement)
        if not dereference:
            result.append(data)
            continue

        contributions = []
        for contribution in statement.contributions:
            contribution_serialized = serialize_instance(instance=contribution)
            contribution_serialized['agent'] = serialize_instance(instance=contribution.agents)
            contribution_serialized.pop('agent_id', None)
            contributions.append(contribution_serialized)
        data['contributions'] = contributions

        documents = []
        for document in statement.documents:
            document_serialized = serialize_instance(instance=document)
            document_serialized['organization'] = serialize_instance(instance=document.organization)
            document_serialized.pop('organization_id', None)
            documents.append(document_serialized)
        data['reportedIn'] = documents

        indication = serialize_instance(instance=statement.indication)
        indication['document'] = serialize_instance(instance=statement.indication.documents)
        indication['document']['organization'] = serialize_instance(
            instance=statement.indication.documents.organization
        )
        indication.pop('document_id', None)
        indication['document'].pop('organization_id', None)
        data['indication'] = indication
        data.pop('indication_id', None)

        # Proposition
        proposition = serialize_instance(instance=statement.proposition)

        # Biomarkers
        biomarkers = []
        for biomarker in statement.proposition.biomarkers:
            b = serialize_instance(instance=biomarker)
            if biomarker.genes:
                genes = []
                for gene in biomarker.genes:
                    g = serialize_instance(instance=gene)
                    g['primaryCoding'] = serialize_instance(instance=gene.primary_coding)
                    g.pop('primary_coding_id', None)
                    mappings = []
                    for mapping in gene.mappings:
                        m = serialize_instance(instance=mapping)
                        m['coding'] = serialize_instance(instance=mapping.coding)
                        m.pop('coding_id', None)
                        m.pop('primary_coding_id', None)
                        mappings.append(m)
                    g['mappings'] = mappings
                    genes.append(g)
                b['genes'] = genes
            biomarkers.append(b)
        proposition['biomarkers'] = biomarkers

        # Disease
        disease = serialize_instance(instance=statement.proposition.condition_qualifier)
        primary_coding = serialize_instance(instance=statement.proposition.condition_qualifier.primary_coding)
        disease['primaryCoding'] = primary_coding
        disease.pop('primary_coding_id', None)
        proposition['disease'] = disease
        proposition.pop('condition_qualifier_id', None)

        # data['proposition'] = serialize_instance(instance=statement.proposition)
        # data['proposition']['conditionQualifier'] = serialize_instance(instance=statement.proposition.condition_qualifier)
        data['proposition'] = proposition
        data.pop('proposition_id', None)

        if statement.proposition.therapy:
            therapy_instance = serialize_instance(statement.proposition.therapy)
            therapy_instance['primaryCoding'] = serialize_instance(statement.proposition.therapy.primary_coding)
            therapy_instance.pop('primary_coding_id', None)
            # therapy_instance['therapy_strategy'] = serialize_instance(statement.proposition.therapy.therapy_strategy)
            mappings = []
            for mapping in statement.proposition.therapy.mappings:
                m = serialize_instance(instance=mapping)
                m['coding'] = serialize_instance(instance=mapping.coding)
                m.pop('coding_id', None)
                m.pop('primary_coding_id', None)
                mappings.append(m)
            therapy_instance['mappings'] = mappings
        else:
            therapy_instance = serialize_instance(statement.proposition.therapy_group)
            therapies = []
            for therapy in statement.proposition.therapy_group.therapies:
                member_therapy_instance = serialize_instance(therapy)
                member_therapy_instance['primaryCoding'] = serialize_instance(therapy.primary_coding)
                member_therapy_instance.pop('primary_coding_id', None)
                # therapy_instance['therapy_strategy'] = serialize_instance(statement.proposition.therapy.therapy_strategy)
                mappings = []
                for mapping in therapy.mappings:
                    m = serialize_instance(instance=mapping)
                    m['coding'] = serialize_instance(instance=mapping.coding)
                    m.pop('coding_id', None)
                    m.pop('primary_coding_id', None)
                    mappings.append(m)
                member_therapy_instance['mappings'] = mappings
                therapies.append(member_therapy_instance)
            therapy_instance['therapies'] = therapies
        data['proposition']['targetTherapeutic'] = therapy_instance

        strength = serialize_instance(instance=statement.strength)
        strength['primaryCoding'] = serialize_instance(instance=statement.strength.primary_coding)
        strength.pop('primary_coding_id', None)
        data['strength'] = strength
        data.pop('strength_id', None)

        result.append(data)
    return result



@main_bp.route('/statements', defaults={'statement_id': None}, methods=['GET'])
@main_bp.route('/statements/<statement_id>', methods=['GET'])
def get_statements(statement_id=None):
    """

    """
    session = flask.current_app.config['SESSION']()
    handler = handlers.Statements(session=session)
    try:
        query_parameters = flask.request.args.to_dict()
        query = handler.construct_base_query(model=models.Statements)
        if statement_id:
            query = query.filter(models.Statements.id == statement_id)
        query = handler.perform_joins(query=query, parameters=query_parameters)
        query = handler.apply_joinedload(query=query)
        query = handler.apply_filters(query=query, parameters=query_parameters)
        result = handler.execute_query(query=query)
        serialized = handler.serialize_instances(instances=result)

        return create_response(
            data=serialized,
            message=f"Statements retrieved successfully",
            status=200
        )
    finally:
        session.close()

    """
        query_parameters = flask.request.args.to_dict()
        query = handlers.Statements.construct_base_query(session=session, model=models.Statements)
        if statement_id:
            query = query.filter(models.Statements.id == statement_id)

        query = get_statement_query(session=session, parameters=query_parameters)
        if statement_id:
            query = query.filter(models.Statements.id == statement_id)

        results = query.all()
        results_serialized = serialize_statement_instance(query_results=results, dereference=False)

        return create_response(
            data=results,
            message="Statements successfully retrieved",
            status=200
        )
    finally:
        session.close()
    """
"""
@main_bp.route('/statements', defaults={'statement_id': None}, methods=['GET'])
@main_bp.route('/statements/<statement_id>', methods=['GET'])
def get_statements(statement_id=None):
    session = flask.current_app.config['SESSION']()
    try:
        query_parameters = flask.request.args.to_dict()


        #filter_criteria = []
        #for field in ['organization', 'drug_name_brand', 'drug_name_generic']:
        #    filter_field = {'filter': field, 'values': flask.request.args.getlist(field)}
        #    filter_criteria.append(filter_field)
        #print(filter_criteria)

        query_parameters = flask.request.args.to_dict()
        query = get_statement_query(session=session, parameters=query_parameters)
        if statement_id:
            query = query.filter(models.Statements.id == statement_id)

        # Get and apply filters
        fields = [
            'cancer_type',
            'biomarker',
            'biomarker_type',
            'drug_name_brand',
            # This field is not present in the Statement table natively, and instead comes in a dictionary once joined
            'gene',  # I need to split gene off to its own table
            #'oncotree_code',
            #'oncotree_term',
            'organization',
            'therapy_name',
            'therapy_type',
        ]
        filter_criteria = []
        for field in fields:
            filter_field = {'filter': field, 'values': flask.request.args.getlist(field)}
            filter_criteria.append(filter_field)

        #query = apply_filters(
        #    filter_criteria=filter_criteria,
        #    query=query
        #)
        print(query)

        # Execute query and return all results
        #dereference=False
        results = query.all()
        results_serialized = serialize_statement_instance(query_results=results, dereference=dereference)

        return create_response(
            data=results_serialized,
            message="Statements successfully retrieved",
            status=200
        )
    finally:
        session.close()
"""