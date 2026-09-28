"""
Handlers translate query parameters into the ids of matching records, and look
those ids up in the dereferenced cache built by app.dereferenced.

Each handler's `perform_joins` filters a `select(model.id)` statement based on
query parameters, joining through association tables where a filter reaches
another entity (for example `?gene=BRAF` on `/propositions`). The route then calls
`execute_query` for the matching ids and `serialize` to look them up in
`app.state.dereferenced[entity]`. Because that cache already holds fully resolved,
correctly ordered records (built by moalmanac-db's own `utils.dereference`), no
handler builds or reorders a response dictionary itself.
"""

import typing

import sqlalchemy
import sqlalchemy.orm

from app import dereferenced, models

Parameters = dict[str, list[str]]


class BaseHandler:
    """
    Base class for entity handlers.

    Subclasses set `entity` (the handler's key into the dereferenced cache) and
    `model` (its SQLAlchemy model), and override `perform_joins` if the entity
    supports query parameter filters.
    """

    entity: typing.ClassVar[str] = ""
    model: typing.ClassVar[type[models.Base]] = models.Base

    @classmethod
    def construct_base_query(cls) -> sqlalchemy.Select:
        """
        Builds the base statement selecting this entity's ids.

        Returns:
            sqlalchemy.Select: A `SELECT DISTINCT <model>.id` statement. `DISTINCT`
            guards against duplicate rows introduced by a join applied later.
        """
        return sqlalchemy.select(cls.model.id).distinct()

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: Parameters,
        base_table: type[models.Base] | None = None,
        joined_tables: set[type[models.Base]] | None = None,
    ) -> tuple[sqlalchemy.Select, set[type[models.Base]]]:
        """
        Applies this entity's query parameter filters to `statement`.

        The base implementation is a no-op; entities with filters override it.

        Args:
            statement (sqlalchemy.Select): The statement to filter.
            parameters (Parameters): Query parameter values, from `get_parameters`.
            base_table (type[models.Base] | None): The model the route's base query
                selects from (defaults to the handler's own model).
            joined_tables (set[type[models.Base]] | None): Tables (or association
                models) already joined into `statement`, so callers sharing a
                statement do not join the same table twice.

        Returns:
            tuple[sqlalchemy.Select, set[type[models.Base]]]: The filtered statement, and
                `joined_tables` with any tables this call joined added.
        """
        return statement, joined_tables if joined_tables is not None else set()

    @staticmethod
    def execute_query(
        session: sqlalchemy.orm.Session,
        statement: sqlalchemy.Select,
    ) -> set[str]:
        """
        Executes `statement` and returns the matching ids.

        Args:
            session (sqlalchemy.orm.Session): The database session to query against.
            statement (sqlalchemy.Select): A statement selecting one id column.

        Returns:
            set[str]: The distinct ids returned by the query.
        """
        return set(session.execute(statement).scalars().all())

    @classmethod
    def serialize(
        cls,
        ids: set[str],
        cache: dereferenced.Cache,
    ) -> list[dict]:
        """
        Looks up `ids` in the dereferenced cache, in the cache's order.

        Args:
            ids (set[str]): The ids to include, typically from `execute_query`.
            cache (dereferenced.Cache): The application's dereferenced cache
                (`request.app.state.dereferenced`).

        Returns:
            list[dict]: The matching records, in the cache's (file) order rather than the order
                `ids` was produced in, so results are deterministic regardless of SQL join order.
        """
        entity_cache = cache[cls.entity]
        return [
            entity_cache[record_id] for record_id in entity_cache if record_id in ids
        ]

    @staticmethod
    def normalize_to_list(value: typing.Any) -> list[str] | None:
        """
        Normalizes a query parameter value to a list of strings.

        Args:
            value (typing.Any): A value from a `Parameters` dict, or None.

        Returns:
            list[str] | None: `value` as a list, or None if it was falsy.
        """
        if not value:
            return None
        if isinstance(value, (list, tuple, set)):
            return list(value)
        return [value]

    @staticmethod
    def get_parameters(arguments) -> Parameters:
        """
        Converts request query parameters to a dict of lists.

        Args:
            arguments: `request.query_params` (a Starlette `QueryParams`).

        Returns:
            Parameters: Query parameter values, keyed by parameter name.
        """
        dictionary: Parameters = {}
        for key, value in arguments.multi_items():
            dictionary.setdefault(key, []).append(value)
        return dictionary


class Agents(BaseHandler):
    """Handler for the Agents entity."""

    entity = "agents"
    model = models.Agents

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: Parameters,
        base_table: type[models.Base] | None = None,
        joined_tables: set[type[models.Base]] | None = None,
    ) -> tuple[sqlalchemy.Select, set[type[models.Base]]]:
        """
        Filters by `agent` (name), `agent_id`, and `agent_type`.

        When `base_table` is Contributions or Documents, joins to Agents through
        that table's `agent_id` foreign key first (added by the caller who already
        joined `base_table` into the statement).

        See BaseHandler.perform_joins for the parameters and return value.
        """
        base_table = base_table or models.Agents
        joined_tables = joined_tables if joined_tables is not None else set()
        if not parameters:
            return statement, joined_tables

        agent_ids = parameters.get("agent_id")
        agent_names = parameters.get("agent")
        agent_types = parameters.get("agent_type")
        if not (agent_ids or agent_names or agent_types):
            return statement, joined_tables

        if base_table == models.Contributions:
            if models.Agents not in joined_tables:
                statement = statement.join(
                    models.Agents,
                    models.Agents.id == models.Contributions.agent_id,
                )
                joined_tables.add(models.Agents)
        elif base_table == models.Documents:
            if models.Agents not in joined_tables:
                statement = statement.join(
                    models.Agents,
                    models.Agents.id == models.Documents.agent_id,
                )
                joined_tables.add(models.Agents)
        elif base_table != models.Agents:
            raise ValueError(
                f"Unsupported base table for Agents.perform_joins: {base_table}.",
            )

        conditions = []
        if agent_ids:
            conditions.append(models.Agents.id.in_(agent_ids))
        if agent_names:
            conditions.append(models.Agents.name.in_(agent_names))
        if agent_types:
            conditions.append(models.Agents.agentType.in_(agent_types))
        if conditions:
            statement = statement.where(sqlalchemy.and_(*conditions))

        return statement, joined_tables


class Alleles(BaseHandler):
    """Handler for the Alleles entity. No query parameter filters."""

    entity = "alleles"
    model = models.Alleles


class Biomarkers(BaseHandler):
    """Handler for the Biomarkers entity."""

    entity = "biomarkers"
    model = models.Biomarkers

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: Parameters,
        base_table: type[models.Base] | None = None,
        joined_tables: set[type[models.Base]] | None = None,
    ) -> tuple[sqlalchemy.Select, set[type[models.Base]]]:
        """
        Filters by `biomarker` (name), `biomarker_type`, and `gene` (delegated to
        Genes.perform_joins).

        When `base_table` is Propositions or Statements, joins through
        BiomarkerCriteria: `<base> -> AssociationBiomarkerCriteriaAndPropositions ->
        BiomarkerCriteria -> Biomarkers`.

        See BaseHandler.perform_joins for the parameters and return value.
        """
        base_table = base_table or models.Biomarkers
        joined_tables = joined_tables if joined_tables is not None else set()
        if not parameters:
            return statement, joined_tables

        biomarker_values = parameters.get("biomarker")
        biomarker_type_values = parameters.get("biomarker_type")
        gene_values = parameters.get("gene")
        if not (biomarker_values or biomarker_type_values or gene_values):
            return statement, joined_tables

        if base_table in (models.Propositions, models.Statements):
            criteria_propositions = models.AssociationBiomarkerCriteriaAndPropositions
            if models.Biomarkers not in joined_tables:
                statement = statement.join(
                    criteria_propositions,
                    criteria_propositions.proposition_id == models.Propositions.id,
                )
                joined_tables.add(criteria_propositions)
                statement = statement.join(
                    models.BiomarkerCriteria,
                    models.BiomarkerCriteria.id
                    == criteria_propositions.biomarker_criterion_id,
                )
                joined_tables.add(models.BiomarkerCriteria)
                statement = statement.join(
                    models.Biomarkers,
                    models.Biomarkers.id == models.BiomarkerCriteria.subject_id,
                )
                joined_tables.add(models.Biomarkers)
        elif base_table != models.Biomarkers:
            raise ValueError(
                f"Unsupported base table for Biomarkers.perform_joins: {base_table}.",
            )

        conditions = []
        if biomarker_values:
            conditions.append(models.Biomarkers.name.in_(biomarker_values))
        if biomarker_type_values:
            conditions.append(
                models.Biomarkers.biomarker_type.in_(biomarker_type_values),
            )
        if conditions:
            statement = statement.where(sqlalchemy.and_(*conditions))

        statement, joined_tables = Genes.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables,
        )
        return statement, joined_tables


class BiomarkerCriteria(BaseHandler):
    """Handler for the BiomarkerCriteria entity. No query parameter filters."""

    entity = "biomarker_criteria"
    model = models.BiomarkerCriteria


class Codings(BaseHandler):
    """Handler for the Codings entity. No query parameter filters."""

    entity = "codings"
    model = models.Codings


class Contributions(BaseHandler):
    """Handler for the Contributions entity."""

    entity = "contributions"
    model = models.Contributions

    @staticmethod
    def get_records(
        session: sqlalchemy.orm.Session,
        contribution_ids: set[str],
        cache: dereferenced.Cache,
    ) -> dict[str, list[dict]]:
        """
        Looks up the indications and statements each contribution was made to.

        Records of every status are included, including deprecated ones.

        Args:
            session (sqlalchemy.orm.Session): The database session to query against.
            contribution_ids (set[str]): The contribution ids to look up.
            cache (dereferenced.Cache): The application's dereferenced cache
                (`request.app.state.dereferenced`).

        Returns:
            dict[str, list[dict]]: `{contribution_id: [{id, type, name, description}, ...]}`,
                with indications before statements and each group in association order.
                Contributions without records are absent.
        """
        associations = [
            (models.AssociationContributionsAndIndications, "indication_id", "indications"),
            (models.AssociationContributionsAndStatements, "statement_id", "statements"),
        ]
        records: dict[str, list[dict]] = {}
        for association, record_column, entity in associations:
            statement = (
                sqlalchemy.select(
                    association.contribution_id,
                    getattr(association, record_column),
                )
                .where(association.contribution_id.in_(contribution_ids))
                .order_by(association.id)
            )
            for contribution_id, record_id in session.execute(statement).all():
                record = cache[entity].get(record_id)
                if record is None:
                    continue
                records.setdefault(contribution_id, []).append(
                    {
                        "id": record["id"],
                        "type": record.get("type"),
                        "name": record.get("name"),
                        "description": record.get("description"),
                    },
                )
        return records

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: Parameters,
        base_table: type[models.Base] | None = None,
        joined_tables: set[type[models.Base]] | None = None,
    ) -> tuple[sqlalchemy.Select, set[type[models.Base]]]:
        """
        Filters by `contribution` (id), and (only when `base_table` is
        Contributions itself) `agent`/`agent_id`, delegated to Agents.perform_joins.

        When `base_table` is Statements, joins through
        AssociationContributionsAndStatements.

        See BaseHandler.perform_joins for the parameters and return value.
        """
        base_table = base_table or models.Contributions
        joined_tables = joined_tables if joined_tables is not None else set()
        if not parameters:
            return statement, joined_tables

        contribution_values = parameters.get("contribution")

        if base_table == models.Contributions:
            if contribution_values:
                statement = statement.where(
                    models.Contributions.id.in_(contribution_values),
                )
            statement, joined_tables = Agents.perform_joins(
                statement=statement,
                parameters=parameters,
                base_table=base_table,
                joined_tables=joined_tables,
            )
        elif base_table == models.Statements:
            if contribution_values:
                contributions_statements = models.AssociationContributionsAndStatements
                if models.Contributions not in joined_tables:
                    statement = statement.join(
                        contributions_statements,
                        contributions_statements.statement_id == models.Statements.id,
                    )
                    joined_tables.add(contributions_statements)
                    statement = statement.join(
                        models.Contributions,
                        models.Contributions.id
                        == contributions_statements.contribution_id,
                    )
                    joined_tables.add(models.Contributions)
                statement = statement.where(
                    models.Contributions.id.in_(contribution_values),
                )
        else:
            raise ValueError(
                f"Unsupported base table for Contributions.perform_joins: {base_table}.",
            )

        return statement, joined_tables


class CopyChanges(BaseHandler):
    """Handler for the CopyChanges entity. No query parameter filters."""

    entity = "copy_changes"
    model = models.CopyChanges


class Diseases(BaseHandler):
    """Handler for the Diseases entity."""

    entity = "diseases"
    model = models.Diseases

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: Parameters,
        base_table: type[models.Base] | None = None,
        joined_tables: set[type[models.Base]] | None = None,
    ) -> tuple[sqlalchemy.Select, set[type[models.Base]]]:
        """
        Filters by `disease` (name).

        When `base_table` is Propositions or Statements, joins to Diseases through
        `Propositions.conditionQualifier_id`.

        See BaseHandler.perform_joins for the parameters and return value.
        """
        base_table = base_table or models.Diseases
        joined_tables = joined_tables if joined_tables is not None else set()
        if not parameters:
            return statement, joined_tables

        disease_values = parameters.get("disease")
        if not disease_values:
            return statement, joined_tables

        if base_table in (models.Propositions, models.Statements):
            if models.Diseases not in joined_tables:
                statement = statement.join(
                    models.Diseases,
                    models.Diseases.id == models.Propositions.conditionQualifier_id,
                )
                joined_tables.add(models.Diseases)
        elif base_table != models.Diseases:
            raise ValueError(
                f"Unsupported base table for Diseases.perform_joins: {base_table}.",
            )

        statement = statement.where(models.Diseases.name.in_(disease_values))
        return statement, joined_tables


class Documents(BaseHandler):
    """Handler for the Documents entity. Only Active documents are returned by default."""

    entity = "documents"
    model = models.Documents

    @classmethod
    def construct_base_query(cls, include_deprecated: bool = False) -> sqlalchemy.Select:
        """
        Builds the base statement selecting Documents ids, excluding Deprecated
        documents unless `include_deprecated` is true.

        Args:
            include_deprecated (bool): If true, also select Deprecated documents.

        Returns:
            sqlalchemy.Select: A statement selecting the ids of Active documents, or of all documents if `include_deprecated`.
        """
        statement = super().construct_base_query()
        if include_deprecated:
            return statement
        return statement.where(cls.model.status == "Active")

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: Parameters,
        base_table: type[models.Base] | None = None,
        joined_tables: set[type[models.Base]] | None = None,
    ) -> tuple[sqlalchemy.Select, set[type[models.Base]]]:
        """
        Filters by `document` (id), and `agent`/`agent_id` (delegated to
        Agents.perform_joins once Documents is joined).

        When `base_table` is Statements, joins through
        AssociationDocumentsAndStatements (`reportedIn`); when Indications, through
        AssociationDocumentsAndIndications (also `reportedIn`).

        See BaseHandler.perform_joins for the parameters and return value.
        """
        base_table = base_table or models.Documents
        joined_tables = joined_tables if joined_tables is not None else set()
        if not parameters:
            return statement, joined_tables

        document_values = parameters.get("document")
        agent_values = parameters.get("agent")
        agent_id_values = parameters.get("agent_id")
        if not (document_values or agent_values or agent_id_values):
            return statement, joined_tables

        if base_table == models.Documents:
            pass
        elif base_table == models.Statements:
            documents_statements = models.AssociationDocumentsAndStatements
            if models.Documents not in joined_tables:
                statement = statement.join(
                    documents_statements,
                    documents_statements.statement_id == models.Statements.id,
                )
                joined_tables.add(documents_statements)
                statement = statement.join(
                    models.Documents,
                    models.Documents.id == documents_statements.document_id,
                )
                joined_tables.add(models.Documents)
        elif base_table == models.Indications:
            documents_indications = models.AssociationDocumentsAndIndications
            if models.Documents not in joined_tables:
                statement = statement.join(
                    documents_indications,
                    documents_indications.indication_id == models.Indications.id,
                )
                joined_tables.add(documents_indications)
                statement = statement.join(
                    models.Documents,
                    models.Documents.id == documents_indications.document_id,
                )
                joined_tables.add(models.Documents)
        else:
            raise ValueError(
                f"Unsupported base table for Documents.perform_joins: {base_table}.",
            )

        if document_values:
            statement = statement.where(models.Documents.id.in_(document_values))

        statement, joined_tables = Agents.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=models.Documents,
            joined_tables=joined_tables,
        )
        return statement, joined_tables


class FunctionConsequences(BaseHandler):
    """Handler for the FunctionConsequences entity. No query parameter filters."""

    entity = "function_consequences"
    model = models.FunctionConsequences


class Genes(BaseHandler):
    """Handler for the Genes entity."""

    entity = "genes"
    model = models.Genes

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: Parameters,
        base_table: type[models.Base] | None = None,
        joined_tables: set[type[models.Base]] | None = None,
    ) -> tuple[sqlalchemy.Select, set[type[models.Base]]]:
        """
        Filters by `gene` (name).

        When `base_table` is Biomarkers, Propositions, or Statements, joins to
        Genes through AssociationBiomarkersAndGenes (Biomarkers must already be
        joined into the statement).

        See BaseHandler.perform_joins for the parameters and return value.
        """
        base_table = base_table or models.Genes
        joined_tables = joined_tables if joined_tables is not None else set()
        if not parameters:
            return statement, joined_tables

        gene_values = parameters.get("gene")
        if not gene_values:
            return statement, joined_tables

        if base_table in (models.Biomarkers, models.Propositions, models.Statements):
            biomarkers_genes = models.AssociationBiomarkersAndGenes
            if models.Genes not in joined_tables:
                statement = statement.join(
                    biomarkers_genes,
                    biomarkers_genes.biomarker_id == models.Biomarkers.id,
                )
                joined_tables.add(biomarkers_genes)
                statement = statement.join(
                    models.Genes,
                    models.Genes.id == biomarkers_genes.gene_id,
                )
                joined_tables.add(models.Genes)
        elif base_table != models.Genes:
            raise ValueError(
                f"Unsupported base table for Genes.perform_joins: {base_table}.",
            )

        statement = statement.where(models.Genes.name.in_(gene_values))
        return statement, joined_tables


class Indications(BaseHandler):
    """Handler for the Indications entity. Only Approved and Accelerated indications are returned by default."""

    entity = "indications"
    model = models.Indications

    @classmethod
    def construct_base_query(cls, include_deprecated: bool = False) -> sqlalchemy.Select:
        """
        Builds the base statement selecting Indications ids, excluding Superseded and Withdrawn indications unless `include_deprecated` is true.

        Args:
            include_deprecated (bool): If true, also select Superseded and Withdrawn indications.

        Returns:
            sqlalchemy.Select: A statement selecting the ids of Approved and Accelerated indications, or of all indications if `include_deprecated`.
        """
        statement = super().construct_base_query()
        if include_deprecated:
            return statement
        return statement.where(cls.model.status.in_(("Approved", "Accelerated")))

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: Parameters,
        base_table: type[models.Base] | None = None,
        joined_tables: set[type[models.Base]] | None = None,
    ) -> tuple[sqlalchemy.Select, set[type[models.Base]]]:
        """
        Filters by `indication` (id): a direct `id` match against Indications
        itself, or against `Statements.indication_id` (a plain foreign key, so no
        join is needed) when `base_table` is Statements.

        When `base_table` is Indications, also delegates `document`/`agent`/
        `agent_id` to Documents.perform_joins. (When `base_table` is Statements,
        those are applied separately, directly from Statements.perform_joins.)

        See BaseHandler.perform_joins for the parameters and return value.
        """
        base_table = base_table or models.Indications
        joined_tables = joined_tables if joined_tables is not None else set()
        if not parameters:
            return statement, joined_tables

        indication_values = parameters.get("indication")

        if base_table == models.Indications:
            if indication_values:
                statement = statement.where(
                    models.Indications.id.in_(indication_values),
                )
            statement, joined_tables = Documents.perform_joins(
                statement=statement,
                parameters=parameters,
                base_table=base_table,
                joined_tables=joined_tables,
            )
        elif base_table == models.Statements:
            if indication_values:
                statement = statement.where(
                    models.Statements.indication_id.in_(indication_values),
                )
        else:
            raise ValueError(
                f"Unsupported base table for Indications.perform_joins: {base_table}.",
            )

        return statement, joined_tables


class Mappings(BaseHandler):
    """Handler for the Mappings entity. No query parameter filters."""

    entity = "mappings"
    model = models.Mappings


class Propositions(BaseHandler):
    """Handler for the Propositions entity."""

    entity = "propositions"
    model = models.Propositions

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: Parameters,
        base_table: type[models.Base] | None = None,
        joined_tables: set[type[models.Base]] | None = None,
    ) -> tuple[sqlalchemy.Select, set[type[models.Base]]]:
        """
        Filters by `proposition_id`, and delegates `biomarker`/`biomarker_type`/
        `gene`, `disease`, and `therapy`/`therapy_type` to Biomarkers, Diseases, and
        Therapies respectively.

        When `base_table` is Statements, joins Propositions in first, via
        `Statements.proposition_id`.

        See BaseHandler.perform_joins for the parameters and return value.
        """
        base_table = base_table or models.Propositions
        joined_tables = joined_tables if joined_tables is not None else set()
        if not parameters:
            return statement, joined_tables

        if base_table == models.Statements:
            if models.Propositions not in joined_tables:
                statement = statement.join(
                    models.Propositions,
                    models.Statements.proposition_id == models.Propositions.id,
                )
                joined_tables.add(models.Propositions)
        elif base_table != models.Propositions:
            raise ValueError(
                f"Unsupported base table for Propositions.perform_joins: {base_table}.",
            )

        proposition_values = parameters.get("proposition_id")
        if proposition_values:
            statement = statement.where(models.Propositions.id.in_(proposition_values))

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


class Searches(Propositions):
    """
    Handler for `/search`: Propositions with per-proposition Statement aggregates
    attached.

    Which propositions match is decided the same way as `/propositions`
    (`Propositions.perform_joins`, inherited). The aggregates are computed directly
    from Statements, optionally narrowed by `document`, `indication`, and
    `agent_id`; those parameters do not affect which propositions are returned.
    """

    entity = "propositions"

    @classmethod
    def aggregate_statements_by_proposition_ids(
        cls,
        session: sqlalchemy.orm.Session,
        proposition_ids: list[str],
        parameters: Parameters | None = None,
    ) -> dict[str, dict[str, typing.Any]]:
        """
        Computes statement counts by proposition id, overall and broken down by
        direction, document, agent, and strength.

        Args:
            session (sqlalchemy.orm.Session): The database session to query against.
            proposition_ids (list[str]): The proposition ids to aggregate over.
            parameters (Parameters | None): Optional `document`, `indication`, and
                `agent_id` filters narrowing which Statements are counted.

        Returns:
            dict[str, dict[str, typing.Any]]: One aggregates dict (see
            `empty_aggregates`) per proposition id.
        """
        if not proposition_ids:
            return {}

        base_query = cls.filtered_statements_query(
            session=session,
            proposition_ids=proposition_ids,
            parameters=parameters,
        )

        statement_counts = dict(
            base_query.with_entities(
                models.Statements.proposition_id,
                sqlalchemy.func.count(models.Statements.id),
            )
            .group_by(models.Statements.proposition_id)
            .all(),
        )

        by_direction: dict[str, list[dict[str, typing.Any]]] = {}
        for proposition_id, direction, count in (
            base_query.with_entities(
                models.Statements.proposition_id,
                models.Statements.direction,
                sqlalchemy.func.count(models.Statements.id),
            )
            .group_by(models.Statements.proposition_id, models.Statements.direction)
            .all()
        ):
            by_direction.setdefault(proposition_id, []).append(
                {"direction": direction, "count": int(count)},
            )

        by_document: dict[str, list[dict[str, typing.Any]]] = {}
        for proposition_id, document_id, count in (
            base_query.with_entities(
                models.Statements.proposition_id,
                models.Documents.id,
                sqlalchemy.func.count(models.Statements.id),
            )
            .join(models.Statements.documents)
            .group_by(models.Statements.proposition_id, models.Documents.id)
            .all()
        ):
            by_document.setdefault(proposition_id, []).append(
                {"id": document_id, "count": int(count)},
            )

        by_agent: dict[str, list[dict[str, typing.Any]]] = {}
        for proposition_id, agent_id, count in (
            base_query.with_entities(
                models.Statements.proposition_id,
                models.Agents.id,
                sqlalchemy.func.count(models.Statements.id),
            )
            .join(models.Statements.documents)
            .join(models.Documents.agent)
            .group_by(models.Statements.proposition_id, models.Agents.id)
            .all()
        ):
            by_agent.setdefault(proposition_id, []).append(
                {"id": agent_id, "count": int(count)},
            )

        by_strength: dict[str, list[dict[str, typing.Any]]] = {}
        for proposition_id, strength_id, count in (
            base_query.with_entities(
                models.Statements.proposition_id,
                models.Statements.strength_id,
                sqlalchemy.func.count(models.Statements.id),
            )
            .group_by(models.Statements.proposition_id, models.Statements.strength_id)
            .all()
        ):
            by_strength.setdefault(proposition_id, []).append(
                {"id": strength_id, "count": int(count)},
            )

        return {
            proposition_id: {
                "statement_count": int(statement_counts.get(proposition_id, 0)),
                "by_direction": by_direction.get(proposition_id, []),
                "by_document": by_document.get(proposition_id, []),
                "by_agent": by_agent.get(proposition_id, []),
                "by_strength": by_strength.get(proposition_id, []),
            }
            for proposition_id in proposition_ids
        }

    @staticmethod
    def empty_aggregates() -> dict[str, typing.Any]:
        """
        The aggregates value for a proposition with no matching Statements.

        Returns:
            dict[str, typing.Any]: An aggregates dict with zero counts and empty breakdowns.
        """
        return {
            "statement_count": 0,
            "by_direction": [],
            "by_document": [],
            "by_agent": [],
            "by_strength": [],
        }

    @staticmethod
    def filtered_statements_query(
        session: sqlalchemy.orm.Session,
        proposition_ids: list[str],
        parameters: Parameters | None,
    ) -> sqlalchemy.orm.Query:
        """
        Builds the Statements query aggregates are computed from, restricted to
        Active statements.

        Args:
            session (sqlalchemy.orm.Session): The database session to query against.
            proposition_ids (list[str]): The proposition ids to restrict to.
            parameters (Parameters | None): Optional `document`, `indication`, and
                `agent_id` filters.

        Returns:
            sqlalchemy.orm.Query: The filtered Statements query.
        """
        query = session.query(models.Statements).filter(
            models.Statements.proposition_id.in_(proposition_ids),
            models.Statements.status == "Active",
        )

        document_ids = (parameters or {}).get("document")
        indication_ids = (parameters or {}).get("indication")
        agent_ids = (parameters or {}).get("agent_id")

        if document_ids or agent_ids:
            query = query.join(models.Statements.documents)
        if document_ids:
            query = query.filter(models.Documents.id.in_(document_ids))
        if indication_ids:
            query = query.filter(models.Statements.indication_id.in_(indication_ids))
        if agent_ids:
            query = query.join(models.Documents.agent).filter(
                models.Agents.id.in_(agent_ids),
            )

        return query

    @classmethod
    def serialize(
        cls,
        ids: set[str],
        cache: dereferenced.Cache,
        session: sqlalchemy.orm.Session | None = None,
        parameters: Parameters | None = None,
    ) -> list[dict]:
        """
        Looks up matching propositions and attaches per-proposition aggregates.

        Args:
            ids (set[str]): The matching proposition ids.
            cache (dereferenced.Cache): The application's dereferenced cache.
            session (sqlalchemy.orm.Session | None): The database session to
                compute aggregates against; if None, every record gets
                `empty_aggregates()`.
            parameters (Parameters | None): Optional `document`/`indication`/
                `agent_id` filters narrowing the aggregates.

        Returns:
            list[dict]: Shallow copies of the matching proposition records (the
            cache itself is never mutated), each with an `aggregates` key added.
        """
        records = super().serialize(ids=ids, cache=cache)
        if session is None or not records:
            return [
                {**record, "aggregates": cls.empty_aggregates()} for record in records
            ]

        aggregates = cls.aggregate_statements_by_proposition_ids(
            session=session,
            proposition_ids=[record["id"] for record in records],
            parameters=parameters,
        )
        return [
            {
                **record,
                "aggregates": aggregates.get(record["id"], cls.empty_aggregates()),
            }
            for record in records
        ]


class SequenceLocations(BaseHandler):
    """Handler for the SequenceLocations entity. No query parameter filters."""

    entity = "sequence_locations"
    model = models.SequenceLocations


class SequenceReferences(BaseHandler):
    """Handler for the SequenceReferences entity. No query parameter filters."""

    entity = "sequence_references"
    model = models.SequenceReferences


class Statements(BaseHandler):
    """Handler for the Statements entity. Only Active statements are returned by default."""

    entity = "statements"
    model = models.Statements

    @classmethod
    def construct_base_query(cls, include_deprecated: bool = False) -> sqlalchemy.Select:
        """
        Builds the base statement selecting Statements ids, excluding Superseded
        and Deprecated statements unless `include_deprecated` is true.

        Args:
            include_deprecated (bool): If true, also select Superseded and Deprecated statements.

        Returns:
            sqlalchemy.Select: A statement selecting the ids of Active statements, or of all statements if `include_deprecated`.
        """
        statement = super().construct_base_query()
        if include_deprecated:
            return statement
        return statement.where(cls.model.status == "Active")

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: Parameters,
        base_table: type[models.Base] | None = None,
        joined_tables: set[type[models.Base]] | None = None,
    ) -> tuple[sqlalchemy.Select, set[type[models.Base]]]:
        """
        Applies every cross-entity filter by delegating, in turn, to Propositions
        (which itself covers biomarker/gene/disease/therapy), Documents, Indications,
        and Contributions.

        See BaseHandler.perform_joins for the parameters and return value.
        """
        base_table = base_table or models.Statements
        joined_tables = joined_tables if joined_tables is not None else set()
        if not parameters:
            return statement, joined_tables

        statement, joined_tables = Propositions.perform_joins(
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
        statement, joined_tables = Contributions.perform_joins(
            statement=statement,
            parameters=parameters,
            base_table=base_table,
            joined_tables=joined_tables,
        )
        return statement, joined_tables


class Strengths(BaseHandler):
    """Handler for the Strengths entity. No query parameter filters."""

    entity = "strengths"
    model = models.Strengths


class Therapies(BaseHandler):
    """Handler for the Therapies entity."""

    entity = "therapies"
    model = models.Therapies

    @staticmethod
    def perform_joins(
        statement: sqlalchemy.Select,
        parameters: Parameters,
        base_table: type[models.Base] | None = None,
        joined_tables: set[type[models.Base]] | None = None,
    ) -> tuple[sqlalchemy.Select, set[type[models.Base]]]:
        """
        Filters by `therapy` (name) and `therapy_type`.

        When `base_table` is Propositions or Statements, a proposition's therapy
        may be set directly (`Propositions.therapy_id`) or through a therapy group
        (`Propositions.therapy_group_id`), so both paths are outer-joined and
        matched with `OR`.

        See BaseHandler.perform_joins for the parameters and return value.
        """
        base_table = base_table or models.Therapies
        joined_tables = joined_tables if joined_tables is not None else set()
        if not parameters:
            return statement, joined_tables

        therapy_values = parameters.get("therapy")
        therapy_type_values = parameters.get("therapy_type")
        if not (therapy_values or therapy_type_values):
            return statement, joined_tables

        if base_table == models.Therapies:
            conditions = []
            if therapy_values:
                conditions.append(models.Therapies.name.in_(therapy_values))
            if therapy_type_values:
                conditions.append(
                    models.Therapies.therapy_type.in_(therapy_type_values),
                )
            statement = statement.where(sqlalchemy.and_(*conditions))
            return statement, joined_tables

        if base_table not in (models.Propositions, models.Statements):
            raise ValueError(
                f"Unsupported base table for Therapies.perform_joins: {base_table}.",
            )

        direct = sqlalchemy.orm.aliased(models.Therapies)
        indirect = sqlalchemy.orm.aliased(models.Therapies)
        if models.Therapies not in joined_tables:
            therapies_therapy_groups = models.AssociationTherapiesAndTherapyGroups
            statement = statement.outerjoin(
                direct,
                direct.id == models.Propositions.therapy_id,
            )
            statement = statement.outerjoin(
                models.TherapyGroups,
                models.TherapyGroups.id == models.Propositions.therapy_group_id,
            )
            statement = statement.outerjoin(
                therapies_therapy_groups,
                therapies_therapy_groups.therapy_group_id == models.TherapyGroups.id,
            )
            statement = statement.outerjoin(
                indirect,
                indirect.id == therapies_therapy_groups.therapy_id,
            )
            joined_tables.add(models.Therapies)
            joined_tables.add(models.TherapyGroups)
            joined_tables.add(therapies_therapy_groups)

        conditions = []
        if therapy_values:
            conditions.append(
                sqlalchemy.or_(
                    direct.name.in_(therapy_values),
                    indirect.name.in_(therapy_values),
                ),
            )
        if therapy_type_values:
            conditions.append(
                sqlalchemy.or_(
                    direct.therapy_type.in_(therapy_type_values),
                    indirect.therapy_type.in_(therapy_type_values),
                ),
            )
        statement = statement.where(sqlalchemy.and_(*conditions))
        return statement, joined_tables


class TherapyGroups(BaseHandler):
    """Handler for the TherapyGroups entity. No query parameter filters."""

    entity = "therapy_groups"
    model = models.TherapyGroups
