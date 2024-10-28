import flask
import sqlalchemy
from sqlalchemy import inspect

from . import models


TABLE_MAP = {
        'biomarkers': models.Biomarker,
        'contexts': models.Context,
        'documents': models.Document,
        'implications': models.Implication,
        'indication': models.Indication,
        'organization': models.Organization,
        'organizations': models.Organization,
        'therapy': models.Therapy,
        'therapies': models.Therapy,
        'statements': models.Statement
}


def create_response(data, message="", status=200):
    """Wrapper function to create a response with metadata."""
    response = {
        "status": status,
        "message": message,
        "data": data,
        "count": data if isinstance(data, int) else len(data)
    }
    #print(response)
    return flask.jsonify(response), status


def serialize_instance(instance):
    """Convert SQLAlchemy instance to a dictionary."""
    return {
        column.name: getattr(instance, column.name) for column in instance.__table__.columns
    }


@flask.current_app.route('/test', methods=['GET'])
def test_route():
    return "Test route is working"


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
        print(f"Error occured: {e}")
        return create_response(
            data={"error": {e}},
            message="An error occured while retrieving about metadata",
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
    # This should have a statement count instead of indication count
    organization = flask.request.args.get('organization')
    drug_name_brand = flask.request.args.get('drug_name_brand')
    drug_name_generic = flask.request.args.get('drug_name_generic')
    session = models.Session()
    try:
        indication_count_subquery = (
            session
            .query(
                models.Indication.document_id,
                sqlalchemy.func.count(models.Indication.id).label('indication_count')
            )
            .group_by(models.Indication.document_id)
            .subquery()
        )

        query = (
            session
            .query(
                models.Document,
                indication_count_subquery.c.indication_count
            )
            .outerjoin(
                indication_count_subquery,
                models.Document.id == indication_count_subquery.c.document_id
            )
         )

        filters = []
        if organization:
            filters.append(models.Document.organization == organization)
        if drug_name_brand:
            filters.append(models.Document.drug_name_brand == drug_name_brand)
        if drug_name_generic:
            filters.append(models.Document.drug_name_generic == drug_name_generic)
        if filters:
            query = query.filter(sqlalchemy.and_(*filters))

        results = query.all()

        result = []
        for document, indication_count in results:
            data = document.__dict__
            data.pop('_sa_instance_state', None)
            data['indication_count'] = indication_count or 0
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
            .query(models.Statement)
            .join(models.Indication, models.Statement.indication == models.Indication.id)
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


@flask.current_app.route('/statements', methods=['GET'])
def get_statements():
    session = models.Session()
    try:
        query = (
            session
            .query(models.Statement)
            .options(
                sqlalchemy.orm.joinedload(models.Statement.document),
                sqlalchemy.orm.joinedload(models.Statement.biomarkers),
                sqlalchemy.orm.joinedload(models.Statement.context),
                #sqlalchemy.orm.joinedload(models.Statement.implication),
                #sqlalchemy.orm.joinedload(models.Statement.indication),
            )
        )
        results = query.all()

        result = []
        for statement in results:
            data = serialize_instance(statement)
            data['document'] = serialize_instance(statement.document)
            data['biomarkers'] = [serialize_instance(b) for b in statement.biomarkers]
            data['context'] = serialize_instance(statement.context)
            data.pop('document_id', None)

            #result.append(data)

            # data = {
            #     'id': statement.id,
            #     'description': statement.description,
            #     'evidence': statement.evidence,
            #     'last_updated': statement.last_updated,
            #     'deprecated': statement.deprecated,
            #     'document': {
            #         'id': statement.document.id,
            #         'label': statement.document.label,
            #         'description': statement.document.description,
            #         'alternative_labels': statement.document.alternative_labels,
            #         'citation': statement.document.citation,
            #         'document_type': statement.document.document_type,
            #         'drug_name_brand': statement.document.drug_name_brand,
            #         'drug_name_generic': statement.document.drug_name_generic,
            #         'first_published': statement.document.first_published,
            #         'last_updated': statement.document.last_updated,
            #         'organization': statement.document.organization,
            #         'publication_date': statement.document.publication_date,
            #         'url': statement.document.url,
            #         'url_epar': statement.document.url_epar
            #     },
            #     'biomarkers': [
            #         {
            #             'id': biomarker.id,
            #             'bioamrker_type': biomarker.biomarker_type
            #         }
            #         for biomarker in statement.biomarkers
            #     ],
            #     'context': {
            #         'id': statement.context
            #     },
            #     'implication': {
            #         'id': statement.implication
            #     },
            #     'indication': {
            #         'id': statement.indication
            #     }
            # }
            # data.pop('_sa_instance_state', None)
            result.append(data)

        return create_response(
            data=result,
            message="Statements successfully retrieved",
            status=200
        )
    finally:
        session.close()
