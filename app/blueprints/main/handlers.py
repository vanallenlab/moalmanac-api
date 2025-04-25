import datetime
import sqlalchemy
import typing

from sqlalchemy.orm import DeclarativeBase, Query
from werkzeug.datastructures import ImmutableMultiDict

from app import models


class BaseHandler:
    """
    A base class for handling SQL queries. This class provides common functionality for managing SQL queries and serves
    as a template for specific Handler classes, which inherit from BaseHandler and implement route-specific logic.
    """
    def __init__(self, session):
        """
        Initializes the BaseHandler class with a Flask Session.

        Args:
            session (Session): The Flask Session object.
        """
        self.session = session

    def construct_base_query(self, model: typing.Type[DeclarativeBase]) -> Query:
        """
        Constructs a base query from the primary table model.

        This is Step 1 in managing the query.

        Args:
            model (typing.Type[DeclarativeBase]): The SQLAlchemy model class representing the table.

        Returns:
            Query: A SQLAlchemy query object for the provided `model`.
        """
        return self.session.query(model)

    def perform_joins(self, query: Query, parameters: dict[str, typing.Any] = None) -> Query:
        """
        Performs join operations on the query to include related tables. This is needed to perform filtering against
        any field from a related table. Joins are _not_ required for any tables not being filtered against. This
        function should be implemented by each route's Handler class.

        This is Step 2 of managing the query.

        Args:
            query (Query): The SQLAlchemy query to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.

        Returns:
            Query: The SQLAlchemy query after join operations are applied.

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

    def apply_filters(self, query: Query, **filters: dict[str, typing.Any]) -> Query:
        """
        Applies filters to the query, based on the parameters provided to the route. This function should be implemented
        by each route's Handler class, and it may reference apply_filter functions from other Handler classes.
        For example, when filtering propositions by biomarker name, the Propositions' Handler class may reference the
        Biomarker Handler class' apply_filters function.

        This is Step 4 of managing the query.

        Args:
            query (Query): The SQLAlchemy query to apply filter operations to.
            filters (dict[str, typing.Any): A dictionary of filters to apply to the query.

        Returns:
            Query: The SQLAlchemy query after filter operations are applied.

        Raises:
            NotImplementedError: If the route's Handler class does not implement this method.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    @staticmethod
    def execute_query(query: Query) -> list[DeclarativeBase]:
        """
        Executes the SQL query and retrieves the results.

        This is Step 5 of managing the query.

        Args:
            query (Query): The SQLAlchemy query to execute.

        Returns:
            list[DeclarativeBase]: A list of SQLAlchemy model instances returned by the query.
        """
        return query.all()

    @classmethod
    def serialize_primary_records(cls, records: list[DeclarativeBase]) -> list[dict[str, typing.Any]]:
        """
        Serializes the fields of the primary table's records.

        This is Step 6 of managing the query.

        Args:
            records (list[DeclarativeBase]): A list of SQLAlchemy model instances to serialize.

        Returns:
            list[dict[str, typing.Any]]: A list of dictionaries containing the serialized records from the primary table.

        Raises:
            NotImplementedError: If the route's Handler class does not implement this method.
        """
        result = []
        for record in records:
            serialized_record = cls.serialize_instance(instance=record)
            result.append(serialized_record)
        return result

    def serialize_instances(self, instances: list[DeclarativeBase]) -> list[dict[str, typing.Any]]:
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
        raise NotImplementedError("Subclasses should implement this method.")

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
            return value.lower()

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
    def serialize_instance(instance: DeclarativeBase):
        """Convert an SQLAlchemy instance to a dictionary."""
        result= {
            column.name: getattr(instance, column.name) for column in instance.__table__.columns
        }
        return result

    @staticmethod
    def pop_keys(keys: list[str], record: dict[str, typing.Any]) -> None:
        for key in keys:
            record.pop(key, None)


class Biomarkers(BaseHandler):
    """
    Handler class to manage queries against the Biomarkers table.
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

    @staticmethod
    def convert_fields_to_extensions(record: dict[str, typing.Any]) -> list[dict[str, typing.Any]]:
        extensions = []
        fields = [
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
    def serialize_secondary_instances(cls, instance: models.Biomarkers, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['genes'] = Genes.serialize_instances(instances=instance.genes)
        return record

    @classmethod
    def serialize_single_instance(cls, instance: models.Biomarkers) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['type'] = 'CategoricalVariant'
        serialized_record['extensions'] = cls.convert_fields_to_extensions(record=serialized_record)
        keys_to_remove=[
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
            'locus',
            'direction',
            'cytoband',
            'arm',
            'status'
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_instances(cls, instances: list[models.Biomarkers]) -> list[dict[str, typing.Any]]:
        """
        7. Serialize Related Records: A function to serialize related table records.

        """
        result = []
        for instance in instances:
            serialized_record = cls.serialize_single_instance(instance=instance)
            result.append(serialized_record)
        return result


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
    def serialize_secondary_instances(cls, instance: models.Codings, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return record

    @classmethod
    def serialize_single_instance(cls, instance: models.Codings) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_instance(instance=instance)
        #serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['iris'] = [serialized_record['iris']]
        return serialized_record

    @classmethod
    def serialize_instances(cls, instances: list[models.Codings]) -> list[dict[str, typing.Any]]:
        """
        7. Serialize Related Records: A function to serialize related table records.

        """
        result = []
        for instance in instances:
            serialized_record = cls.serialize_single_instance(instance=instance)
            result.append(serialized_record)
        return result


class Contributions(BaseHandler):
    """
    Handler class to manage queries against the Contributions table.
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
    def serialize_secondary_instances(cls, instance: models.Contributions, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['agent'] = cls.serialize_instance(instance=instance.agent)
        return record

    @classmethod
    def serialize_single_instance(cls, instance: models.Contributions) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['date'] = cls.convert_date_to_iso(value=instance.date)

        keys_to_remove = [
            'agent_id'
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_instances(cls, instances: list[models.Contributions]) -> list[dict[str, typing.Any]]:
        """
        7. Serialize Related Records: A function to serialize related table records.

        """
        result = []
        for instance in instances:
            serialized_record = cls.serialize_single_instance(instance=instance)
            result.append(serialized_record)
        return result


class Diseases(BaseHandler):
    """
    Handler class to manage queries against the Diseases table.
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
    def serialize_secondary_instances(cls, instance: models.Diseases, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['primaryCoding'] = Codings.serialize_single_instance(instance=instance.primary_coding)
        record['mappings'] = Mappings.serialize_instances(instances=instance.mappings)
        return record

    @classmethod
    def serialize_single_instance(cls, instance: models.Diseases) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['extensions'] = cls.convert_fields_to_extensions(instance=instance)

        keys_to_remove = [
            'primary_coding_id',
            'solid_tumor',
            'therapy_strategy_description',
            'therapy_type',
            'therapy_type_description'
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_instances(cls, instances: list[models.Diseases]) -> list[dict[str, typing.Any]]:
        """
        7. Serialize Related Records: A function to serialize related table records.

        """
        result = []
        for instance in instances:
            serialized_record = cls.serialize_single_instance(instance=instance)
            result.append(serialized_record)
        return result


class Documents(BaseHandler):
    """
    Handler class to manage queries against the Documents table.
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
    def serialize_secondary_instances(cls, instance: models.Documents, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['organization'] = Organizations.serialize_single_instance(instance=instance.organization)
        record.pop('organization_id', None)
        return record

    @classmethod
    def serialize_single_instance(cls, instance: models.Documents) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['first_published'] = cls.convert_date_to_iso(value=instance.first_published) if instance.first_published else None
        serialized_record['access_date'] = cls.convert_date_to_iso(value=instance.access_date)# if instance.access_date else None
        serialized_record['publication_date'] = cls.convert_date_to_iso(value=instance.publication_date)
        return serialized_record

    @classmethod
    def serialize_instances(cls, instances: list[models.Documents]) -> list[dict[str, typing.Any]]:
        """
        7. Serialize Related Records: A function to serialize related table records.

        """
        result = []
        for instance in instances:
            serialized_record = cls.serialize_single_instance(instance=instance)
            result.append(serialized_record)
        return result


class Genes(BaseHandler):
    """
    Handler class to manage queries against the Genes table.
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
    def serialize_secondary_instances(cls, instance: models.Genes, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['primaryCoding'] = Codings.serialize_single_instance(instance=instance.primary_coding)
        record['mappings'] = Mappings.serialize_instances(instances=instance.mappings)
        return record

    @classmethod
    def serialize_single_instance(cls, instance: models.Genes) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_instance(instance=instance)
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
    def serialize_instances(cls, instances: list[models.Genes]) -> list[dict[str, typing.Any]]:
        """
        7. Serialize Related Records: A function to serialize related table records.

        """
        result = []
        for instance in instances:
            serialized_record = cls.serialize_single_instance(instance=instance)
            result.append(serialized_record)
        return result


class Indications(BaseHandler):
    """
    Handler class to manage queries against the Documents table.
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
    def serialize_secondary_instances(cls, instance: models.Indications, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['document'] = Documents.serialize_single_instance(instance=instance.document)
        record.pop('document_id', None)
        return record

    @classmethod
    def serialize_single_instance(cls, instance: models.Indications) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['initial_approval_date'] = cls.convert_date_to_iso(value=instance.initial_approval_date) if instance.initial_approval_date else None
        serialized_record['reimbursement_date'] = cls.convert_date_to_iso(value=instance.reimbursement_date) if instance.reimbursement_date else None
        serialized_record['date_regular_approval'] = cls.convert_date_to_iso(value=instance.date_regular_approval) if instance.date_regular_approval else None
        serialized_record['date_accelerated_approval'] = cls.convert_date_to_iso(value=instance.date_accelerated_approval) if instance.date_accelerated_approval else None
        return serialized_record

    @classmethod
    def serialize_instances(cls, instances: list[models.Indications]) -> list[dict[str, typing.Any]]:
        """
        7. Serialize Related Records: A function to serialize related table records.

        """
        result = []
        for instance in instances:
            serialized_record = cls.serialize_single_instance(instance=instance)
            result.append(serialized_record)
        return result


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
    def serialize_secondary_instances(cls, instance: models.Mappings, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['coding'] = Codings.serialize_single_instance(instance=instance.coding)
        return record

    @classmethod
    def serialize_single_instance(cls, instance: models.Mappings) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)

        keys_to_remove = [
            'primary_coding_id',
            'coding_id'
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_instances(cls, instances: list[models.Mappings]) -> list[dict[str, typing.Any]]:
        """
        7. Serialize Related Records: A function to serialize related table records.

        """
        result = []
        if instances:
            for instance in instances:
                serialized_record = cls.serialize_single_instance(instance=instance)
                result.append(serialized_record)
        return result


class Organizations(BaseHandler):
    """
    Handler class to manage queries against the Organizations table.
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
    def serialize_secondary_instances(cls, instance: models.Organizations, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return record

    @classmethod
    def serialize_single_instance(cls, instance: models.Organizations) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_instance(instance=instance)
        #serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['last_updated'] = cls.convert_date_to_iso(value=instance.last_updated)
        return serialized_record

    @classmethod
    def serialize_instances(cls, instances: list[models.Organizations]) -> list[dict[str, typing.Any]]:
        """
        7. Serialize Related Records: A function to serialize related table records.

        """
        result = []
        for instance in instances:
            serialized_record = cls.serialize_single_instance(instance=instance)
            result.append(serialized_record)
        return result


class Propositions(BaseHandler):
    """
    Handler class to manage queries against the Propositions table.
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
    def serialize_target_therapeutic(cls, therapy: models.Propositions.therapy, therapy_group: models.Propositions.therapy_group) -> dict[str, typing.Any]:
        if therapy:
            return Therapies.serialize_single_instance(instance=therapy)
        else:
            return TherapyGroups.serialize_single_instance(instance=therapy_group)

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Propositions, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['biomarkers'] = Biomarkers.serialize_instances(instances=instance.biomarkers)
        record['conditionQualifier'] = Diseases.serialize_single_instance(instance=instance.condition_qualifier)
        record['targetTherapeutic'] = cls.serialize_target_therapeutic(therapy=instance.therapy, therapy_group=instance.therapy_group)
        return record

    @classmethod
    def serialize_single_instance(cls, instance: models.Propositions) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_instance(instance=instance)
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
    def serialize_instances(cls, instances: list[models.Propositions]) -> list[dict[str, typing.Any]]:
        """
        7. Serialize Related Records: A function to serialize related table records.

        """
        result = []
        for instance in instances:
            serialized_record = cls.serialize_single_instance(instance=instance)
            result.append(serialized_record)
        return result


class Statements(BaseHandler):
    """
    Handler class to manage queries against the Statements table.
    """

    def perform_joins(self, query: Query, parameters: dict[str, int | str] = None) -> Query:
        """
            Allow filtering based on:
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
        #if 'gene' in parameters:


        return query

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

        return query.options(*eager_load_options)

    def apply_filters(self, query: Query, **filters: dict[str, int | str]) -> Query:
        return query

    @classmethod
    def serialize_primary_records(cls, records: list[DeclarativeBase]) -> list[dict[str, typing.Any]]:
        """
        6. Serialize Primary Records: A function to serialize the primary table records.

        """
        result = []
        for record in records:
            serialized_record = cls.serialize_instance(instance=record)
            result.append(serialized_record)
        return result

    @classmethod
    def serialize_secondary_instances(cls, instance: models.Statements, record: dict[str, typing.Any]):
        record['contributions'] = Contributions.serialize_instances(instances=instance.contributions)
        record['indication'] = Indications.serialize_single_instance(instance=instance.indication)
        record['reportedIn'] = Documents.serialize_instances(instances=instance.documents)
        record['proposition'] = Propositions.serialize_single_instance(instance=instance.proposition)
        return record

    @classmethod
    def serialize_single_instance(cls, instance: models.Statements) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)

        keys_to_remove = [
            'indication_id',
            'proposition_id',
            'strength_id'
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_instances(cls, instances: list[models.Statements]) -> list[dict[str, typing.Any]]:
        """
        7. Serialize Related Records: A function to serialize related table records.
        Go through and create a function within each table to serialize their fields
        """
        result = []
        for instance in instances:
            serialized_record = cls.serialize_single_instance(instance=instance)
            result.append(serialized_record)
        return result


class Therapies(BaseHandler):
    """
    Handler class to manage queries against the Therapies table.
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
    def serialize_secondary_instances(cls, instance: models.Therapies, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        record['primaryCoding'] = Codings.serialize_single_instance(instance=instance.primary_coding)
        record['mappings'] = Mappings.serialize_instances(instances=instance.mappings)
        return record

    @classmethod
    def serialize_single_instance(cls, instance: models.Therapies) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        serialized_record['extensions'] = cls.convert_fields_to_extensions(instance=instance)

        keys_to_remove = [
            'primary_coding_id',
            'therapy_strategy_description',
            'therapy_type',
            'therapy_type_description'
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_instances(cls, instances: list[models.Therapies]) -> list[dict[str, typing.Any]]:
        """
        7. Serialize Related Records: A function to serialize related table records.

        """
        result = []
        for instance in instances:
            serialized_record = cls.serialize_single_instance(instance=instance)
            result.append(serialized_record)
        return result


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
    def serialize_secondary_instances(cls, instance: models.TherapyGroups, record: dict[str, typing.Any]) -> dict[str, typing.Any]:
        therapies = []
        for therapy in instance.therapies:
            therapy_instance = Therapies.serialize_single_instance(instance=therapy)
            therapies.append(therapy_instance)
        record['therapies'] = therapies
        return record

    @classmethod
    def serialize_single_instance(cls, instance: models.TherapyGroups) -> dict[str, typing.Any]:
        serialized_record = cls.serialize_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(instance=instance, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_instances(cls, instances: list[models.TherapyGroups]) -> list[dict[str, typing.Any]]:
        """
        7. Serialize Related Records: A function to serialize related table records.

        """
        result = []
        for instance in instances:
            serialized_record = cls.serialize_single_instance(instance=instance)
            result.append(serialized_record)
        return result
