import datetime
import logging
import sqlalchemy
import typing

from sqlalchemy.orm import DeclarativeBase, Query
from werkzeug.datastructures import ImmutableMultiDict

from app import models


#logging.basicConfig()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


class BaseHandler:
    """
    A base class for handling SQL queries. This class provides common functionality for managing SQL queries and serves
    as a template for specific Handler classes, which inherit from BaseHandler and implement route-specific logic.
    """
    def __init__(self):
        """
        Initializes the BaseHandler class.
        """
        pass

    @staticmethod
    def construct_base_query(model: typing.Type[sqlalchemy.orm.DeclarativeBase]) -> sqlalchemy.Select:
        """
        Constructs a base SQLAlchemy select statement from the primary table model.

        This is Step 1 in managing the query.

        Args:
            model (typing.Type[sqlalchemy.orm.DeclarativeBase]): The SQLAlchemy model class representing the table.

        Returns:
            Select: A SQLAlchemy select statement for the provided `model`.
        """
        return sqlalchemy.select(model)

    @staticmethod
    def perform_joins(statement: sqlalchemy.Select, parameters: ImmutableMultiDict) -> sqlalchemy.Select:
        """
        Performs join operations on the query to include related tables. This is needed to perform filtering against
        any field from a related table. Joins are _not_ required for any tables not being filtered against. This
        function should be implemented by each route's Handler class.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.

        Returns:
            sqlalchemy.Select: The SQLAlchemy query after join operations are applied.

        Raises:
            NotImplementedError: If the route's Handler class does not implement this method.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def apply_joinedload(self, query: Query) -> Query:
        """
        Applies joinedload operations for eager loading of related records from other tables. This is needed to
        serialize fields from other tables. This function should be implemented by each route's Handler class.

        This is Step 3 of managing the query.

        Args:
            query (Query): The SQLAlchemy query to apply joinedload operations to.

        Returns:
            Query: The SQLAlchemy query after joinedload operations are applied.

        Raises:
            NotImplementedError: If the route's Handler class does not implement this method.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    @classmethod
    def apply_filters(cls, statement: sqlalchemy.Select, parameters: ImmutableMultiDict) -> sqlalchemy.Select:
        """
        Applies filters to the query, based on the parameters provided to the route. This function should be implemented
        by each route's Handler class, and it may reference apply_filter functions from other Handler classes.
        For example, when filtering propositions by biomarker name, the Propositions' Handler class may reference the
        Biomarker Handler class' apply_filters function.

        This is Step 4 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply filter operations to.
            parameters (ImmutableMultiDict): Parameters provided to the route as a flask.request.args.

        Returns:
            Query: The SQLAlchemy query after filter operations are applied.
        """
        filter_map = {
            'agent': models.Agents.name,
            'biomarker_type': models.Biomarkers.biomarker_type,
            'biomarker': models.Biomarkers.name,
            'contribution': models.Contributions.id,
            'disease': models.Diseases.name,
            'document': models.Documents.id,
            'gene': models.Genes.name,
            'indication': models.Indications.id,
            'organization': models.Organizations.name,
            #'strength': models.Strengths.id,
            'therapy': models.Therapies.name,
            'therapy_type': models.Therapies.therapy_type
        }

        and_conditions = []
        or_conditions = []

        filter_criteria = parameters
        for filter_key, filter_values in filter_criteria.items():
            column = filter_map.get(filter_key.lower(), None)
            if not column:
                continue

            filter_conditions = [column == value for value in filter_values]
            if len(filter_conditions) > 1:
                or_conditions.append(sqlalchemy.or_(*filter_conditions))
            else:
                and_conditions.append(filter_conditions[0])

        if and_conditions:
            statement = statement.where(sqlalchemy.and_(*and_conditions))
        if or_conditions:
            statement = statement.where(sqlalchemy.or_(*or_conditions))
        return statement

    @staticmethod
    def execute_query(session: sqlalchemy.orm.Session, statement: sqlalchemy.sql.Executable) -> list[DeclarativeBase]:
        """
        Executes the given SQLAlchemy statement and returns the results as a list of SQLAlchemy model instances.

        This is Step 5 of managing the query.

        Args:
            session (sqlalchemy.orm.Session): A session instance.
            statement (sqlalchemy.sql.Executable): The SQLAlchemy statement to execute.

        Returns:
            list[DeclarativeBase]: A list of SQLAlchemy model instances returned by the query.
        """
        result = session.execute(statement).unique()
        return result.scalars().all()

    @classmethod
    def serialize_instances(cls, instances: list[DeclarativeBase]) -> list[dict[str, typing.Any]]:
        """
        Serializes the fields populated by relationships with other tables, defined by this table's model
        and the applied joinedload operation.

        This is Step 6 of managing the query.

        Args:
            instances (list[DeclarativeBase]): A list of SQLAlchemy model instances to serialize.

        Returns:
            list[dict[str, typing.Any]]: A list of dictionaries with all keys serialized.

        Raises:
            NotImplementedError: If the route's Handler class does not implement this method.
        """
        result = []
        for instance in instances:
            serialized_instance = cls.serialize_single_instance(instance=instance)
            result.append(serialized_instance)
        return result

    @staticmethod
    def serialize_primary_instance(instance: sqlalchemy.orm.DeclarativeBase) -> dict[str, typing.Any]:
        """
        Serializes the fields of the primary table's records.

        This is Step 6.2 of managing the query.

        Args:
            instance (sqlalchemy.engine.row.Row): The SQLAlchemy Row object to convert.

        Returns:
            dict[str, typing.Any]: A dictionary representation of the Row object.
        """
        return {column.name: getattr(instance, column.name) for column in instance.__table__.columns}

    @staticmethod
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

    @staticmethod
    def convert_parameter_value(value: str) -> int | str:
        """
        Attempts to return the value as an integer, if possible. If not, returns the value as a lowercase string.

        Arg:
            value (str): The value to convert.

        Returns:
            int | str: The converted value.
        """
        try:
            return int(value)
        except ValueError:
            return value

    @classmethod
    def get_query_parameters(cls, arguments: ImmutableMultiDict) -> dict[str, int | str]:
        """
        Converts the request arguments to a dictionary, converting all keys and values to lowercase. If a provided value
        and attempts to convert values to integers, if applicable.

        Args:
            arguments (ImmutableMultiDict): The request arguments to convert.

        Returns:
            dict[str, int | str]: A dictionary containing the arguments passed to the route.
        """
        return {key.lower(): cls.convert_parameter_value(value) for key, value in arguments.to_dict().items()}

    @staticmethod
    def pop_keys(keys: list[str], record: dict[str, typing.Any]) -> None:
        for key in keys:
            record.pop(key, None)

    @classmethod
    def serialize_single_instance(cls, instance: sqlalchemy.orm.DeclarativeBase) -> dict[str, typing.Any]:
        raise NotImplementedError("Subclasses should implement this method.")

    @classmethod
    def get_parameters(cls, arguments):
        #return arguments.to_dict(flat=False)
        dictionary = arguments.to_dict(flat=False)
        for key, values in dictionary.items():
            new_values = []
            for value in values:
                new_value = cls.convert_parameter_value(value=value)
                new_values.append(new_value)
            dictionary[key] = new_values
        return dictionary


class Agents(BaseHandler):
    """
    Handler class to manage queries against the Agents table.
    """
    @staticmethod
    def perform_joins(statement: sqlalchemy.Select,
                      parameters: ImmutableMultiDict,
                      base_table=models.Agents,
                      joined_tables=None) -> sqlalchemy.Select:
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        agent_values = parameters.get('agent', None)
        if agent_values:
            if base_table in [models.Contributions, models.Statements] and models.Agents not in joined_tables:
                statement = statement.join(
                    models.Agents,
                    models.Agents.id == models.Contributions.agent_id
                )
                joined_tables.add(models.Agents)
            elif base_table != models.Agents:
                raise ValueError(f'Unsupported base table for Diseases.perform_joins: {base_table}.')

            conditions = [models.Agents.name.in_(agent_values)]
            statement = statement.where(sqlalchemy.and_(*conditions))

        return statement, joined_tables

    def apply_joinedload(self, query: Query) -> Query:
        """
        3. Joinedload Operations: A function to apply joinedload options for eager loading.

        """
        return query

    def apply_filters(self, query: Query, **filters: dict[str, int | str]) -> Query:
        return query

    @classmethod
    def serialize_single_instance(cls, instance: models.Agents) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_primary_instance(instance=instance)
#        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)

        #keys_to_remove = [
        #]
        #cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Agents, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return record


class Biomarkers(BaseHandler):
    """
    Handler class to manage queries against the Biomarkers table.
    """

    @staticmethod
    def perform_joins(
            statement: sqlalchemy.Select,
            parameters: ImmutableMultiDict,
            base_table=models.Biomarkers,
            joined_tables=None) -> sqlalchemy.Select:
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        biomarker_values = parameters.get('biomarker', None)
        biomarker_type_values = parameters.get('biomarker_type', None)
        gene_values = parameters.get('gene', None)
        if biomarker_values or biomarker_type_values or gene_values:
            b_p = models.AssociationBiomarkersAndPropositions
            if base_table in [models.Propositions, models.Statements] and b_p not in joined_tables:
                statement = statement.join(
                    b_p,
                    b_p.proposition_id == models.Propositions.id
                )
                joined_tables.add(b_p)

                statement = statement.join(
                    models.Biomarkers,
                    models.Biomarkers.id == b_p.biomarker_id
                )
                joined_tables.add(models.Biomarkers)
            elif base_table != models.Biomarkers:
                raise ValueError(f'Unsupported base table for Biomarkers.perform_joins: {base_table}.')

            conditions = []
            if biomarker_values:
                conditions.append(models.Biomarkers.name.in_(biomarker_values))
            if biomarker_type_values:
                conditions.append(models.Biomarkers.biomarker_type.in_(biomarker_type_values))
            statement = statement.where(sqlalchemy.and_(*conditions))

            statement, joined_tables = Genes.perform_joins(
                statement=statement,
                parameters=parameters,
                base_table=base_table,
                joined_tables=joined_tables
            )

        return statement, joined_tables

    def apply_joinedload(self, query: Query) -> Query:
        """
        3. Joinedload Operations: A function to apply joinedload options for eager loading.

        """
        return query

    def apply_filters(self, query: Query, **filters: dict[str, int | str]) -> Query:
        return query

    @staticmethod
    def convert_fields_to_extensions(record: dict[str, typing.Any]) -> list[dict[str, typing.Any]]:
        extensions = []
        fields = [
            'biomarker_type',
            'present',
            'marker',
            'unit',
            'equality',
            'value',
            'chromosome',
            'start_position',
            'end_position',
            'reference_allele',
            'alternate_allele',
            'cdna_change',
            'protein_change',
            'variant_annotation',
            'exon',
            'rsid',
            'hgvsg',
            'hgsvc',
            'requires_oncogenic',
            'requires_pathogenic',
            'rearrangement_type',
            'locus',
            'direction',
            'cytoband',
            'arm',
            'status'
        ]
        for field in fields:
            if record.get(field, None):
                extensions.append({'name': field, 'value': record.get(field, None)})
        return extensions

    @classmethod
    def serialize_single_instance(cls, instance: models.Biomarkers) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['type'] = 'CategoricalVariant'
        serialized_record['extensions'] = cls.convert_fields_to_extensions(record=serialized_record)
        keys_to_remove = [
            'biomarker_type',
            'present',
            'marker',
            'unit',
            'equality',
            'value',
            'chromosome',
            'start_position',
            'end_position',
            'reference_allele',
            'alternate_allele',
            'cdna_change',
            'protein_change',
            'variant_annotation',
            'exon',
            'rsid',
            'hgvsg',
            'hgvsc',
            'requires_oncogenic',
            'requires_pathogenic',
            'rearrangement_type',
            'locus',
            'direction',
            'cytoband',
            'arm',
            'status'
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Biomarkers, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['genes'] = Genes.serialize_instances(instances=instance.genes)
        return record


class Codings(BaseHandler):
    """
    Handler class to manage queries against the Codings table.
    """

    def perform_joins(self, query: Query, parameters: dict[str, int | str] = None) -> Query:
        """
        """

        return query

    def apply_joinedload(self, query: Query) -> Query:
        """
        3. Joinedload Operations: A function to apply joinedload options for eager loading.

        """
        return query

    def apply_filters(self, query: Query, **filters: dict[str, int | str]) -> Query:
        return query

    @classmethod
    def serialize_single_instance(cls, instance: models.Codings) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_primary_instance(instance=instance)
        #serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['iris'] = [serialized_record['iris']]
        return serialized_record

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Codings, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return record


class Contributions(BaseHandler):
    """
    Handler class to manage queries against the Contributions table.
    """
    @staticmethod
    def perform_joins(statement: sqlalchemy.Select,
                      parameters: ImmutableMultiDict,
                      base_table=models.Contributions,
                      joined_tables=None) -> sqlalchemy.Select:
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        agent_values = parameters.get('agent', None)
        contribution_values = parameters.get('contribution', None)
        # Could expand this to have a filter criteria based on contribution date
        if agent_values or contribution_values:
            c_s = models.AssociationContributionsAndStatements
            if base_table in [models.Statements] and c_s not in joined_tables:
                statement = statement.join(
                    c_s,
                    c_s.statement_id == models.Statements.id
                )
                joined_tables.add(c_s)

                statement = statement.join(
                    models.Contributions,
                    models.Contributions.id == c_s.contribution_id
                )
                joined_tables.add(models.Contributions)
            elif base_table != models.Contributions:
                raise ValueError(f'Unsupported base table for Contributions.perform_joins: {base_table}.')

            conditions = []
            if contribution_values:
                conditions = [models.Contributions.id.in_(contribution_values)]
            statement = statement.where(sqlalchemy.and_(*conditions))

            statement, joined_tables = Agents.perform_joins(
                statement=statement,
                parameters=parameters,
                base_table=base_table,
                joined_tables=joined_tables
            )

        return statement, joined_tables

    def apply_joinedload(self, query: Query) -> Query:
        """
        3. Joinedload Operations: A function to apply joinedload options for eager loading.

        """
        return query

    def apply_filters(self, query: Query, **filters: dict[str, int | str]) -> Query:
        return query

    @classmethod
    def serialize_single_instance(cls, instance: models.Contributions) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['date'] = cls.convert_date_to_iso(value=instance.date)

        keys_to_remove = [
            'agent_id'
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Contributions, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['agent'] = cls.serialize_primary_instance(instance=instance.agent)
        return record


class Diseases(BaseHandler):
    """
    Handler class to manage queries against the Diseases table.
    """
    @staticmethod
    def perform_joins(statement: sqlalchemy.Select,
                      parameters: ImmutableMultiDict,
                      base_table=models.Diseases,
                      joined_tables=None) -> sqlalchemy.Select:
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        disease_values = parameters.get('disease', None)
        if disease_values:
            if base_table in [models.Propositions, models.Statements] and models.Diseases not in joined_tables:
                statement = statement.join(
                    models.Diseases,
                    models.Diseases.id == models.Propositions.condition_qualifier_id
                )
                joined_tables.add(models.Diseases)
            elif base_table != models.Diseases:
                raise ValueError(f'Unsupported base table for Diseases.perform_joins: {base_table}.')

            conditions = [models.Diseases.name.in_(disease_values)]
            statement = statement.where(sqlalchemy.and_(*conditions))

        return statement, joined_tables

    def apply_joinedload(self, query: Query) -> Query:
        """
        3. Joinedload Operations: A function to apply joinedload options for eager loading.

        """
        return query

    def apply_filters(self, query: Query, **filters: dict[str, int | str]) -> Query:
        return query

    @staticmethod
    def convert_fields_to_extensions(instance: models.Diseases):
        return [
            {
                'name': 'solid_tumor',
                'value': instance.solid_tumor,
                'description': 'Boolean value for if this tumor type is categorized as a solid tumor.'
            }
        ]

    @classmethod
    def serialize_single_instance(cls, instance: models.Diseases) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['conceptType'] = serialized_record['concept_type']
        serialized_record['extensions'] = cls.convert_fields_to_extensions(instance=instance)

        keys_to_remove = [
            'concept_type',
            'primary_coding_id',
            'solid_tumor',
            'therapy_strategy_description',
            'therapy_type',
            'therapy_type_description'
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Diseases, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['primaryCoding'] = Codings.serialize_single_instance(instance=instance.primary_coding)
        record['mappings'] = Mappings.serialize_instances(instances=instance.mappings)
        return record


class Documents(BaseHandler):
    """
    Handler class to manage queries against the Documents table.
    """
    @staticmethod
    def perform_joins(
            statement: sqlalchemy.Select,
            parameters: ImmutableMultiDict,
            base_table=models.Documents,
            joined_tables=None) -> sqlalchemy.Select:
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        documents_via_statements = sqlalchemy.orm.aliased(models.Documents)
        documents_via_indications = sqlalchemy.orm.aliased(models.Documents)

        document_values = parameters.get('document', None)
        organization_values = parameters.get('organization', None)
        if document_values or organization_values:
            if base_table == models.Documents and models.Documents not in joined_tables:
                conditions = [models.Documents.id.in_(document_values)]
                statement = statement.where(sqlalchemy.and_(*conditions))
            elif base_table in [models.Indications, models.Statements] and models.Documents not in joined_tables:
                conditions = []
                d_s = models.AssociationDocumentsAndStatements
                statement = statement.join(
                    d_s,
                    d_s.statement_id == models.Statements.id
                )
                joined_tables.add(d_s)

                statement = statement.join(
                    documents_via_statements,
                    documents_via_statements.id == d_s.document_id
                )
                joined_tables.add(models.Documents)
                if document_values:
                    conditions.append(documents_via_statements.id.in_(document_values))

                statement = statement.join(
                    documents_via_indications,
                    documents_via_indications.id == models.Indications.document_id
                )
                joined_tables.add(models.Documents)
                if document_values:
                    conditions.append(documents_via_indications.id.in_(document_values))

                if len(conditions) > 1:
                    combined_condition = sqlalchemy.or_(*conditions)
                elif conditions:
                    combined_condition = conditions[0]
                else:
                    combined_condition = None

                if combined_condition is not None:
                    statement = statement.where(sqlalchemy.and_(combined_condition))
            elif base_table != models.Documents:
                raise ValueError(f'Unsupported base table for Documents.perform_joins: {base_table}.')

            statement, joined_tables = Organizations.perform_joins(
                statement=statement,
                parameters=parameters,
                base_table=base_table,
                joined_tables=joined_tables,
                documents_via_statements=documents_via_statements,
                documents_via_indications=documents_via_indications
            )

        return statement, joined_tables

    def apply_joinedload(self, query: Query) -> Query:
        """
        3. Joinedload Operations: A function to apply joinedload options for eager loading.

        """
        return query

    def apply_filters(self, query: Query, **filters: dict[str, int | str]) -> Query:
        return query

    @classmethod
    def serialize_single_instance(cls, instance: models.Documents) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['first_published'] = cls.convert_date_to_iso(value=instance.first_published) if instance.first_published else None
        serialized_record['access_date'] = cls.convert_date_to_iso(value=instance.access_date) if instance.access_date else None
        serialized_record['publication_date'] = cls.convert_date_to_iso(value=instance.publication_date)
        return serialized_record

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Documents, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['organization'] = Organizations.serialize_single_instance(instance=instance.organization)
        record.pop('organization_id', None)
        return record


class Genes(BaseHandler):
    """
    Handler class to manage queries against the Genes table.
    """
    @staticmethod
    def perform_joins(
            statement: sqlalchemy.Select,
            parameters: ImmutableMultiDict,
            base_table=models.Genes,
            joined_tables=None) -> sqlalchemy.Select:
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        gene_values = parameters.get('gene', None)
        if gene_values:
            b_g = models.AssociationBiomarkersAndGenes
            if base_table in [models.Biomarkers, models.Propositions, models.Statements] and b_g not in joined_tables:
                statement = statement.join(b_g, b_g.biomarker_id == models.Biomarkers.id)
                joined_tables.add(b_g)

                statement = statement.join(models.Genes, models.Genes.id == b_g.gene_id)
                joined_tables.add(models.Genes)
            elif base_table != models.Genes:
                raise ValueError(f'Unsupported base table for Genes.perform_joins: {base_table}.')

            conditions = [models.Genes.name.in_(gene_values)]
            statement = statement.where(sqlalchemy.and_(*conditions))

        return statement, joined_tables

    def apply_joinedload(self, query: Query) -> Query:
        """
        3. Joinedload Operations: A function to apply joinedload options for eager loading.

        """
        return query

    def apply_filters(self, query: Query, **filters: dict[str, int | str]) -> Query:
        return query

    @staticmethod
    def convert_fields_to_extensions(instance: models.Genes):
        return [
            {
                'name': 'location',
                'value': instance.location
            },
            {
                'name': 'location_sortable',
                'value': instance.location_sortable
            }
        ]

    @classmethod
    def serialize_single_instance(cls, instance: models.Genes) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['extensions'] = cls.convert_fields_to_extensions(instance=instance)

        keys_to_remove = [
            'primary_coding_id',
            'location',
            'location_sortable'
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Genes, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['primaryCoding'] = Codings.serialize_single_instance(instance=instance.primary_coding)
        record['mappings'] = Mappings.serialize_instances(instances=instance.mappings)
        return record


class Indications(BaseHandler):
    """
    Handler class to manage queries against the Indications table.
    """

    @staticmethod
    def perform_joins(
            statement: sqlalchemy.Select,
            parameters: ImmutableMultiDict,
            base_table=models.Indications,
            joined_tables=None) -> sqlalchemy.Select:
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        document_values = parameters.get('document', None)
        indication_values = parameters.get('indication', None)
        organization_values = parameters.get('organization', None)
        if document_values or indication_values or organization_values:
            if base_table in [models.Statements] and models.Indications not in joined_tables:
                statement = statement.join(
                    models.Indications,
                    models.Indications.id == models.Statements.indication_id
                )
                joined_tables.add(models.Indications)
            elif base_table != models.Indications:
                raise ValueError(f'Unsupported base table for Indications.perform_joins: {base_table}.')

            conditions = []
            if indication_values:
                conditions.append(models.Indications.id.in_(indication_values))
            statement = statement.where(sqlalchemy.and_(*conditions))

            if base_table in [models.Documents] and models.Documents not in joined_tables:
                statement, joined_tables = Documents.perform_joins(
                    statement=statement,
                    parameters=parameters,
                    base_table=base_table,
                    joined_tables=joined_tables
                )

        return statement, joined_tables

    def apply_joinedload(self, query: Query) -> Query:
        """
        3. Joinedload Operations: A function to apply joinedload options for eager loading.

        """
        return query

    def apply_filters(self, query: Query, **filters: dict[str, int | str]) -> Query:
        return query

    @classmethod
    def serialize_single_instance(cls, instance: models.Indications) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['initial_approval_date'] = cls.convert_date_to_iso(value=instance.initial_approval_date) if instance.initial_approval_date else None
        serialized_record['reimbursement_date'] = cls.convert_date_to_iso(value=instance.reimbursement_date) if instance.reimbursement_date else None
        serialized_record['date_regular_approval'] = cls.convert_date_to_iso(value=instance.date_regular_approval) if instance.date_regular_approval else None
        serialized_record['date_accelerated_approval'] = cls.convert_date_to_iso(value=instance.date_accelerated_approval) if instance.date_accelerated_approval else None
        return serialized_record

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Indications, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['document'] = Documents.serialize_single_instance(instance=instance.document)
        record.pop('document_id', None)
        return record


class Mappings(BaseHandler):
    """
    Handler class to manage queries against the Mappings table.
    """

    def perform_joins(self, query: Query, parameters: dict[str, int | str] = None) -> Query:
        """
        """

        return query

    def apply_joinedload(self, query: Query) -> Query:
        """
        3. Joinedload Operations: A function to apply joinedload options for eager loading.

        """
        return query

    def apply_filters(self, query: Query, **filters: dict[str, int | str]) -> Query:
        return query

    @classmethod
    def serialize_single_instance(cls, instance: models.Mappings) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)

        keys_to_remove = [
            'primary_coding_id',
            'coding_id'
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Mappings, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['coding'] = Codings.serialize_single_instance(instance=instance.coding)
        return record


class Organizations(BaseHandler):
    """
    Handler class to manage queries against the Organizations table.
    """
    @staticmethod
    def perform_joins(statement: sqlalchemy.Select,
                      parameters: ImmutableMultiDict,
                      base_table=models.Organizations,
                      joined_tables=None,
                      documents_via_statements=None,
                      documents_via_indications=None) -> sqlalchemy.Select:
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        organizations_via_statements = sqlalchemy.orm.aliased(models.Organizations)
        organizations_via_indications = sqlalchemy.orm.aliased(models.Organizations)

        organization_values = parameters.get('organization', None)
        if organization_values:
            if base_table == models.Organizations and models.Organizations not in joined_tables:
                conditions = [models.Organizations.name.in_(organization_values)]
                statement = statement.where(sqlalchemy.and_(*conditions))
            elif base_table in [models.Documents, models.Indications, models.Statements] and models.Organizations not in joined_tables:
                conditions = []
                if documents_via_statements:
                    statement = statement.join(
                        organizations_via_statements,
                        organizations_via_statements.id == documents_via_statements.organization_id
                    )
                    conditions.append(organizations_via_statements.name.in_(organization_values))
                if documents_via_indications:
                    statement = statement.join(
                        organizations_via_indications,
                        organizations_via_indications.id == documents_via_indications.organization_id
                    )
                    conditions.append(organizations_via_indications.name.in_(organization_values))
                if not (documents_via_statements or documents_via_indications):
                    message = f'Basetable specified as {base_table} to Organizations.perform_joins without providing document alias(es).'
                    raise ValueError(message)
                joined_tables.add(models.Organizations)

                if len(conditions) > 1:
                    combined_condition = sqlalchemy.or_(*conditions)
                elif conditions:
                    combined_condition = conditions[0]
                else:
                    combined_condition = None

                if combined_condition is not None:
                    statement = statement.where(sqlalchemy.and_(combined_condition))
            elif base_table != models.Organizations:
                raise ValueError(f'Unsupported base table for Organizations.perform_joins: {base_table}.')

        return statement, joined_tables

    def apply_joinedload(self, query: Query) -> Query:
        """
        3. Joinedload Operations: A function to apply joinedload options for eager loading.

        """
        return query

    def apply_filters(self, query: Query, **filters: dict[str, int | str]) -> Query:
        return query

    @classmethod
    def serialize_single_instance(cls, instance: models.Organizations) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_primary_instance(instance=instance)
        #serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['last_updated'] = cls.convert_date_to_iso(value=instance.last_updated)
        return serialized_record

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Organizations, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return record


class Propositions(BaseHandler):
    """
    Handler class to manage queries against the Propositions table.
    """
    @staticmethod
    def perform_joins(statement: sqlalchemy.Select,
                      parameters: ImmutableMultiDict,
                      base_table=models.Propositions,
                      joined_tables=None) -> sqlalchemy.Select:
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        if base_table == models.Statements and models.Propositions not in joined_tables:
            statement = statement.join(models.Propositions, models.Statements.proposition_id == models.Propositions.id)
            joined_tables.add(models.Propositions)
        elif base_table != models.Propositions:
            raise ValueError(f'Unsupported base table for Propositions.perform_joins: {base_table}.')

        statement, joined_tables = Biomarkers.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables
        )
        statement, joined_tables = Diseases.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables
        )
        statement, joined_tables = Therapies.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables
        )

        return statement, joined_tables

    def apply_joinedload(self, query: Query) -> Query:
        """
        3. Joinedload Operations: A function to apply joinedload options for eager loading.

        """
        return query

    def apply_filters(self, query: Query, **filters: dict[str, int | str]) -> Query:
        return query

    @classmethod
    def serialize_target_therapeutic(cls, therapy: models.Propositions.therapy, therapy_group: models.Propositions.therapy_group) -> dict[str, typing.Any]:
        if therapy:
            return Therapies.serialize_single_instance(instance=therapy)
        else:
            return TherapyGroups.serialize_single_instance(instance=therapy_group)

    @classmethod
    def serialize_single_instance(cls, instance: models.Propositions) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)

        keys_to_remove = [
            'condition_qualifier_id',
            'strength_id',
            'therapy_id',
            'therapy_group_id'
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Propositions, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['biomarkers'] = Biomarkers.serialize_instances(instances=instance.biomarkers)
        record['conditionQualifier'] = Diseases.serialize_single_instance(instance=instance.condition_qualifier)
        record['targetTherapeutic'] = cls.serialize_target_therapeutic(therapy=instance.therapy, therapy_group=instance.therapy_group)
        return record


class Statements(BaseHandler):
    """
    Handler class to manage queries against the Statements table.
    """
    @staticmethod
    def perform_joins(statement: sqlalchemy.Select,
                      parameters: ImmutableMultiDict,
                      base_table=models.Statements,
                      joined_tables=None) -> sqlalchemy.Select:
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        statement, joined_tables = Contributions.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables
        )
        statement, joined_tables = Documents.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables
        )
        statement, joined_tables = Indications.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables
        )
        statement, joined_tables = Propositions.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables
        )
        statement, joined_tables = Strengths.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables
        )

        return statement, joined_tables

    def perform_joins_(self, query: Query, parameters: ImmutableMultiDict) -> Query:
        """
            Allow filtering based on:
            - Biomarker name
            - Biomarker type
            - Biomarker coding (name for now, probably?) -- first pass
            - Gene name
            - Gene coding -- first pass
            - Disease coding -- first pass
            - Therapy name coding -- first pass
            - Therapy strategy -- not yet implemented
            - Therapy type coding -- first pass
            - Document name
            - Document organization -- first pass
            - Indication id (or name?) -- first pass
            - Strength coding
            - Contribution id
            - Contribution date -- not yet implemented
            - Agent name
            - Proposition id -- first pass
            - Statement id -- don't need a join
        """
        if parameters is {} or None:
            return query

        CodingFromGene = sqlalchemy.orm.aliased(models.Codings)
        CodingFromDisease = sqlalchemy.orm.aliased(models.Codings)
        CodingFromTherapy = sqlalchemy.orm.aliased(models.Codings)

        MappingFromGene = sqlalchemy.orm.aliased(models.Mappings)
        MappingFromDisease = sqlalchemy.orm.aliased(models.Mappings)
        MappingFromTherapy = sqlalchemy.orm.aliased(models.Mappings)

        OrganizationFromDocument = sqlalchemy.orm.aliased(models.Organizations)

        DocumentFromStatement = sqlalchemy.orm.aliased(models.Documents)
        DocumentFromIndication = sqlalchemy.orm.aliased(models.Documents)

        parameter_fields = set(parameters.to_dict(flat=False).keys())

        # Join for Propositions
        query = (
            query
            .join(models.Propositions, models.Statements.proposition_id == models.Propositions.id)
        )
        # Propositions - join for biomarkers and genes
        biomarkers_propositions = models.AssociationBiomarkersAndPropositions
        biomarkers_genes = models.AssociationBiomarkersAndGenes
        genes_mappings = models.AssociationGenesAndMappings
        alias_genes = sqlalchemy.orm.aliased(models.Genes)
        alias_codings_p_genes = sqlalchemy.orm.aliased(models.Codings)
        alias_codings_genes = sqlalchemy.orm.aliased(models.Codings)
        alias_mappings_genes = sqlalchemy.orm.aliased(models.Mappings)
        query = (
            query
            .join(biomarkers_propositions, models.Propositions.id == biomarkers_propositions.proposition_id)
            .join(models.Biomarkers, biomarkers_propositions.biomarker_id == models.Biomarkers.id)
            .join(biomarkers_genes, models.Biomarkers.id == biomarkers_genes.biomarker_id)
            .join(models.Genes, biomarkers_genes.gene_id == models.Genes.id)
            .join(alias_codings_p_genes, models.Genes.primary_coding_id == alias_codings_p_genes.id)

            .join(genes_mappings, models.Genes.id == genes_mappings.gene_id)
            .join(alias_mappings_genes, genes_mappings.mapping_id == alias_mappings_genes.id)
            .join(alias_codings_genes, alias_mappings_genes.coding_id == alias_codings_genes.id)
        )
        # Propositions - join for diseases
        diseases_mappings = models.AssociationDiseasesAndMappings
        alias_codings_p_diseases = sqlalchemy.orm.aliased(models.Codings)
        alias_codings_diseases = sqlalchemy.orm.aliased(models.Codings)
        alias_mappings_diseases = sqlalchemy.orm.aliased(models.Mappings)
        query = (
            query
            .join(models.Diseases, models.Propositions.condition_qualifier_id == models.Diseases.id)
            .join(alias_codings_p_diseases, models.Diseases.primary_coding_id == alias_codings_p_diseases.id)

            .join(diseases_mappings, models.Diseases.id == diseases_mappings.disease_id)
            .join(alias_mappings_diseases, diseases_mappings.mapping_id == alias_mappings_diseases.id)
            .join(alias_codings_diseases, alias_mappings_diseases.coding_id == alias_codings_diseases.id)
        )
        # Propositions - join for therapies
        therapies_therapy_groups = models.AssociationTherapyAndTherapyGroup
        alias_codings_p_therapies = sqlalchemy.orm.aliased(models.Codings)
        alias_codings_p_therapies_tg = sqlalchemy.orm.aliased(models.Codings)
        alias_mappings_therapies = sqlalchemy.orm.aliased(models.Mappings)
        alias_mappings_therapy_groups = sqlalchemy.orm.aliased(models.Mappings)
        alias_therapies = sqlalchemy.orm.aliased(models.Therapies)
        query = (
            query
            .join(models.Therapies, models.Propositions.therapy_id == models.Therapies.id)
            .join(alias_codings_p_therapies, models.Therapies.primary_coding_id == alias_codings_p_therapies.id)

            # .join(models.TherapyGroups, models.Propositions.therapy_group_id == models.TherapyGroups.id)
            # .join(therapies_therapy_groups, models.TherapyGroups.id == therapies_therapy_groups.therapy_group_id)
            # .join(alias_therapies, therapies_therapy_groups.therapy_id == alias_therapies.id)
            # .join(alias_codings_p_therapies_tg, models.Therapies.primary_coding_id == alias_codings_p_therapies_tg.id)
        )

        # Strengths
        alias_codings_strengths = sqlalchemy.orm.aliased(models.Codings)
        query = (
            query
            .join(models.Strengths, models.Statements.strength_id == models.Strengths.id)
            .join(alias_codings_strengths, models.Strengths.primary_coding_id == alias_codings_strengths.id)
        )

        # Documents
        documents_statements = models.AssociationDocumentsAndStatements
        alias_documents_statements = sqlalchemy.orm.aliased(models.Documents)
        alias_organizations_statements = sqlalchemy.orm.aliased(models.Organizations)
        query = (
            query
            .join(documents_statements, models.Statements.id == documents_statements.statement_id)
            .join(alias_documents_statements, documents_statements.document_id == alias_documents_statements.id)
            .join(alias_organizations_statements, alias_documents_statements.organization_id == alias_organizations_statements.id)
        )

        # Indications
        alias_documents_indications = sqlalchemy.orm.aliased(models.Documents)
        alias_organizations_indications = sqlalchemy.orm.aliased(models.Organizations)
        query = (
            query
            .join(models.Indications, models.Statements.indication_id == models.Indications.id)
            .join(alias_documents_indications, models.Indications.document_id == alias_documents_indications.id)
            .join(alias_organizations_indications, alias_documents_indications.organization_id == alias_organizations_indications.id)
        )

        # Contributions
        contributions_statements = models.AssociationContributionsAndStatements
        query = (
            query
            .join(contributions_statements, models.Statements.id == contributions_statements.statements_id)
            .join(models.Contributions, contributions_statements.contribution_id == models.Contributions.id)
            .join(models.Agents, models.Contributions.agent_id == models.Agents.id)
        )

        """
        proposition_fields = {
            'biomarker',
            'biomarker_type',
            'disease',
            'gene',
            'therapy',
            'therapy_strategy',
            'therapy_type'
        }
        if proposition_fields.intersection(parameter_fields):
            query = (
                query
                .join(models.Propositions, models.Statements.proposition_id == models.Propositions.id)
            )
            if {'biomarker', 'biomarker_type', 'gene'}.intersection(parameter_fields):
                biomarkers_propositions = models.AssociationBiomarkersAndPropositions
                biomarkers_genes = models.AssociationBiomarkersAndGenes
                genes_mappings = models.AssociationGenesAndMappings

                alias_genes = sqlalchemy.orm.aliased(models.Genes)
                alias_codings_p_genes = sqlalchemy.orm.aliased(models.Codings)
                alias_codings_genes = sqlalchemy.orm.aliased(models.Codings)
                alias_mappings_genes = sqlalchemy.orm.aliased(models.Mappings)
                query = (
                    query
                    .join(biomarkers_propositions, models.Propositions.id == biomarkers_propositions.proposition_id)
                    .join(models.Biomarkers, biomarkers_propositions.biomarker_id == models.Biomarkers.id)
                    .join(biomarkers_genes, models.Biomarkers.id == biomarkers_genes.biomarker_id)
                    .join(models.Genes, biomarkers_genes.gene_id == models.Genes.id)
                    .join(alias_codings_p_genes, models.Genes.primary_coding_id == alias_codings_p_genes.id)

                    .join(genes_mappings, models.Genes.id == genes_mappings.gene_id)
                    .join(alias_mappings_genes, genes_mappings.mapping_id == alias_mappings_genes.id)
                    .join(alias_codings_genes, alias_mappings_genes.coding_id == alias_codings_genes.id)
                )
            if {'disease'}.intersection(parameter_fields):
                diseases_mappings = models.AssociationDiseasesAndMappings
                alias_codings_p_diseases = sqlalchemy.orm.aliased(models.Codings)
                alias_codings_diseases = sqlalchemy.orm.aliased(models.Codings)
                alias_mappings_diseases = sqlalchemy.orm.aliased(models.Mappings)
                query = (
                    query
                    .join(models.Diseases, models.Propositions.condition_qualifier_id == models.Diseases.id)
                    .join(alias_codings_p_diseases, models.Diseases.primary_coding_id == alias_codings_p_diseases.id)

                    .join(diseases_mappings, models.Diseases.id == diseases_mappings.disease_id)
                    .join(alias_mappings_diseases, diseases_mappings.mapping_id == alias_mappings_diseases.id)
                    .join(alias_codings_diseases, alias_mappings_diseases.coding_id == alias_codings_diseases.id)
                )
            if {'therapy', 'therapy_strategy', 'therapy_type'}.intersection(parameter_fields):
                therapies_therapy_groups = models.AssociationTherapyAndTherapyGroup
                alias_codings_p_therapies = sqlalchemy.orm.aliased(models.Codings)
                alias_codings_p_therapies_tg = sqlalchemy.orm.aliased(models.Codings)
                alias_mappings_therapies = sqlalchemy.orm.aliased(models.Mappings)
                alias_mappings_therapy_groups = sqlalchemy.orm.aliased(models.Mappings)
                alias_therapies = sqlalchemy.orm.aliased(models.Therapies)
                query = (
                    query
                    .join(models.Therapies, models.Propositions.therapy_id == models.Therapies.id)
                    .join(alias_codings_p_therapies, models.Therapies.primary_coding_id == alias_codings_p_therapies.id)

                    #.join(models.TherapyGroups, models.Propositions.therapy_group_id == models.TherapyGroups.id)
                    #.join(therapies_therapy_groups, models.TherapyGroups.id == therapies_therapy_groups.therapy_group_id)
                    #.join(alias_therapies, therapies_therapy_groups.therapy_id == alias_therapies.id)
                    #.join(alias_codings_p_therapies_tg, models.Therapies.primary_coding_id == alias_codings_p_therapies_tg.id)
                )
        """
        return query

    def apply_joinedload(self, statement: sqlalchemy.Select) -> sqlalchemy.Select:
        """
        Applies joinedload operations for eager loading of related records from other tables. This is needed to
        serialize fields from other tables. This function should be implemented by each route's Handler class.

        This is Step 3 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply joinedload operations to.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after joinedload operations are applied.
        """
        eager_load_options = [
            (
                sqlalchemy.orm.joinedload(models.Statements.contributions)
                .joinedload(models.Contributions.agent)
            ),
            (
                sqlalchemy.orm.joinedload(models.Statements.documents)
                .joinedload(models.Documents.organization)
             ),
            (
                sqlalchemy.orm.joinedload(models.Statements.indication)
                .joinedload(models.Indications.document)
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
        return statement.options(*eager_load_options)

    @classmethod
    def serialize_single_instance(cls, instance: models.Statements) -> dict[str, typing.Any]:
        """
        This is Step 6.1 of managing the query.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)

        keys_to_remove = [
            'indication_id',
            'proposition_id',
            'strength_id'
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Statements, record: dict[str, typing.Any]):
        """
        This is step 6.3
        """
        record['contributions'] = Contributions.serialize_instances(instances=instance.contributions)
        record['indication'] = Indications.serialize_single_instance(instance=instance.indication)
        record['reportedIn'] = Documents.serialize_instances(instances=instance.documents)
        record['proposition'] = Propositions.serialize_single_instance(instance=instance.proposition)
        record['strengths'] = Strengths.serialize_single_instance(instance=instance.strength)
        return record


class Strengths(BaseHandler):
    """
    Handler class to manage queries against the Strengths table.
    """
    @staticmethod
    def perform_joins(statement: sqlalchemy.Select,
                      parameters: ImmutableMultiDict,
                      base_table=models.Strengths,
                      joined_tables=None) -> sqlalchemy.Select:
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        """
        I'm not sure what this will look like, but it will likely be a join to the codings and mappings table
        statement, joined_tables = Codings.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables
        )
        """

        return statement, joined_tables

    def apply_joinedload(self, query: Query) -> Query:
        """
        3. Joinedload Operations: A function to apply joinedload options for eager loading.

        """
        return query

    def apply_filters(self, query: Query, **filters: dict[str, int | str]) -> Query:
        return query

    @classmethod
    def serialize_single_instance(cls, instance: models.Strengths) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['conceptType'] = serialized_record['concept_type']

        keys_to_remove = [
            'concept_type',
            'primary_coding_id'
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Strengths, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['primaryCoding'] = Codings.serialize_single_instance(instance=instance.primary_coding)
        #record['mappings'] = Mappings.serialize_instances(instances=instance.mappings)
        return record


class Therapies(BaseHandler):
    """
    Handler class to manage queries against the Therapies table.
    """
    @staticmethod
    def perform_joins(
            statement: sqlalchemy.Select,
            parameters: ImmutableMultiDict,
            base_table=models.Therapies,
            joined_tables=None) -> sqlalchemy.Select:
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        therapy_values = parameters.get('therapy', None)
        therapy_type_values = parameters.get('therapy_type', None)
        if therapy_values or therapy_type_values:
            therapies_direct = sqlalchemy.orm.aliased(models.Therapies)
            therapies_indirect = sqlalchemy.orm.aliased(models.Therapies)
            if base_table in [models.Propositions, models.Statements] and models.Therapies not in joined_tables:
                # Outerjoin because sometimes therapy_id is null
                statement = statement.outerjoin(
                    therapies_direct,
                    therapies_direct.id == models.Propositions.therapy_id
                )
                joined_tables.add(models.Therapies)

                statement = statement.outerjoin(
                    models.TherapyGroups,
                    models.TherapyGroups.id == models.Propositions.therapy_group_id
                )
                joined_tables.add(models.TherapyGroups)

                statement = statement.outerjoin(
                    models.AssociationTherapyAndTherapyGroup,
                    models.AssociationTherapyAndTherapyGroup.therapy_group_id == models.TherapyGroups.id
                )
                joined_tables.add(models.AssociationTherapyAndTherapyGroup)

                statement = statement.outerjoin(
                    therapies_indirect,
                    therapies_indirect.id == models.AssociationTherapyAndTherapyGroup.therapy_id
                )
                joined_tables.add(models.Therapies)
            elif base_table != models.Therapies:
                raise ValueError(f'Unsupported base table for Biomarkers.perform_joins: {base_table}.')

            conditions = []
            if therapy_values:
                condition_direct = therapies_direct.name.in_(therapy_values)
                condition_indirect = therapies_indirect.name.in_(therapy_values)
                conditions.append((condition_direct | condition_indirect))
            if therapy_type_values:
                condition_direct = therapies_direct.therapy_type.in_(therapy_type_values)
                condition_indirect = therapies_indirect.therapy_type.in_(therapy_type_values)
                conditions.append((condition_direct | condition_indirect))
            statement = statement.where(sqlalchemy.and_(*conditions))

        return statement, joined_tables

    def apply_joinedload(self, query: Query) -> Query:
        """
        3. Joinedload Operations: A function to apply joinedload options for eager loading.

        """
        return query

    def apply_filters(self, query: Query, **filters: dict[str, int | str]) -> Query:
        return query

    @staticmethod
    def convert_fields_to_extensions(instance: models.Therapies):
        return [
            {
                'name': 'therapy_strategy',
                'value': instance.therapy_strategy,
                'description': 'Description...'
            },
            {
                'name': 'therapy_type',
                'value': instance.therapy_type,
                'description': 'Description...'
            }
        ]

    @classmethod
    def serialize_single_instance(cls, instance: models.Therapies) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['conceptType'] = serialized_record['concept_type']
        serialized_record['extensions'] = cls.convert_fields_to_extensions(instance=instance)

        keys_to_remove = [
            'concept_type',
            'primary_coding_id',
            'therapy_strategy_description',
            'therapy_type',
            'therapy_type_description'
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Therapies, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['primaryCoding'] = Codings.serialize_single_instance(instance=instance.primary_coding)
        record['mappings'] = Mappings.serialize_instances(instances=instance.mappings)
        return record


class TherapyGroups(BaseHandler):
    """
    Handler class to manage queries against the TherapyGroups table.
    """

    def perform_joins(self, query: Query, parameters: dict[str, int | str] = None) -> Query:
        """
        """

        return query

    def apply_joinedload(self, query: Query) -> Query:
        """
        3. Joinedload Operations: A function to apply joinedload options for eager loading.

        """
        return query

    def apply_filters(self, query: Query, **filters: dict[str, int | str]) -> Query:
        return query

    @classmethod
    def serialize_single_instance(cls, instance: models.TherapyGroups) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_secondary_instances(cls, instance: models.TherapyGroups, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        therapies = []
        for therapy in instance.therapies:
            therapy_instance = Therapies.serialize_single_instance(instance=therapy)
            therapies.append(therapy_instance)
        record['therapies'] = therapies
        return record
