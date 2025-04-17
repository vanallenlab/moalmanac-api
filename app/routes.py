import flask
import sqlalchemy
from sqlalchemy import inspect

from . import models


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
        'biomarker_type': lambda value: models.Biomarkers.biomarker_type == value,
        'biomarker': lambda value: models.Biomarkers.name == value,
        'gene': lambda value: models.Genes.name == value,
        'cancer_type': lambda value: models.Diseases.name == value,
        #'oncotree_code': lambda value: models.Context.oncotree_code == value,
        #'oncotree_term': lambda value: models.Context.oncotree_term == value,
        'organization': lambda value: models.Organizations.name == value,
        'drug_name_brand': lambda value: models.Documents.drug_name_brand == value,
        'drug_name_generic': lambda value: models.Documents.drug_name_generic == value,
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


def create_response(data, message="", status=200):
    """Wrapper function to create a response with metadata."""
    response = {
        "status_code": status,
        "message": message,
        "count": data if isinstance(data, int) else len(data),
        "data": data,
    }
    return flask.jsonify(response), status


def serialize_instance(instance):
    """Convert SQLAlchemy instance to a dictionary."""
    return {
        column.name: getattr(instance, column.name) for column in instance.__table__.columns
    }


@flask.current_app.route('/about', methods=['GET'])
def get_about():
    session = models.Session()
    try:
        about = session.query(models.About).filter_by(id=0).first()
        if about:
            data = about.__dict__
            data.pop('_sa_instance_state', None)
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


@flask.current_app.route('/tables', methods=['GET'])
def list_tables():
    inspector = inspect(models.engine)
    tables = inspector.get_table_names()
    return create_response(tables, "Tables retrieved successfully")


@flask.current_app.route('/rows', methods=['GET'])
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

    session = models.Session()
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


@flask.current_app.route('/documents', methods=['GET'])
def get_documents():
    session = models.Session()
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


@flask.current_app.route('/therapy', defaults={'therapy_name': None}, methods=['GET'])
@flask.current_app.route('/therapy/<therapy_name>', methods=['GET'])
def get_therapy(therapy_name=None):
    """
    This should list all therapies with the statement count associated with each
    Providing a specific therapy name should list all statements involving the therapy
    :param therapy_name:
    :return:
    """
    session = models.Session()
    try:
        statements = (
            session
            .query(models.Statements)
            .join(models.Indications, models.Statements.indication_id == models.Indications.id)
            #.join(models.Implication, models.Statement.implication == models.Implication.id)
            #.join(models.Therapy, models.Implication.therapies)

            .all()
        )

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


@flask.current_app.route('/unique', methods=['GET'])
def get_unique_values():
    table_name = flask.request.args.get('table')
    column_name = flask.request.args.get('column')

    if not table_name or not column_name:
        return create_response(
            data={},
            message="Table name and column name are required",
            status=400
        )

    session = models.Session()
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


@flask.current_app.route('/statements', defaults={'statement_id': None}, methods=['GET'])
@flask.current_app.route('/statements/<statement_id>', methods=['GET'])
def get_statements(statement_id=None):
    session = models.Session()
    try:
        # Base query
        query = (
            session
            .query(
                models.Statements
            )
            .join(models.Indications, models.Statements.indication_id == models.Indications.id)
            .join(models.Propositions, models.Statements.proposition_id == models.Propositions.id)
            .join(models.Strengths, models.Statements.strength_id == models.Strengths.id)
            .options(
                # Join tables that are referenced in Statements
                sqlalchemy.orm.joinedload(models.Statements.contributions),
                sqlalchemy.orm.joinedload(models.Statements.documents),
                sqlalchemy.orm.joinedload(models.Statements.indication),
                sqlalchemy.orm.joinedload(models.Statements.proposition).joinedload(models.Propositions.condition_qualifier),
                sqlalchemy.orm.joinedload(models.Statements.proposition).joinedload(models.Propositions.therapy),
                sqlalchemy.orm.joinedload(models.Statements.proposition).joinedload(models.Propositions.therapy_group).joinedload(models.TherapyGroups.therapies),
                sqlalchemy.orm.joinedload(models.Statements.strength)
            )
        )

        if statement_id:
            query = query.filter(models.Statements.id == statement_id)

        # Get and apply filters
        fields = [
            'cancer_type',
            'biomarker',
            'biomarker_type',
            'drug_name_brand', # This field is not present in the Statement table natively, and instead comes in a dictionary once joined
            'gene', # I need to split gene off to its own table
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

        query = apply_filters(
            filter_criteria=filter_criteria,
            query=query
        )

        # Execute query and return all results
        results = query.all()
        result = []
        for statement in results:
            data = serialize_instance(statement)
            data['contributions'] = [serialize_instance(instance=c) for c in statement.contributions]
            data['reportedIn'] = [serialize_instance(instance=d) for d in statement.documents]
            data['indication'] = serialize_instance(instance=statement.indication)
            data['proposition'] = serialize_instance(instance=statement.proposition)
            data['proposition']['conditionQualifier'] = serialize_instance(instance=statement.proposition.condition_qualifier)

            if statement.proposition.therapy:
                therapy_instance = serialize_instance(statement.proposition.therapy)
            else:
                therapy_instance = serialize_instance(statement.proposition.therapy_group)
                therapy_instance['therapies'] = [serialize_instance(instance=t) for t in statement.proposition.therapy_group.therapies]
            data['proposition']['targetTherapeutic'] = therapy_instance
            data['strength'] = serialize_instance(statement.strength)
            #data['biomarkers'] = [serialize_instance(b) for b in statement.biomarkers]
            #data['context'] = serialize_instance(statement.context)
            #data['document'] = serialize_instance(statement.document)
            #data['implication'] = serialize_instance(statement.implication)
            #data['implication']['therapy'] = [serialize_instance(t) for t in statement.implication.therapy]
            #data['indication'] = serialize_instance(statement.indication)

            # Remove referenced ids
            #data.pop('context_id', None)
            #data.pop('document_id', None)
            data.pop('indication_id', None)
            data.pop('proposition_id', None)
            data.pop('strength_id', None)
            result.append(data)

        return create_response(
            data=result,
            message="Statements successfully retrieved",
            status=200
        )
    finally:
        session.close()
