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

    def __init__(self):
        """
        Initializes the BaseHandler class.
        """
        pass

    @staticmethod
    def construct_base_query(model: models.Base) -> sqlalchemy.Select:
        """
        Constructs a base SQLAlchemy select statement from the primary table model.

        This is Step 1 in managing the query.

        Args:
            model (models.Base): The SQLAlchemy model class representing the table.

        Returns:
            Select: A SQLAlchemy select statement for the provided `model`.
        """
        return sqlalchemy.select(model)

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Base,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs join operations on the query to include related tables. This is needed to perform filtering against
        any field from a related table. Joins are _not_ required for any tables not being filtered against. This
        function should be implemented by each route's Handler class.

        This is Step 2 of managing the query.

        At the moment, this function is also performing filtering based on provided parameters. I am not sure if it
        makes sense to have apply_filters as a separate function, because it also is dependent on table aliases, I
        think.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.Base): The SQLAlchemy model class representing the base table of the query.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.

        Raises:
            NotImplementedError: If the route's Handler class does not implement this method.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    @staticmethod
    def apply_joinedload(statement: sqlalchemy.Select) -> sqlalchemy.Select:
        """
        Applies joinedload operations for eager loading of related records from other tables. This is optional to speed
        up serializing fields from other tables. Otherwise, a separate query is made for each time a specific instance
        is serialized. If used, this function should be implemented by each route's Handler class.

        I decided to remove this function from each Handler after some tests when accessing the /statements route. When
        applying joinedloads, it took 1.0762, 1.0843, and 1.0488 seconds to return and serialize all statements in the
        database (~1400). Without applying joinedloads, it took 0.9771, 0.9389, and 0.9704 seconds. This was removed for
        the time being because it was causing warnings when trying to selectively join and filter statements. Plus, not
        inlcuding it only seems to add a tenth of a second with the current database size.

        This is Step 3 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply joinedload operations to.

        Returns:
            statement (sqlalchemy.Select): The SQLAlchemy select statement after joinedload operations are applied.
        """
        return statement

    @classmethod
    def apply_filters(
        cls, statement: sqlalchemy.Select, parameters: ImmutableMultiDict
    ) -> sqlalchemy.Select:
        """
        Applies filters to the query, based on the parameters provided to the route.

        This is Step 4 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply filter operations to.
            parameters (ImmutableMultiDict): Parameters provided to the route as a flask.request.args.

        Returns:
            statement (sqlalchemy.Select): The SQLAlchemy select statement after filter operations are applied.
        """
        filter_map = {
            "agent": models.Agents.name,
            "biomarker_type": models.Biomarkers.biomarker_type,
            "biomarker": models.Biomarkers.name,
            "contribution": models.Contributions.id,
            "disease": models.Diseases.name,
            "document": models.Documents.id,
            "gene": models.Genes.name,
            "indication": models.Indications.id,
            "organization": models.Organizations.name,
            # 'strength': models.Strengths.id,
            "therapy": models.Therapies.name,
            "therapy_type": models.Therapies.therapy_type,
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
    def execute_query(
        session: sqlalchemy.orm.Session, statement: sqlalchemy.sql.Executable
    ) -> list[models.Base]:
        """
        Executes the given SQLAlchemy statement and returns the results as a list of SQLAlchemy model instances.

        This is Step 5 of managing the query.

        Args:
            session (sqlalchemy.orm.Session): A session instance.
            statement (sqlalchemy.sql.Executable): The SQLAlchemy statement to execute.

        Returns:
            list[model.Base]: A list of SQLAlchemy model instances returned by the query.
        """
        return session.execute(statement=statement).unique().scalars().all()

    @classmethod
    def serialize_instances(
        cls, instances: list[models.Base], **kwargs
    ) -> list[dict[str, typing.Any]]:
        """
        Serializes the fields populated by relationships with other tables, defined by this table's model
        and the applied joinedload operation.

        This is Step 6 of managing the query.

        Args:
            instances (list[models.Base]): A list of SQLAlchemy model instances to serialize.

        Returns:
            list[dict[str, typing.Any]]: A list of dictionaries with all keys serialized.
        """
        result = []
        for instance in instances:
            serialized_instance = cls.serialize_single_instance(
                instance=instance, **kwargs
            )
            result.append(serialized_instance)
        return result

    @classmethod
    def serialize_single_instance(
        cls, instance: models.Base, **kwargs
    ) -> dict[str, typing.Any]:
        """
        Performs operations needed to serialize a single instance of the SQLAlchemy model. At minimum, it will serialize
        the primary instance and then any secondary instances that are populated by relationships with other tables. It
        will also remove any keys that are not needed after serialization.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Base): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.

        Raises:
            NotImplementedError: If the route's Handler class does not implement this method.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    @classmethod
    def serialize_primary_instance(cls, instance: models.Base) -> dict[str, typing.Any]:
        """
        Serializes the fields of the primary table's records.

        This is Step 6.2 of managing the query.

        Args:
            instance (models.Base): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A dictionary representation of the Row object.
        """
        return {
            column.name: getattr(instance, column.name)
            for column in instance.__table__.columns
        }

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.Base, record: dict[str, typing.Any], **kwargs
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table that is referenced
        within the instance. This function should be implemented by each route's Handler class.

        This is Step 6.3 of managing the query.

        Args:
            instance (models.Base): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Raises:
            NotImplementedError: If the route's Handler class does not implement this method.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    @staticmethod
    def convert_date_to_iso(value: datetime.date) -> str:
        """
        Converts a datetime.date value to an ISO 8601 format string.

        Args:
            value (datetime.date): The datetime.date value to convert.

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
        Attempts to return the value as an integer, if possible. If not, returns the value as a string.

        Args:
            value (str): The value to convert.

        Returns:
            int | str: The converted value.
        """
        try:
            return int(value)
        except ValueError:
            return value

    @classmethod
    def get_parameters(cls, arguments) -> dict[str, list[str | int]]:
        """
        Converts flask route arguments to a dictionary with keys as parameter names and values as lists of parameter
        values. Values will be converted from strings to integers, if possible.

        Args:
            arguments (ImmutableMultiDict): The arguments from the flask route.

        Returns:
            dictionary (dict[str, list[str | int]]): A dictionary with parameter names as keys and values as lists.
        """
        dictionary = {}
        for key, value in arguments.multi_items():
            if key not in dictionary:
                dictionary[key] = []
            new_value = cls.convert_parameter_value(value=value)
            dictionary[key].append(new_value)
        return dictionary

    @staticmethod
    def pop_keys(keys: list[str], record: dict[str, typing.Any]) -> None:
        """
        Removes keys from the provided dictionary.

        Args:
            keys (list[str]): A list of keys to remove from the dictionary.
            record (dict[str, typing.Any]): The dictionary from which to remove the keys.
        """
        for key in keys:
            record.pop(key, None)

    @staticmethod
    def reorder_dictionary(dictionary: dict, key_order: list[str]) -> dict:
        """
        Reorders the keys in a dictionary based on a given list of keys.

        Args:
            dictionary (dict): The original dictionary to reorder.
            key_order (list[str]): A list of keys specifying the desired order.

        Returns:
            dict: A new dictionary with keys reordered.
        """
        return {key: dictionary[key] for key in key_order if key in dictionary}


class About(BaseHandler):
    """
    Handler class to manage queries against the About table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Agents = models.Agents,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Not used for the About table.
        """
        return statement, joined_tables

    @classmethod
    def serialize_single_instance(cls, instance: models.About) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the About table.

        This method extends the base class implementation by serializing the instance and any related tables. The key
        `id` is removed after serialization.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Agents): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record["last_updated"] = cls.convert_date_to_iso(
            value=serialized_record["last_updated"]
        )

        keys_to_remove = ["id"]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.About, record: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table.

        The About class does not currently reference other tables.

        This is Step 6.3 of managing the query.

        Args:
            instance (models.About): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        return record


class Agents(BaseHandler):
    """
    Handler class to manage queries against the Agents table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Agents = models.Agents,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs joins relevant to the Agents table.

        This method extends the base class implementation by performing a join with the Contributions table and joining
        on the Agents table using the `id` field of Agents.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.Base, models.Agents): The SQLAlchemy model class initially queried against.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.
        """
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        agent_values = parameters.get("agent", None)
        if agent_values:
            if (
                base_table in [models.Contributions, models.Statements]
                and models.Agents not in joined_tables
            ):
                statement = statement.join(
                    models.Agents, models.Agents.id == models.Contributions.agent_id
                )
                joined_tables.add(models.Agents)
            elif base_table != models.Agents:
                raise ValueError(
                    f"Unsupported base table for Diseases.perform_joins: {base_table}."
                )

            conditions = [models.Agents.name.in_(agent_values)]
            statement = statement.where(sqlalchemy.and_(*conditions))

        return statement, joined_tables

    @classmethod
    def serialize_single_instance(
        cls, instance: models.Agents
    ) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the Agents table.

        This method extends the base class implementation by serializing the instance and any related tables. No keys
        are removed after serialization.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Agents): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(
            instance=instance, record=serialized_record
        )

        # keys_to_remove = [
        # ]
        # cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.Agents, record: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table.

        The Agents class does not currently reference other tables.

        This is Step 6.3 of managing the query.

        Args:
            instance (models.Agents): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        return record


class Biomarkers(BaseHandler):
    """
    Handler class to manage queries against the Biomarkers table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Biomarkers = models.Biomarkers,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs joins relevant to the Biomarkers table.

        This method extends the base class implementation. Specifically, it performs a join with the Propositions
        table, joins the Biomarkers table if either `biomarker`, `biomarker_type`, or `gene` are provided as a parameter, and
        references the Genes perform_joins function if `gene` is provided as a parameter.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.Biomarkers, models.Biomarkers): The SQLAlchemy model class initially queried against.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.
        """
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        biomarker_values = parameters.get("biomarker", None)
        biomarker_type_values = parameters.get("biomarker_type", None)
        gene_values = parameters.get("gene", None)
        if biomarker_values or biomarker_type_values or gene_values:
            b_p = models.AssociationBiomarkersAndPropositions
            if (
                base_table in [models.Propositions, models.Statements]
                and b_p not in joined_tables
            ):
                statement = statement.join(
                    b_p, b_p.proposition_id == models.Propositions.id
                )
                joined_tables.add(b_p)

                statement = statement.join(
                    models.Biomarkers, models.Biomarkers.id == b_p.biomarker_id
                )
                joined_tables.add(models.Biomarkers)
            elif base_table != models.Biomarkers:
                raise ValueError(
                    f"Unsupported base table for Biomarkers.perform_joins: {base_table}."
                )

            conditions = []
            if biomarker_values:
                conditions.append(models.Biomarkers.name.in_(biomarker_values))
            if biomarker_type_values:
                conditions.append(
                    models.Biomarkers.biomarker_type.in_(biomarker_type_values)
                )
            statement = statement.where(sqlalchemy.and_(*conditions))

            statement, joined_tables = Genes.perform_joins(
                statement=statement,
                parameters=parameters,
                base_table=base_table,
                joined_tables=joined_tables,
            )

        return statement, joined_tables

    @classmethod
    def serialize_single_instance(
        cls, instance: models.Biomarkers
    ) -> dict[str, typing.Any]:
        """
        Performs operations needed to serialize a single instance of the SQLAlchemy model. At minimum, it will serialize
        the primary instance and then any secondary instances that are populated by relationships with other tables. It
        will also remove any keys that are not needed after serialization.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Agents): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(
            instance=instance, record=serialized_record
        )
        serialized_record["type"] = "CategoricalVariant"
        serialized_record["extensions"] = cls.convert_fields_to_extensions(
            record=serialized_record
        )

        keys_to_remove = [
            "biomarker_type",
            "present",
            "marker",
            "unit",
            "equality",
            "value",
            "chromosome",
            "start_position",
            "end_position",
            "reference_allele",
            "alternate_allele",
            "cdna_change",
            "protein_change",
            "variant_annotation",
            "exon",
            "rsid",
            "hgvsg",
            "hgvsc",
            "requires_oncogenic",
            "requires_pathogenic",
            "rearrangement_type",
            "locus",
            "direction",
            "cytoband",
            "arm",
            "status",
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)

        """
        key_order = [
            'id',
            'conceptType',
            'name',
            'primaryCoding',
            'mappings'
        ]
        serialized_record = cls.reorder_dictionary(dictionary=serialized_record, key_order=key_order)
        """
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.Biomarkers, record: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table that is referenced
        within the instance. Specifically, this function extends the base class implementation by serializing the
        `genes` key by using the Genes model.

        This is Step 6.3 of managing the query.

        Args:
            instance (models.Biomarkers): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        record["genes"] = Genes.serialize_instances(instances=instance.genes)
        return record

    @staticmethod
    def convert_fields_to_extensions(
        record: dict[str, typing.Any],
    ) -> list[dict[str, typing.Any]]:
        """
        Converts biomarker fields to extensions. This is going to be replaced very soon.
        """
        extensions = []
        fields = [
            "biomarker_type",
            "present",
            "marker",
            "unit",
            "equality",
            "value",
            "chromosome",
            "start_position",
            "end_position",
            "reference_allele",
            "alternate_allele",
            "cdna_change",
            "protein_change",
            "variant_annotation",
            "exon",
            "rsid",
            "hgvsg",
            "hgsvc",
            "requires_oncogenic",
            "requires_pathogenic",
            "rearrangement_type",
            "locus",
            "direction",
            "cytoband",
            "arm",
            "status",
        ]
        for field in fields:
            if record.get(field, None):
                extensions.append({"name": field, "value": record.get(field, None)})
        return extensions


class Codings(BaseHandler):
    """
    Handler class to manage queries against the Codings table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Codings = models.Codings,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs join operations on the query to include related tables. This is needed to perform filtering against
        any field from a related table. Joins are _not_ required for any tables not being filtered against. This
        function should be implemented by each route's Handler class.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.Base, models.Codings): The SQLAlchemy model class initially queried against.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.
        """
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        return statement, joined_tables

    @classmethod
    def serialize_single_instance(
        cls, instance: models.Codings
    ) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the Codings table.

        This method extends the base class implementation by serializing the instance and any related tables. No keys
        are removed after serialization, but the `iris` key is turned from a value to a list. If the database expands
        to support multiple URLs per document, then we will have to move URLs to their own table and change this key
        to a reference.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Codings): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(
            instance=instance, record=serialized_record
        )
        serialized_record["iris"] = [serialized_record["iris"]]

        key_order = ["id", "code", "name", "system", "systemVersion", "iris"]
        serialized_record = cls.reorder_dictionary(
            dictionary=serialized_record, key_order=key_order
        )
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.Codings, record: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table.

        The Codings class does not currently reference other tables.

        This is Step 6.3 of managing the query.

        Args:
            instance (models.Codings): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        return record


class Contributions(BaseHandler):
    """
    Handler class to manage queries against the Contributions table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Contributions = models.Contributions,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs joins relevant to the Contributions table.

        This method extends the base class implementation by performing a join with the Statements table through the
        `AssociationContributionsAndStatements` table.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.Base, models.Contributions): The SQLAlchemy model class initially queried against.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.
        """
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        agent_values = parameters.get("agent", None)
        contribution_values = parameters.get("contribution", None)
        # Could expand this to have a filter criteria based on contribution date
        if agent_values or contribution_values:
            c_s = models.AssociationContributionsAndStatements
            if base_table in [models.Statements] and c_s not in joined_tables:
                statement = statement.join(
                    c_s, c_s.statement_id == models.Statements.id
                )
                joined_tables.add(c_s)

                statement = statement.join(
                    models.Contributions, models.Contributions.id == c_s.contribution_id
                )
                joined_tables.add(models.Contributions)
            elif base_table != models.Contributions:
                raise ValueError(
                    f"Unsupported base table for Contributions.perform_joins: {base_table}."
                )

            conditions = []
            if contribution_values:
                conditions = [models.Contributions.id.in_(contribution_values)]
            statement = statement.where(sqlalchemy.and_(*conditions))

            statement, joined_tables = Agents.perform_joins(
                statement=statement,
                parameters=parameters,
                base_table=base_table,
                joined_tables=joined_tables,
            )

        return statement, joined_tables

    @classmethod
    def serialize_single_instance(
        cls, instance: models.Contributions
    ) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the Contributions table.

        This method extends the base class implementation by serializing the instance and any related tables. The
        `agent_id` key is removed after serialization.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Contributions): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(
            instance=instance, record=serialized_record
        )
        serialized_record["date"] = cls.convert_date_to_iso(value=instance.date)

        keys_to_remove = ["agent_id"]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)

        key_order = ["id", "type", "agent", "description", "date"]
        serialized_record = cls.reorder_dictionary(
            dictionary=serialized_record, key_order=key_order
        )
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.Contributions, record: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table. Specifically, this
        function extends the base class implementationby serializing the `agent` key using the Agents model.

        This is Step 6.3 of managing the query.

        Args:
            instance (models.Contributions): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        record["agent"] = cls.serialize_primary_instance(instance=instance.agent)
        return record


class Diseases(BaseHandler):
    """
    Handler class to manage queries against the Diseases table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Diseases = models.Diseases,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs joins relevant to the Diseases table.

        This method extends the base class implementation. Specifically, it performs a join with the Propositions
        table if `disease` is provided as a parameter.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.Diseases, models.Diseases): The SQLAlchemy model class initially queried against.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.
        """
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        disease_values = parameters.get("disease", None)
        if disease_values:
            if (
                base_table in [models.Propositions, models.Statements]
                and models.Diseases not in joined_tables
            ):
                statement = statement.join(
                    models.Diseases,
                    models.Diseases.id == models.Propositions.condition_qualifier_id,
                )
                joined_tables.add(models.Diseases)
            elif base_table != models.Diseases:
                raise ValueError(
                    f"Unsupported base table for Diseases.perform_joins: {base_table}."
                )

            conditions = [models.Diseases.name.in_(disease_values)]
            statement = statement.where(sqlalchemy.and_(*conditions))

        return statement, joined_tables

    @classmethod
    def serialize_single_instance(
        cls, instance: models.Diseases
    ) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the Diseases table.

        This method extends the base class implementation by serializing the instance and any related tables.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Diseases): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(
            instance=instance, record=serialized_record
        )
        serialized_record["conceptType"] = serialized_record["concept_type"]
        serialized_record["extensions"] = cls.convert_fields_to_extensions(
            instance=instance
        )

        keys_to_remove = ["concept_type", "primary_coding_id", "solid_tumor"]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)

        key_order = ["id", "conceptType", "name", "primaryCoding", "mappings"]
        serialized_record = cls.reorder_dictionary(
            dictionary=serialized_record, key_order=key_order
        )
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.Diseases, record: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table. Specifically, this
        function extends the base class implementationby serializing the:
         - `primary_coding` key using the Codings model
         - `mappings` key using the Mappings model

        This is Step 6.3 of managing the query.

        Args:
            instance (models.Diseases): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        record["primaryCoding"] = Codings.serialize_single_instance(
            instance=instance.primary_coding
        )
        record["mappings"] = Mappings.serialize_instances(instances=instance.mappings)
        return record

    @staticmethod
    def convert_fields_to_extensions(
        instance: models.Diseases,
    ) -> list[dict[str, typing.Any]]:
        """
        Converts specific fields to extensions. Specifically, the `solid_tumor` field of the Diseases model.

        Args:
            instance (models.Diseases): A SQLAlchemy model instance of the Diseases table to serialize.

        Returns:
            dict [str, typing.Any]: A dictionary representation of the instance's serialized extensions.
        """
        return [
            {
                "name": "solid_tumor",
                "value": instance.solid_tumor,
                "description": "Boolean value for if this tumor type is categorized as a solid tumor.",
            }
        ]


class Documents(BaseHandler):
    """
    Handler class to manage queries against the Documents table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Documents = models.Documents,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs joins relevant to the Documents table.

        This method extends the base class implementation. Specifically, it performs joins with the Indications and/or
        Statements tables if `document` or `organization` are provided as parameters.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.Documents, models.Documents): The SQLAlchemy model class initially queried against.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.
        """
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        documents_via_statements = sqlalchemy.orm.aliased(models.Documents)
        documents_via_indications = sqlalchemy.orm.aliased(models.Documents)

        document_values = parameters.get("document", None)
        organization_values = parameters.get("organization", None)
        if document_values or organization_values:
            if base_table == models.Documents and models.Documents not in joined_tables:
                if document_values:
                    conditions = [models.Documents.id.in_(document_values)]
                    statement = statement.where(sqlalchemy.and_(*conditions))
            elif (
                base_table in [models.Statements, models.Indications]
                and models.Documents not in joined_tables
            ):
                conditions = []
                if base_table == models.Statements:
                    d_s = models.AssociationDocumentsAndStatements
                    statement = statement.join(
                        d_s, d_s.statement_id == models.Statements.id
                    )
                    joined_tables.add(d_s)

                    statement = statement.join(
                        documents_via_statements,
                        documents_via_statements.id == d_s.document_id,
                    )
                    joined_tables.add(models.Documents)
                    if document_values:
                        conditions.append(
                            documents_via_statements.id.in_(document_values)
                        )

                    statement = statement.join(
                        documents_via_indications,
                        documents_via_indications.id == models.Indications.document_id,
                    )
                    joined_tables.add(models.Documents)
                    if document_values:
                        conditions.append(
                            documents_via_indications.id.in_(document_values)
                        )

                if base_table == models.Indications:
                    statement = statement.join(
                        documents_via_indications,
                        documents_via_indications.id == models.Indications.document_id,
                    )
                    joined_tables.add(models.Documents)
                    if document_values:
                        conditions.append(
                            documents_via_indications.id.in_(document_values)
                        )

                if len(conditions) > 1:
                    combined_condition = sqlalchemy.or_(*conditions)
                elif conditions:
                    combined_condition = conditions[0]
                else:
                    combined_condition = None

                if combined_condition is not None:
                    statement = statement.where(sqlalchemy.and_(combined_condition))
            elif base_table != models.Documents:
                raise ValueError(
                    f"Unsupported base table for Documents.perform_joins: {base_table}."
                )

            statement, joined_tables = Organizations.perform_joins(
                statement=statement,
                parameters=parameters,
                base_table=base_table,
                joined_tables=joined_tables,
                documents_via_statements=documents_via_statements,
                documents_via_indications=documents_via_indications,
            )

        return statement, joined_tables

    @classmethod
    def serialize_single_instance(
        cls, instance: models.Documents
    ) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the Documents table.

        This method extends the base class implementation by serializing the instance and any related tables. A few
        keys are also converted to iso date format. The key `organization_id` is removed after serialization.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Documents): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(
            instance=instance, record=serialized_record
        )
        serialized_record["first_published"] = (
            cls.convert_date_to_iso(value=instance.first_published)
            if instance.first_published
            else None
        )
        serialized_record["access_date"] = (
            cls.convert_date_to_iso(value=instance.access_date)
            if instance.access_date
            else None
        )
        serialized_record["publication_date"] = cls.convert_date_to_iso(
            value=instance.publication_date
        )

        keys_to_remove = ["organization_id"]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)

        """
        Will add once we have a proper data model for documents
        key_order = [
            'id',
            'conceptType',
            'name',
            'primaryCoding',
            'mappings'
        ]
        serialized_record = cls.reorder_dictionary(dictionary=serialized_record, key_order=key_order)
        """
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.Documents, record: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table. Specifically, this
        function extends the base class implementationby serializing the `organization` key using the Organizations
        model.

        This is Step 6.3 of managing the query.

        Args:
            instance (models.Documents): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        record["organization"] = Organizations.serialize_single_instance(
            instance=instance.organization
        )
        return record


class Genes(BaseHandler):
    """
    Handler class to manage queries against the Genes table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Genes = models.Genes,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs joins relevant to the Genes table.

        This method extends the base class implementation by performing a join with the Biomarkers table through the
        `AssociationBiomarkersAndGenes` table.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.Base, models.Genes): The SQLAlchemy model class initially queried against.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.
        """
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        gene_values = parameters.get("gene", None)
        if gene_values:
            b_g = models.AssociationBiomarkersAndGenes
            if (
                base_table
                in [models.Biomarkers, models.Propositions, models.Statements]
                and b_g not in joined_tables
            ):
                statement = statement.join(
                    b_g, b_g.biomarker_id == models.Biomarkers.id
                )
                joined_tables.add(b_g)

                statement = statement.join(models.Genes, models.Genes.id == b_g.gene_id)
                joined_tables.add(models.Genes)
            elif base_table != models.Genes:
                raise ValueError(
                    f"Unsupported base table for Genes.perform_joins: {base_table}."
                )

            conditions = [models.Genes.name.in_(gene_values)]
            statement = statement.where(sqlalchemy.and_(*conditions))

        return statement, joined_tables

    @classmethod
    def serialize_single_instance(cls, instance: models.Genes) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the Genes table.

        This method extends the base class implementation by serializing the instance and any related tables. Several
        keys are also removed after serialization, specifically: `primary_coding_id`, `location` and
        `location_sortable`.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Genes): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(
            instance=instance, record=serialized_record
        )
        serialized_record["extensions"] = cls.convert_fields_to_extensions(
            instance=instance
        )

        keys_to_remove = ["primary_coding_id", "location", "location_sortable"]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)

        key_order = [
            "id",
            "conceptType",
            "name",
            "primaryCoding",
            "mappings",
            "extensions",
        ]
        serialized_record = cls.reorder_dictionary(
            dictionary=serialized_record, key_order=key_order
        )
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.Genes, record: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table. Specifically, this
        function extends the base class implementationby serializing the:
         - `primary_coding` key using the Codings model
         - `mappings` key using the Mappings model

        This is Step 6.3 of managing the query.

        Args:
            instance (models.Genes): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        record["primaryCoding"] = Codings.serialize_single_instance(
            instance=instance.primary_coding
        )
        record["mappings"] = Mappings.serialize_instances(instances=instance.mappings)
        return record

    @staticmethod
    def convert_fields_to_extensions(instance: models.Genes):
        """
        Converts specific fields to extensions. Specifically, the `location` and `location_sortable` fields of
        the Genes model.

        Args:
            instance (models.Genes): A SQLAlchemy model instance of the Genes table to serialize.

        Returns:
            dict [str, typing.Any]: A dictionary representation of the instance's serialized extensions.
        """
        return [
            {"name": "location", "value": instance.location},
            {"name": "location_sortable", "value": instance.location_sortable},
        ]


class Indications(BaseHandler):
    """
    Handler class to manage queries against the Indications table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Indications = models.Indications,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs joins relevant to the Indications table.

        This method extends the base class implementation. Specifically, it performs a join with the Statements table
        if `document`, `indication`, or `organization` are provided as a parameter.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.Indications, models.Indications): The SQLAlchemy model class initially queried against.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.
        """
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        document_values = parameters.get("document", None)
        indication_values = parameters.get("indication", None)
        organization_values = parameters.get("organization", None)
        if document_values or indication_values or organization_values:
            if (
                base_table in [models.Statements]
                and models.Indications not in joined_tables
            ):
                statement = statement.join(
                    models.Indications,
                    models.Indications.id == models.Statements.indication_id,
                )
                joined_tables.add(models.Indications)
            elif base_table != models.Indications:
                raise ValueError(
                    f"Unsupported base table for Indications.perform_joins: {base_table}."
                )

            conditions = []
            if indication_values:
                conditions.append(models.Indications.id.in_(indication_values))
            statement = statement.where(sqlalchemy.and_(*conditions))

            if models.Documents not in joined_tables:
                statement, joined_tables = Documents.perform_joins(
                    statement=statement,
                    parameters=parameters,
                    base_table=base_table,
                    joined_tables=joined_tables,
                )

        return statement, joined_tables

    @classmethod
    def serialize_single_instance(
        cls, instance: models.Indications
    ) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the Indications table.

        This method extends the base class implementation by serializing the instance and any related tables. In
        addition, date related fields are converted to iso date format.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Indications): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(
            instance=instance, record=serialized_record
        )
        serialized_record["initial_approval_date"] = (
            cls.convert_date_to_iso(value=instance.initial_approval_date)
            if instance.initial_approval_date
            else None
        )
        serialized_record["reimbursement_date"] = (
            cls.convert_date_to_iso(value=instance.reimbursement_date)
            if instance.reimbursement_date
            else None
        )
        serialized_record["date_regular_approval"] = (
            cls.convert_date_to_iso(value=instance.date_regular_approval)
            if instance.date_regular_approval
            else None
        )
        serialized_record["date_accelerated_approval"] = (
            cls.convert_date_to_iso(value=instance.date_accelerated_approval)
            if instance.date_accelerated_approval
            else None
        )

        keys_to_remove = ["document_id"]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)

        """
        Add once have proper datamodel
        key_order = [
            'id',
            'conceptType',
            'name',
            'primaryCoding',
            'mappings'
        ]
        serialized_record = cls.reorder_dictionary(dictionary=serialized_record, key_order=key_order)
        """
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.Indications, record: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table. Specifically, this
        function extends the base class implementationby serializing the:
         - `document` key using the Documents model

        This is Step 6.3 of managing the query.

        Args:
            instance (models.Documents): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        record["document"] = Documents.serialize_single_instance(
            instance=instance.document
        )
        return record


class Mappings(BaseHandler):
    """
    Handler class to manage queries against the Mappings table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Mappings = models.Mappings,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs joins relevant to the Mappings table.

        This method extends the base class implementation. This function isn't used at the moment and we will need
        to expand it, if we want to perform filtering against Mappings and Codings.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.Mappings, models.Mappings): The SQLAlchemy model class initially queried against.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.
        """
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        return statement, joined_tables

    @classmethod
    def serialize_single_instance(
        cls, instance: models.Mappings, pop_primary_coding=True
    ) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the Mappings table.

        This method extends the base class implementation by serializing the instance and any related tables.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Mappings): A SQLAlchemy model instance to serialize.
            pop_primary_coding (bool): Remove the primaryCoding key, if True.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(
            instance=instance,
            record=serialized_record,
            serialize_primary_coding=True if not pop_primary_coding else False,
        )

        keys_to_remove = ["primary_coding_id", "coding_id"]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)
        if pop_primary_coding:
            key_order = ["relation", "coding"]
        else:
            key_order = ["id", "relation", "primaryCoding", "coding"]
        serialized_record = cls.reorder_dictionary(
            dictionary=serialized_record, key_order=key_order
        )
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls,
        instance: models.Mappings,
        record: dict[str, typing.Any],
        serialize_primary_coding=True,
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table. Specifically, this
        function extends the base class implementationby serializing the:
         - `coding` key using the Codings model

        This is Step 6.3 of managing the query.

        Args:
            instance (models.Mappings): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
            serialize_primary_coding (bool): Serialize the primaryCoding key, if True.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        if serialize_primary_coding:
            record["primaryCoding"] = Codings.serialize_single_instance(
                instance=instance.primary_coding
            )
        record["coding"] = Codings.serialize_single_instance(instance=instance.coding)
        return record


class Organizations(BaseHandler):
    """
    Handler class to manage queries against the Organizations table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Organizations = models.Organizations,
        joined_tables: list[models.Base] = None,
        documents_via_statements: models.Documents = None,
        documents_via_indications: models.Documents = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs joins relevant to the Organizations table.

        This method extends the base class implementation. Specifically, it performs a join with the Propositions
        table if `disease` is provided as a parameter.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.Organizations, models.Organizations): The SQLAlchemy model class initially queried against.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.
            documents_via_statements (models.Documents, optional): An alias of the Documents table used in the query.
            documents_via_indications (models.Documents, optional): An alias of the Documents table used in the query.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.
        """
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        organizations_via_statements = sqlalchemy.orm.aliased(models.Organizations)
        organizations_via_indications = sqlalchemy.orm.aliased(models.Organizations)

        organization_values = parameters.get("organization", None)
        if organization_values:
            if (
                base_table == models.Organizations
                and models.Organizations not in joined_tables
            ):
                conditions = [models.Organizations.id.in_(organization_values)]
                statement = statement.where(sqlalchemy.and_(*conditions))
            elif (
                base_table in [models.Documents, models.Indications, models.Statements]
                and models.Organizations not in joined_tables
            ):
                conditions = []
                if base_table == models.Documents:
                    statement = statement.join(
                        models.Organizations,
                        models.Organizations.id == models.Documents.organization_id,
                    )
                    conditions.append(models.Organizations.id.in_(organization_values))
                elif base_table == models.Indications:
                    # if documents_via_indications:
                    statement = statement.join(
                        organizations_via_indications,
                        organizations_via_indications.id
                        == documents_via_indications.organization_id,
                    )
                    conditions.append(
                        organizations_via_indications.id.in_(organization_values)
                    )
                elif base_table == models.Statements:
                    # if documents_via_statements:
                    statement = statement.join(
                        organizations_via_statements,
                        organizations_via_statements.id
                        == documents_via_statements.organization_id,
                    )
                    conditions.append(
                        organizations_via_statements.id.in_(organization_values)
                    )
                else:
                    # if not (documents_via_statements or documents_via_indications):
                    message = f"Basetable specified as {base_table} to Organizations.perform_joins without providing document alias(es)."
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
                raise ValueError(
                    f"Unsupported base table for Organizations.perform_joins: {base_table}."
                )

        return statement, joined_tables

    @classmethod
    def serialize_single_instance(
        cls, instance: models.Organizations
    ) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the Organizations table.

        This method extends the base class implementation by serializing the instance and any related tables.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Organizations): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(
            instance=instance, record=serialized_record
        )
        serialized_record["last_updated"] = cls.convert_date_to_iso(
            value=instance.last_updated
        )

        key_order = ["id", "name", "description", "url", "last_updated"]
        serialized_record = cls.reorder_dictionary(
            dictionary=serialized_record, key_order=key_order
        )
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.Organizations, record: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table. The Organizations
        table does not currently reference any other tables.

        This is Step 6.3 of managing the query.

        Args:
            instance (models.Organizations): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        return record


class Propositions(BaseHandler):
    """
    Handler class to manage queries against the Propositions table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Propositions = models.Propositions,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs joins relevant to the Propositions table.

        This method extends the base class implementation. Specifically, it performs a join with the Statements table.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.Propositions, models.Propositions): The SQLAlchemy model class initially queried against.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.
        """
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        if base_table == models.Statements and models.Propositions not in joined_tables:
            statement = statement.join(
                models.Propositions,
                models.Statements.proposition_id == models.Propositions.id,
            )
            joined_tables.add(models.Propositions)
        elif base_table != models.Propositions:
            raise ValueError(
                f"Unsupported base table for Propositions.perform_joins: {base_table}."
            )

        proposition_values = parameters.get("proposition_id", None)
        if proposition_values:
            conditions = [models.Propositions.id.in_(proposition_values)]
            statement = statement.where(sqlalchemy.and_(*conditions))

        statement, joined_tables = Biomarkers.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables,
        )
        statement, joined_tables = Diseases.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables,
        )
        statement, joined_tables = Therapies.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables,
        )

        return statement, joined_tables

    @classmethod
    def serialize_single_instance(
        cls, instance: models.Propositions
    ) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the Propositions table.

        This method extends the base class implementation by serializing the instance and any related tables.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Propositions): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(
            instance=instance, record=serialized_record
        )

        keys_to_remove = [
            "condition_qualifier_id",
            "strength_id",
            "therapy_id",
            "therapy_group_id",
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)

        key_order = [
            "id",
            "type",
            "predicate",
            "biomarkers",
            "subjectVariant",
            "conditionQualifier",
            "objectTherapeutic",
        ]
        serialized_record = cls.reorder_dictionary(
            dictionary=serialized_record, key_order=key_order
        )
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.Propositions, record: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table. Specifically, this
        function extends the base class implementationby serializing the:
         - `biomarkers` key using the Biomarkers model
         - `condition_qualifier` key using the Diseases model
        - `therapy and `therapy_group` keys using the Therapies and Therapy Groups models.

        This is Step 6.3 of managing the query.

        Args:
            instance (models.Propositions): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        record["biomarkers"] = Biomarkers.serialize_instances(
            instances=instance.biomarkers
        )
        record["subjectVariant"] = {}
        record["conditionQualifier"] = Diseases.serialize_single_instance(
            instance=instance.condition_qualifier
        )
        record["objectTherapeutic"] = cls.serialize_target_therapeutic(
            therapy=instance.therapy, therapy_group=instance.therapy_group
        )
        return record

    @classmethod
    def serialize_target_therapeutic(
        cls,
        therapy: models.Propositions.therapy,
        therapy_group: models.Propositions.therapy_group,
    ) -> dict[str, typing.Any]:
        """
        A helper function to serialize the target therapeutic for a Proposition instance.

        Uses the Therapies model if the `therapy` field is set, otherwise the `therapy_group` key.

        Args:
            therapy (models.Propositions.therapy): The `therapy` field of the Proposition instance.
            therapy_group (models.Propositions.therapy_group): The `therapy_group` field of the Proposition instance.

        Returns:
            dict[str, typing.Any]: A dictionary representation of the target therapeutic.
        """
        if therapy:
            return Therapies.serialize_single_instance(instance=therapy)
        else:
            return TherapyGroups.serialize_single_instance(instance=therapy_group)


class Searches(Propositions):
    """
    Handler class to manage queries involving searching. This primarily originates from the Propositions table with aggregating functions relative to the Statements table.
    """

    @classmethod
    def aggregate_statements_by_proposition_ids(
        cls,
        session: sqlalchemy.orm.Session,
        proposition_ids: list[int],
        parameters: dict[str, typing.Any] | None = None,
    ) -> dict[int, dict[str, typing.Any]]:
        """
        Computes statement counts by proposition_id.
        """
        if not proposition_ids:
            return {}

        base_statement_query = cls.filtered_statements_query_by_organizations(
            session=session, proposition_ids=proposition_ids, parameters=parameters
        )

        statement_counts = dict(
            base_statement_query.with_entities(
                models.Statements.proposition_id,
                sqlalchemy.func.count(models.Statements.id).label("count"),
            )
            .filter(models.Statements.proposition_id.in_(proposition_ids))
            .group_by(models.Statements.proposition_id)
            .all()
        )

        by_direction_rows = (
            base_statement_query.with_entities(
                models.Statements.proposition_id,
                models.Statements.direction,
                sqlalchemy.func.count(models.Statements.id).label("count"),
            )
            .filter(models.Statements.proposition_id.in_(proposition_ids))
            .group_by(models.Statements.proposition_id, models.Statements.direction)
            .all()
        )
        by_direction: dict[int, list[dict[str, typing.Any]]] = {}
        for prop_id, direction, count in by_direction_rows:
            by_direction.setdefault(prop_id, []).append(
                {"direction": direction, "count": int(count)}
            )

        by_document_rows = (
            base_statement_query.with_entities(
                models.Statements.proposition_id,
                models.Documents.id.label("document_id"),
                sqlalchemy.func.count(models.Statements.id).label("count"),
            )
            .join(models.Statements.documents)
            .filter(models.Statements.proposition_id.in_(proposition_ids))
            .group_by(models.Statements.proposition_id, models.Documents.id)
            .all()
        )
        by_document: dict[int, list[dict[str, typing.Any]]] = {}
        for prop_id, document_id, count in by_document_rows:
            by_document.setdefault(prop_id, []).append(
                {"id": document_id, "count": int(count)}
            )

        by_organization_rows = (
            base_statement_query.with_entities(
                models.Statements.proposition_id,
                models.Organizations.id.label("organization_id"),
                sqlalchemy.func.count(models.Statements.id).label("count"),
            )
            .join(models.Statements.documents)
            .join(models.Documents.organization)
            .filter(models.Statements.proposition_id.in_(proposition_ids))
            .group_by(models.Statements.proposition_id, models.Organizations.id)
            .all()
        )
        by_organization: dict[int, list[dict[str, typing.Any]]] = {}
        for prop_id, organization_id, count in by_organization_rows:
            by_organization.setdefault(prop_id, []).append(
                {"id": organization_id, "count": int(count)}
            )

        by_strength_rows = (
            base_statement_query.with_entities(
                models.Statements.proposition_id,
                models.Statements.strength_id,
                sqlalchemy.func.count(models.Statements.id).label("count"),
            )
            .filter(models.Statements.proposition_id.in_(proposition_ids))
            .group_by(models.Statements.proposition_id, models.Statements.strength_id)
            .all()
        )
        by_strength: dict[int, list[dict[str, typing.Any]]] = {}
        for prop_id, strength_id, count in by_strength_rows:
            by_strength.setdefault(prop_id, []).append(
                {"id": strength_id, "count": int(count)}
            )

        aggregates: dict[int, dict[str, typing.Any]] = {}
        for proposition_id in proposition_ids:
            aggregates[proposition_id] = {
                "statement_count": int(statement_counts.get(proposition_id, 0)),
                "by_direction": by_direction.get(proposition_id, []),
                "by_document": by_document.get(proposition_id, []),
                "by_organization": by_organization.get(proposition_id, []),
                "by_strength": by_strength.get(proposition_id, []),
            }

        return aggregates

    @staticmethod
    def dereference_aggregate_counts(
        session: sqlalchemy.orm.Session, aggregates: dict[int, dict[str, typing.Any]]
    ) -> None:
        """
        Dereferences ids within aggregates dictionary from /search endpoint.
        Currently dereferences organizations and strengths.
        """

        # These are typing hints, and are the dtype of the `id` value for each dict.
        # Typing hints are probably my favorite Python thing I learned in 2025.
        # Say hello if you read this!
        organization_ids: set[str] = set()
        strength_ids: set[int] = set()

        for agg in aggregates.values():
            for row in agg.get("by_organization", []):
                organization_id = row.get("organization_id")
                if organization_id is not None:
                    organization_ids.add(organization_id)
            for row in agg.get("by_strength", []):
                strength_id = row.get("strength_id")
                if strength_id is not None:
                    strength_ids.add(strength_id)

        organization_lookup: dict[str, dict[str, typing.Any]] = {}
        if organization_ids:
            organization_instances = (
                session.query(models.Organizations)
                .filter(models.Organizations.id.in_(list(organization_ids)))
                .all()
            )
            for organization in organization_instances:
                organization_lookup[organization.id] = (
                    Organizations.serialize_single_instance(instance=organization)
                )

        strength_lookup: dict[int, dict[str, typing.Any]] = {}
        if strength_ids:
            strength_instances = (
                session.query(models.Strengths)
                .filter(models.Strengths.id.in_(list(strength_ids)))
                .all()
            )
            for strength in strength_instances:
                strength_lookup[strength.id] = Strengths.serialize_single_instance(
                    instance=strength
                )

        for agg in aggregates.values():
            for row in agg.get("by_organization", []):
                organization_id = row.pop("organization_id", None)
                row["organization"] = organization_lookup.get(organization_id)
            for row in agg.get("by_strength", []):
                strength_id = row.pop("strength_id", None)
                row["strength"] = strength_lookup.get(strength_id)

    @staticmethod
    def empty_aggregates() -> dict[str, typing.Any]:
        return {
            "statement_count": 0,
            "by_organization": [],
            "by_strength": [],
            "by_document": [],
        }

    @staticmethod
    def filtered_statements_query_by_organizations(
        session: sqlalchemy.orm.Session,
        proposition_ids: list[int],
        parameters: dict[str, typing.Any] | None,
    ):
        query = session.query(models.Statements).filter(
            models.Statements.proposition_id.in_(proposition_ids)
        )

        organization_ids = (parameters or {}).get("organization")
        if organization_ids:
            if isinstance(organization_ids, str):
                organization_ids = [organization_ids]
            query = (
                query.join(models.Statements.documents)
                .join(models.Documents.organization)
                .filter(models.Organizations.id.in_(organization_ids))
            )

        return query

    @classmethod
    def serialize_instances(
        cls,
        instances: list[models.Base],
        parameters: dict[str, typing.Any] | None = None,
        *,
        session: sqlalchemy.orm.Session | None = None,
        **kwargs,
    ) -> list[dict[str, typing.Any]]:
        """
        Serialize propositions and attach aggregates of statement counts.
        """
        serialized = super().serialize_instances(instances=instances, **kwargs)

        if session is None or not serialized:
            for rec in serialized:
                rec["aggregates"] = cls.empty_aggregates()
            return serialized

        proposition_ids = [rec["id"] for rec in serialized if "id" in rec]
        agg = cls.aggregate_statements_by_proposition_ids(
            session=session,
            proposition_ids=proposition_ids,
            parameters=parameters,
        )

        for rec in serialized:
            proposition_id = rec.get("id")
            rec["aggregates"] = agg.get(proposition_id, cls.empty_aggregates())

        return serialized


class Statements(BaseHandler):
    """
    Handler class to manage queries against the Statements table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Statements = models.Statements,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs joins relevant to the Diseases table.

        This method extends the base class implementation by referencing the perform_joins function of other models.
        Specifically: Contributions, Documents, Indications, Propositions, and Strengths.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.Statements, models.Statements): The SQLAlchemy model class initially queried against.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.
        """
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        statement, joined_tables = Contributions.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables,
        )
        statement, joined_tables = Documents.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables,
        )
        statement, joined_tables = Indications.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables,
        )
        statement, joined_tables = Propositions.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables,
        )
        statement, joined_tables = Strengths.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables,
        )

        return statement, joined_tables

    @classmethod
    def serialize_single_instance(
        cls, instance: models.Statements
    ) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the Statements table.

        This method extends the base class implementation by serializing the instance and any related tables.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Statements): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(
            instance=instance, record=serialized_record
        )

        keys_to_remove = ["indication_id", "proposition_id", "strength_id"]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)

        key_order = [
            "id",
            "type",
            "description",
            "contributions",
            "reportedIn",
            "direction",
            "indication",
            "proposition",
            "strength",
        ]
        serialized_record = cls.reorder_dictionary(
            dictionary=serialized_record, key_order=key_order
        )
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.Statements, record: dict[str, typing.Any]
    ):
        """
        References `serialize_instance` functions from relevant classes for each secondary table. Specifically, this
        function extends the base class implementationby serializing the:
         - `contributions` key using the Contributions model
         - `documents` key using the Documents model
         - `indication` key using the Indication model
         - `proposition` key using the Proposition model
         - `strength` key using the Strengths model

        This is Step 6.3 of managing the query.

        Args:
            instance (models.Statements): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        record["contributions"] = Contributions.serialize_instances(
            instances=instance.contributions
        )
        record["indication"] = Indications.serialize_single_instance(
            instance=instance.indication
        )
        record["reportedIn"] = Documents.serialize_instances(
            instances=instance.documents
        )
        record["proposition"] = Propositions.serialize_single_instance(
            instance=instance.proposition
        )
        record["strengths"] = Strengths.serialize_single_instance(
            instance=instance.strength
        )
        return record


class Strengths(BaseHandler):
    """
    Handler class to manage queries against the Strengths table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Strengths = models.Strengths,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs joins relevant to the Strengths table.

        This method extends the base class implementation.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.Strengths, models.Strengths): The SQLAlchemy model class initially queried against.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.
        """
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

    @classmethod
    def serialize_single_instance(
        cls, instance: models.Strengths
    ) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the Strengths table.

        This method extends the base class implementation by serializing the instance and any related tables.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Strengths): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(
            instance=instance, record=serialized_record
        )
        serialized_record["conceptType"] = serialized_record["concept_type"]

        keys_to_remove = ["concept_type", "primary_coding_id"]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)

        key_order = ["id", "conceptType", "name", "primaryCoding", "mappings"]
        serialized_record = cls.reorder_dictionary(
            dictionary=serialized_record, key_order=key_order
        )
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.Strengths, record: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table. Specifically, this
        function extends the base class implementationby serializing the:
         - `primary_coding` key using the Codings model
         - `mappings` key using the Mappings model

        This is Step 6.3 of managing the query.

        Args:
            instance (models.Strengths): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        record["primaryCoding"] = Codings.serialize_single_instance(
            instance=instance.primary_coding
        )
        record["mappings"] = []
        # record['mappings'] = Mappings.serialize_instances(instances=instance.mappings)
        return record


class Therapies(BaseHandler):
    """
    Handler class to manage queries against the Therapies table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.Therapies = models.Therapies,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs joins relevant to the Therapies table.

        This method extends the base class implementation. Specifically, it performs a join with the Propositions
        table if either `therapy` or `therapy_group` are provided as a parameter.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.Therapies, models.Therapies): The SQLAlchemy model class initially queried against.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.
        """
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        therapy_values = parameters.get("therapy", None)
        therapy_type_values = parameters.get("therapy_type", None)
        if therapy_values or therapy_type_values:
            therapies_direct = sqlalchemy.orm.aliased(models.Therapies)
            therapies_indirect = sqlalchemy.orm.aliased(models.Therapies)
            if (
                base_table in [models.Propositions, models.Statements]
                and models.Therapies not in joined_tables
            ):
                # Outerjoin because sometimes therapy_id is null
                statement = statement.outerjoin(
                    therapies_direct,
                    therapies_direct.id == models.Propositions.therapy_id,
                )
                joined_tables.add(models.Therapies)

                statement = statement.outerjoin(
                    models.TherapyGroups,
                    models.TherapyGroups.id == models.Propositions.therapy_group_id,
                )
                joined_tables.add(models.TherapyGroups)

                statement = statement.outerjoin(
                    models.AssociationTherapyAndTherapyGroup,
                    models.AssociationTherapyAndTherapyGroup.therapy_group_id
                    == models.TherapyGroups.id,
                )
                joined_tables.add(models.AssociationTherapyAndTherapyGroup)

                statement = statement.outerjoin(
                    therapies_indirect,
                    therapies_indirect.id
                    == models.AssociationTherapyAndTherapyGroup.therapy_id,
                )
                joined_tables.add(models.Therapies)
            elif base_table != models.Therapies:
                raise ValueError(
                    f"Unsupported base table for Biomarkers.perform_joins: {base_table}."
                )

            conditions = []
            if therapy_values:
                condition_direct = therapies_direct.name.in_(therapy_values)
                condition_indirect = therapies_indirect.name.in_(therapy_values)
                conditions.append((condition_direct | condition_indirect))
            if therapy_type_values:
                condition_direct = therapies_direct.therapy_type.in_(
                    therapy_type_values
                )
                condition_indirect = therapies_indirect.therapy_type.in_(
                    therapy_type_values
                )
                conditions.append((condition_direct | condition_indirect))
            statement = statement.where(sqlalchemy.and_(*conditions))

        return statement, joined_tables

    @classmethod
    def serialize_single_instance(
        cls, instance: models.Therapies
    ) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the Therapies table.

        This method extends the base class implementation by serializing the instance and any related tables.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.Therapies): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(
            instance=instance, record=serialized_record
        )
        serialized_record["conceptType"] = serialized_record["concept_type"]
        serialized_record["extensions"] = cls.convert_fields_to_extensions(
            instance=instance
        )

        keys_to_remove = [
            "concept_type",
            "primary_coding_id",
            "therapy_strategy" "therapy_strategy_description",
            "therapy_type",
            "therapy_type_description",
        ]
        cls.pop_keys(keys=keys_to_remove, record=serialized_record)

        key_order = [
            "id",
            "conceptType",
            "name",
            "primaryCoding",
            "mappings",
            "extensions",
        ]
        serialized_record = cls.reorder_dictionary(
            dictionary=serialized_record, key_order=key_order
        )
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.Therapies, record: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table. Specifically, this
        function extends the base class implementationby serializing the:
         - `primary_coding` key using the Codings model
         - `mappings` key using the Mappings model

        This is Step 6.3 of managing the query.

        Args:
            instance (models.Therapies): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        record["primaryCoding"] = Codings.serialize_single_instance(
            instance=instance.primary_coding
        )
        record["mappings"] = Mappings.serialize_instances(instances=instance.mappings)
        return record

    @staticmethod
    def convert_fields_to_extensions(instance: models.Therapies):
        """
        Converts specific fields to extensions. Specifically, the `therapy_strategy` and `therapy_type` field
        of the Therapies model.

        Args:
            instance (models.Therapies): A SQLAlchemy model instance of the Therapies table to serialize.

        Returns:
            dict [str, typing.Any]: A dictionary representation of the instance's serialized extensions.
        """
        return [
            {
                "name": "therapy_strategy",
                "value": [s.name for s in instance.therapy_strategy],
                "description": instance.therapy_strategy_description,
            },
            {
                "name": "therapy_type",
                "value": instance.therapy_type,
                "description": instance.therapy_type_description,
            },
        ]


class TherapyGroups(BaseHandler):
    """
    Handler class to manage queries against the TherapyGroups table.
    """

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: ImmutableMultiDict,
        base_table: models.TherapyGroups = models.TherapyGroups,
        joined_tables: list[models.Base] = None,
    ) -> tuple[sqlalchemy.Select, list[models.Base]]:
        """
        Performs joins relevant to the TherapyGroups table.

        This method extends the base class implementation. The joins needed for therapy groups are currently covered by
        the Therapies class.

        This is Step 2 of managing the query.

        Args:
            statement (sqlalchemy.Select): The SQLAlchemy select statement to apply join operations to.
            parameters (dict[str, typing.Any): A dictionary of route parameters to apply to the query as filters.
            base_table (models.TherapyGroups, models.TherapyGroups): The SQLAlchemy model class initially queried against.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined.

        Returns:
            sqlalchemy.Select: The SQLAlchemy select statement after join operations are applied.
            joined_tables (list[models.Base], optional): A list of SQLAlchemy model classes of tables already joined,
                with tables joined within this function added.
        """
        if not parameters:
            return statement, joined_tables

        if joined_tables is None:
            joined_tables = set()

        return statement, joined_tables

    @classmethod
    def serialize_single_instance(
        cls, instance: models.TherapyGroups
    ) -> dict[str, typing.Any]:
        """
        Serializes a single instance of the TherapyGroups table.

        This method extends the base class implementation by serializing the instance and any related tables.

        This is Step 6.1 of managing the query.

        Args:
            instance (models.TherapyGroups): A SQLAlchemy model instance to serialize.

        Returns:
            dict[str, typing.Any]: A list of dictionaries with all keys serialized.
        """
        serialized_record = cls.serialize_primary_instance(instance=instance)
        serialized_record = cls.serialize_secondary_instances(
            instance=instance, record=serialized_record
        )
        return serialized_record

    @classmethod
    def serialize_secondary_instances(
        cls, instance: models.TherapyGroups, record: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        """
        References `serialize_instance` functions from relevant classes for each secondary table. Specifically, this
        function extends the base class implementationby serializing the:
         - `therapy` key using the Therapies model

        This is Step 6.3 of managing the query.

        Args:
            instance (models.TherapyGroups): A SQLAlchemy model instance to serialize.
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.

        Returns:
            record (dict[str, typing.Any]): A dictionary representation of the primary instance object.
        """
        therapies = []
        for therapy in instance.therapies:
            therapy_instance = Therapies.serialize_single_instance(instance=therapy)
            therapies.append(therapy_instance)
        record["therapies"] = therapies
        return record
